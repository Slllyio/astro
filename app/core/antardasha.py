"""Vimshottari Antardasha (sub-period) calculations.

Antardasha is the second nesting level inside a Mahadasha. The current MD is
divided into 9 sub-periods, ordered starting with the MD lord itself, then
proceeding through the canonical Vimshottari sequence (Ketu, Venus, Sun, Moon,
Mars, Rahu, Jupiter, Saturn, Mercury), wrapping back around as needed.

Each AD's length is proportional to the AD lord's own Vimshottari weight:

    AD_years = MD_total_years * AD_lord_years / 120

All calendar arithmetic happens in Julian Day space (`birth_jd + days`) so
that converting back via `swe.revjul(jd, swe.GREG_CAL)` yields the exact
Gregorian date Swiss Ephemeris itself would. Substituting `datetime.timedelta`
introduces ~0.75 days of drift over a century — see the regression guard in
`tests/test_dasha_dates.py::test_jd_arithmetic_diverges_from_naive_timedelta_julian`.
"""
from __future__ import annotations

from typing import TypedDict

import swisseph as swe

from app.core.ephemeris_engine import (
    DASHA_LORDS,
    DAYS_PER_VEDIC_YEAR,
    calculate_vimshottari_mahadasha,
)


class AntardashaPeriod(TypedDict):
    maha_lord: str
    antar_lord: str
    start_date: str
    end_date: str
    start_jd: float
    end_jd: float
    duration_years: float


# Total Vimshottari cycle in years. Sum of every lord's tenure in DASHA_LORDS.
_TOTAL_VIMSHOTTARI_YEARS = 120


def _format_iso_date(jd: float) -> str:
    """Convert a Julian Day to an ISO YYYY-MM-DD string via Swiss Ephemeris."""
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _md_start_jd(moon_longitude: float, birth_jd: float) -> tuple[str, float, float]:
    """Resolve the *current* Mahadasha's lord, start_jd, and total years.

    Reuses the existing engine for the lord identification + elapsed-fraction
    math so we don't duplicate the nakshatra logic. The returned start_jd is
    computed independently in JD space (consistent with the existing engine's
    method) so we never round-trip through the ISO string.
    """
    md = calculate_vimshottari_mahadasha(moon_longitude, birth_jd)
    lord: str = md["mahadasha_lord"]
    total_years: float = md["total_duration_years"]
    years_elapsed: float = md["time_elapsed_years"]
    start_jd = birth_jd - years_elapsed * DAYS_PER_VEDIC_YEAR
    return lord, start_jd, total_years


def _antar_sequence(starting_lord: str) -> list[tuple[str, int]]:
    """Return the 9 (lord, lord_years) pairs ordered for an AD sequence
    beginning with `starting_lord`.

    The Vimshottari order is fixed (Ketu -> Venus -> ... -> Mercury, wrapping).
    Inside an MD, the AD ordering is the same cycle but rotated so the first
    element is the MD lord itself (Mercury MD's first AD is Mercury–Mercury).
    """
    lord_names = [name for name, _ in DASHA_LORDS]
    try:
        start_index = lord_names.index(starting_lord)
    except ValueError as exc:
        raise ValueError(f"Unknown dasha lord: {starting_lord!r}") from exc

    n = len(DASHA_LORDS)
    return [DASHA_LORDS[(start_index + offset) % n] for offset in range(n)]


def compute_antardashas(
    moon_longitude: float, birth_jd: float
) -> list[AntardashaPeriod]:
    """All 9 Antardashas within the *current* Mahadasha for this birth.

    Vimshottari Antardasha math:
      - The current Mahadasha is determined as in the existing engine.
      - The Mahadasha is divided into 9 sub-periods, ordered starting with the
        MD lord itself, then proceeding through the Vimshottari sequence
        (Ketu -> Venus -> Sun -> Moon -> Mars -> Rahu -> Jupiter -> Saturn ->
        Mercury, wrapping).
      - Sub-period length: AD_years = MD_total_years * AD_lord_years / 120.
      - First AD's start_jd = MD start_jd; subsequent AD's start_jd = previous
        AD's end_jd.
      - All date math in JD space: end_jd = start_jd + duration_years * 365.2425,
        then swe.revjul.

    Returns the 9 ADs of the *current* MD. Out of scope: Pratyantar (next
    nesting level).
    """
    md_lord, md_start_jd, md_total_years = _md_start_jd(moon_longitude, birth_jd)
    sequence = _antar_sequence(md_lord)

    periods: list[AntardashaPeriod] = []
    cursor_jd = md_start_jd

    for antar_lord, antar_lord_years in sequence:
        duration_years = md_total_years * antar_lord_years / _TOTAL_VIMSHOTTARI_YEARS
        start_jd = cursor_jd
        end_jd = start_jd + duration_years * DAYS_PER_VEDIC_YEAR

        periods.append(
            AntardashaPeriod(
                maha_lord=md_lord,
                antar_lord=antar_lord,
                start_date=_format_iso_date(start_jd),
                end_date=_format_iso_date(end_jd),
                start_jd=start_jd,
                end_jd=end_jd,
                duration_years=duration_years,
            )
        )
        cursor_jd = end_jd

    return periods
