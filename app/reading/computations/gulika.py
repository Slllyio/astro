"""Tier-0 primitive: Gulika, Mandi, and auxiliary Saturn-derived upagrahas.

Doctrine lock — D-6 (``docs/doctrine-decisions.md``)
====================================================

**Gulika and Mandi are TWO DISTINCT upagrahas**, not synonyms (the common
modern conflation contradicts both BPHS Vol.I Ch.5 and Phaladeepika
Ch.25):

* **Gulika** — the *ascendant at the START* of Saturn's day or night
  segment, computed per BPHS Vol.I Ch.5 vv.10–12.
* **Mandi** — the *ascendant at the MIDPOINT* of the same Saturn
  segment, per Phaladeepika Ch.25.

Algorithm
=========

1. Compute the actual sunrise and sunset Julian Days at the birth
   location via Swiss Ephemeris (``swe.rise_trans``).
2. Determine which 1/8 segment of the day (for day-births) or night
   (for night-births) Saturn rules. The starting lord of part 1 is the
   weekday lord; subsequent parts follow the planetary-hour order
   (Sa-Ju-Ma-Su-Ve-Me-Mo, descending speed).
3. Gulika longitude = ascendant longitude at the start JD of Saturn's
   segment.  Mandi longitude = ascendant longitude at the midpoint JD.

The same procedure (with a different lord) yields Yamakantaka
(Jupiter's segment) and Kala (Sun's segment). These auxiliary
upagrahas use a single representative point (segment midpoint); the
distinct-START-vs-MIDPOINT contract is reserved for Gulika/Mandi per
D-6.

Public API
==========

    compute_gulika_and_mandi(
        birth_jd, lat, lon, is_daytime, weekday
    ) -> dict[str, Finding]

Returns four keys: ``gulika``, ``mandi``, ``yamakantaka``, ``kala``.

Inputs
======

* ``birth_jd`` — Julian Day at birth.
* ``lat``, ``lon`` — geographic coordinates (decimal degrees; east/north positive).
* ``is_daytime`` — True if birth was between sunrise and sunset locally;
  False for night births.
* ``weekday`` — 0..6 with 0=Sunday (matches the project convention used
  by ``app.core.panchanga._vara_info``).

Usage
=====

    >>> from app.reading.computations.gulika import compute_gulika_and_mandi
    >>> ups = compute_gulika_and_mandi(2448088.27083, 12.97, 77.59, True, 0)
    >>> ups["gulika"].verdict
    'Gulika at ...'
"""
from __future__ import annotations

import logging
from typing import Final

import swisseph as swe

from app.core.ephemeris_engine import ZODIAC_SIGNS
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# 3-vote envelope.
_PRIMITIVE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# Planetary-hour order: Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon
# (descending mean apparent motion). The weekday's lord owns segment 1;
# subsequent segments cycle through the 7-lord sequence. Saturn's
# segment depends on the weekday via the indices below.
_PLANETARY_HOUR_ORDER: Final[tuple[str, ...]] = (
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon",
)

# Weekday -> weekday lord (segment 1's ruler).
# 0=Sunday(Sun), 1=Monday(Moon), 2=Tuesday(Mars), 3=Wednesday(Mercury),
# 4=Thursday(Jupiter), 5=Friday(Venus), 6=Saturday(Saturn).
_WEEKDAY_LORD_DAY: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)

# For night-births the lord of part 1 is the 5th planet from the
# day-lord in the Sa-Ju-Ma-Su-Ve-Me-Mo cycle. Equivalent: the lord of
# the weekday three days later in the Sun-Moon-Mars-Mercury-Jupiter
# -Venus-Saturn cycle. (This implements BPHS Ch.5 v.7 "for night divide
# from sunset to sunrise and assign the lord of the 5th from the
# weekday lord".)
_WEEKDAY_LORD_NIGHT: Final[tuple[str, ...]] = tuple(
    _WEEKDAY_LORD_DAY[(i + 4) % 7] for i in range(7)
)


def _segment_index_for(lord_of_part_1: str, target_lord: str) -> int:
    """Return the 0-based segment index where ``target_lord`` rules.

    Segment 1 is owned by ``lord_of_part_1``; subsequent segments
    cycle through ``_PLANETARY_HOUR_ORDER`` starting at that lord.
    """
    start = _PLANETARY_HOUR_ORDER.index(lord_of_part_1)
    target = _PLANETARY_HOUR_ORDER.index(target_lord)
    return (target - start) % 7


