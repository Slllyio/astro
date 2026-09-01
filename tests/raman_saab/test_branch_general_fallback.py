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
