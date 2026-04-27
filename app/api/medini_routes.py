"""HTTP endpoints for Tab 3 (Project Medini-Intelligence: the Geo-Astrological Engine).

Public — no auth required. The Kurma Chakra grid is universal/non-personal,
and v1 personalized astrocartography (POST /medini/cartography) accepts birth
data without auth for demo simplicity. Future versions can auth-gate the
personalized endpoints; the /regions and /kurma-widget endpoints stay open.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from app.medini.kurma_chakra import (
    ALL_REGIONS,
    all_nakshatra_regions,
    all_regions_geojson,
    info_for_region,
    region_for_coordinates,
)

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
