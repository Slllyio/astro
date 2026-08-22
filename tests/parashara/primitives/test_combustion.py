"""Combustion / Astangata (BPHS ch.7) — a planet within its orb of the Sun.

Pinned to Parashara's table (Mercury 14 direct / 12 retro, Venus 10/8, Mars 17/8) and to the two
never-combust rules: the Sun itself and the nodes. Circular separation across the 0/360 cusp is
checked too.
"""
from __future__ import annotations

from app.parashara.doctrine.sources import verify
from app.parashara.primitives import combustion as C


class TestIsCombust:
    def test_mercury_within_14_is_combust(self):
        assert C.is_combust("Mercury", 100.0, 110.0) is True        # 10 deg < 14
        assert C.is_combust("Mercury", 100.0, 120.0) is False       # 20 deg > 14

    def test_retrograde_uses_the_smaller_orb(self):
        # Mercury 13 deg from Sun: combust direct (orb 14), NOT combust retrograde (orb 12).
        assert C.is_combust("Mercury", 100.0, 113.0, retrograde=False) is True
        assert C.is_combust("Mercury", 100.0, 113.0, retrograde=True) is False

    def test_sun_and_nodes_never_combust(self):
        assert C.is_combust("Sun", 100.0, 100.0) is False
        assert C.is_combust("Rahu", 101.0, 100.0) is False
        assert C.is_combust("Ketu", 99.5, 100.0) is False

    def test_separation_wraps_across_zero(self):
        # Venus at 359, Sun at 2 -> 3 deg apart -> combust (orb 10), despite the raw diff being 357.
        assert C.is_combust("Venus", 359.0, 2.0) is True


class TestCombustPlanets:
    def test_lists_combust_and_respects_retrograde_speed(self):
        lons = {"Sun": 100.0, "Mercury": 108.0, "Mars": 100.0, "Jupiter": 200.0}
        # Mercury 8 deg (combust), Mars 0 deg (combust), Jupiter far (not).
        got = C.combust_planets(lons, speeds={"Mercury": 1.0, "Mars": 0.5})
        assert set(got) == {"Mercury", "Mars"}

    def test_no_sun_is_empty(self):
        assert C.combust_planets({"Mars": 10.0}) == ()


class TestCitation:
    def test_source_resolves(self):
        assert verify(C.SOURCE)
