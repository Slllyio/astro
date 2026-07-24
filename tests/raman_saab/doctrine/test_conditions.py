"""The condition algebra — composable predicates over a chart (Phase 2, first batch)."""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C


def _ctx(lons: dict[str, float], asc_lon: float = 0.0) -> C.EvalContext:
    chart = RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")
    return C.EvalContext(chart)


def test_leaf_predicates():
    ctx = _ctx({"Saturn": 185.0, "Sun": 5.0})  # Aries lagna: Saturn 7th(Libra), Sun 1st(Aries)
    assert C.InRashiHouse("Saturn", 7).evaluate(ctx) is True
    assert C.InRashiHouse("Saturn", 8).evaluate(ctx) is False
    assert C.InSign("Sun", 1).evaluate(ctx) is True
    assert C.Aspects("Saturn", "Sun").evaluate(ctx) is True   # 7th aspect
    assert C.HasDignity("Sun", {"exalt"}).evaluate(ctx) is True   # Sun in Aries = exalt sign


def test_combinators_and_operators():
    ctx = _ctx({"Saturn": 185.0, "Sun": 5.0})
    rule = C.And(C.InRashiHouse("Saturn", 7), C.Aspects("Saturn", "Sun"))
    assert rule.evaluate(ctx) is True
    # operator forms
    assert (C.InRashiHouse("Sun", 1) & C.InSign("Sun", 1)).evaluate(ctx) is True
    assert (C.InRashiHouse("Sun", 2) | C.InSign("Sun", 1)).evaluate(ctx) is True
    assert (~C.InRashiHouse("Sun", 2)).evaluate(ctx) is True
    assert C.AtLeastN(2, [C.InRashiHouse("Sun", 1), C.InSign("Sun", 1),
                          C.InRashiHouse("Sun", 9)]).evaluate(ctx) is True   # 2 of 3 true


def test_lord_in():
    # Aries lagna: 7th lord = Venus (Libra). Venus in the 1st (Aries) -> LordIn(7, 1).
    ctx = _ctx({"Venus": 5.0})
    assert C.LordIn(7, 1).evaluate(ctx) is True
    assert C.LordIn(7, 2).evaluate(ctx) is False


def test_missing_planet_is_false_not_error():
    ctx = _ctx({"Sun": 5.0})
    assert C.InRashiHouse("Mars", 1).evaluate(ctx) is False
    assert C.Aspects("Mars", "Sun").evaluate(ctx) is False
    assert C.Combust("Mars").evaluate(ctx) is False


def test_in_house_from_origin():
    # Moon in 1st (Aries), Mars in 7th (Libra) -> Mars is 7th from the Moon.
    ctx = _ctx({"Moon": 5.0, "Mars": 185.0})
    assert C.InHouseFrom("Mars", "MOON", 7).evaluate(ctx) is True
    assert C.InHouseFrom("Mars", "LAGNA", 7).evaluate(ctx) is True
    assert C.InHouseFrom("Mars", "MOON", 4).evaluate(ctx) is False


def test_tara_of():
    # Moon @5.0 -> nakshatra 1 (Janma). Saturn @30.0 -> nakshatra 3 -> the 3rd (vipat) tara.
    ctx = _ctx({"Moon": 5.0, "Saturn": 30.0})
    assert C.TaraOf("Saturn", {3, 5, 7}).evaluate(ctx) is True     # vipat
    assert C.TaraOf("Saturn", {1, 4}).evaluate(ctx) is False
    # Dynamic subject: Aries lagna lord = Mars. Mars @60.0 -> nakshatra 5 -> the 5th (pratyak) tara.
    ctx2 = _ctx({"Moon": 5.0, "Mars": 60.0})
    assert C.TaraOf("LORD_OF:1", {3, 5, 7}).evaluate(ctx2) is True  # pratyak
    # Mars @45.0 -> nakshatra 4 -> the 4th (kshema) tara, not a malefic tara.
    ctx3 = _ctx({"Moon": 5.0, "Mars": 45.0})
    assert C.TaraOf("LORD_OF:1", {3, 5, 7}).evaluate(ctx3) is False


def test_tara_of_is_none_safe():
    # No Moon (no Janma nakshatra) or absent subject -> False, never an error.
    assert C.TaraOf("Saturn", {3}).evaluate(_ctx({"Saturn": 30.0})) is False
    assert C.TaraOf("Mars", {3}).evaluate(_ctx({"Moon": 5.0})) is False


