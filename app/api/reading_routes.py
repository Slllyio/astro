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
