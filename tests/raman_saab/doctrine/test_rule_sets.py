"""Encoded RuleRecord sets: every rule's citation must resolve to a real on-disk
corpus line (spec §5.4), and evaluable rules fire their condition trees correctly.
This guards the house-by-house encoding as it grows."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets import (
    ALL_RULES, house_01_lagna, house_02_dhana, house_03_sahaja, house_04_sukha,
    house_05_putra, house_06_ari, house_07_kalatra, house_08_ayur, house_09_bhagya,
    house_10_karma, house_11_labha, house_12_vyaya)
from app.raman_saab.doctrine.sources import verify

# Every encoded house module exposes a `RULES` tuple. Add new houses here as they land.
ALL_RULE_SETS = [
    house_01_lagna, house_02_dhana, house_03_sahaja, house_04_sukha, house_05_putra,
    house_06_ari, house_07_kalatra, house_08_ayur, house_09_bhagya, house_10_karma,
    house_11_labha, house_12_vyaya]


def _all_rules():
    for mod in ALL_RULE_SETS:
        yield from mod.RULES


def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


def test_rule_ids_are_globally_unique():
    """No rule id is defined twice anywhere in the corpus (the one-owner-per-corpus-rule
    invariant). A duplicate id means a record was double-encoded across modules — which
    double-counts the same testimony in the ledger and silently regresses the ratchet."""
    ids = [r.id for r in ALL_RULES]
    from collections import Counter
    dupes = sorted(i for i, c in Counter(ids).items() if c > 1)
    assert len(set(ids)) == len(ids), f"duplicate rule ids: {dupes}"


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


def test_h1_b15_requires_a_distinct_sushka_cotenant():
    """Rule #15 (HTJAH-I:1107-1108): "lord of Lagna in conjunction with Sushka
    planets". A lone Sushka *lord* in its own sign is NOT a conjunction with itself
    (that is rule #13's territory) — #15 needs a SECOND distinct Sushka body.

    Aquarius lagna (asc 305deg): lord = Saturn. Saturn alone in Capricorn -> no
    distinct Sushka co-tenant -> False. Add Mars to Saturn's sign -> True."""
    rule = next(r for r in house_01_lagna.RULES if r.id == "H1.B.15")
    # Saturn (Aquarius-lord) alone in Capricorn (285deg): self-conjunction only -> False.
    assert rule.fires(_chart({"Saturn": 285.0}, asc_lon=305.0)) is False
    # Saturn + Mars both in Capricorn: a distinct Sushka body joins the lord -> True.
    assert rule.fires(_chart({"Saturn": 285.0, "Mars": 288.0}, asc_lon=305.0)) is True


def test_h1_g2_afflicts_lagna_uses_true_drishti():
    """G2 'Lagna afflicted' must use TRUE Vedic drishti, not a {1,4,7,8}-house proxy.

    Mars in the 10th (10th-from-Lagna) casts its special 4th aspect onto house 1
    (dist 4 from house 10 = house 1) -> the Lagna IS afflicted. The old proxy
    (in-house 1/4/7/8 only) missed this. Aries lagna (asc 5deg): Mars in Capricorn
    (house 10, 285deg)."""
    from app.raman_saab.doctrine.conditions import EvalContext
    from app.raman_saab.doctrine.rule_sets.house_01_lagna import moon_mind
    cond = moon_mind._aspects_lagna("Mars")
    # Mars in the 10th -> 4th-aspect onto the Lagna -> afflicts house 1.
    assert cond.evaluate(EvalContext(_chart({"Mars": 285.0}, asc_lon=5.0))) is True
    # Mars in the 3rd (Gemini, 65deg): dist 3 from house 3 to house 1 is not a Mars
    # aspect house (Mars = 4/7/8) and Mars is not in house 1 -> does NOT afflict.
    assert cond.evaluate(EvalContext(_chart({"Mars": 65.0}, asc_lon=5.0))) is False