def test_neecha_bhanga_resolves_dynamic_lord_subject():
    # Aries lagna, 1st lord = Mars debilitated in Cancer (h4); the Moon (Cancer's dispositor) is
    # in a kendra from itself -> cancellation. "LORD_OF:1" must resolve to Mars, same as a static name.
    ctx = _ctx({"Moon": 70.0, "Mars": 100.0})
    assert C.NeechaBhanga("Mars").evaluate(ctx) is True
    assert C.NeechaBhanga("LORD_OF:1").evaluate(ctx) is True
    # Absent subject -> False, never an error.
    assert C.NeechaBhanga("LORD_OF:1").evaluate(_ctx({"Sun": 5.0})) is False


def test_lord_has_dignity():
    # Aries lagna: 1st lord = Mars. Mars in Aries (own); 4th lord = Moon exalted in Taurus.
    ctx = _ctx({"Mars": 5.0, "Moon": 45.0})
    assert C.LordHasDignity(1, {"own", "moolatrikona"}).evaluate(ctx) is True
    assert C.LordHasDignity(4, {"exalt"}).evaluate(ctx) is True
    assert C.LordHasDignity(1, {"debil"}).evaluate(ctx) is False
    # Mars debilitated in Cancer (the 4th) -> LordHasDignity(1, {debil}).
    assert C.LordHasDignity(1, {"debil"}).evaluate(_ctx({"Mars": 100.0})) is True
    # Absent lord -> False, not an error.
    assert C.LordHasDignity(1, {"own"}).evaluate(_ctx({"Sun": 5.0})) is False


def test_in_house_class_and_vargottama():
    ctx = _ctx({"Sun": 5.0, "Saturn": 65.0})  # Sun 1st(kendra), Saturn 3rd(upachaya)
    assert C.InHouseClass("Sun", "kendra").evaluate(ctx) is True
    assert C.InHouseClass("Saturn", "upachaya").evaluate(ctx) is True
    assert C.InHouseClass("Saturn", "kendra").evaluate(ctx) is False
    assert C.Vargottama("Sun").evaluate(_ctx({"Sun": 0.0})) is True   # 0° Aries -> Aries navamsa


def test_parivartana_exchange_mutual_aspect():
    # Aries lagna: 1st lord Mars in 2nd (Taurus), 2nd lord Venus in 1st (Aries).
    ctx = _ctx({"Mars": 35.0, "Venus": 5.0})
    assert C.Parivartana(1, 2).evaluate(ctx) is True
    assert C.Exchange("Mars", "Venus").evaluate(ctx) is True
    # Saturn 1st & Mars 7th -> mutual 7th aspect.
    assert C.MutualAspect("Saturn", "Mars").evaluate(_ctx({"Saturn": 5.0, "Mars": 185.0})) is True


def test_hemmed_by_malefics():
    # Aries lagna: Sun in 1st; Saturn in 2nd (Taurus), Mars in 12th (Pisces) -> papakartari.
    ctx = _ctx({"Sun": 5.0, "Saturn": 35.0, "Mars": 340.0})
    assert C.HemmedBy("Sun", "malefic").evaluate(ctx) is True
    assert C.HemmedBy("Sun", "benefic").evaluate(ctx) is False


def test_functional_nature_star_moonphase_count():
    ctx = _ctx({"Jupiter": 5.0})  # Aries lagna -> Jupiter benefic
    assert C.FunctionalNature("Jupiter", {"benefic"}).evaluate(ctx) is True
    assert C.InStarOf("Moon", "Ketu").evaluate(_ctx({"Moon": 0.0})) is True   # Ashwini = Ketu
    assert C.MoonPhase("waxing").evaluate(_ctx({"Moon": 100.0, "Sun": 10.0})) is True
    assert C.MoonPhase("waning").evaluate(_ctx({"Moon": 200.0, "Sun": 10.0})) is True
    # two malefics in the 1st
    ctx2 = _ctx({"Sun": 5.0, "Saturn": 6.0, "Mars": 7.0})
    assert C.CountInHouse(1, 2, "malefic").evaluate(ctx2) is True
    assert C.CountInHouse(1, 4, "malefic").evaluate(ctx2) is False


def test_class_in_house_from_origin():
    # Aries lagna: Venus 1st (Aries), Saturn (malefic) in the 8th (Scorpio) = 8th from Venus.
    ctx = _ctx({"Venus": 5.0, "Saturn": 220.0})
    assert C.ClassInHouseFrom("malefic", "Venus", {4, 8, 12}).evaluate(ctx) is True
    assert C.ClassInHouseFrom("malefic", "Venus", {7}).evaluate(ctx) is False
    assert C.ClassInHouseFrom("benefic", "Venus", {4, 8, 12}).evaluate(ctx) is False
