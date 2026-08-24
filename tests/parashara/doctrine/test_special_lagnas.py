"""Special ascendants — Bhava / Hora / Ghatika Lagna (BPHS ch.5).

The load-bearing test is Parashara's OWN worked example: Sun at sunrise 132deg, birth 12gh30vi ->
Bhava Lagna Libra 27deg (207), Hora Lagna Capricorn 12deg (282), Ghatika Lagna Leo 27deg (147).
Also pins the per-ghati rates and that the ephemeris path yields valid longitudes on a cast chart.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.chart.ephemeris import special_lagnas as ephem_special_lagnas
from app.parashara.doctrine.special_lagnas import PERIODS, SOURCE, special_lagna_longitudes
from app.parashara.doctrine.sources import verify


class TestWorkedExample:
    def test_bphs_ch5_example(self):
        sl = special_lagna_longitudes(132.0, 12.5)     # Sun 132deg, 12gh30vi past sunrise
        assert sl["Bhava"] == pytest.approx(207.0)     # Libra 27
        assert sl["Hora"] == pytest.approx(282.0)      # Capricorn 12
        assert sl["Ghati"] == pytest.approx(147.0)     # Leo 27 (507 - 360)

    def test_periods(self):
        assert PERIODS == {"Bhava": 5.0, "Hora": 2.5, "Ghati": 1.0}

    def test_ghati_advances_one_sign_per_ghati(self):
        base = special_lagna_longitudes(0.0, 0.0)["Ghati"]
        assert base == 0.0
        assert special_lagna_longitudes(0.0, 1.0)["Ghati"] == pytest.approx(30.0)
        assert special_lagna_longitudes(0.0, 2.0)["Ghati"] == pytest.approx(60.0)

    def test_all_in_range(self):
        for g in (0.0, 30.0, 59.9):
            for v in special_lagna_longitudes(200.0, g).values():
                assert 0.0 <= v < 360.0


class TestEphemerisPath:
    def test_cast_chart_carries_three_special_lagnas(self):
        ch = cast(year=1990, month=7, day=15, hour=12, minute=0,
                  tz_offset=5.5, latitude=12.97, longitude=77.59)
        assert set(ch.special_lagnas) == {"Bhava", "Hora", "Ghati"}
        for v in ch.special_lagnas.values():
            assert 0.0 <= v < 360.0

    def test_ephemeris_helper_matches_the_chart(self):
        kw = dict(year=1990, month=7, day=15, hour=12, minute=0,
                  tz_offset=5.5, latitude=12.97, longitude=77.59)
        ch = cast(**kw)
        assert ephem_special_lagnas(**kw) == ch.special_lagnas


class TestCitation:
    def test_source_resolves(self):
        assert verify(SOURCE) and SOURCE.work == "BPHS-5"
