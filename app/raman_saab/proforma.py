"""Proforma assembly — the one pure entry point `read_chart(birth) -> RamanReading`
(spec §9). Casts the chart and judges all 12 houses into an ordinal, fully-cited
reading. Longevity / timeline / chart-overview overlays land here in Phases 4-5.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges.house_judge import HouseVerdict, judge_all_houses


@dataclass(frozen=True)
class RamanReading:
    birth: BirthData
    ayanamsa: str
    asc_sign: int
    asc_lon: float
    houses: tuple[HouseVerdict, ...]


def read_chart(birth: BirthData, *, ayanamsa: str = "raman") -> RamanReading:
    """Birth data -> a deterministic, cited, house-by-house Raman reading."""
    chart = cast_chart(birth, ayanamsa=ayanamsa)
    return RamanReading(birth=birth, ayanamsa=chart.ayanamsa, asc_sign=chart.asc_sign,
                        asc_lon=chart.asc_lon, houses=tuple(judge_all_houses(chart)))
