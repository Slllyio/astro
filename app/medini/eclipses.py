"""Eclipse Impact Mapper — find upcoming solar & lunar eclipses, tag each
with its astrological nakshatra + Kurma region, and surface the geographic
point of greatest eclipse.

Solar eclipse impact in Vedic mundane astrology runs on three axes:
  1. WHEN (the JD of greatest eclipse)
  2. WHERE on Earth (geocentric path of totality / annularity / max partial)
  3. WHAT in the chart (the nakshatra the Sun/Moon conjunction falls in,
     which then maps to a Kurma region via the Phase 0 grid)

This module computes all three. Drawing the actual path of totality
(complex polygon math) is out of scope; we surface the single point of
greatest eclipse instead, which is sufficient for the consumer-facing
map. The full path of totality could be added later via NASA's Besselian
elements if needed.

Pure functions, no IO, no DB. Swisseph eclipse search is deterministic
given a starting JD.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Literal

import swisseph as swe

from app.core.ephemeris_engine import PLANETS, ZODIAC_SIGNS
from app.core.nakshatra import nakshatra_for_longitude
from app.medini.kurma_chakra import (
    info_for_region,
    region_for_nakshatra,
    tattva_for_region,
)

logger = logging.getLogger(__name__)

EclipseFamily = Literal["SOLAR", "LUNAR"]
SolarSubtype = Literal["TOTAL", "ANNULAR", "HYBRID", "PARTIAL"]
LunarSubtype = Literal["TOTAL", "PARTIAL", "PENUMBRAL"]

DEFAULT_LOOKAHEAD_COUNT = 5  # next 5 of each family = 10 eclipses total


# ---------- Subtype decoders ----------

def _solar_subtype(retflag: int) -> SolarSubtype:
    """Decode swisseph's retflag bits for a solar eclipse type."""
    if retflag & swe.ECL_TOTAL:
        return "TOTAL"
    if retflag & swe.ECL_ANNULAR_TOTAL:
        return "HYBRID"
    if retflag & swe.ECL_ANNULAR:
        return "ANNULAR"
    return "PARTIAL"


def _lunar_subtype(retflag: int) -> LunarSubtype:
    """Decode retflag for a lunar eclipse type."""
    if retflag & swe.ECL_TOTAL:
        return "TOTAL"
    if retflag & swe.ECL_PARTIAL:
        return "PARTIAL"
    return "PENUMBRAL"


# ---------- JD ↔ Gregorian helpers ----------

def _jd_to_iso(jd_ut: float) -> str:
    """Convert a JD (UT) to an ISO 8601 timestamp."""
    y, m, d, h_decimal = swe.revjul(jd_ut, swe.GREG_CAL)
    h = int(h_decimal)
    mi = int((h_decimal - h) * 60)
    s = int(round((((h_decimal - h) * 60) - mi) * 60))
    s = max(0, min(59, s))
    return dt.datetime(int(y), int(m), int(d), h, mi, s, tzinfo=dt.timezone.utc).isoformat()


