"""Kartari (hemming) primitive — `doctrine/hemming.py`.

Papakartari/Subhakartari geometry: a house or planet hemmed when the 2nd and the 12th from it
are both occupied by one class of planet. The planet form was already covered by the DSL leaf
`conditions.HemmedBy`; the house form (an EMPTY bhava hemmed) is the new capability. Each test
states the geometric fact it checks.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import hemming


def _chart(planets: dict[str, float], asc_lon: float = 5.0) -> RamanChart:
    stated = {n: {"lon": lo, "bhava": 1} for n, lo in planets.items()}
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


class TestHouseForm:
    def test_empty_lagna_is_hemmed_by_flanking_malefics(self) -> None:
        """Aries asc, empty Lagna: a malefic in Pisces (12th) and Taurus (2nd) hem it — the
        capability the planet-only leaf lacks (no planet sits in the Lagna to key on)."""
        c = _chart({"Ketu": 345.0, "Mars": 45.0})       # Pisces(12th), Taurus(2nd)
        assert hemming.hemmed_house(c, 1) is True

    def test_one_side_only_is_not_hemmed(self) -> None:
        """A malefic on only ONE flank does not hem — both the 2nd and the 12th are required."""
        c = _chart({"Mars": 45.0})                        # Taurus(2nd) only
        assert hemming.hemmed_house(c, 1) is False

    def test_benefic_flanks_are_not_malefic_hemming(self) -> None:
        """Benefics flanking give subhakartari, not papakartari."""
        c = _chart({"Jupiter": 345.0, "Venus": 45.0})     # Pisces, Taurus — both benefic
        assert hemming.hemmed_house(c, 1, "malefic") is False
        assert hemming.hemmed_house(c, 1, "benefic") is True

    def test_house_form_uses_the_2nd_and_12th_from_the_target(self) -> None:
        """The 7th house (Libra, from Aries asc) is hemmed by malefics in the 6th (Virgo) and
        8th (Scorpio) — the 2nd and 12th counted FROM the 7th, not from the Lagna."""
        c = _chart({"Saturn": 160.0, "Rahu": 220.0})      # Virgo(6th), Scorpio(8th)
        assert hemming.hemmed_house(c, 7) is True
        assert hemming.hemmed_house(c, 1) is False         # the Lagna's own flanks are empty


class TestPlanetForm:
    def test_planet_hemmed_by_adjacent_sign_malefics(self) -> None:
        """The Moon in Cancer (4th) hemmed by malefics in Gemini (3rd) and Leo (5th)."""
        c = _chart({"Moon": 100.0, "Mars": 70.0, "Saturn": 130.0})
        assert hemming.hemmed_planet(c, "Moon") is True

    def test_absent_planet_reads_false(self) -> None:
        """A Track-B sparse chart with no such planet is never hemmed (None-safe)."""
        c = _chart({"Mars": 45.0})
        assert hemming.hemmed_planet(c, "Venus") is False

    def test_nodes_count_as_flankers(self) -> None:
        """Rahu/Ketu are natural malefics and Raman's paradigmatic flankers — they hem by the
        sign they occupy though they own none (HTJAH-I:1127)."""
        c = _chart({"Sun": 100.0, "Rahu": 70.0, "Ketu": 130.0})   # nodes flank the Sun
        assert hemming.hemmed_planet(c, "Sun") is True


class TestSharedGeometry:
    def test_dsl_leaf_delegates_to_the_primitive(self) -> None:
        """`conditions.HemmedBy` (the planet-form DSL leaf) now delegates to the same geometry
        — refactor guard: the leaf and the primitive agree on every planet."""
        from app.raman_saab.doctrine.conditions import EvalContext, HemmedBy
        c = _chart({"Moon": 100.0, "Mars": 70.0, "Saturn": 130.0, "Jupiter": 200.0})
        ctx = EvalContext(c)
        for planet in ("Moon", "Jupiter", "Mars"):
            leaf = HemmedBy(planet, "malefic").evaluate(ctx)
            prim = hemming.hemmed_planet(c, planet, "malefic")
            assert leaf == prim, planet
