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


class NakshatraInfo(BaseModel):
    index: int                       # 0..26
    name: str
    pada: int                        # 1..4
    lord: str                        # Vimshottari nakshatra lord
    longitude_in_nakshatra: float    # 0..13.333


class PlanetaryPosition(BaseModel):
    name: str
    longitude: float
    sign: int
    sign_name: str
    degree_in_sign: float
    is_retrograde: bool
    # House (1..12) under whole-sign Vedic counting, computed only when a
    # geographic anchor (lat/lon) is supplied. Divisional charts (D9, D10)
    # leave this as None - the ascendant is a D1-frame concept.
    house: int | None = None
    # Nakshatra annotation, populated for D1 entries only (divisional charts
    # don't carry it). Optional so existing pre-Phase-3 callers don't break.
    nakshatra: NakshatraInfo | None = None


class Ascendant(BaseModel):
    longitude: float
    sign: int
    sign_name: str
    degree_in_sign: float


class AntardashaPeriod(BaseModel):
    maha_lord: str
    antar_lord: str
    start_date: str       # ISO YYYY-MM-DD
    end_date: str
    start_jd: float
    end_jd: float
    duration_years: float


class Yoga(BaseModel):
    """Chart-based yoga (Pancha Mahapurusha / Gajakesari / Budha-Aditya).
    Distinct from the panchanga yoga (Sun+Moon harmonic) below."""
    name: str
    type: str
    planets_involved: list[str]
    description: str


class TithiInfo(BaseModel):
    index: int            # 0..29
    name: str
    paksha: str           # "Shukla" | "Krishna"


class KaranaInfo(BaseModel):
    index: int            # 0..59
    name: str


class PanchangaYogaInfo(BaseModel):
    """Panchanga's yoga (Sun+Moon harmonic). NOT the chart yoga schema above."""
    index: int            # 0..26
    name: str


class VaraInfo(BaseModel):
    index: int            # 0..6
    name: str


class Panchanga(BaseModel):
    tithi: TithiInfo
    karana: KaranaInfo
    yoga: PanchangaYogaInfo
    vara: VaraInfo
    nakshatra: NakshatraInfo


class DashaPeriod(BaseModel):
    mahadasha_lord: str
    start_date: str = Field(..., description="ISO YYYY-MM-DD start of current Mahadasha")
    end_date: str = Field(..., description="ISO YYYY-MM-DD end of current Mahadasha")
    time_elapsed_years: float
    total_duration_years: float


class ChartResponse(BaseModel):
    jd: float
    ayanamsa: float
    # Ascendant is None for transit-style charts where lat/lon weren't provided
    # (the daemon's "where are the planets right now" call). It's always set
    # for /chart/calculate and /profiles which require BirthDataInput.
    ascendant: Ascendant | None = None
    d1: dict[str, PlanetaryPosition]
    d9: dict[str, PlanetaryPosition]
    d10: dict[str, PlanetaryPosition]
    current_mahadasha: DashaPeriod
    # Phase 3 feature payloads. All defaulted so older callers and the
    # daemon's transit-only call (which still produces a chart-shaped dict
    # with these populated) don't break.
    antardashas: list[AntardashaPeriod] = Field(default_factory=list)
    divisional_charts: dict[str, dict[str, PlanetaryPosition]] = Field(default_factory=dict)
    panchanga: Panchanga | None = None
    yogas: list[Yoga] = Field(default_factory=list)


class UserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    birth_data: BirthDataInput


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: dt.datetime
    chart: ChartResponse | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str | None = None
    picture: str | None = None
    created_at: dt.datetime
    last_login_at: dt.datetime


class TokenResponse(BaseModel):
    """Returned by /auth/google/callback after successful login."""
    access_token: str
    token_type: str = "bearer"
    account: AccountResponse


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
