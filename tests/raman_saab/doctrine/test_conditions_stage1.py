"""Stage-1a condition predicates — varga overlays (C2), Dwirdwadasha, sign-class
data, lords-conjunct, and the new "LORD_OF:n" frame origin.

Worked-example pins come from the HTJAH-I navamsa block (lines 1709-1789) and the
first-house combination list (lines 1105-1140). Charts are built via
``RamanChart.from_stated_positions`` so every test also exercises the sparse
Track-B path (missing planets must yield False, never raise).

Navamsa quick reference (element starts: Fire->Aries, Earth->Capricorn,
Air->Libra, Water->Cancer; one navamsa = 3°20'):
    1° Aries   -> Aries navamsa (part 0 of a fire sign)
    5° Aries   -> Taurus navamsa        21° Aries -> Libra navamsa
    1° Taurus  -> Capricorn navamsa     24° Taurus -> Leo navamsa
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C


def _ctx(lons: dict[str, float], asc_lon: float = 0.0) -> C.EvalContext:
    chart = RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")
    return C.EvalContext(chart)


class TestInVargaHouseFrom:
    def test_lagna_lord_in_12th_navamsa_from_varga_lagna_fires(self):
        """HTJAH-I:1709-1712: lord of Lagna in the 12th in the Navamsa — asc 5° Aries has
        navamsa-Lagna Taurus; Mars at 1° Aries falls in the Aries navamsa, 12th from it."""
        ctx = _ctx({"Mars": 1.0}, asc_lon=5.0)
        assert C.InVargaHouseFrom("Mars", "LAGNA", {12}).evaluate(ctx) is True
        assert C.InVargaHouseFrom("Mars", "LAGNA", {6, 8}).evaluate(ctx) is False

    def test_lagna_lord_in_8th_navamsa_from_2nd_lord_fires(self):
        """HTJAH-I:1714-1718 worked example: Lagnadhipati 'occupies 6th, 8th or 12th in the
        Navamsha from the sign held by the 2nd lord' — Mars (Lagna lord, 24° Taurus = Leo
        navamsa) is 8th from Venus (2nd lord, 1° Taurus = Capricorn navamsa)."""
        ctx = _ctx({"Mars": 54.0, "Venus": 31.0}, asc_lon=5.0)
        assert C.InVargaHouseFrom("Mars", "LORD_OF:2", {6, 8, 12}).evaluate(ctx) is True

    def test_lagna_lord_with_2nd_lord_in_same_navamsa_does_not_fire(self):
        """Same frame, negative: Mars at 1.5° Taurus shares the Capricorn navamsa with
        Venus (1st from it), so the 6/8/12 navamsa affliction does not fire."""
        ctx = _ctx({"Mars": 31.5, "Venus": 31.0}, asc_lon=5.0)
        assert C.InVargaHouseFrom("Mars", "LORD_OF:2", {6, 8, 12}).evaluate(ctx) is False

    def test_planet_origin_uses_both_d9_endpoints(self):
        """BOTH endpoints are varga positions: Mars (Leo navamsa) is 8th from Venus
        (Capricorn navamsa) although the two share Taurus in D1 (1st-from in rasi)."""
        ctx = _ctx({"Mars": 54.0, "Venus": 31.0}, asc_lon=5.0)
        assert C.InVargaHouseFrom("Mars", "Venus", {8}).evaluate(ctx) is True
        assert C.InHouseFrom("Mars", "Venus", 1).evaluate(ctx) is True  # D1 disagrees: proof

    def test_int_origin_counts_from_navamsa_lagna(self):
        """Integer origin n = the nth sign from the navamsa Lagna: navamsa-Lagna Taurus
        makes origin 2 = Gemini; Mars in the Aries navamsa is 11th from Gemini."""
        ctx = _ctx({"Mars": 1.0}, asc_lon=5.0)
        assert C.InVargaHouseFrom("Mars", 2, {11}).evaluate(ctx) is True
        assert C.InVargaHouseFrom("Mars", 2, 11).evaluate(ctx) is True  # bare-int houses ok

    def test_sparse_chart_missing_planet_or_origin_is_false(self):
        """Sparse Track-B chart: absent planet or absent origin lord -> False, no raise."""
        ctx = _ctx({"Mars": 54.0}, asc_lon=5.0)  # Venus (2nd lord) absent
        assert C.InVargaHouseFrom("Mars", "LORD_OF:2", {6, 8, 12}).evaluate(ctx) is False
        assert C.InVargaHouseFrom("Jupiter", "LAGNA", {12}).evaluate(ctx) is False
        assert C.InVargaHouseFrom("Mars", "MOON", {5}).evaluate(ctx) is False

    def test_unsupported_varga_raises_at_construction(self):
        """Only D9 is implemented; an unknown varga is an encoding error -> ValueError."""
        with pytest.raises(ValueError):
            C.InVargaHouseFrom("Mars", "LAGNA", {12}, varga="D10")


class TestVargaDignity:
    def test_exalted_in_navamsa_matches(self):
        """Sun at 1° Aries falls in the Aries navamsa — the Sun's exaltation sign."""
        assert C.VargaDignity("Sun", "D9", {"exalt"}).evaluate(_ctx({"Sun": 1.0})) is True

    def test_debilitated_in_navamsa_matches(self):
        """Sun at 21° Aries falls in the Libra navamsa — the Sun's debilitation sign."""
        ctx = _ctx({"Sun": 21.0})
        assert C.VargaDignity("Sun", "D9", {"debil"}).evaluate(ctx) is True
        assert C.VargaDignity("Sun", "D9", {"exalt", "own"}).evaluate(ctx) is False

    def test_own_navamsa_matches(self):
        """Mars at 1° Aries falls in the Aries navamsa — Mars's own sign."""
        assert C.VargaDignity("Mars", "D9", {"own"}).evaluate(_ctx({"Mars": 1.0})) is True

    def test_friendly_and_inimical_navamsa_use_naisargika(self):
        """Sun in a Cancer navamsa (lord Moon = natural friend) is 'friend'; in a Taurus
        navamsa (lord Venus = natural enemy) it is 'enemy'."""
        assert C.VargaDignity("Sun", "D9", {"friend"}).evaluate(_ctx({"Sun": 11.0})) is True
        assert C.VargaDignity("Sun", "D9", {"enemy"}).evaluate(_ctx({"Sun": 5.0})) is True

    def test_d1_moolatrikona_degree_is_ignored(self):
        """Sun at 5° Leo is inside its D1 moolatrikona arc, but varga dignity reads ONLY
        the D9 sign (Taurus navamsa -> 'enemy'): moolatrikona is a D1-degree concept."""
        assert C.VargaDignity("Sun", "D9", {"enemy"}).evaluate(_ctx({"Sun": 125.0})) is True

    def test_moolatrikona_state_rejected(self):
        """'moolatrikona' is not a legal varga state (no degree-within-sign in D9)."""
        with pytest.raises(ValueError):
            C.VargaDignity("Sun", "D9", {"moolatrikona"})

    def test_nodes_are_neutral(self):
        """Rahu/Ketu carry no varga dignity — always 'neutral' (mirrors primitives.dignity)."""
        ctx = _ctx({"Rahu": 1.0})
        assert C.VargaDignity("Rahu", "D9", {"neutral"}).evaluate(ctx) is True
        assert C.VargaDignity("Rahu", "D9", {"own", "exalt"}).evaluate(ctx) is False

    def test_sparse_chart_missing_planet_is_false(self):
        """Absent planet on a sparse chart -> False, no raise."""
        assert C.VargaDignity("Saturn", "D9", {"own"}).evaluate(_ctx({"Sun": 1.0})) is False

    def test_unsupported_varga_raises(self):
        """Only D9 is implemented -> ValueError for any other varga tag."""
        with pytest.raises(ValueError):
            C.VargaDignity("Sun", "D60", {"own"})


