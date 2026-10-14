"""Drekkana (decanate, D3) — BPHS ch.6 sl.7-8.

Pins the 1st/5th/9th-from-sign decanate rule, the part index, deities, lord derivation, full body
coverage, and the citation.
"""
from __future__ import annotations

from app.parashara.chart.cast import cast
from app.parashara.doctrine.drekkana import DEITIES, SOURCE, drekkana, drekkana_all
from app.parashara.doctrine.sources import verify


class TestDecanate:
    def test_first_decanate_is_the_sign_itself(self):
        d = drekkana(5.0)          # Aries 5 deg
        assert d.index == 1 and d.sign == 1 and d.lord == "Mars" and d.deity == "Narada"

    def test_second_decanate_is_fifth_from_sign(self):
        d = drekkana(15.0)         # Aries 15 deg -> Leo
        assert d.index == 2 and d.sign == 5 and d.deity == "Agasthya"

    def test_third_decanate_is_ninth_from_sign(self):
        d = drekkana(25.0)         # Aries 25 deg -> Sagittarius
        assert d.index == 3 and d.sign == 9 and d.deity == "Doorvasa"

    def test_index_by_degree(self):
        assert drekkana(0.0).index == 1
        assert drekkana(45.0).index == 2       # Taurus 15 deg
        assert drekkana(359.0).index == 3      # Pisces 29 deg

    def test_deities_are_the_three_sages(self):
        assert DEITIES == ("Narada", "Agasthya", "Doorvasa")


class TestChart:
    def test_all_bodies_covered(self):
        ch = cast(year=1990, month=7, day=15, hour=12, minute=0,
                  tz_offset=5.5, latitude=12.97, longitude=77.59)
        da = drekkana_all(ch.longitudes)
        for b in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
            assert b in da and 1 <= da[b].index <= 3 and 1 <= da[b].sign <= 12


class TestCitation:
    def test_source_resolves(self):
        assert verify(SOURCE) and SOURCE.work == "BPHS-6"
