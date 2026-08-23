"""Maraka planets (BPHS ch.44) — lords of 2nd/7th + malefics in/with them."""
from __future__ import annotations

from app.parashara.doctrine.maraka import maraka_planets
from app.parashara.doctrine.sources import verify


def _names(ms):
    return {m.planet for m in ms}


class TestMaraka:
    def test_second_and_seventh_lords_are_marakas(self):
        # Aries lagna: 2nd = Taurus (Venus), 7th = Libra (Venus). So Venus is the maraka lord.
        ms = maraka_planets({"Venus": 2}, asc_sign=1)
        assert "Venus" in _names(ms)
        assert any("2nd" in m.reason and "stronger" in m.reason for m in ms if m.planet == "Venus")

    def test_malefic_in_a_maraka_house(self):
        # Aries lagna: Saturn in the 7th (Libra) -> a malefic in a maraka house.
        ms = maraka_planets({"Saturn": 7}, asc_sign=1)
        sat = next(m for m in ms if m.planet == "Saturn")
        assert "malefic" in sat.reason

    def test_malefic_conjunct_a_maraka_lord(self):
        # Aries lagna, 2nd/7th lord Venus in Gemini(3); Mars also in Gemini -> conjunct a maraka lord.
        ms = maraka_planets({"Venus": 3, "Mars": 3}, asc_sign=1)
        assert "Mars" in _names(ms)

    def test_second_is_the_stronger_maraka(self):
        ms = maraka_planets({"Venus": 5}, asc_sign=1)   # Venus lords both 2nd and 7th for Aries
        assert any("stronger" in m.reason for m in ms)

    def test_source_resolves(self):
        assert verify(maraka_planets({"Venus": 2}, asc_sign=1)[0].source)