class TestDwirdwadasha:
    def test_pair_in_adjacent_signs_fires_both_orders(self):
        """Sun in Taurus and Moon in Gemini sit 2nd/12th from each other (symmetric)."""
        ctx = _ctx({"Sun": 31.0, "Moon": 61.0})
        assert C.PlanetPairIn2_12("Sun", "Moon").evaluate(ctx) is True
        assert C.PlanetPairIn2_12("Moon", "Sun").evaluate(ctx) is True

    def test_pair_same_sign_or_trine_does_not_fire(self):
        """Conjunction (1st-from) and trine (5/9) placements are not Dwirdwadasha."""
        assert C.PlanetPairIn2_12("Sun", "Mars").evaluate(
            _ctx({"Sun": 31.0, "Mars": 35.0})) is False
        assert C.PlanetPairIn2_12("Sun", "Jupiter").evaluate(
            _ctx({"Sun": 31.0, "Jupiter": 155.0})) is False

    def test_pair_includes_nodes_as_placed(self):
        """Nodes count as placed: Rahu in Gemini is 2nd from the Sun in Taurus."""
        assert C.PlanetPairIn2_12("Sun", "Rahu").evaluate(
            _ctx({"Sun": 31.0, "Rahu": 61.0})) is True

    def test_pair_sparse_chart_is_false(self):
        """Either planet absent on a sparse chart -> False, no raise."""
        assert C.PlanetPairIn2_12("Sun", "Moon").evaluate(_ctx({"Sun": 31.0})) is False

    def test_aggregate_chain_of_adjacent_signs_fires(self):
        """HTJAH-I:1138-1140 affliction form: Taurus-Gemini-Cancer chain — every planet
        is 2nd/12th from at least one other planet."""
        ctx = _ctx({"Sun": 31.0, "Venus": 35.0, "Moon": 61.0, "Mars": 95.0})
        assert C.AllPlanetsInDwirdwadasha().evaluate(ctx) is True

    def test_aggregate_one_isolated_planet_still_fires_almost_all(self):
        """HTJAH-I:1981 / 2223 "almost all planets in DwirdwaDasha": a SINGLE isolated
        planet does NOT exonerate an otherwise web-bound chart. Sun(Taurus)/Moon(Gemini)
        are a 2/12 pair; Jupiter alone in Sagittarius is the one isolated body -> the
        web still binds (unpaired == 1) -> True. (Under the old strict every-planet
        reading this was False, making the fortunate negation almost always vacuously
        True; the corpus "almost all" threshold restores its discriminating power.)"""
        ctx = _ctx({"Sun": 31.0, "Moon": 61.0, "Jupiter": 245.0})
        assert C.AllPlanetsInDwirdwadasha().evaluate(ctx) is True

    def test_aggregate_two_isolated_planets_break_the_web(self):
        """Two (or more) unpaired planets exceed the "almost all" tolerance -> False,
        so the #34 fortunate negation fires for a genuinely scattered chart.
        Sun(Taurus)/Moon(Gemini) pair; Jupiter(Sagittarius) AND Saturn(Leo, 125deg)
        are BOTH isolated (Leo is 4th from Taurus, not 2/12; Sagittarius is 8th) ->
        unpaired == 2 -> False."""
        ctx = _ctx({"Sun": 31.0, "Moon": 61.0, "Jupiter": 245.0, "Saturn": 125.0})
        assert C.AllPlanetsInDwirdwadasha().evaluate(ctx) is False

    def test_aggregate_sparse_chart_is_false(self):
        """Fewer than two planets cannot form a Dwirdwadasha web -> False, no raise."""
        assert C.AllPlanetsInDwirdwadasha().evaluate(_ctx({"Sun": 31.0})) is False
        assert C.AllPlanetsInDwirdwadasha().evaluate(_ctx({})) is False


