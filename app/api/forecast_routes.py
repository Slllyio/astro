"""HTTP endpoints for the multi-day Mundane Forecast + Almanac (Phase 2).

Two thin routers over ``app.medini.mundane.range_forecast``:

  - ``forecast_router`` (``/medini/forecast``): forward-looking. Scans the next
    N days for ingresses, stations, and conjunction onsets.
  - ``almanac_router`` (``/medini/almanac``): backward-looking. Scans the
    previous N days for the same event classes.

Both are public (no auth) like the rest of the Geo-Astrological Engine. The
underlying scan is pure compute (no IO/DB), so these endpoints are stateless
and cheap. ``days`` is bounded to keep a single request's ephemeris work
predictable.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.medini.mundane import (
    DEFAULT_CONJUNCTION_ORB,
    current_jd_ut,
    range_forecast,
)

forecast_router = APIRouter(prefix="/medini/forecast", tags=["Mundane Forecast"])
almanac_router = APIRouter(prefix="/medini/almanac", tags=["Mundane Almanac"])

# Bound the scan window so one request can't ask for an unbounded ephemeris
# walk. 90 days ≈ 820 planet evaluations + refinements — still sub-second.
_MAX_DAYS = 90
_DEFAULT_DAYS = 14


@forecast_router.get("")
async def forecast(
    days: int = Query(_DEFAULT_DAYS, ge=1, le=_MAX_DAYS, description="Days to look ahead"),
    jd: float | None = Query(None, description="Start moment as UT Julian Day; defaults to now"),
    conjunction_orb: float = Query(
        DEFAULT_CONJUNCTION_ORB, gt=0, le=15, description="Conjunction orb in degrees",
    ),
) -> dict:
    """Forward Mundane Forecast: events over the next ``days`` days.

    Returns ingresses, stations, and conjunction onsets between now (or the
    supplied ``jd``) and ``days`` days later, each tagged ``UPCOMING`` and
    mapped to the Kurma region it activates.
    """
    start = jd if jd is not None else current_jd_ut()
    return range_forecast(
        start, start + days, direction="UPCOMING", conjunction_orb=conjunction_orb,
    )


@almanac_router.get("")
async def almanac(
    days: int = Query(_DEFAULT_DAYS, ge=1, le=_MAX_DAYS, description="Days to look back"),
    jd: float | None = Query(None, description="End moment as UT Julian Day; defaults to now"),
    conjunction_orb: float = Query(
        DEFAULT_CONJUNCTION_ORB, gt=0, le=15, description="Conjunction orb in degrees",
    ),
) -> dict:
    """Backward Mundane Almanac: events over the previous ``days`` days.

    Same event classes as the forecast, scanning from ``days`` days ago up to
    now (or the supplied ``jd``), each tagged ``PAST``.
    """
    end = jd if jd is not None else current_jd_ut()
    return range_forecast(
        end - days, end, direction="PAST", conjunction_orb=conjunction_orb,
    )
