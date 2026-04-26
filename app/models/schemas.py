"""Pydantic schemas for request/response payloads."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class BirthDataInput(BaseModel):
    # Year bound: Swiss Ephemeris is accurate over a far wider range, but
    # 1800-2100 is plenty for a Vedic-astrology user base and bounds the
    # CPU work an unauthenticated POST can trigger.
    year: int = Field(..., ge=1800, le=2100, description="Birth year (1800-2100)")
    month: int = Field(..., ge=1, le=12, description="Birth month (1-12)")
    day: int = Field(..., ge=1, le=31, description="Birth day (1-31)")
    hour: int = Field(..., ge=0, le=23, description="Birth hour (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Birth minute (0-59)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    # tz_offset: Earth's true range is approx [-12, +14]; clamp here to stop
    # NaN/inf values from poisoning the Julian Day calc.
    tz_offset: float = Field(..., ge=-12.0, le=14.0, description="Timezone offset from UTC (e.g. 5.5 for IST)")


class PlanetaryPosition(BaseModel):
    name: str
    longitude: float
    sign: int
    sign_name: str
    degree_in_sign: float
    is_retrograde: bool


class DashaPeriod(BaseModel):
    mahadasha_lord: str
    start_date: str = Field(..., description="ISO YYYY-MM-DD start of current Mahadasha")
    end_date: str = Field(..., description="ISO YYYY-MM-DD end of current Mahadasha")
    time_elapsed_years: float
    total_duration_years: float


class ChartResponse(BaseModel):
    jd: float
    ayanamsa: float
    d1: dict[str, PlanetaryPosition]
    d9: dict[str, PlanetaryPosition]
    d10: dict[str, PlanetaryPosition]
    current_mahadasha: DashaPeriod


class UserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    birth_data: BirthDataInput


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: dt.datetime
    chart: ChartResponse | None = None


class TransitAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_type: str
    description: str
    transit_planet: str
    natal_planet: str
    is_exact: bool
    exact_date: dt.datetime
    is_active: bool