class TestSignClassHelpers:
    def test_sushka_signs_are_signs_owned_by_mars_saturn_and_sun(self):
        """HTJAH-I:1106-1107: Sushka rashis = signs owned by Mars, Saturn and the Sun
        (Aries, Leo, Scorpio, Capricorn, Aquarius)."""
        assert C.SUSHKA_SIGNS == frozenset({1, 5, 8, 10, 11})
        for s in (1, 5, 8, 10, 11):
            assert C.SignIsSushka(s) is True
        for s in (2, 3, 4, 6, 7, 9, 12):
            assert C.SignIsSushka(s) is False

    def test_watery_signs_are_cancer_scorpio_pisces(self):
        """HTJAH-I:1109: the corpulence (watery) rashis are Cancer, Scorpio and Pisces."""
        assert C.WATERY_SIGNS == frozenset({4, 8, 12})
        assert C.SignIsWatery(4) is True
        assert C.SignIsWatery(12) is True
        assert C.SignIsWatery(1) is False
        assert C.SignIsWatery(10) is False

    def test_scorpio_is_both_sushka_and_watery(self):
        """Scorpio (8) is Sushka by Mars-ownership AND watery by element — both hold."""
        assert C.SignIsSushka(8) is True
        assert C.SignIsWatery(8) is True

    def test_sushka_and_watery_planet_data(self):
        """HTJAH-I:1105-1106 + 1109-1110: Sushka planets = Sun, Mars, Saturn; watery
        planets = Venus and the Moon."""
        assert C.SUSHKA_PLANETS == frozenset({"Sun", "Mars", "Saturn"})
        assert C.WATERY_PLANETS == frozenset({"Venus", "Moon"})


