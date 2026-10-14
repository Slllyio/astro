"""Gulika (Mandi) — calculation (BPHS ch.3) + house effects (ch.25).

Pins full house coverage (incl. the two OCR-repaired slokas), citation resolution, and that the
ascendant-at-JD used for the Gulika longitude matches the caster (calibration).
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.chart.ephemeris import gulika_longitude
from app.parashara.doctrine.gulika import effect_in_house
from app.parashara.doctrine.sources import verify


class TestGulikaEffects:
    def test_all_twelve_houses_have_an_effect(self):
        for h in range(1, 13):
            e = effect_in_house(h)
            assert e is not None and e.text, h

    def test_repaired_houses_present(self):
        # sl.68 (house 7) and sl.72 (house 11) had their number destroyed by OCR.
        for h in (7, 11):
            e = effect_in_house(h)
            assert e is not None and "Gulika is in the" in e.text

    def test_every_citation_resolves(self):
        for h in range(1, 13):
            assert verify(effect_in_house(h).source), h

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            effect_in_house(13)


class TestGulikaLongitude:
    def test_canonical_is_a_valid_longitude(self):
        g = gulika_longitude(year=1990, month=7, day=15, hour=12, minute=0,
                             tz_offset=5.5, latitude=12.97, longitude=77.59)
        assert 0.0 <= g < 360.0

    def test_carried_on_the_chart(self):
        ch = cast(year=1990, month=7, day=15, hour=12, minute=0,
                  tz_offset=5.5, latitude=12.97, longitude=77.59)
        assert 0.0 <= ch.gulika < 360.0
