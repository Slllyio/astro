"""Proforma assembly — the one pure entry point `read_chart(birth) -> RamanReading`
(spec §9). Casts the chart and judges all 12 houses through the MODERN judge
(`house_template`), which carries the cited rule-engine verdict, the graded degree, AND
the metadata overlays (yoga / ayurdaya / beeja-kshetra / drekkana / Dasha event-timing).
`houses` keeps the legacy `HouseVerdict` shape for back-compat; `proformas` carries the
full modern per-house result incl. `metadata`.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges.house_judge import HouseVerdict
from app.raman_saab.judges.house_template import HouseProforma, judge_house


@dataclass(frozen=True)
class RamanReading:
    birth: BirthData
    ayanamsa: str
    asc_sign: int
    asc_lon: float
    houses: tuple[HouseVerdict, ...]
    proformas: tuple[HouseProforma, ...] = ()


def read_chart(birth: BirthData, *, ayanamsa: str = "raman") -> RamanReading:
    """Birth data -> a deterministic, cited, house-by-house Raman reading (modern judge)."""
    chart = cast_chart(birth, ayanamsa=ayanamsa)
    proformas = tuple(judge_house(chart, h) for h in range(1, 13))
    houses = tuple(p.as_house_verdict() for p in proformas)
    return RamanReading(birth=birth, ayanamsa=chart.ayanamsa, asc_sign=chart.asc_sign,
                        asc_lon=chart.asc_lon, houses=houses, proformas=proformas)
