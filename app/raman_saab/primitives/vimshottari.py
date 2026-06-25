"""Vimshottari Dasha — the event-timing layer.

The 120-year Vimshottari cycle is the spine of Vedic event prediction: it sequences
the planetary Mahadasha (major period) and Bhukti (sub-period) lords across a life, so
a NATAL verdict ("the 8th is afflicted") can be projected onto TIME ("the maraka period
runs 1962-1966"). This is what lets the engine reason about *when* a significator's
results manifest — the layer the placement-only judges deliberately lacked.

Sequence + weights (the canonical Vimshottari order, 120 years total):
    Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17.

The birth Mahadasha lord + elapsed fraction come from the Moon's nakshatra (reusing the
main engine's ``calculate_vimshottari_mahadasha``). The full timeline is then unrolled
forward in **Julian-Day space** (``birth_jd ± years * 365.2425``; never
``datetime.timedelta`` — see CLAUDE.md), and a Bhukti subdivides its Mahadasha
proportionally (``Bhukti_years = MD_years * bhukti_lord_years / 120``), ordered from the
MD lord onward.

Validated against Raman's dated deaths (``tests/raman_saab/test_vimshottari.py``): the
running Mahadasha at the death date reproduces Raman's stated period for every dated
death golden (Lincoln Saturn/Mercury, Hitler Rahu/Moon match to the Bhukti).

Usage:
    from app.raman_saab.primitives.vimshottari import dasha_on, date_to_jd
    period = dasha_on(chart, date_to_jd(1966, 2, 7))   # -> DashaPeriod(maha='Rahu', antar=...)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

import swisseph as swe

from app.core.ephemeris_engine import (
    DASHA_LORDS, DAYS_PER_VEDIC_YEAR, calculate_vimshottari_mahadasha)
from app.raman_saab.chart.model import RamanChart

_LORD_YEARS: Final[dict[str, int]] = dict(DASHA_LORDS)
_SEQUENCE: Final[tuple[str, ...]] = tuple(name for name, _ in DASHA_LORDS)
_TOTAL_YEARS: Final[int] = 120


@dataclass(frozen=True)
class DashaPeriod:
    """A running period: its Mahadasha lord, its Bhukti (antar) lord (None for an
    MD-level span), and its [start, end) bounds in Julian Days."""
    maha: str
    antar: Optional[str]
    start_jd: float
    end_jd: float

    def contains(self, jd: float) -> bool:
        return self.start_jd <= jd < self.end_jd


def date_to_jd(year: int, month: int, day: int, hour: float = 12.0) -> float:
    """Gregorian calendar date -> Julian Day (Swiss Ephemeris, GREG_CAL)."""
    return swe.julday(year, month, day, hour, swe.GREG_CAL)


def _sequence_from(lord: str) -> list[str]:
    """The 9-lord Vimshottari cycle rotated to begin with `lord`."""
    i = _SEQUENCE.index(lord)
    return [_SEQUENCE[(i + offset) % 9] for offset in range(9)]


def mahadasha_timeline(chart: RamanChart, span_years: float = 140.0) -> list[DashaPeriod]:
    """The Mahadasha sequence from the birth MD's true start, unrolled `span_years`
    forward (>= a full 120-year cycle, so it covers any realistic lifespan). The first
    MD began BEFORE birth; ``time_elapsed_years`` of it had already run at birth."""
    md = calculate_vimshottari_mahadasha(chart.planets["Moon"].lon, chart.jd_ut)
    lord = md["mahadasha_lord"]
    md_start = chart.jd_ut - md["time_elapsed_years"] * DAYS_PER_VEDIC_YEAR
    periods: list[DashaPeriod] = []
    cursor, accrued, idx = md_start, 0.0, 0
    sequence = _sequence_from(lord)
    while accrued < span_years:
        lord_i = sequence[idx % 9]
        years = _LORD_YEARS[lord_i]
        end = cursor + years * DAYS_PER_VEDIC_YEAR
        periods.append(DashaPeriod(lord_i, None, cursor, end))
        cursor, accrued, idx = end, accrued + years, idx + 1
    return periods


def bhuktis(md: DashaPeriod) -> list[DashaPeriod]:
    """The 9 Bhuktis (antardashas) of a Mahadasha, proportional and ordered from the MD
    lord onward."""
    total_years = (md.end_jd - md.start_jd) / DAYS_PER_VEDIC_YEAR
    out: list[DashaPeriod] = []
    cursor = md.start_jd
    for antar in _sequence_from(md.maha):
        years = total_years * _LORD_YEARS[antar] / _TOTAL_YEARS
        end = cursor + years * DAYS_PER_VEDIC_YEAR
        out.append(DashaPeriod(md.maha, antar, cursor, end))
        cursor = end
    return out


def dasha_on(chart: RamanChart, jd: float) -> Optional[DashaPeriod]:
    """The (Mahadasha, Bhukti) period running on Julian Day `jd`, or None if `jd` falls
    outside the unrolled timeline."""
    for md in mahadasha_timeline(chart):
        if md.contains(jd):
            for bh in bhuktis(md):
                if bh.contains(jd):
                    return bh
            return md
    return None


def maraka_lords(chart: RamanChart) -> frozenset[str]:
    """The maraka (death-inflicting) graha set: the lords of the 2nd and 7th houses
    (the maraka bhavas) plus Saturn (Ayushkaraka / the natural killer). The Dasha of a
    maraka is when a fatal 8th/longevity affliction is most apt to mature."""
    from app.raman_saab.chart.constants import SIGN_LORDS
    second = SIGN_LORDS[((chart.asc_sign - 1) + 1) % 12 + 1]
    seventh = SIGN_LORDS[((chart.asc_sign - 1) + 6) % 12 + 1]
    return frozenset({second, seventh, "Saturn"})


def is_maraka_period(chart: RamanChart, jd: float) -> bool:
    """True when the Mahadasha OR Bhukti lord running on `jd` is a maraka — the timing
    signature for a death/longevity-affliction maturing."""
    period = dasha_on(chart, jd)
    if period is None:
        return False
    marakas = maraka_lords(chart)
    return period.maha in marakas or (period.antar is not None and period.antar in marakas)
