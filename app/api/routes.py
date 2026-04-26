"""HTTP endpoints. The chart engine is exposed at /chart/calculate; the profile and
transit-alert endpoints live at /profiles."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.ephemeris_engine import calculate_all_charts
from app.models.domain import NatalChart, TransitAlert, UserProfile
from app.models.schemas import (
    BirthDataInput,
    ChartResponse,
    TransitAlertResponse,
    UserProfileCreate,
    UserProfileResponse,
)

# Mounted at /chart in main.py (preserves Phase 1 contract).
chart_router = APIRouter()

# Mounted at root in main.py.
profile_router = APIRouter()


@chart_router.post("/calculate", response_model=ChartResponse)
async def calculate_chart(birth_data: BirthDataInput) -> dict:
    """Calculate D1, D9, D10 charts and current Mahadasha. Stateless; does not persist."""
    # calculate_all_charts is sync CPU-bound (Swiss Ephemeris C calls). Running
    # it in the request task would block the event loop and starve other
    # requests + the daemon. asyncio.to_thread offloads to the default executor.
    return await asyncio.to_thread(
        calculate_all_charts,
        year=birth_data.year,
        month=birth_data.month,
        day=birth_data.day,
        hour=birth_data.hour,
        minute=birth_data.minute,
        tz_offset=birth_data.tz_offset,
    )


def _build_natal_chart(user_id: int, chart: dict) -> NatalChart:
    """Map the engine's chart dict onto a NatalChart row.

    Storing both the longitude and the whole-sign index per graha lets the daemon
    do whole-sign aspect lookups without recomputing int(lon // 30) per tick.
    """
    d1 = chart["d1"]
    return NatalChart(
        user_id=user_id,
        birth_jd=chart["birth_jd"],
        birth_moon_longitude=d1["Moon"]["longitude"],
        sun_lon=d1["Sun"]["longitude"],         sun_sign=d1["Sun"]["sign"],
        moon_lon=d1["Moon"]["longitude"],       moon_sign=d1["Moon"]["sign"],
        mars_lon=d1["Mars"]["longitude"],       mars_sign=d1["Mars"]["sign"],
        mercury_lon=d1["Mercury"]["longitude"], mercury_sign=d1["Mercury"]["sign"],
        jupiter_lon=d1["Jupiter"]["longitude"], jupiter_sign=d1["Jupiter"]["sign"],
        venus_lon=d1["Venus"]["longitude"],     venus_sign=d1["Venus"]["sign"],
        saturn_lon=d1["Saturn"]["longitude"],   saturn_sign=d1["Saturn"]["sign"],
        rahu_lon=d1["Rahu"]["longitude"],       rahu_sign=d1["Rahu"]["sign"],
        ketu_lon=d1["Ketu"]["longitude"],       ketu_sign=d1["Ketu"]["sign"],
        full_chart_json=chart,
    )


@profile_router.post(
    "/profiles",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    payload: UserProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Persist a user, calculate their natal chart once, and store both atomically."""
    bd = payload.birth_data
    chart = await asyncio.to_thread(
        calculate_all_charts,
        year=bd.year, month=bd.month, day=bd.day,
        hour=bd.hour, minute=bd.minute, tz_offset=bd.tz_offset,
    )

    user = UserProfile(
        name=payload.name,
        birth_year=bd.year, birth_month=bd.month, birth_day=bd.day,
        birth_hour=bd.hour, birth_minute=bd.minute,
        latitude=bd.latitude, longitude=bd.longitude, tz_offset=bd.tz_offset,
    )
    db.add(user)
    await db.flush()  # populate user.id without committing

    db.add(_build_natal_chart(user.id, chart))
    await db.commit()
    await db.refresh(user)

    return UserProfileResponse(
        id=user.id,
        name=user.name,
        created_at=user.created_at,
        chart=ChartResponse.model_validate(chart),
    )


@profile_router.get(
    "/profiles/{user_id}/transits",
    response_model=list[TransitAlertResponse],
)
async def list_transits(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[TransitAlert]:
    """Return active transit alerts for a user, newest first."""
    user = await db.get(UserProfile, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    stmt = (
        select(TransitAlert)
        .where(TransitAlert.user_id == user_id, TransitAlert.is_active.is_(True))
        .order_by(TransitAlert.exact_date.desc())
        .options(selectinload(TransitAlert.user))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