def _jd_to_iso_date(jd_ut: float) -> str:
    """Date-only ISO YYYY-MM-DD, without time. Useful for headlines."""
    y, m, d, _ = swe.revjul(jd_ut, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


# ---------- Astrological tagging ----------

def _luminary_nakshatra(eclipse_jd: float, family: EclipseFamily) -> dict[str, Any]:
    """The luminary whose nakshatra matters for mundane impact.

    Solar eclipse: the Sun's nakshatra at eclipse maximum. Sun and Moon
    are conjunct, so either luminary's nakshatra is identical here.

    Lunar eclipse: the Moon's nakshatra at eclipse maximum. Sun and Moon
    are in opposition; Moon's nakshatra is the impact axis in classical
    Vedic mundane analysis (the "darkening Moon" indicator).
    """
    flags = swe.FLG_SIDEREAL
    luminary_id = PLANETS["Sun"] if family == "SOLAR" else PLANETS["Moon"]
    result, _ = swe.calc_ut(eclipse_jd, luminary_id, flags)
    lon = float(result[0])
    nak = nakshatra_for_longitude(lon)
    region = region_for_nakshatra(nak["index"])
    info = info_for_region(region)
    sign_idx = int(lon // 30)
    return {
        "luminary": "Sun" if family == "SOLAR" else "Moon",
        "longitude": lon,
        "sign_name": ZODIAC_SIGNS[sign_idx],
        "nakshatra_index": nak["index"],
        "nakshatra_name": nak["name"],
        "kurma_region": region,
        "kurma_tattva": info.tattva,
        "kurma_description": info.description,
    }


# ---------- Eclipse search ----------

def _next_solar_eclipse(jd_search: float) -> tuple[float, int] | None:
    """Find the next solar eclipse anywhere on Earth.

    Returns (eclipse_max_jd, retflag) or None if swisseph couldn't find one.
    `tret[0]` is the JD of greatest eclipse (the moment of mundane impact).
    """
    try:
        retflag, tret = swe.sol_eclipse_when_glob(jd_search, swe.FLG_SWIEPH, 0, False)
    except Exception:
        logger.exception("solar eclipse search failed at jd=%s", jd_search)
        return None
    if retflag < 0:
        return None
    return float(tret[0]), int(retflag)


def _next_lunar_eclipse(jd_search: float) -> tuple[float, int] | None:
    """Find the next lunar eclipse globally."""
    try:
        retflag, tret = swe.lun_eclipse_when(jd_search, swe.FLG_SWIEPH, 0, False)
    except Exception:
        logger.exception("lunar eclipse search failed at jd=%s", jd_search)
        return None
    if retflag < 0:
        return None
    return float(tret[0]), int(retflag)


def _solar_eclipse_max_location(eclipse_jd: float) -> tuple[float, float] | None:
    """Geographic point of greatest eclipse for a solar eclipse.

    Returns (lat, lon) in WGS-84 decimal degrees, or None if swisseph
    can't determine it (rare; happens for very-grazing eclipses).
    """
    try:
        retflag, geopos, _attr = swe.sol_eclipse_where(eclipse_jd, swe.FLG_SWIEPH)
    except Exception:
        logger.exception("solar eclipse location lookup failed at jd=%s", eclipse_jd)
        return None
    if retflag < 0:
        return None
    # geopos: [lon, lat, ...] in swisseph's convention.
    return float(geopos[1]), float(geopos[0])


# ---------- Public API ----------

def find_upcoming_eclipses(
    jd_now: float | None = None,
    count: int = DEFAULT_LOOKAHEAD_COUNT,
) -> list[dict[str, Any]]:
    """Return the next `count` solar AND `count` lunar eclipses, merged
    and sorted by JD ascending.

    Each entry is a dict with:
      - family:           "SOLAR" | "LUNAR"
      - subtype:          "TOTAL" / "ANNULAR" / "HYBRID" / "PARTIAL"
                          (or "PENUMBRAL" for lunar)
      - jd:               JD of greatest eclipse (UT)
      - date:             ISO date YYYY-MM-DD
      - timestamp_utc:    ISO 8601 timestamp
      - greatest_lat:     lat of greatest-eclipse point (solar only; lunar = None)
      - greatest_lon:     lon of greatest-eclipse point (solar only)
      - astrology:        dict with luminary nakshatra + Kurma region info
    """
    if jd_now is None:
        now = dt.datetime.now(dt.timezone.utc)
        decimal_hour = now.hour + now.minute / 60.0 + now.second / 3600.0
        jd_now = swe.julday(now.year, now.month, now.day, decimal_hour, swe.GREG_CAL)

    eclipses: list[dict[str, Any]] = []

    # Solar
    jd_search = jd_now
    for _ in range(count):
        result = _next_solar_eclipse(jd_search)
        if result is None:
            break
        eclipse_jd, retflag = result
        location = _solar_eclipse_max_location(eclipse_jd)
        astro = _luminary_nakshatra(eclipse_jd, "SOLAR")
        eclipses.append({
            "family": "SOLAR",
            "subtype": _solar_subtype(retflag),
            "jd": eclipse_jd,
            "date": _jd_to_iso_date(eclipse_jd),
            "timestamp_utc": _jd_to_iso(eclipse_jd),
            "greatest_lat": location[0] if location else None,
            "greatest_lon": location[1] if location else None,
            "astrology": astro,
        })
        # Advance past this eclipse so the next search doesn't re-find it.
        jd_search = eclipse_jd + 1.0

    # Lunar
    jd_search = jd_now
    for _ in range(count):
        result = _next_lunar_eclipse(jd_search)
        if result is None:
            break
        eclipse_jd, retflag = result
        astro = _luminary_nakshatra(eclipse_jd, "LUNAR")
        eclipses.append({
            "family": "LUNAR",
            "subtype": _lunar_subtype(retflag),
            "jd": eclipse_jd,
            "date": _jd_to_iso_date(eclipse_jd),
            "timestamp_utc": _jd_to_iso(eclipse_jd),
            "greatest_lat": None,
            "greatest_lon": None,
            "astrology": astro,
        })
        jd_search = eclipse_jd + 1.0

    eclipses.sort(key=lambda e: e["jd"])
    return eclipses


def upcoming_eclipses_payload(
    jd_now: float | None = None,
    count: int = DEFAULT_LOOKAHEAD_COUNT,
) -> dict[str, Any]:
    """Top-level dict for the /medini/eclipses endpoint.

    Includes a summary that the frontend can render at-a-glance:
    counts of upcoming totals/partials, etc.
    """
    eclipses = find_upcoming_eclipses(jd_now=jd_now, count=count)
    return {
        "as_of_jd": jd_now if jd_now is not None else None,
        "as_of_timestamp_utc": (
            _jd_to_iso(jd_now) if jd_now is not None else dt.datetime.now(dt.timezone.utc).isoformat()
        ),
        "lookahead_count_per_family": count,
        "eclipses": eclipses,
        "summary": {
            "total_count": len(eclipses),
            "solar_count": sum(1 for e in eclipses if e["family"] == "SOLAR"),
            "lunar_count": sum(1 for e in eclipses if e["family"] == "LUNAR"),
            "next": eclipses[0] if eclipses else None,
        },
    }
