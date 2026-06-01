"""HTTP endpoints for the per-chart doctrine reader (Round 10 pivot).

After Round-9 retired the population-statistics doctrine claim,
the per-chart reading is the natural next surface: take ONE chart,
let an LLM with RAG access produce a multi-section reading with
doctrine citations.

Endpoints:

  POST /medini/reading              JSON reading for a birth chart
  GET  /medini/reading/page         HTML form + reading viewer
"""
from __future__ import annotations

import asyncio
import dataclasses
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from app.core.ephemeris_engine import calculate_all_charts
from app.medini.services.chart_reader import Reading, read_chart
from app.medini.services.framework_reader import (
    read_chart_via_framework,
    reading_to_dict as framework_reading_to_dict,
)
from app.models.schemas import BirthDataInput

logger = logging.getLogger(__name__)

reading_router = APIRouter(
    prefix="/medini/reading",
    tags=["Chart Reader (Round 10)"],
)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "medini" / "templates"


def _reading_to_dict(r: Reading) -> dict:
    """Frozen dataclass → JSON-safe dict. Recursively unwraps nested
    dataclasses (sections + citations)."""
    return {
        "chart_summary": r.chart_summary,
        "sections": [
            {
                "title": s.title,
                "text": s.text,
                "citations": [dataclasses.asdict(c) for c in s.citations],
            }
            for s in r.sections
        ],
        "source": r.source,
        "model": r.model,
        "n_citations_total": r.n_citations_total,
    }


@reading_router.post("")
async def post_reading(birth_data: BirthDataInput) -> dict:
    """Synthesize a doctrine-grounded reading from a birth chart.

    The chart computation + RAG retrieval + LLM synthesis can take
    20-60s depending on (a) cold RAG-model load, (b) number of LLM
    calls (one per section, ~5 sections), (c) which LLM is configured.
    We offload to a worker thread so the event loop stays responsive.
    """
    def _compute_sync() -> Reading:
        chart = calculate_all_charts(
            year=birth_data.year, month=birth_data.month, day=birth_data.day,
            hour=birth_data.hour, minute=birth_data.minute,
            tz_offset=birth_data.tz_offset,
            latitude=birth_data.latitude, longitude=birth_data.longitude,
        )
        return read_chart(chart)

    try:
        reading = await asyncio.to_thread(_compute_sync)
    except Exception as exc:  # noqa: BLE001 - top of route, surface as 500
        logger.exception("chart reading failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"chart reading failed: {exc}",
        ) from exc
    return _reading_to_dict(reading)


@reading_router.post("/prashna")
async def post_prashna_reading(payload: dict) -> dict:
    """Prashna route — answer a natural-language question via the framework.

    Body: ``{"question": "...", "birth_data": {...BirthDataInput}}``.

    Returns the routed bhava + structured framework verdict for that bhava
    + matched keywords + confidence. The full framework Reading is also
    included so the UI can show context.
    """
    from app.core.prashna import route_question

    question = (payload.get("question") or "").strip()
    birth_payload = payload.get("birth_data") or {}
    if not question:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="question field required",
        )
    try:
        birth_data = BirthDataInput(**birth_payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"birth_data validation failed: {exc}",
        ) from exc

    def _compute_sync() -> dict:
        chart = calculate_all_charts(
            year=birth_data.year, month=birth_data.month, day=birth_data.day,
            hour=birth_data.hour, minute=birth_data.minute,
            tz_offset=birth_data.tz_offset,
            latitude=birth_data.latitude, longitude=birth_data.longitude,
        )
        reading = read_chart_via_framework(chart)
        match = route_question(question)
        bhava_claim = reading.bhava_claims.get(match.bhava)
        framework_dict = framework_reading_to_dict(reading)
        return {
            "question": question,
            "routed_bhava": match.bhava,
            "routing_confidence": match.confidence,
            "matched_keywords": list(match.matched_keywords),
            "candidates_considered": [
                {"bhava": b, "score": s} for b, s in match.candidates_considered
            ],
            "primary_claim": framework_dict["bhava_claims"][str(match.bhava)] if bhava_claim else None,
            "reading": framework_dict,
        }

    try:
        return await asyncio.to_thread(_compute_sync)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("prashna reading failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"prashna reading failed: {exc}",
        ) from exc


@reading_router.post("/framework")
async def post_framework_reading(birth_data: BirthDataInput) -> dict:
    """Astrologer's-lens framework reading (Phases 1-9, doctrine-faithful).

    Distinct from POST /medini/reading (RAG + LLM narrative) — this
    endpoint returns the STRUCTURED framework verdict per bhava with
    classical citations, no LLM call required. Fast (~50ms per chart).
    """
    def _compute_sync() -> dict:
        chart = calculate_all_charts(
            year=birth_data.year, month=birth_data.month, day=birth_data.day,
            hour=birth_data.hour, minute=birth_data.minute,
            tz_offset=birth_data.tz_offset,
            latitude=birth_data.latitude, longitude=birth_data.longitude,
        )
        reading = read_chart_via_framework(chart)
        return framework_reading_to_dict(reading)

    try:
        return await asyncio.to_thread(_compute_sync)
    except Exception as exc:  # noqa: BLE001
        logger.exception("framework reading failed")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"framework reading failed: {exc}",
        ) from exc


@reading_router.get("/page", response_class=HTMLResponse)
async def reading_page() -> HTMLResponse:
    """Birth-data form + rendered reading viewer."""
    html_path = _TEMPLATES_DIR / "reading.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reading template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