def _sunrise_sunset(birth_jd: float, lat: float, lon: float) -> tuple[float, float]:
    """Compute the sunrise and sunset JDs straddling ``birth_jd``.

    Strategy:
        * sunrise = next sunrise on/after (birth_jd - 1)
        * sunset  = next sunset on/after sunrise
    This works for both day and night births because we always anchor
    on the sunrise of the local day.

    Raises ``RuntimeError`` if Swiss Ephemeris fails to find the event.
    """
    # geopos: lon (east+), lat (north+), alt (m). Modern swisseph
    # rise_trans signature: (tjdut, body, rsmi, geopos, atpress, attemp, flags).
    # Returns (status, tret). status >= 0 = success, -2 = circumpolar.
    geopos = (lon, lat, 0.0)
    epheflag = swe.FLG_SWIEPH

    status, tret = swe.rise_trans(
        birth_jd - 1.0,
        swe.SUN,
        swe.CALC_RISE,
        geopos,
        0.0,
        0.0,
        epheflag,
    )
    if status < 0 or not tret:
        raise RuntimeError(
            f"swe.rise_trans failed to find sunrise: status={status}"
        )
    sunrise_jd = tret[0]

    status, tret = swe.rise_trans(
        sunrise_jd,
        swe.SUN,
        swe.CALC_SET,
        geopos,
        0.0,
        0.0,
        epheflag,
    )
    if status < 0 or not tret:
        raise RuntimeError(
            f"swe.rise_trans failed to find sunset: status={status}"
        )
    sunset_jd = tret[0]
    return sunrise_jd, sunset_jd


def _next_sunrise(jd: float, lat: float, lon: float) -> float:
    """Compute the next sunrise after ``jd``."""
    geopos = (lon, lat, 0.0)
    status, tret = swe.rise_trans(
        jd,
        swe.SUN,
        swe.CALC_RISE,
        geopos,
        0.0,
        0.0,
        swe.FLG_SWIEPH,
    )
    if status < 0 or not tret:
        raise RuntimeError(
            f"swe.rise_trans failed to find next sunrise: status={status}"
        )
    return tret[0]


