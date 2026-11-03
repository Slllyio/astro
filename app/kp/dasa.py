"""Vimshottari dasa / bhukti / antara / sookshma from the KP Moon.

The balance at birth comes from the Moon's position in its star, using the
Krishnamurti-ayanamsa Moon. Year length is the repo's locked
``DAYS_PER_VEDIC_YEAR = 365.2425`` (CLAUDE.md); Reader 3 does not state one
(ruling R11). Sub-periods are proportional (period x years / 120).

Usage:
    from app.kp.dasa import periods_on, periods_between
    periods_on(chart, jd)                       # (MD, AD, PD, SD) running at jd
    periods_between(chart, jd0, jd1, depth=3)   # all antaras overlapping
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterator

import swisseph as swe

from app.kp.chart import KPChart
from app.kp.subs import DASA_ORDER, DASA_YEARS, STAR_SPAN

DAYS_PER_VEDIC_YEAR: Final[float] = 365.2425
_LEVEL_NAMES: Final[tuple[str, ...]] = ("dasa", "bhukti", "antara", "sookshma")


@dataclass(frozen=True, slots=True)
class Period:
    """A dasa-level period. ``lords`` runs from MD downward."""

    lords: tuple[str, ...]
    start_jd: float
    end_jd: float

    @property
    def level(self) -> str:
        return _LEVEL_NAMES[len(self.lords) - 1]

    def label(self) -> str:
        return "-".join(self.lords)

    def dates(self) -> tuple[str, str]:
        """Start and end as ISO dates (UT)."""
        def iso(jd: float) -> str:
            y, m, d, _ = swe.revjul(jd, swe.GREG_CAL)
            return f"{y:04d}-{m:02d}-{d:02d}"
        return iso(self.start_jd), iso(self.end_jd)


def _seq(lord: str) -> tuple[str, ...]:
    i = DASA_ORDER.index(lord)
    return DASA_ORDER[i:] + DASA_ORDER[:i]


def mahadashas(chart: KPChart, span_years: float = 120.0) -> list[Period]:
    """Maha dasas from the birth-balance start, covering ``span_years`` after birth."""
    moon = chart.planets["Moon"].longitude
    span = float(STAR_SPAN)
    idx = int(moon // span)
    first = DASA_ORDER[idx % 9]
    elapsed = (moon - idx * span) / span
    start = chart.jd_ut - elapsed * DASA_YEARS[first] * DAYS_PER_VEDIC_YEAR
    out: list[Period] = []
    cur = start
    i = 0
    while cur < chart.jd_ut + span_years * DAYS_PER_VEDIC_YEAR:
        lord = _seq(first)[i % 9]
        end = cur + DASA_YEARS[lord] * DAYS_PER_VEDIC_YEAR
        out.append(Period((lord,), cur, end))
        cur, i = end, i + 1
    return out


def subdivide(p: Period) -> list[Period]:
    """The nine sub-periods of ``p`` in Vimshottari order from its own lord."""
    total = p.end_jd - p.start_jd
    out, cur = [], p.start_jd
    for lord in _seq(p.lords[-1]):
        end = cur + total * DASA_YEARS[lord] / 120
        out.append(Period(p.lords + (lord,), cur, end))
        cur = end
    return out


def periods_on(chart: KPChart, jd: float, depth: int = 4) -> tuple[Period, ...]:
    """The running periods at ``jd`` from MD down to ``depth`` levels (1-4)."""
    chain: list[Period] = []
    level = mahadashas(chart)
    for _ in range(depth):
        hit = next((p for p in level if p.start_jd <= jd < p.end_jd), None)
        if hit is None:
            break
        chain.append(hit)
        level = subdivide(hit)
    return tuple(chain)


def periods_between(chart: KPChart, jd0: float, jd1: float, depth: int = 3) -> Iterator[Period]:
    """All periods at ``depth`` that overlap ``[jd0, jd1)``."""
    def walk(ps: list[Period], d: int) -> Iterator[Period]:
        for p in ps:
            if p.end_jd <= jd0 or p.start_jd >= jd1:
                continue
            if d == depth:
                yield p
            else:
                yield from walk(subdivide(p), d + 1)
    yield from walk(mahadashas(chart), 1)


__all__ = ["DAYS_PER_VEDIC_YEAR", "Period", "mahadashas", "subdivide", "periods_on", "periods_between"]
