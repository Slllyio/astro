"""Vimshottari Pratyantar (sub-sub-period) calculations.

Pratyantar is the third nesting level inside Vimshottari (after Mahadasha
and Antardasha). Within a given Antardasha, 9 Pratyantars are ordered
starting with the AD lord itself, then proceeding through the canonical
Vimshottari cycle (Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn,
Mercury), wrapping.

PT length: PT_days = AD_days * PT_lord_years / 120.

Like the AD layer, all calendar arithmetic is JD-based so swe.revjul
yields exactly the Gregorian date Swiss Ephemeris would. Substituting
datetime.timedelta introduces drift across long spans (regression guarded
in tests/test_dasha_dates.py and mirrored here).
"""
from __future__ import annotations

from typing import TypedDict

import swisseph as swe

from app.core.antardasha import AntardashaPeriod
from app.core.ephemeris_engine import DASHA_LORDS


class PratyantarPeriod(TypedDict):
    maha_lord: str
    antar_lord: str
    pratyantar_lord: str
    start_date: str
    end_date: str
    start_jd: float
    end_jd: float
    duration_days: float


# Total Vimshottari cycle in years. Sum of every lord's tenure in DASHA_LORDS.
_TOTAL_VIMSHOTTARI_YEARS = 120


def _format_iso_date(jd: float) -> str:
    """Convert a Julian Day to an ISO YYYY-MM-DD string via Swiss Ephemeris."""
    y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def _pratyantar_sequence(starting_lord: str) -> list[tuple[str, int]]:
    """Return the 9 (lord, lord_years) pairs ordered for a PT sequence
    beginning with `starting_lord`.

    The Vimshottari order is fixed (Ketu -> Venus -> ... -> Mercury, wrapping).
    Inside an AD, the PT ordering is the same cycle but rotated so the first
    element is the AD lord itself (Mercury AD's first PT is the AD lord).
    """
    lord_names = [name for name, _ in DASHA_LORDS]
    try:
        start_index = lord_names.index(starting_lord)
    except ValueError as exc:
        raise ValueError(f"Unknown dasha lord: {starting_lord!r}") from exc

    n = len(DASHA_LORDS)
    return [DASHA_LORDS[(start_index + offset) % n] for offset in range(n)]


def compute_pratyantars(antardasha: AntardashaPeriod) -> list[PratyantarPeriod]:
    """All 9 Pratyantars within `antardasha`.

    Sequence starts with the AD's own lord and proceeds through the
    Vimshottari cycle wrapping. Bit-exact contiguity: each PT's start_jd
    equals the previous PT's end_jd. The first PT's start_jd is the AD's
    start_jd; the last PT's end_jd equals the AD's end_jd within fp
    rounding (sum of fractions == 1.0).

    The AD total duration in days is derived from
    ``antardasha["end_jd"] - antardasha["start_jd"]`` (rather than
    ``duration_years * DAYS_PER_VEDIC_YEAR``). This guarantees bit-exact
    AD-boundary contiguity: the last PT of the prior AD ends at exactly
    the first PT of the next AD's start_jd, since both derive from the
    same stored JD values.
    """
    ad_start_jd = antardasha["start_jd"]
    ad_total_days = antardasha["end_jd"] - antardasha["start_jd"]

    sequence = _pratyantar_sequence(antardasha["antar_lord"])
    ad_end_jd = antardasha["end_jd"]
    last_index = len(sequence) - 1

    periods: list[PratyantarPeriod] = []
    cursor_jd = ad_start_jd

    for index, (pt_lord, pt_lord_years) in enumerate(sequence):
        start_jd = cursor_jd
        if index == last_index:
            # Snap the final PT's end_jd to the AD's stored end_jd. This
            # preserves bit-exact contiguity at AD boundaries (the prior
            # AD's end_jd is the next AD's start_jd by construction in
            # `compute_antardashas`). Avoids 1-ULP drift from accumulating
            # 9 fractional sums vs. one multiplication.
            end_jd = ad_end_jd
            duration_days = end_jd - start_jd
        else:
            duration_days = (
                ad_total_days * pt_lord_years / _TOTAL_VIMSHOTTARI_YEARS
            )
            end_jd = start_jd + duration_days

        periods.append(
            PratyantarPeriod(
                maha_lord=antardasha["maha_lord"],
                antar_lord=antardasha["antar_lord"],
                pratyantar_lord=pt_lord,
                start_date=_format_iso_date(start_jd),
                end_date=_format_iso_date(end_jd),
                start_jd=start_jd,
                end_jd=end_jd,
                duration_days=duration_days,
            )
        )
        cursor_jd = end_jd

    return periods


def compute_all_pratyantars(
    antardashas: list[AntardashaPeriod],
) -> dict[str, list[PratyantarPeriod]]:
    """For each Antardasha, compute its 9 Pratyantars.

    Keyed by ``f"{maha_lord}-{antar_lord}"`` (e.g. ``'Mercury-Mercury'``,
    ``'Mercury-Ketu'``) so consumers can index by AD without rebuilding
    keys. Each (MD, AD lord) pair is unique within a single MD.
    """
    return {
        f"{ad['maha_lord']}-{ad['antar_lord']}": compute_pratyantars(ad)
        for ad in antardashas
    }
