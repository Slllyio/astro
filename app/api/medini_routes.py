"""HTTP endpoints for Tab 3 (Project Medini-Intelligence: the Geo-Astrological Engine).

Public — no auth required. The Kurma Chakra grid is universal/non-personal,
and v1 personalized astrocartography (POST /medini/cartography) accepts birth
data without auth for demo simplicity. Future versions can auth-gate the
personalized endpoints; the /regions and /kurma-widget endpoints stay open.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from app.core.ephemeris_engine import calculate_all_charts
from app.medini.astrocartography import compute_planetary_lines
from app.medini.kurma_chakra import (
    ALL_REGIONS,
    all_nakshatra_regions,
    all_regions_geojson,
    info_for_region,
    region_for_coordinates,
)
from app.models.schemas import BirthDataInput

medini_router = APIRouter(prefix="/medini", tags=["Geo-Astrological Engine"])

# Templates live alongside the medini module so the FastAPI app finds them
# regardless of which directory uvicorn is invoked from.
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "medini" / "templates"


@medini_router.get("/health")
async def health() -> dict:
    """Liveness check: confirms the Kurma data table loaded."""
    return {
        "status": "ok",
        "kurma_regions_loaded": len(ALL_REGIONS),
        "nakshatra_count": 27,
    }


@medini_router.get("/regions")
async def regions() -> dict:
    """Full Kurma Chakra grid as GeoJSON + metadata.

    Single source of truth for the geographic layer — consumed by both the
    educational widget and the personalized cartography map. Frontend
    Leaflet/Deck.gl renders the GeoJSON directly; the nakshatra_table is
    the per-nakshatra detail panel data; regions_summary is the legend.
    """
    return {
        "geojson": all_regions_geojson(),
        "nakshatra_table": all_nakshatra_regions(),
        "regions_summary": [
            {
                "region": r,
                "tattva": info_for_region(r).tattva,
                "region_planets": list(info_for_region(r).region_planets),
                "description": info_for_region(r).description,
            }
            for r in ALL_REGIONS
        ],
    }


@medini_router.get("/region-for")
async def region_for(latitude: float, longitude: float) -> dict:
    """Look up which Kurma region a lat/lon falls in.

    Convenience endpoint for clients that don't want to do the point-in-polygon
    locally. Returns the matching region plus its full metadata.
    """
    try:
        region = region_for_coordinates(latitude, longitude)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    info = info_for_region(region)
    return {
        "input": {"latitude": latitude, "longitude": longitude},
        "region": region,
        "tattva": info.tattva,
        "region_planets": list(info.region_planets),
        "nakshatras": list(info.nakshatras),
        "description": info.description,
    }


@medini_router.get("/kurma-widget", response_class=HTMLResponse)
async def kurma_widget() -> HTMLResponse:
    """Standalone educational page: visualize the 9 Kurma regions on a world
    map (Leaflet + OpenStreetMap). Click a region to inspect its astrological
    parameters. No birth chart, no auth required."""
    html_path = _TEMPLATES_DIR / "kurma_widget.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Widget template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@medini_router.post("/cartography")
async def cartography(birth_data: BirthDataInput) -> dict:
    """Compute personalized astrocartography lines for a birth chart.

    Returns the 4 angular lines (MC/IC/Asc/Desc) for each of the 9 grahas =
    36 lines total, plus the Kurma Chakra GeoJSON layer so the frontend
    renders both overlays from a single response.

    No auth in v1 — the calculation is stateless and doesn't expose any
    persisted user data. Could be rate-limited or auth-gated later.
    """
    # calculate_all_charts is sync CPU-bound; offload so we don't block
    # the event loop. Same pattern as POST /chart/calculate.
    chart = await asyncio.to_thread(
        calculate_all_charts,
        year=birth_data.year, month=birth_data.month, day=birth_data.day,
        hour=birth_data.hour, minute=birth_data.minute,
        tz_offset=birth_data.tz_offset,
        latitude=birth_data.latitude, longitude=birth_data.longitude,
    )
    lines = await asyncio.to_thread(compute_planetary_lines, chart["birth_jd"])

    return {
        "birth_jd": chart["birth_jd"],
        "ascendant": chart["ascendant"],
        "planetary_lines": lines,
        "kurma_geojson": all_regions_geojson(),
        "summary": {
            "line_count": len(lines),
            "planet_count": len({line["planet"] for line in lines}),
        },
    }


@medini_router.get("/cartography/page", response_class=HTMLResponse)
async def cartography_page() -> HTMLResponse:
    """Personalized astrocartography map. Frontend submits birth data via a
    form, fetches POST /medini/cartography, and overlays the planetary lines
    on top of the same Kurma Chakra layer used by the educational widget."""
    html_path = _TEMPLATES_DIR / "cartography.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cartography template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
