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
