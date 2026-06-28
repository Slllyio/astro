"""Ashtakavarga — the canonical-total checksum. Each planet's Bhinnashtakavarga total is fixed,
and the Sarvashtakavarga total across all 12 signs is ALWAYS 337, regardless of the chart. These
invariants catch any benefic-places table error that would otherwise be silent.
"""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import ashtakavarga as av

_BLR = BirthData(name="BLR", year=1990, month=7, day=15, hour=12, minute=0,
                 tz_offset=5.5, latitude=12.97, longitude=77.59)
_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def test_each_bav_total_is_canonical():
    """Every planet's Bhinnashtakavarga sums to its fixed canonical total."""
    ch = cast_chart(_BLR, ayanamsa="raman")
    for planet, total in av.BAV_TOTALS.items():
        assert sum(av.bhinnashtakavarga(ch, planet).values()) == total, planet


def test_sav_total_is_337():
    """Sarvashtakavarga across the 12 signs is always 337 (sum of 48+49+39+54+56+52+39)."""
    for bd in (_BLR, _MAINPURI):
        ch = cast_chart(bd, ayanamsa="lahiri")
        assert sum(av.sarvashtakavarga(ch).values()) == 337
        assert sum(av.BAV_TOTALS.values()) == 337


def test_benefic_table_house_values_in_range():
    """Sanity: every benefic-place house is 1..12 and every planet has all 8 references."""
    for planet, refs in av._BENEFIC.items():
        assert set(refs) == set(av._REFS), planet
        for houses in refs.values():
            assert all(1 <= h <= 12 for h in houses)


def test_bindus_in_house_matches_sav():
    ch = cast_chart(_MAINPURI, ayanamsa="lahiri")
    sav = av.sarvashtakavarga(ch)
    for h in range(1, 13):
        sign = ((ch.asc_sign - 1) + (h - 1)) % 12 + 1
        assert av.bindus_in_house(ch, h) == sav[sign]
