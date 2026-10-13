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
from app.raman_saab.doctrine.disposition import disposition
from app.raman_saab.doctrine.rule_sets import ALL_RULES
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.primitives.shadbala import total as shadbala_total


@dataclass(frozen=True)
class FiredRule:
    """A rule that fired for a chart, with the branch (fortified/afflicted) chosen."""
    rule: RuleRecord
    branch: str          # "general" | "fortified" | "afflicted"
    text: str            # the chosen branch's reading


def _lord_of(house: int, chart: RamanChart) -> str:
    from app.raman_saab.chart.constants import SIGN_LORDS
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _branch_subject(rule: RuleRecord, chart: RamanChart) -> str:
    """Whose strength decides this rule's reading.

    Normally the bhava lord — Raman brands a lord-in-house or combination reading on the
    house's own lord. But in the "Planets in the Nth House" tables he brands the branch on
    the OCCUPANT: "Sun afflicted: Long and troublesome illness. Sun fortified: Good
    administrative ability, few enemies, wealthy" (HTJAH-I:6116-6117, the Sun in the 6th).

    CORRECTED 2026-09-01 after an engine-blind audit. Every one of the 108 evaluable
    `planet_in_house` rules was being branched on its HOUSE LORD, so a chart with a strong
    6th lord and a combust, node-hemmed Sun was told "administrative ability, few enemies,
    wealthy" — Raman's fortified reading, selected by a planet his sentence never mentions.
    The reviewer called this "systemic across the whole planet_in_house group and by far the
    highest-leverage single finding in this audit; it needs one measured pass, not 84 splits."

    All 108 conditions are `InRashiHouse`, which carries the occupant's name, so the subject
    is read straight off the predicate rather than parsed out of the rule id. Anything else
    falls back to the bhava lord.

    Measured before shipping: the golden ratchet is UNCHANGED at 286/397 — branch selection
    is presentation (`_bucket_fired` buckets by `rule.polarity`), so this could only ever
    change which of Raman's readings is displayed, never a verdict."""
    if rule.group == "planet_in_house":
        planet = getattr(rule.condition, "planet", None)
        if isinstance(planet, str):
            return planet
    return _lord_of(rule.house, chart)


def _branch(rule: RuleRecord, chart: RamanChart) -> str:
    """Pick the reading by the Shadbala of whoever Raman brands the branch on — the bhava
    lord for most rules, the OCCUPANT for `planet_in_house` (see `_branch_subject`). Meets
    its min-required → fortified, else afflicted.

    WHEN STRENGTH IS UNKNOWN, PREFER `general` (2026-09-01). Shadbala is unavailable on 40 of
    the 346 golden charts (12%) — Track-B records with no birth time. The old fallback
    returned "fortified" there, which on 82 rules means showing Raman's STRENGTH-CONDITIONED
    reading ("becomes famous in his own community and country") when his UNCONDITIONED one
    ("lives by own exertion, independent spirit") is what actually applies and is sitting in
    the `general` slot. That asserted a strength the chart cannot establish — the same defect
    class the general-slot work removed from the data, surfacing at the judge instead.

    The `general` slot only exists since that work, so this fallback was not previously
    available. Where a rule has none, the old behaviour stands: there is nothing better to
    show. Presentation only — `_bucket_fired` buckets by `rule.polarity`, so no branch choice
    can move a verdict."""
    subject = _branch_subject(rule, chart)
    # The "Planets in the Nth house" tables brand the branch "X afflicted: ... X fortified: ...",
    # and Raman defines both words by INFLUENCE, not strength: "fortified, that is well aspected
    # or conjoined" (HTJAH-I:4283); "Venus is the strongest planet ... and even he is afflicted"
    # (NH:14852-14854). Two concurring reviews, 2026-10-13 -- see doctrine/disposition.py. Mixed
    # or no testimony shows his unconditioned reading; with none recorded, strength still decides.
    if rule.group == "planet_in_house":
        d = disposition(subject, chart)
        if d is not None:
            want = {"good": "fortified", "bad": "afflicted"}.get(d.reading)
            if want and getattr(rule, want):
                return want
            if want or rule.general:
                return "general"     # never show the opposite pole of a clear disposition
    p = chart.planets.get(subject)
    if p is None or p.shadbala_rupas is None:
        return "general" if rule.general else "fortified"
    strong = shadbala_total.is_powerful(subject, p.shadbala_rupas.total / 60.0)
    if strong:
        return "fortified"
    if rule.afflicted:
        return "afflicted"
    # A WEAK subject must never be routed to the FORTIFIED reading while Raman's
    # unconditioned one is available (2026-09-02). The old fallback did exactly that, so a
    # rule recording only a strength-conditioned upside — H8.L.5's "if fortified in a kendra
    # or trikona, the evil results are intensified" — would assert that fortification of a
    # lord the engine had just measured as weak. Preferring `general` states what Raman says
    # regardless of strength, which is true of every chart.
    return "general" if rule.general else "fortified"


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
            if pref == "general" and rule.general:
                text, branch = rule.general, "general"
            elif pref == "afflicted" and rule.afflicted:
                text, branch = rule.afflicted, "afflicted"
            elif rule.fortified:
                text, branch = rule.fortified, "fortified"
            elif rule.general:
                # Raman's UNCONDITIONED reading beats the opposite pole (2026-09-02). The
                # chain above falls through to `afflicted` when the preferred slot is empty,
                # so a chart whose lord is STRONG but whose rule has `fortified=None` was
                # being shown the affliction reading — a strength claim inverted, not merely
                # absent. Where the rule records what Raman says regardless of strength,
                # that is strictly the better answer than his other pole.
                text, branch = rule.general, "general"
            else:
                text, branch = (rule.afflicted or ""), "afflicted"
            out.append(FiredRule(rule=rule, branch=branch, text=text))
    return out


def fire_house(chart: RamanChart, house: int) -> list[FiredRule]:
    """Fired rules for a single house (1..12).

    Evaluates every rule and then discards eleven twelfths of the result, so calling it once
    per house per signification costs a full pass each time. That is what the house judge used
    to do — 967 passes over one chart, 293,519 condition evaluations. Kept as-is for direct
    callers and tests; anything in a loop wants `fire_house_cached` below.
    """
    return [fr for fr in fire_rules(chart) if fr.rule.house == house]


def fire_house_cached(chart: RamanChart, house: int, ctx: EvalContext) -> list[FiredRule]:
    """Fired rules for one house, evaluating the rule set at most once per chart.

    `EvalContext` is the project's per-chart memo store and already carries the parivartana
    pairs, the functional natures and the fired yogas; the fired RULES belong in it for exactly
    the same reason. The whole set is fired once and indexed by house, so the second and every
    later call is a dict lookup.

    Correctness rests on the context's own guarantee: it is frozen with `init=False` on its
    cache precisely so `dataclasses.replace(ctx, chart=…)` yields a FRESH cache rather than
    carrying this chart's rules into another one (`doctrine/conditions.py:141-152`). Never
    stash the index anywhere else.
    """
    def _index() -> dict[int, list[FiredRule]]:
        by_house: dict[int, list[FiredRule]] = {}
        for fr in fire_rules(chart):
            by_house.setdefault(fr.rule.house, []).append(fr)
        return by_house

    return ctx.get_or_compute("fired_rules_by_house", _index).get(house, [])
