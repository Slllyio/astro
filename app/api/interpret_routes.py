"""HTTP endpoints for the LLM narrative layer.

Two surfaces:
  POST /interpret/chart            → single-paragraph summary of the whole chart
  POST /interpret/chart/{section}  → section drill-down (ascendant, mahadasha, etc.)

Both accept a BirthDataInput, compute the chart via the same pipeline as
/chart/calculate, then run the interpreter. When OLLAMA_ENABLED is False
(default), the response is rendered from the deterministic template — so
the endpoints work out of the box on a fresh checkout.

The `section` path parameter is constrained to ALLOWED_SECTIONS at the
route layer; an unknown section returns 400 before any chart computation
fires (cheap rejection).
"""
from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from app.core.ephemeris_engine import calculate_all_charts
from app.llm.interpreter import Interpretation, interpret_chart
from app.llm.templates import ALLOWED_SECTIONS
from app.models.schemas import BirthDataInput

interpret_router = APIRouter(prefix="/interpret", tags=["LLM Narrative"])

# Templates dir lives at app/templates/; resolve relative to this file so
# the path is stable regardless of uvicorn's CWD.
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def _interpretation_to_dict(interp: Interpretation) -> dict:
    """Pydantic-friendly dict — the dataclass-asdict path keeps the
    `source`/`model` metadata visible to clients."""
    return dataclasses.asdict(interp)


def _compute_chart_sync(birth_data: BirthDataInput) -> dict:
    """Sync helper kept separate so asyncio.to_thread can offload it."""
    return calculate_all_charts(
        year=birth_data.year, month=birth_data.month, day=birth_data.day,
        hour=birth_data.hour, minute=birth_data.minute,
        tz_offset=birth_data.tz_offset,
        latitude=birth_data.latitude, longitude=birth_data.longitude,
    )


@interpret_router.post("/chart")
async def interpret_chart_summary(birth_data: BirthDataInput) -> dict:
    """One-paragraph chart summary.

    Returns: {text, mode='summary', section=None, source: 'llm'|'fallback', model}.
    Source==fallback means OLLAMA_ENABLED was False or Ollama was unreachable;
    the response still contains a useful (factual) narrative.
    """
    chart = await asyncio.to_thread(_compute_chart_sync, birth_data)
    # interpret_chart is sync (httpx.post inside the LLM client). Offload so
    # we don't block the event loop while the LLM responds.
    interp = await asyncio.to_thread(interpret_chart, chart, mode="summary")
    return _interpretation_to_dict(interp)


@interpret_router.post("/chart/{section}")
async def interpret_chart_section(
    section: str,
    birth_data: BirthDataInput,
) -> dict:
    """Drill-down narrative for one section.

    Allowed sections: ascendant, mahadasha, yogas, panchanga, planetary,
    ashtakavarga. Anything else returns 400 with the allow-list in the body
    so the caller can correct without trial-and-error.
    """
    section_lower = section.strip().lower()
    if section_lower not in ALLOWED_SECTIONS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"unknown section {section!r}",
                "allowed_sections": sorted(ALLOWED_SECTIONS),
            },
        )

    chart = await asyncio.to_thread(_compute_chart_sync, birth_data)
    interp = await asyncio.to_thread(
        interpret_chart, chart, mode="section", section=section_lower,
    )
    return _interpretation_to_dict(interp)


@interpret_router.get("/sections")
async def list_sections() -> dict:
    """List the section names valid for /interpret/chart/{section}.

    Cheap discovery endpoint for frontends — no birth data required."""
    return {"sections": sorted(ALLOWED_SECTIONS)}


@interpret_router.get("/page", response_class=HTMLResponse)
async def interpret_page() -> HTMLResponse:
    """Standalone Interpret UI: birth-data form + summary/drill-down picker.

    Embedded as the 'Interpret' tab inside the unified shell at /. The page
    surfaces an LLM/Fallback badge so users can see at a glance whether
    Ollama is wired up; deterministic responses still arrive instantly."""
    html_path = _TEMPLATES_DIR / "interpret.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interpret template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
