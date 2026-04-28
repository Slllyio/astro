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
from app.medini.eclipses import upcoming_eclipses_payload
from app.medini.ml.predictor import (
    NoModelForTarget,
    list_available_targets,
    predict_for_chart,
    run_summary,
)
from app.medini.mundane import daily_mundane_forecast
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


@medini_router.get("/today")
async def today(jd: float | None = None) -> dict:
    """Daily mundane forecast: ingresses, stations, conjunctions, and
    Kurma regions activated by the current planetary positions.

    Optional `jd` query param lets a caller pin the forecast to a specific
    Julian Day (useful for historical analysis or deterministic testing).
    Default is "now in UT".
    """
    return daily_mundane_forecast(jd_now=jd)


@medini_router.get("/today/page", response_class=HTMLResponse)
async def today_page() -> HTMLResponse:
    """The cosmic-weather feed. Renders today's events list + a Kurma map
    where regions are color-graded by how many planets currently sit in
    nakshatras assigned to them."""
    html_path = _TEMPLATES_DIR / "today.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Today template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@medini_router.get("/eclipses")
async def eclipses(jd: float | None = None, count: int = 5) -> dict:
    """Upcoming solar + lunar eclipses, each tagged with the Kurma region
    it activates via the luminary's nakshatra. Solar eclipses also include
    the geographic point of greatest eclipse (lat/lon).

    `count` is per-family; the response merges them and sorts by date.
    Default `jd=None` means "starting from now in UT".
    """
    return upcoming_eclipses_payload(jd_now=jd, count=count)


@medini_router.get("/eclipses/page", response_class=HTMLResponse)
async def eclipses_page() -> HTMLResponse:
    """Eclipse Impact Mapper. Map shows the next 5 solar + 5 lunar
    eclipses; solar ones get pin markers at their greatest-eclipse
    coordinates. Sidebar feed lists upcoming eclipses with their nakshatra
    + Kurma region tag."""
    html_path = _TEMPLATES_DIR / "eclipses.html"
    if not html_path.exists():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Eclipses template missing at {html_path}",
        )
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@medini_router.get("/predict")
async def list_predict_targets() -> dict:
    """List every trained model available for prediction.

    The predict endpoint at POST /medini/predict/{target} requires a model
    trained for that target. This GET surface answers "which targets can I
    actually call?" without requiring filesystem access — useful for
    frontends that want to populate a dropdown of available targets.
    """
    runs = list_available_targets()
    return {
        "available_targets": [
            {
                "target": r.target,
                "trained_at": r.timestamp,
                "run": r.run_dir.name,
            }
            for r in runs
        ],
        "count": len(runs),
    }


@medini_router.get("/runs")
async def list_runs(top_n_features: int = 5) -> dict:
    """Detailed comparison view of every trained run.

    Unlike `/medini/predict` (which only lists target names), this returns
    the metrics + top features per run so a frontend can render a side-by-
    side comparison table. Cheap: reads CSV/JSON artifacts, doesn't load
    any model. `top_n_features` caps the per-run feature list (default 5).
    """
    runs = list_available_targets()
    return {
        "runs": [run_summary(r.run_dir, top_n_features=top_n_features) for r in runs],
        "count": len(runs),
    }


@medini_router.post("/predict/{target}")
async def predict_target(target: str, birth_data: BirthDataInput) -> dict:
    """Predict the probability of `target` for a birth chart.

    Loads the most recent trained model whose run-directory prefix matches
    `target` (case-insensitive, sanitized — "Politician" matches "politician_*").
    Computes the same Vedic Tensor features the trainer saw, aligns dtypes
    via the persisted feature_columns.json + category_levels.json, and
    returns:

      - probability: 0.0–1.0
      - top_contributors: top-N features by |SHAP value| with the chart's
        actual feature value alongside, so the response reads like a story
      - model: which run was used + its training timestamp

    Graceful no-model fallback: if no run matches the target, returns 404
    with `available_targets` in the body so the caller can pick a real one.
    Uses asyncio.to_thread because XGBoost predict + SHAP TreeExplainer
    are sync CPU-bound and would otherwise block the event loop.
    """
    try:
        result = await asyncio.to_thread(
            predict_for_chart,
            target,
            year=birth_data.year, month=birth_data.month, day=birth_data.day,
            hour=birth_data.hour, minute=birth_data.minute,
            tz_offset=birth_data.tz_offset,
            latitude=birth_data.latitude, longitude=birth_data.longitude,
        )
    except NoModelForTarget as exc:
        # 404 with the list of targets that DO have models, so the caller
        # can correct their request without round-tripping through GET /predict.
        runs = list_available_targets()
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={
                "error": str(exc),
                "available_targets": [r.target for r in runs],
                "hint": "GET /medini/predict to see all targets currently trained.",
            },
        ) from exc

    return result
