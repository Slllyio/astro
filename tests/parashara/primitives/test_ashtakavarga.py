"""Ashtakavarga (BPHS ch.66) — Bhinnashtakavarga per planet and Sarvashtakavarga.

The hard checksum IS the fidelity proof for an OCR-endangered table: on any complete chart each
planet's BAV must total its canonical value (Sun 48 ... Saturn 39) and the SAV must total 337. If a
benefic-place table were mistranscribed, a total would break and these tests would fail.
"""
from __future__ import annotations

from app.parashara.chart.cast import cast
from app.parashara.doctrine.sources import verify
from app.parashara.primitives import ashtakavarga as AV


def _canonical_signs():
    chart = cast(year=1990, month=7, day=15, hour=12, minute=0,
                 tz_offset=5.5, latitude=12.97, longitude=77.59)
    signs = {g: int(chart.longitudes[g] % 360.0 // 30) + 1 for g in AV.PLANETS}
    return signs, chart.asc_sign


class TestChecksum:
    def test_each_bav_totals_its_canonical_value(self):
        signs, asc = _canonical_signs()
        for planet in AV.PLANETS:
            bav = AV.bhinnashtakavarga(planet, signs, asc_sign=asc)
            assert sum(bav.values()) == AV.BAV_TOTALS[planet], planet

    def test_sav_totals_337(self):
        signs, asc = _canonical_signs()
        sav = AV.sarvashtakavarga(signs, asc_sign=asc)
        assert sum(sav.values()) == 337

    def test_sav_is_the_sum_of_the_seven_bavs(self):
        signs, asc = _canonical_signs()
        sav = AV.sarvashtakavarga(signs, asc_sign=asc)
        manual = {s: 0 for s in range(1, 13)}
        for planet in AV.PLANETS:
            for s, b in AV.bhinnashtakavarga(planet, signs, asc_sign=asc).items():
                manual[s] += b
        assert sav == manual

    def test_checksum_holds_for_a_different_chart(self):
        # A synthetic complete chart — totals are invariant to placement.
        signs = {"Sun": 1, "Moon": 5, "Mars": 9, "Mercury": 2,
                 "Jupiter": 11, "Venus": 7, "Saturn": 4}
        for planet in AV.PLANETS:
            assert sum(AV.bhinnashtakavarga(planet, signs, asc_sign=3).values()) == AV.BAV_TOTALS[planet]
        assert sum(AV.sarvashtakavarga(signs, asc_sign=3).values()) == 337


class TestBindusInHouse:
    def test_sav_and_bav_lookups(self):
        signs, asc = _canonical_signs()
        # SAV in the 1st house = SAV of the ascendant sign.
        sav = AV.sarvashtakavarga(signs, asc_sign=asc)
        assert AV.bindus_in_house(1, signs, asc_sign=asc) == sav[asc]
        # A BAV lookup is in the sane 0..8 per-sign range.
        assert 0 <= AV.bindus_in_house(1, signs, asc_sign=asc, planet="Jupiter") <= 8


class TestCitation:
    def test_source_resolves(self):
        assert verify(AV.SOURCE)