class TestLordsConjunct:
    def test_lagna_lord_with_6th_lord_fires(self):
        """Aries Lagna: lord of 1 (Mars) and lord of 6 (Mercury, Virgo) share Leo."""
        ctx = _ctx({"Mars": 125.0, "Mercury": 127.0})
        assert C.LordsConjunct(1, 6).evaluate(ctx) is True

    def test_lords_in_different_signs_does_not_fire(self):
        """Mars in Leo, Mercury in Virgo — different rasis, not conjunct."""
        ctx = _ctx({"Mars": 125.0, "Mercury": 155.0})
        assert C.LordsConjunct(1, 6).evaluate(ctx) is False

    def test_same_planet_lording_both_houses_is_not_a_conjunction(self):
        """Taurus Lagna: Venus lords both 1 and 6 (Libra) — identity lordship is not a
        conjunction of two lords, so False by documented convention."""
        ctx = _ctx({"Venus": 35.0}, asc_lon=35.0)
        assert C.LordsConjunct(1, 6).evaluate(ctx) is False

    def test_sparse_chart_missing_lord_is_false(self):
        """6th lord Mercury absent on a sparse chart -> False, no raise."""
        assert C.LordsConjunct(1, 6).evaluate(_ctx({"Mars": 125.0})) is False


class TestLordOfOrigin:
    def test_in_house_from_lord_of_2nd(self):
        """Aries Lagna: 2nd lord Venus in Taurus; the Sun in Cancer is 3rd from Venus."""
        ctx = _ctx({"Venus": 31.0, "Sun": 95.0})
        assert C.InHouseFrom("Sun", "LORD_OF:2", 3).evaluate(ctx) is True
        assert C.InHouseFrom("Sun", "LORD_OF:2", 4).evaluate(ctx) is False

    def test_class_in_house_from_lord_of_9th(self):
        """Aries Lagna: 9th lord Jupiter in Sagittarius; Saturn (malefic) in Capricorn
        sits 2nd from it."""
        ctx = _ctx({"Jupiter": 245.0, "Saturn": 275.0})
        assert C.ClassInHouseFrom("malefic", "LORD_OF:9", {2}).evaluate(ctx) is True
        assert C.ClassInHouseFrom("benefic", "LORD_OF:9", {2}).evaluate(ctx) is False

    def test_house_number_wraps_modulo_12(self):
        """'LORD_OF:14' normalises to 'LORD_OF:2' (mirrors int-origin wrapping)."""
        ctx = _ctx({"Venus": 31.0, "Sun": 95.0})
        assert C.InHouseFrom("Sun", "LORD_OF:14", 3).evaluate(ctx) is True

    def test_sparse_chart_missing_lord_is_false(self):
        """2nd lord Venus absent -> origin unresolvable -> False, no raise."""
        assert C.InHouseFrom("Sun", "LORD_OF:2", 3).evaluate(_ctx({"Sun": 95.0})) is False

    def test_malformed_lord_of_origin_raises(self):
        """A malformed LORD_OF origin is an encoding bug -> ValueError at evaluation."""
        with pytest.raises(ValueError):
            C.InHouseFrom("Sun", "LORD_OF:x", 3).evaluate(_ctx({"Sun": 95.0}))
