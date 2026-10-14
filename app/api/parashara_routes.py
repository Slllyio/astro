"""HTTP endpoints for the Parashara (BPHS) engine — engine #2's serving surface.

Until now the parashara engine was reachable only by direct import; this exposes it over HTTP,
mirroring the request-model + worker-thread shape of `reading_routes.py`. The reading is CPU-bound
(ephemeris + full six-fold Shadbala + all doctrine grids), so each call is offloaded to a worker
thread to keep the event loop responsive.

Endpoints:
  POST /parashara/reading            structured JSON reading (every computed section, machine-readable)
  POST /parashara/reading/markdown   the same reading as the cited markdown report
  POST /parashara/reading/html       the same reading as a standalone HTML document
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.models.schemas import BirthDataInput
from app.parashara.chart.cast import cast
from app.parashara.reading import ParasharaReading, read
from app.parashara.render import to_markdown
from app.parashara.render_json import to_json_dict

logger = logging.getLogger(__name__)

parashara_router = APIRouter(prefix="/parashara", tags=["Parashara (BPHS engine)"])


def _build_reading(b: BirthDataInput) -> ParasharaReading:
    """Cast the birth and assemble the full cited reading (CPU-bound; run in a worker thread)."""
    chart = cast(year=b.year, month=b.month, day=b.day, hour=b.hour, minute=b.minute,
                 tz_offset=b.tz_offset, latitude=b.latitude, longitude=b.longitude)
    return read(chart)


@parashara_router.post("/reading")
async def post_reading(birth: BirthDataInput) -> dict:
    """The full BPHS reading as structured JSON — every computed section, citations included."""
    reading = await asyncio.to_thread(_build_reading, birth)
    return to_json_dict(reading)


@parashara_router.post("/reading/markdown", response_class=PlainTextResponse)
async def post_reading_markdown(birth: BirthDataInput) -> str:
    """The full BPHS reading as the cited markdown report."""
    reading = await asyncio.to_thread(_build_reading, birth)
    return to_markdown(reading)


@parashara_router.post("/reading/html", response_class=HTMLResponse)
async def post_reading_html(birth: BirthDataInput) -> str:
    """The full BPHS reading as a standalone HTML document."""
    from app.parashara.report_html import to_html
    reading = await asyncio.to_thread(_build_reading, birth)
    return to_html(reading)
