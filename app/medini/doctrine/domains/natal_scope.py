"""Natal firing-scope: which fired compendium rules a BIRTH-chart judgment may surface,
and which natal house(s) each concerns (P-firing of the engine overhaul; HOUSE_SCHEME_AUDIT
increment 21).

Motivation (verified on the Mainpuri chart): `judge_house_doctrine` only makes a rule a
candidate if its `domain` tag equals the house's single `HOUSE_DOMAIN` mapping (or it lives
in that house's HTJAH chapter). Two large domains — `general` and `mind_character` — map to
NO house, so hundreds of applicable HPA / three_hundred sutras (present yogas, avasthas/balas,
functional-role, planet-in-sign character) can never fire. This module supplies the doctrinal
scope filter and the house-routing used by `house_judgment.NATAL_FIRING_WIDEN` to close that
gap, while keeping SCORING under the unchanged `sutra_strength` policy.

All selection here is pure functions over `rule` dicts; `house_judgment` owns the flag and
constructs the candidate list. A local `_walk` avoids a circular import.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# Groups a house-valued leaf may name (mirror of engine.predicates.HOUSE_GROUPS; duplicated
# here as plain data to keep this module import-light and circular-import-free).
_HOUSE_GROUPS = {
    "kendra": (1, 4, 7, 10), "trikona": (1, 5, 9), "dusthana": (6, 8, 12),
    "upachaya": (3, 6, 10, 11), "maraka": (2, 7),
}

# Rule types admitted into a natal judgment. The excluded types describe events or lexicon,
# not the birth promise — their antecedents being true on a natal chart is coincidental.
IN_SCOPE_RULE_TYPES = frozenset({
    "bhava_judgment", "yoga", "graha_effect", "strength", "functional_role", "cancellation",
})
OUT_OF_SCOPE_REASONS = {
    "electional":   "muhurtha — judges an election moment, not a birth",
    "prasna":       "horary — judges a query moment, not a birth",
    "dasha_timing": "period-timing — says WHEN, already owned by the timing sub-verdict",
    "transit":      "gochara — needs a transit clock, not a natal placement",
    "definition":   "lexical/definitional — no falsifiable natal claim",
    "method":       "procedure record (antecedent null) — never executable",
}

# Leaves that name a natal house directly (house / in_house specs).
_HOUSE_OPS = frozenset({
    "planet_in_house", "planet_aspects_house", "lord_of_house_in_house", "planet_is_lord_of",
})


def _walk(node: Any) -> list[dict]:
    """Flatten an antecedent tree into its op-dict nodes (recurses args/arg, matching the
    encoder's tree shape)."""
    if not isinstance(node, Mapping):
        return []
    out = [dict(node)]
    for child in node.get("args", ()):
        out.extend(_walk(child))
    if "arg" in node:
        out.extend(_walk(node["arg"]))
    return out


def _houses_of(node: Mapping) -> set[int]:
    """Resolve a leaf's house spec (int / list / group name) to a natal-house set. Both the
    `house`/`in_house` occupancy spec and (for lordship leaves) `of_house` count."""
    houses: set[int] = set()
    for key in ("house", "in_house", "of_house"):
        spec = node.get(key)
        if spec is None:
            continue
        if isinstance(spec, str) and spec in _HOUSE_GROUPS:
            houses |= set(_HOUSE_GROUPS[spec])
        elif isinstance(spec, (list, tuple)):
            houses |= {int(h) for h in spec}
        else:
            try:
                houses.add(int(spec))
            except (TypeError, ValueError):
                pass
    return houses


def in_natal_scope(rule: dict) -> bool:
    """True if the rule may surface in a birth-chart judgment at all."""
    return (
        rule.get("rule_type") in IN_SCOPE_RULE_TYPES
        and rule.get("computability") in ("full", "partial")
        and rule.get("antecedent") is not None
    )


def referenced_houses(rule: dict) -> set[int]:
    """The natal house(s) a rule's antecedent anchors to. Atoms carrying ``frame: 'moon'``
    (and other non-lagna frames) are Moon-relative, NOT natal houses — they are skipped, so
    Anapha/Durudhara/Adhi and other Moon-frame yogas stay chart-global rather than being
    mis-routed onto a Rasi house they never reference."""
    out: set[int] = set()
    for n in _walk(rule.get("antecedent")):
        if n.get("op") not in _HOUSE_OPS:
            continue
        if n.get("frame") not in (None, "lagna"):
            continue
        out |= _houses_of(n)
    return out


def is_chart_global(rule: dict) -> bool:
    """True when a rule has no natal-house anchor (its testimony is about the chart as a
    whole or a planet's intrinsic condition): Moon-frame yogas, planet-in-sign character,
    balas/avasthas, functional-nature assignments. These surface once at chart level, never
    per house."""
    return not referenced_houses(rule)
