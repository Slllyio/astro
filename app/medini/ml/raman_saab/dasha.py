"""Vimshottari Mahadasha / Antardasha timing for the death corpus.

Reuses the repo's locked Vimshottari constants (``DASHA_LORDS``,
``DAYS_PER_VEDIC_YEAR``) so dasha boundaries match the production engine, and
computes the sidereal (Lahiri) Moon longitude with Swiss Ephemeris in Moshier
mode (no ephemeris data files required).

The key primitives for the death-timing test are:

- ``moon_longitude(dob, hour_local, lat, lon)`` — natal sidereal Moon.
- ``md_intervals`` / ``ad_intervals`` — the dasha timeline over a lifespan.
- ``lord_at(jd, intervals)`` — which lord is active at a moment.
- ``exposure(intervals, birth_jd, death_jd)`` — the fraction of the lived
  lifespan spent under each lord (the a-priori "random moment of life"
  baseline that makes the enrichment test exposure-adjusted).

Birth times are unknown in the corpus, so ``hour_local`` is an assumption; the
validation runs a sensitivity sweep over several hours. Timezone is
approximated from longitude (``round(lon/15)``) — good to ~1h, well inside the
sweep's range.
"""
from __future__ import annotations

from dataclasses import dataclass

import swisseph as swe

from app.core.ephemeris_engine import DASHA_LORDS, DAYS_PER_VEDIC_YEAR

_LORD_YEARS: dict[str, int] = {name: yrs for name, yrs in DASHA_LORDS}
_LORD_ORDER: list[str] = [name for name, _ in DASHA_LORDS]
_CYCLE_YEARS: int = sum(_LORD_YEARS.values())  # 120
_NAK_SPAN: float = 360.0 / 27.0

ALL_LORDS: tuple[str, ...] = tuple(sorted(_LORD_YEARS))

_LAHIRI_SET = False


def _ensure_lahiri() -> None:
    global _LAHIRI_SET
    if not _LAHIRI_SET:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        _LAHIRI_SET = True


def julday(year: int, month: int, day: int, hour_ut: float) -> float:
    return swe.julday(year, month, day, hour_ut, swe.GREG_CAL)


def moon_longitude(
    year: int, month: int, day: int, hour_local: float, lon: float,
) -> tuple[float, float]:
    """Return (sidereal Moon longitude in deg, birth_jd) for a birth.

    Timezone approximated from longitude. Uses Moshier (no data files).
    """
    _ensure_lahiri()
    tz = round(lon / 15.0)
    hour_ut = hour_local - tz
    jd = swe.julday(year, month, day, hour_ut, swe.GREG_CAL)
    flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
    lonlat = swe.calc_ut(jd, swe.MOON, flags)[0]
    return float(lonlat[0]) % 360.0, jd


def natal_md_lord(moon_lon: float) -> tuple[str, float]:
    """Return (natal MD lord, fraction of that MD already elapsed at birth)."""
    nak_index = int(moon_lon // _NAK_SPAN)
    frac = (moon_lon % _NAK_SPAN) / _NAK_SPAN
    lord = _LORD_ORDER[nak_index % 9]
    return lord, frac


@dataclass(frozen=True)
class Interval:
    lord: str
    start_jd: float
    end_jd: float


def md_intervals(moon_lon: float, birth_jd: float,
                 span_years: float = 120.0) -> list[Interval]:
    """Mahadasha intervals covering ``span_years`` from birth.

    The natal MD started before birth (birth falls mid-dasha); intervals are
    emitted in cycle order from the natal lord until the span is covered.
    """
    lord, elapsed_frac = natal_md_lord(moon_lon)
    start_idx = _LORD_ORDER.index(lord)
    natal_years = _LORD_YEARS[lord]
    cursor = birth_jd - elapsed_frac * natal_years * DAYS_PER_VEDIC_YEAR
    out: list[Interval] = []
    horizon = birth_jd + span_years * DAYS_PER_VEDIC_YEAR
    offset = 0
    while cursor < horizon:
        L = _LORD_ORDER[(start_idx + offset) % 9]
        dur = _LORD_YEARS[L] * DAYS_PER_VEDIC_YEAR
        out.append(Interval(L, cursor, cursor + dur))
        cursor += dur
        offset += 1
    return out


def ad_intervals_in_md(md: Interval) -> list[Interval]:
    """The 9 antardashas within a mahadasha, in cycle order from the MD lord.

    AD duration = MD duration × (AD-lord years / 120).
    """
    md_days = md.end_jd - md.start_jd
    start_idx = _LORD_ORDER.index(md.lord)
    out: list[Interval] = []
    cursor = md.start_jd
    for offset in range(9):
        L = _LORD_ORDER[(start_idx + offset) % 9]
        dur = md_days * (_LORD_YEARS[L] / _CYCLE_YEARS)
        out.append(Interval(L, cursor, cursor + dur))
        cursor += dur
    return out


def ad_intervals(moon_lon: float, birth_jd: float,
                 span_years: float = 120.0) -> list[Interval]:
    out: list[Interval] = []
    for md in md_intervals(moon_lon, birth_jd, span_years):
        out.extend(ad_intervals_in_md(md))
    return out


def lord_at(jd: float, intervals: list[Interval]) -> str | None:
    for iv in intervals:
        if iv.start_jd <= jd < iv.end_jd:
            return iv.lord
    return None


def exposure(intervals: list[Interval], birth_jd: float,
             death_jd: float) -> dict[str, float]:
    """Fraction of the lived lifespan [birth_jd, death_jd] under each lord.

    This is the exposure-adjusted baseline: under the null "death is a random
    moment of life", P(lord active at death = L) = exposure[L]. Sums to 1.
    """
    span = death_jd - birth_jd
    acc: dict[str, float] = {L: 0.0 for L in ALL_LORDS}
    if span <= 0:
        return acc
    for iv in intervals:
        lo = max(iv.start_jd, birth_jd)
        hi = min(iv.end_jd, death_jd)
        if hi > lo:
            acc[iv.lord] += (hi - lo)
    return {L: v / span for L, v in acc.items()}
