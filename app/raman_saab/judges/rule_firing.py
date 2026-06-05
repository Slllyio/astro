"""Rule firing — the bridge from encoded `RuleRecord`s to a chart reading.

Fires evaluable rules against a chart and reports which fired, with the fortified/
afflicted text and the corpus citation. This is the substrate the Phase-3 house
judge builds on (it adds per-signification sub-verdicts + the StrengthLedger);
on its own it already yields a cited, deterministic "which rules apply" reading.

Usage:
    from app.raman_saab.judges import rule_firing as rf
    for fr in rf.fire_house(chart, 7):
        print(fr.rule.id, fr.text, fr.rule.source)
"""
from __future__ import annotations

from dataclasses import dataclass

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.conditions import EvalContext
from app.raman_saab.doctrine.rule_sets import ALL_RULES
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.primitives.shadbala import total as shadbala_total


@dataclass(frozen=True)
class FiredRule:
    """A rule that fired for a chart, with the branch (fortified/afflicted) chosen."""
    rule: RuleRecord
    branch: str          # "fortified" | "afflicted"
    text: str            # the chosen branch's reading


def _lord_of(house: int, chart: RamanChart) -> str:
    from app.raman_saab.chart.constants import SIGN_LORDS
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _branch(rule: RuleRecord, chart: RamanChart) -> str:
    """Pick the fortified vs afflicted branch by the bhava-lord's Shadbala (if available):
    lord meets its min-required → fortified, else afflicted. Falls back to fortified when
    Shadbala isn't computed (Track-B charts)."""
    lord = _lord_of(rule.house, chart)
    p = chart.planets.get(lord)
    if p is None or p.shadbala_rupas is None:
        return "fortified"
    strong = shadbala_total.is_powerful(lord, p.shadbala_rupas.total / 60.0)
    if strong:
        return "fortified"
    return "afflicted" if rule.afflicted else "fortified"


def fire_rules(chart: RamanChart, rules=ALL_RULES) -> list[FiredRule]:
    """Every evaluable rule whose condition holds for `chart`, with its chosen branch."""
    ctx = EvalContext(chart)
    out: list[FiredRule] = []
    for rule in rules:
        if rule.kind != "evaluable" or rule.condition is None:
            continue
        if rule.condition.evaluate(ctx):
            pref = _branch(rule, chart)
            # Resolve to a branch that actually has text (some rules give only one side,
            # e.g. nodes with fortified=None) so `text` is never None.
            if pref == "afflicted" and rule.afflicted:
                text, branch = rule.afflicted, "afflicted"
            elif rule.fortified:
                text, branch = rule.fortified, "fortified"
            else:
                text, branch = (rule.afflicted or ""), "afflicted"
            out.append(FiredRule(rule=rule, branch=branch, text=text))
    return out


def fire_house(chart: RamanChart, house: int) -> list[FiredRule]:
    """Fired rules for a single house (1..12)."""
    return [fr for fr in fire_rules(chart) if fr.rule.house == house]