def _ascendant_longitude_at(jd: float, lat: float, lon: float) -> float:
    """Sidereal Lahiri ascendant longitude at ``jd`` (degrees, [0, 360))."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _cusps, ascmc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    return float(ascmc[0]) % 360.0


def _segment_anchor_jds(
    birth_jd: float,
    lat: float,
    lon: float,
    is_daytime: bool,
    weekday: int,
    target_lord: str,
) -> tuple[float, float]:
    """Return (start_jd, midpoint_jd) of the target lord's segment.

    The lord-of-part-1 table depends on whether the birth is by day or
    night (BPHS Ch.5 v.7). The 8-segment partition divides the day
    (sunrise -> sunset) or night (sunset -> next sunrise).
    """
    sunrise_jd, sunset_jd = _sunrise_sunset(birth_jd, lat, lon)
    if is_daytime:
        period_start = sunrise_jd
        period_end = sunset_jd
        lord_of_part_1 = _WEEKDAY_LORD_DAY[weekday]
    else:
        period_start = sunset_jd
        # Night runs from sunset to the next sunrise.
        period_end = _next_sunrise(sunset_jd, lat, lon)
        lord_of_part_1 = _WEEKDAY_LORD_NIGHT[weekday]

    segment_count = 8  # BPHS Ch.5 fixed convention.
    segment_length = (period_end - period_start) / segment_count
    idx = _segment_index_for(lord_of_part_1, target_lord)
    start_jd = period_start + idx * segment_length
    midpoint_jd = period_start + (idx + 0.5) * segment_length
    return start_jd, midpoint_jd


def _sign_for(longitude: float) -> str:
    """Return the sign name for a longitude in ``[0, 360)``."""
    idx = int(longitude // 30.0) % 12
    return ZODIAC_SIGNS[idx]


def _upagraha_finding(
    key: str,
    label: str,
    longitude: float,
    anchor: str,
    target_lord: str,
    is_daytime: bool,
    weekday: int,
) -> Finding:
    """Build a Finding for one upagraha placement."""
    deg_in_sign = longitude % 30.0
    sign = _sign_for(longitude)
    verdict = f"{label} at {deg_in_sign:.2f}° {sign}"
    return Finding(
        id=f"primitive.gulika.{key}",
        rule=key,
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"target_lord={target_lord}",
            f"anchor={anchor}",
            f"is_daytime={is_daytime}",
            f"weekday={weekday}",
            f"longitude={longitude:.6f}",
            f"sign={sign}",
            f"degree_in_sign={deg_in_sign:.4f}",
            "doctrine=D-6 (gulika_mandi_distinct)",
        ],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def compute_gulika_and_mandi(
    birth_jd: float,
    lat: float,
    lon: float,
    is_daytime: bool,
    weekday: int,
) -> dict[str, Finding]:
    """Compute Gulika, Mandi, Yamakantaka and Kala (D-6 locked).

    Args:
        birth_jd: Julian Day at birth.
        lat: Geographic latitude in decimal degrees (north positive).
        lon: Geographic longitude in decimal degrees (east positive).
        is_daytime: True for births between sunrise and sunset, False
            otherwise.
        weekday: 0..6 with 0=Sunday (matches
            ``app.core.panchanga._vara_info`` convention).

    Returns:
        Dict with four keys:
            * ``"gulika"`` — Saturn segment START longitude (D-6).
            * ``"mandi"``  — Saturn segment MIDPOINT longitude (D-6).
            * ``"yamakantaka"`` — Jupiter segment midpoint (auxiliary).
            * ``"kala"``        — Sun segment midpoint (auxiliary).

    Raises:
        ValueError: if ``weekday`` is not in 0..6.
        RuntimeError: if Swiss Ephemeris fails to compute sunrise/sunset
            (e.g. at extreme latitudes with no sunrise on that day).
    """
    if not 0 <= weekday <= 6:
        raise ValueError(f"weekday must be 0..6, got {weekday}")

    findings: dict[str, Finding] = {}

    # --- Gulika (Saturn START) + Mandi (Saturn MIDPOINT) ----------------- #
    saturn_start_jd, saturn_mid_jd = _segment_anchor_jds(
        birth_jd, lat, lon, is_daytime, weekday, "Saturn"
    )
    gulika_lon = _ascendant_longitude_at(saturn_start_jd, lat, lon)
    mandi_lon = _ascendant_longitude_at(saturn_mid_jd, lat, lon)

    findings["gulika"] = _upagraha_finding(
        "gulika", "Gulika",
        gulika_lon, "segment_start", "Saturn", is_daytime, weekday,
    )
    findings["mandi"] = _upagraha_finding(
        "mandi", "Mandi",
        mandi_lon, "segment_midpoint", "Saturn", is_daytime, weekday,
    )

    # --- Yamakantaka (Jupiter) and Kala (Sun) — auxiliary upagrahas ----- #
    # These use only the segment midpoint per the project's v1 convention;
    # a future task may refine each to BPHS-exact start/midpoint splits.
    _, yk_mid = _segment_anchor_jds(
        birth_jd, lat, lon, is_daytime, weekday, "Jupiter"
    )
    yk_lon = _ascendant_longitude_at(yk_mid, lat, lon)
    findings["yamakantaka"] = _upagraha_finding(
        "yamakantaka", "Yamakantaka",
        yk_lon, "segment_midpoint", "Jupiter", is_daytime, weekday,
    )

    _, kala_mid = _segment_anchor_jds(
        birth_jd, lat, lon, is_daytime, weekday, "Sun"
    )
    kala_lon = _ascendant_longitude_at(kala_mid, lat, lon)
    findings["kala"] = _upagraha_finding(
        "kala", "Kala",
        kala_lon, "segment_midpoint", "Sun", is_daytime, weekday,
    )

    return findings


__all__ = ["compute_gulika_and_mandi"]

# TODO(reading.gulika): refine Yamakantaka / Kala to the per-upagraha
# BPHS Ch.5 segment-fraction (each upagraha has its own fractional
# anchor — e.g. Kala = 1/8 into Sun's segment, Mrityu = 2/8, etc.).
# v1 currently uses the segment midpoint uniformly for the auxiliaries;
# Gulika and Mandi are fully BPHS-compliant per D-6.
