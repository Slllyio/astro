"""Dhana (wealth) yogas — BPHS ch.41, the crisp two families.

Pins a representative of each family (own-sign 5th + 11th planets; own-sign lagna + aspecters),
the negative case, and that every fired yoga cites a real BPHS-41 line.
"""
from __future__ import annotations

from app.parashara.doctrine.dhana_yogas import SOURCE, detect
from app.parashara.doctrine.sources import verify


def _names(ys):
    return {y.name for y in ys}


class TestFamilyA:
    def test_venus_own_fifth_mars_eleventh(self):
        # Gemini asc (3): 5th = Libra (Venus own); Venus in Libra(195), Mars in the 11th (Aries, 5deg)
        lons = {"Venus": 195.0, "Mars": 5.0, "Sun": 100.0, "Moon": 130.0,
                "Mercury": 160.0, "Jupiter": 220.0, "Saturn": 300.0}
        ys = detect(lons, asc_sign=3)
        assert any("Venus in own sign in the 5th" in n for n in _names(ys))

    def test_requires_the_eleventh_planet(self):
        # same but Mars NOT in the 11th -> no yoga
        lons = {"Venus": 195.0, "Mars": 100.0, "Sun": 40.0, "Moon": 130.0,
                "Mercury": 160.0, "Jupiter": 220.0, "Saturn": 300.0}
        assert not any("Venus in own sign in the 5th" in n for n in _names(detect(lons, asc_sign=3)))


class TestFamilyB:
    def test_sun_own_lagna_aspected_by_mars_jupiter(self):
        # Leo asc (5): Sun in Leo (125), Mars conjunct (128), Jupiter in Aries (5) aspects Leo (5th)
        lons = {"Sun": 125.0, "Mars": 128.0, "Jupiter": 5.0, "Moon": 200.0,
                "Mercury": 230.0, "Venus": 260.0, "Saturn": 290.0}
        ys = detect(lons, asc_sign=5)
        assert any("Sun in own-sign lagna" in n for n in _names(ys))

    def test_needs_both_aspecters(self):
        # Jupiter removed from aspecting -> no Sun yoga
        lons = {"Sun": 125.0, "Mars": 128.0, "Jupiter": 200.0, "Moon": 40.0,
                "Mercury": 230.0, "Venus": 260.0, "Saturn": 290.0}
        assert not any("Sun in own-sign lagna" in n for n in _names(detect(lons, asc_sign=5)))


class TestCitations:
    def test_fired_yogas_cite_ch41(self):
        lons = {"Venus": 195.0, "Mars": 5.0, "Sun": 100.0, "Moon": 130.0,
                "Mercury": 160.0, "Jupiter": 220.0, "Saturn": 300.0}
        for y in detect(lons, asc_sign=3):
            assert verify(y.source) and y.source.work == "BPHS-41"

    def test_source_resolves(self):
        assert verify(SOURCE) and SOURCE.work == "BPHS-41"
