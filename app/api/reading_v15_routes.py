"""V1.5 Web UI for the deterministic kundli reading engine.

A minimal HTTP wrapper over `app.reading.proforma.compute`. Three routes:

    GET  /reading/v15/                — HTML chart-entry form
    POST /reading/v15/generate        — compute + render reading
    GET  /reading/v15/download/{id}   — stream the reading as JSON

The engine call itself is synchronous (cpu-bound ephemeris + python). We
offload it to a worker thread so the async event loop stays responsive when
multiple users hit the route concurrently.

In-memory cache for downloads is v1.5-scope only — v2 will persist the
reading to the existing SQLite/Postgres store so links survive a restart.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.reading.proforma import compute
from app.reading.schema import ChartInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reading/v15", tags=["reading-v15"])

# Module-level template dir so the path resolves regardless of cwd.
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

# In-memory cache for JSON downloads. Keyed by an 8-char uuid prefix; that's
# 16^8 = ~4B namespace, plenty for the v1.5 session-scope use case.
# v2 should move this into the existing DB so a restart doesn't drop links.
_READING_CACHE: dict[str, dict[str, Any]] = {}

# Hard cap to prevent unbounded memory growth in a long-running process.
# When exceeded we evict the oldest entry (insertion order via dict).
_CACHE_MAX_ENTRIES = 256


def _cache_put(reading_id: str, payload: dict[str, Any]) -> None:
    """Insert into the cache, evicting the oldest entry when at capacity."""
    if len(_READING_CACHE) >= _CACHE_MAX_ENTRIES:
        # dict preserves insertion order; pop the first (oldest) key.
        oldest_key = next(iter(_READING_CACHE))
        _READING_CACHE.pop(oldest_key, None)
    _READING_CACHE[reading_id] = payload


def _form_data(
    dob: str, time: str, tz: str, lat: float | str, lon: float | str, enrich: bool
) -> dict[str, Any]:
    """Repack form values for re-rendering after a validation error."""
    return {
        "dob": dob,
        "time": time,
        "tz": tz,
        "lat": lat,
        "lon": lon,
        "enrich": enrich,
    }


def _first_error_message(exc: ValidationError) -> str:
    """Extract a human-readable first-error message from a Pydantic error."""
    errors = exc.errors()
    if not errors:
        return "Invalid input."
    err = errors[0]
    loc = ".".join(str(x) for x in err.get("loc", ()))
    msg = err.get("msg", "invalid value")
    return f"{loc}: {msg}" if loc else msg


@router.get("/", response_class=HTMLResponse)
async def reading_form(request: Request) -> HTMLResponse:
    """Render the chart-entry form."""
    return templates.TemplateResponse(
        request,
        "reading_v15_form.html",
        {"form_data": None, "error": None},
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_reading(
    request: Request,
    dob: Annotated[str, Form()],
    time: Annotated[str, Form()],
    tz: Annotated[str, Form()],
    lat: Annotated[float, Form()],
    lon: Annotated[float, Form()],
    enrich: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    """Validate the form, run the engine, render the reading view.

    Validation errors render the form with an error banner (200 OK with the
    form re-rendered; the user keeps their typed values). Engine crashes
    do the same with a 500-class banner; we never leak a Python traceback
    to the browser.
    """
    try:
        chart_input = ChartInput(dob=dob, time=time, tz=tz, lat=lat, lon=lon)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request,
            "reading_v15_form.html",
            {
                "form_data": _form_data(dob, time, tz, lat, lon, enrich),
                "error": f"Invalid input — {_first_error_message(exc)}",
            },
        )

    try:
        # compute() is synchronous + cpu-bound; offload to a thread so we
        # don't pin the event loop while ephemeris crunches.
        reading = await asyncio.to_thread(compute, chart_input, enrich)
    except Exception as exc:  # noqa: BLE001 — top of route; surface friendly
        logger.exception("reading engine failed for dob=%s time=%s", dob, time)
        return templates.TemplateResponse(
            request,
            "reading_v15_form.html",
            {
                "form_data": _form_data(dob, time, tz, lat, lon, enrich),
                "error": f"Engine failed: {type(exc).__name__}: {exc}",
            },
        )

    reading_id = uuid.uuid4().hex[:8]
    _cache_put(reading_id, reading)

    return templates.TemplateResponse(
        request,
        "reading_v15_view.html",
        {
            "reading": reading,
            "reading_id": reading_id,
            "input": chart_input.model_dump(),
        },
    )


@router.get("/download/{reading_id}", response_class=JSONResponse)
async def download_reading_json(reading_id: str) -> JSONResponse:
    """Stream a previously-generated reading as a JSON download.

    Returns 404 if the id isn't in the cache (process restarted, cache
    evicted, or bad id). Content-Disposition triggers a browser download.
    """
    reading = _READING_CACHE.get(reading_id)
    if reading is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading expired or not found. Please regenerate.",
        )
    return JSONResponse(
        content=reading,
        headers={
            "Content-Disposition": f"attachment; filename=kundli_{reading_id}.json",
        },
    )
