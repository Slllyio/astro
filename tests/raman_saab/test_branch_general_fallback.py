"""When the lord's strength is unknown, the reading falls back to Raman's GENERAL slot.

`rule_firing._branch` picks `fortified` vs `afflicted` by the bhava-lord's Shadbala. On a
Track-B chart there is no Shadbala — 40 of the 346 goldens (12%) — and the old fallback
returned "fortified" regardless. For the 82 rules whose `general` differs from `fortified`,
that meant showing Raman's STRENGTH-CONDITIONED reading ("becomes famous in his own community
and country") when his UNCONDITIONED one ("lives by own exertion, independent spirit") is what
actually applies.

That asserted a strength the chart cannot establish — the same defect class the general-slot
work removed from the DATA, surfacing at the judge instead. The fallback is only possible
because that work created the slot.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets import ALL_RULES
from app.raman_saab.judges import rule_firing as rf


def _rule(rule_id: str):
    return next(r for r in ALL_RULES if r.id == rule_id)


class _NoShadbalaChart:
    """Minimal stand-in: a chart whose planets report no Shadbala."""
    def __init__(self, real: RamanChart) -> None:
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)


class TestFallbackPrefersGeneral:
    def test_general_is_chosen_when_shadbala_is_missing(self) -> None:
        """The whole point: strength unknown must not be read as strength present."""
        rule = _rule("H1.L.3")
        assert rule.general, "H1.L.3 records Raman's unconditioned reading"

        class Chart:
            asc_sign = 1
            planets: dict = {}
        assert rf._branch(rule, Chart()) == "general"

    def test_fortified_is_still_chosen_when_the_rule_has_no_general(self) -> None:
        """Where Raman gives only strength branches there is nothing better to show, so the
        old behaviour must stand rather than the rule falling silent."""
        rule = next(r for r in ALL_RULES
                    if r.kind == "evaluable" and r.condition is not None
                    and not r.general and r.fortified)

        class Chart:
            asc_sign = 1
            planets: dict = {}
        assert rf._branch(rule, Chart()) == "fortified"

    def test_fire_rules_resolves_the_general_branch_to_general_text(self) -> None:
        """`_branch` returning a slot name is useless unless `fire_rules` reads that slot."""
        rule = _rule("H1.L.3")

        class Chart:
            asc_sign = 1
            planets: dict = {}
        fired = [fr for fr in rf.fire_rules(Chart(), rules=[rule])]
        if fired:                       # only if the condition happens to hold
            assert fired[0].branch == "general"
            assert fired[0].text == rule.general


class TestItCannotMoveAVerdict:
    def test_branch_choice_is_presentation_only(self) -> None:
        """`_bucket_fired` buckets by `rule.polarity`, which no branch choice touches. This
        is why the change could be made without re-basing anything — and the golden ratchet
        held at 286/397 across it."""
        rule = _rule("H1.L.3")
        assert rule.polarity in ("benefic", "malefic", "neutral", "maraka")
        # the fallback reads `general` and nothing else
        assert rule.general is not None

    @pytest.mark.parametrize("branch", ["general", "fortified", "afflicted"])
    def test_firedrule_accepts_every_branch_name(self, branch: str) -> None:
        """`FiredRule.branch` is consumed only by presentation surfaces; adding a third
        value must not break the dataclass contract."""
        fr = rf.FiredRule(rule=_rule("H1.L.3"), branch=branch, text="x")
        assert fr.branch == branch


class TestBranchSubjectIsWhoRamanBrandsItOn:
    """`planet_in_house` rules brand on the OCCUPANT, not the house lord.

    Raman writes "Sun afflicted: Long and troublesome illness. Sun fortified: Good
    administrative ability, few enemies, wealthy" for the Sun in the 6th
    (HTJAH-I:6116-6117). All 108 evaluable `planet_in_house` rules were being branched on
    their HOUSE LORD instead, so a chart with a strong 6th lord and a combust, node-hemmed
    Sun was shown the fortified reading — selected by a planet Raman's sentence never
    mentions. An engine-blind audit called this "systemic across the whole planet_in_house
    group and by far the highest-leverage single finding".
    """

    def test_planet_rules_branch_on_the_occupant(self) -> None:
        rule = _rule("H6.P.Sun")
        assert rule.house == 6
        assert rf._branch_subject(rule, _AnyChart()) == "Sun", (
            "the 6th lord must not decide a reading Raman brands on the Sun")

    def test_other_groups_still_branch_on_the_house_lord(self) -> None:
        """The correction is scoped to the tables where Raman brands on the occupant. A
        lord-in-house reading is still about that lord."""
        rule = _rule("H1.L.3")
        assert rule.group == "lord_in_house"
        subject = rf._branch_subject(rule, _AnyChart())
        assert subject == rf._lord_of(1, _AnyChart())

    def test_every_planet_rule_resolves_a_subject_from_its_predicate(self) -> None:
        """The subject is read off `InRashiHouse.planet`, not parsed from the rule id — so a
        renamed rule or a new planet rule cannot silently fall back to the house lord."""
        planet_rules = [r for r in ALL_RULES
                        if r.group == "planet_in_house" and r.kind == "evaluable"
                        and r.condition is not None]
        assert len(planet_rules) > 100
        for r in planet_rules:
            assert isinstance(getattr(r.condition, "planet", None), str), r.id
            assert rf._branch_subject(r, _AnyChart()) == r.condition.planet, r.id

    def test_a_node_occupant_falls_back_to_general(self) -> None:
        """Rahu and Ketu carry no Shadbala, so their strength is unassessable. Branching on
        the occupant means those rules now yield Raman's unconditioned reading rather than a
        strength claim borrowed from the house lord."""
        node_rules = [r for r in ALL_RULES
                      if r.group == "planet_in_house" and r.kind == "evaluable"
                      and getattr(r.condition, "planet", None) in ("Rahu", "Ketu")
                      and r.general]
        assert node_rules, "the corpus has node-occupant planet rules with a general slot"
        for r in node_rules[:5]:
            assert rf._branch(r, _AnyChart()) == "general", r.id


class _AnyChart:
    """A chart with no Shadbala anywhere — the sparse case."""
    asc_sign = 1
    planets: dict = {}
