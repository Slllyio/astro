"""M2 — Transit engine adapter (Gochara).

Wraps Track B's ``app.core.gochara_engine.compute_gochara`` which has been
present in the codebase but never invoked by any integration adapter.

Provides:
- ``transit_signs_at(target_jd)`` — sidereal Lahiri sign per planet at JD
- ``transit_state_at(reading, target_jd=None)`` — full GocharaVerdict
  (per-bhava double-transit flags, Sade-Sati active, Saturn-from-Moon position)
- ``transit_at_now(reading)`` — convenience for current moment

Classical basis
---------------
- Lahiri ayanamsa locked per project (CLAUDE.md)
- Double-transit doctrine: BPHS Ch.36 (Phala) — an event fires when Jupiter
  AND Saturn simultaneously aspect a bhava/its lord
- Sade-Sati: Saturn transits 12H/1H/2H from natal Moon (7.5y total)
- Sthira Vedha: Saturn's vedha cancellation rules

Track-B's gochara_engine implements all of these. This adapter just
exposes them with a clean integration API.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

import swisseph as swe
from pydantic import BaseModel, ConfigDict, Field

from app.core.gochara_engine import GocharaVerdict, compute_gochara
from app.integration.gap_annotator import chart_from_reading


# Swiss Ephemeris planet IDs (same as ephemeris_engine).
_PLANET_IDS: dict[str, int] = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS, "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


class TransitStateView(BaseModel):
    """JSON-friendly projection of one TransitState (per bhava)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bhava: int = Field(ge=1, le=12)
    transit_planets_in_bhava: tuple[str, ...]
    transit_planets_aspecting_bhava: tuple[str, ...]
    saturn_present: bool
    jupiter_present: bool
    rahu_present: bool
    is_double_transit_bhava: bool
    is_double_transit_lord: bool
    is_double_transit_karaka: bool
    sthira_vedha_cancelled: bool
    notes: tuple[str, ...] = ()


class TransitReport(BaseModel):
    """High-signal projection of a GocharaVerdict + the source transit_signs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_jd: float
    target_iso: str | None = None
    transit_signs: dict[str, int]
    per_bhava: dict[int, TransitStateView]
    active_double_transit_bhavas: tuple[int, ...]
    sade_sati_active: bool
    saturn_vedha_cancelled: bool
    saturn_from_moon: int


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _jd_now_utc() -> float:
    """Current Julian Day (UTC). Same algorithm as dasha_now."""
    now = datetime.now(timezone.utc)
    y, m, d = now.year, now.month, now.day
    hh, mm, ss = now.hour, now.minute, now.second
    day_fraction = (hh + mm / 60 + ss / 3600) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + (a // 4)
    return (
        int(365.25 * (y + 4716))
        + int(30.6001 * (m + 1))
        + d + b - 1524.5 + day_fraction
    )


def _sidereal_sign_at_jd(jd: float, planet_id: int) -> int:
    """Lahiri-sidereal sign 1..12 for one planet at given JD."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    res, _ = swe.calc_ut(jd, planet_id, flags)
    longitude = res[0]
    return int(longitude // 30) + 1


def _iso_from_jd(jd: float) -> str | None:
    """Convert JD back to ISO YYYY-MM-DD (same algorithm as dasha_now)."""
    try:
        jd = jd + 0.5
        z = int(jd)
        f = jd - z
        if z < 2299161:
            a = z
        else:
            alpha = int((z - 1867216.25) / 36524.25)
            a = z + 1 + alpha - alpha // 4
        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)
        day = b - d - int(30.6001 * e) + f
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transit_signs_at(target_jd: float | None = None) -> dict[str, int]:
    """Return Lahiri-sidereal sign 1..12 per planet at ``target_jd``.

    Includes all 9 grahas (Rahu computed; Ketu derived as Rahu+180).
    """
    if target_jd is None:
        target_jd = _jd_now_utc()

    out: dict[str, int] = {}
    for planet, planet_id in _PLANET_IDS.items():
        out[planet] = _sidereal_sign_at_jd(target_jd, planet_id)

    # Ketu = exactly 180° from Rahu, so 6 signs away (mod 12).
    rahu_sign = out["Rahu"]
    out["Ketu"] = ((rahu_sign - 1 + 6) % 12) + 1
    return out


def transit_state_at(
    reading: Mapping[str, Any],
    target_jd: float | None = None,
) -> TransitReport:
    """Compute GocharaVerdict for the given natal reading at ``target_jd``.

    Wraps ``app.core.gochara_engine.compute_gochara`` and emits a
    JSON-friendly TransitReport with all sub-fields.
    """
    if target_jd is None:
        target_jd = _jd_now_utc()

    transit_signs = transit_signs_at(target_jd)
    chart = chart_from_reading(reading)
    verdict: GocharaVerdict = compute_gochara(chart, transit_signs=transit_signs)

    per_bhava_view: dict[int, TransitStateView] = {}
    for bhava, state in verdict.per_bhava.items():
        per_bhava_view[int(bhava)] = TransitStateView(
            bhava=int(state.bhava),
            transit_planets_in_bhava=tuple(state.transit_planets_in_bhava),
            transit_planets_aspecting_bhava=tuple(state.transit_planets_aspecting_bhava),
            saturn_present=bool(state.saturn_present),
            jupiter_present=bool(state.jupiter_present),
            rahu_present=bool(state.rahu_present),
            is_double_transit_bhava=bool(state.is_double_transit_bhava),
            is_double_transit_lord=bool(state.is_double_transit_lord),
            is_double_transit_karaka=bool(state.is_double_transit_karaka),
            sthira_vedha_cancelled=bool(state.sthira_vedha_cancelled),
            notes=tuple(state.notes),
        )

    return TransitReport(
        target_jd=target_jd,
        target_iso=_iso_from_jd(target_jd),
        transit_signs=transit_signs,
        per_bhava=per_bhava_view,
        active_double_transit_bhavas=tuple(verdict.active_double_transit_bhavas),
        sade_sati_active=bool(verdict.sade_sati_active),
        saturn_vedha_cancelled=bool(verdict.saturn_vedha_cancelled),
        saturn_from_moon=int(verdict.saturn_from_moon),
    )


def transit_at_now(reading: Mapping[str, Any]) -> TransitReport:
    """Convenience: transit state at the current UTC moment."""
    return transit_state_at(reading, target_jd=_jd_now_utc())
