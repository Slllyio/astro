"""Encoded RuleRecord sets: every rule's citation must resolve to a real on-disk
corpus line (spec §5.4), and evaluable rules fire their condition trees correctly.
This guards the house-by-house encoding as it grows."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets import house_07_kalatra
from app.raman_saab.doctrine.sources import verify

# Every encoded house module exposes a `RULES` tuple. Add new houses here as they land.
ALL_RULE_SETS = [house_07_kalatra]


def _all_rules():
    for mod in ALL_RULE_SETS:
        yield from mod.RULES


def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


@pytest.mark.parametrize("rule", list(_all_rules()), ids=lambda r: r.id)
def test_every_rule_cites_a_real_corpus_line(rule):
    assert verify(rule.source), f"{rule.id} cites {rule.source} which does not resolve on disk"


@pytest.mark.parametrize("rule", list(_all_rules()), ids=lambda r: r.id)
def test_evaluable_rules_have_a_condition(rule):
    if rule.kind == "evaluable":
        assert rule.condition is not None, f"{rule.id} is evaluable but has no condition"


def test_house7_impotency_rule_fires():
    # Saturn in the 6th from Venus -> impotency rule (H7.K.1) fires.
    rule = next(r for r in house_07_kalatra.RULES if r.id == "H7.K.1")
    # Aries lagna: Venus in 1st (Aries 5°), Saturn in 6th (Virgo 165°) = 6th from Venus.
    assert rule.fires(_chart({"Venus": 5.0, "Saturn": 165.0})) is True
    # Saturn elsewhere (3rd from Venus) -> does not fire.
    assert rule.fires(_chart({"Venus": 5.0, "Saturn": 65.0})) is False


def test_house7_seventh_lord_in_lagna_fires():
    rule = next(r for r in house_07_kalatra.RULES if r.id == "H7.L.1")
    # Aries lagna: 7th lord = Venus (Libra). Venus in the 1st (Aries) -> fires.
    assert rule.fires(_chart({"Venus": 5.0})) is True
