"""Dasha-driven, temporally-prioritized reading (Raman's two-layer method).

The static all-house PROMISE (`proforma.read_chart`) says what each house *can* give; this
module adds the ACTIVATION layer — the running Mahadasha/Bhukti lights up the houses it
signifies (`vimshottari.active_houses`), so the reading focuses on what is live now. Two modes:

* SNAPSHOT (`read_chart_on_date`): given a date, the active houses + their natal promise + the
  activating lord's delivery quality.
* LIFE-NARRATIVE (`reading_timeline`): Raman's Dasha-by-Dasha worked-reading structure — each
  period's active houses across the life.

ADDITIVE: the natal verdicts are NEVER changed; the unchanged `RamanReading` is carried as
`promise`. The reading is judged once (`read_chart`) and reused — no rule re-firing.

Usage:
    python -m app.raman_saab.cli --date 1809-02-12 --time 06:54 --tz -5 \
        --lat 37.5 --lon -85.5 --at 1865-04-14 --format text
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import swisseph as swe

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vd
from app.raman_saab.primitives.vimshottari import ActiveHouse, DashaPeriod, LordQuality
from app.raman_saab.proforma import RamanReading, read_chart


@dataclass(frozen=True)
class ActivatedHouseReading:
    """One lit house in a period: its activation grade + its UNCHANGED natal promise (verdict +
    degree) + the activating lord(s) and how well they deliver it."""
    house: int
    grade: str
    natal_verdict: str
    natal_degree: str
    md_lord: str
    antar_lord: Optional[str]
    md_activates: bool
    antar_activates: bool
    md_quality: LordQuality
    antar_quality: Optional[LordQuality]


@dataclass(frozen=True)
class DashaSnapshot:
    birth: BirthData
    jd: float
    period: Optional[DashaPeriod]
    activated: tuple[ActivatedHouseReading, ...]   # par_excellence first
    promise: RamanReading                          # the all-house reading, UNCHANGED


@dataclass(frozen=True)
class TimelinePeriodReading:
    period: DashaPeriod
    activated: tuple[ActivatedHouseReading, ...]


@dataclass(frozen=True)
class DashaTimeline:
    birth: BirthData
    promise: RamanReading
    periods: tuple[TimelinePeriodReading, ...]


def _today_jd() -> float:
    now = datetime.now(timezone.utc)
    return swe.julday(now.year, now.month, now.day, 12.0, swe.GREG_CAL)


def _activated_row(chart, promise: RamanReading, a: ActiveHouse) -> ActivatedHouseReading:
    pf = promise.proformas[a.house - 1]                 # proformas are ordered house 1..12
    # degree of the signification that DROVE the rollup (verdict == rollup), so the degree word
    # agrees with the verdict word (was significations[0], a frequently-different sub-matter).
    driver = next((sv for sv in pf.significations if sv.verdict == pf.rollup), None)
    degree = driver.degree if driver else (
        pf.significations[0].degree if pf.significations else "moderate")
    antar_q = vd.lord_quality(chart, a.antar_lord) if a.antar_lord is not None else None
    return ActivatedHouseReading(
        house=a.house, grade=a.grade, natal_verdict=pf.rollup, natal_degree=degree,
        md_lord=a.md_lord, antar_lord=a.antar_lord,
        md_activates=a.md_activates, antar_activates=a.antar_activates,
        md_quality=vd.lord_quality(chart, a.md_lord), antar_quality=antar_q)


def read_chart_on_date(birth: BirthData, jd: Optional[float] = None, *,
                       ayanamsa: str = "lahiri") -> DashaSnapshot:
    """Snapshot: the houses the running period lights up on `jd` (default today), each with its
    unchanged natal promise and the activating lord's delivery quality."""
    chart = cast_chart(birth, ayanamsa=ayanamsa)
    if jd is None:
        jd = _today_jd()
    promise = read_chart(birth, ayanamsa=ayanamsa)       # verdicts UNCHANGED (additive)
    period = vd.dasha_on(chart, jd)
    rows = tuple(_activated_row(chart, promise, a) for a in vd.active_houses(chart, jd))
    return DashaSnapshot(birth=birth, jd=jd, period=period, activated=rows, promise=promise)


def reading_timeline(birth: BirthData, *, ayanamsa: str = "lahiri",
                     expand_bhuktis: bool = False) -> DashaTimeline:
    """Life-narrative: walk the Vimshottari timeline (Mahadasha, or Mahadasha->Bhukti when
    `expand_bhuktis`), listing each period's active houses — Raman's Dasha-by-Dasha structure."""
    chart = cast_chart(birth, ayanamsa=ayanamsa)
    promise = read_chart(birth, ayanamsa=ayanamsa)
    periods: list[TimelinePeriodReading] = []
    for md in vd.mahadasha_timeline(chart):
        for span in (vd.bhuktis(md) if expand_bhuktis else [md]):
            sample = max(span.start_jd + 1.0, chart.jd_ut)   # clamp the pre-birth balance period
            rows = tuple(_activated_row(chart, promise, a)
                         for a in vd.active_houses(chart, sample))
            periods.append(TimelinePeriodReading(period=span, activated=rows))
    return DashaTimeline(birth=birth, promise=promise, periods=tuple(periods))
