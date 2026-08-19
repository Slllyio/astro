"""Sutra-fed strength: route strength-relevant fired compendium rules into the
numeric factor verdicts (P1 of the engine overhaul; HOUSE_SCHEME_AUDIT increment 17).

Root cause 1 of the strength ceiling (increment 16 context): the 1,359 encoded sutras
fired into a parallel, unscored path — readings only — while the graded verdicts came
entirely from ~15 hand-decoded weights. This module selects which fired rules may
contribute strength testimony and with what weight, under three disciplines:

1. **Novelty (no double-counting).** The assessors already mechanically score dignity,
   placement, aspects, conjunctions, kartari, vargottama and combustion. A sutra that
   merely restates those is REDUNDANT and contributes nothing. Only rules whose
   antecedents test configurations the assessor cannot see (lord-of-X-in-Y specifics,
   yogas/parivartana compounds, varga placements, ashtakavarga counts, nodal pairs,
   nakshatra/khara/chidra, waxing-moon state) are NOVEL and contribute. A bare
   planet-in-house rule (HPA ch. XXI style) is CORRECTIVE only when its polarity
   contradicts the assessor's mechanical occupant sign — agreement is redundant.
2. **Doctrine-fixed weights (no fitting).** delta = polarity sign x the rule's own
   printed magnitude class, valued in the assessor's existing units
   (strong=1.2 == a kendra; moderate=0.7 == one aspect; slight=0.35). Nothing is fit.
3. **Bounded contribution.** Per factor, summed sutra deltas are clamped to +/-1.6
   (one exaltation's worth) by proportional rescale, and the positive side then flows
   through the assessor's existing `_cap_positive` — no second stacking path.

All selection here is pure functions over (rule, bucket, house); `house_judgment`
constructs the `Finding`s and owns the flags (`SUTRA_STRENGTH`, `SUTRA_OCCUPANT_OVERRIDE`,
`SUTRA_GATE`), all default OFF.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# Rule types admitted as strength testimony. Outcome-signification types (dasha_timing,
# definition, method) describe *events*, not factor strength — the known conflation risk.
ADMITTED_RULE_TYPES = frozenset({"bhava_judgment", "yoga", "graha_effect"})

# Antecedent leaves the numeric assessor already scores mechanically — a rule built
# only from these restates existing testimony and is dropped.
REDUNDANT_OPS = frozenset({
    "dignity_is", "exalted", "debilitated", "own_sign", "vargottama", "combust",
    "planet_aspects_house", "planets_conjunct", "strong", "strength_gte",
})

# Leaves the assessor cannot see: their presence makes a rule NOVEL.
NOVEL_OPS = frozenset({
    "lord_of_house_in_house", "planet_is_lord_of", "planet_in_sign", "lagna_sign_is",
    "varga_sign_is", "varga_lord_is", "av_bindus_gte", "sav_bindus_gte",
    "reduced_av_total_cmp", "occupies_khara", "occupies_chidra", "yoga_present",
    "tara_class", "karaka_is", "planet_aspects_planet", "waxing_moon", "retrograde",
})

_NODES = ("Rahu", "Ketu")
# Magnitude class -> delta magnitude, in the assessor's own units (see module docstring).
MAG_W = {"strong": 1.2, "moderate": 0.7, "slight": 0.35, None: 0.7}
# Per-factor clamp on total sutra contribution: one exaltation's worth.
FACTOR_CLAMP = 1.6
_POL_SIGN = {"favorable": +1.0, "unfavorable": -1.0}

_BUCKET_FACTOR = {"bhava": "bhava", "occupants": "bhava",
                  "lord": "lord", "karaka": "karaka"}


def _walk(node: Any) -> list[dict]:
    """Flatten an antecedent tree into its dict nodes (local copy of the tiny
    house_judgment helper, kept here to avoid a circular import)."""
    out: list[dict] = []
    if isinstance(node, Mapping):
        out.append(dict(node))
        for v in node.values():
            out.extend(_walk(v))
    elif isinstance(node, (list, tuple)):
        for v in node:
            out.extend(_walk(v))
    return out


def _leaf_ops(rule: dict) -> set[str]:
    return {n["op"] for n in _walk(rule.get("antecedent"))
            if isinstance(n, dict) and "op" in n}


def _nodal_conjunction(rule: dict) -> bool:
    """A named planets_conjunct pair involving Rahu/Ketu is nodal affliction the
    conjunction assessor treats as just another malefic — count it novel."""
    for n in _walk(rule.get("antecedent")):
        if n.get("op") == "planets_conjunct":
            ps = n.get("planets") or n.get("planet") or ()
            if isinstance(ps, str):
                ps = (ps,)
            if any(p in _NODES for p in ps):
                return True
    return False


def novelty(rule: dict, *, is_combination: bool) -> str | None:
    """'novel' | 'corrective' | None (excluded or redundant)."""
    if rule.get("rule_type") not in ADMITTED_RULE_TYPES:
        return None
    if rule.get("computability") not in ("full", "partial"):
        return None
    if rule["consequent"].get("polarity") not in _POL_SIGN:
        return None                                    # mixed/neutral: no signed testimony
    if is_combination:
        return "novel"                                 # yogas / parivartana compounds
    ops = _leaf_ops(rule)
    if ops & NOVEL_OPS or _nodal_conjunction(rule):
        return "novel"
    if ops == {"planet_in_house"}:
        return "corrective"                            # caller checks polarity disagreement
    return None                                        # ops subset of REDUNDANT_OPS + combinators


def target_factor(rule: dict, bucket: str, house: int) -> str | None:
    """Which factor verdict a fired rule testifies about. Buckets map directly;
    a 'combinations' rule is resolved by its atoms (lordship of the judged house ->
    lord; placement in the judged house -> bhava; else none — it stays display-only)."""
    if bucket in _BUCKET_FACTOR:
        return _BUCKET_FACTOR[bucket]
    if bucket != "combinations":
        return None
    for n in _walk(rule.get("antecedent")):
        op = n.get("op")
        if op == "lord_of_house_in_house" and int(n.get("of_house", -1)) == house:
            return "lord"
        if op == "planet_is_lord_of" and int(n.get("house", -1)) == house:
            return "lord"
    for n in _walk(rule.get("antecedent")):
        if n.get("op") == "planet_in_house":
            h = n.get("house")
            hs = set(h) if isinstance(h, (list, tuple)) else {h}
            if house in hs:
                return "bhava"
    return None


def delta_of(rule: dict) -> float:
    c = rule["consequent"]
    return _POL_SIGN[c["polarity"]] * MAG_W.get(c.get("magnitude"), 0.7)


def clamp_factor(items: list[tuple[str, str, float]]) -> list[tuple[str, str, float]]:
    """Proportionally rescale a factor's sutra deltas so |sum| <= FACTOR_CLAMP."""
    total = sum(d for _, _, d in items)
    if abs(total) <= FACTOR_CLAMP or not items:
        return items
    k = FACTOR_CLAMP / abs(total)
    return [(rid, text, round(d * k, 2)) for rid, text, d in items]


def sutra_findings(fired: list[tuple[dict, str, bool]], house: int
                   ) -> dict[str, list[tuple[str, str, float]]]:
    """NOVEL rules -> per-factor (rule_id, text, delta) lists, clamped.
    ``fired`` = [(rule, bucket, is_combination), ...] from the judge's fired loop."""
    by_factor: dict[str, list[tuple[str, str, float]]] = {
        "bhava": [], "lord": [], "karaka": []}
    for rule, bucket, is_combo in fired:
        if novelty(rule, is_combination=is_combo) != "novel":
            continue
        fac = target_factor(rule, bucket, house)
        if fac is None:
            continue
        by_factor[fac].append(
            (rule["id"], rule["consequent"]["text"], delta_of(rule)))
    return {fac: clamp_factor(items) for fac, items in by_factor.items()}


def corrective_candidates(fired: list[tuple[dict, str, bool]], house: int
                          ) -> dict[str, int]:
    """CORRECTIVE planet-in-THIS-house rules -> {planet: sutra polarity sign}.
    The caller compares against the assessor's mechanical occupant sign and applies
    an override only on disagreement (SUTRA_OCCUPANT_OVERRIDE)."""
    out: dict[str, int] = {}
    for rule, _bucket, is_combo in fired:
        if novelty(rule, is_combination=is_combo) != "corrective":
            continue
        for n in _walk(rule.get("antecedent")):
            if n.get("op") != "planet_in_house":
                continue
            h = n.get("house")
            hs = set(h) if isinstance(h, (list, tuple)) else {h}
            p = n.get("planet")
            if house in hs and isinstance(p, str):
                out[p] = int(_POL_SIGN[rule["consequent"]["polarity"]])
    return out


def strong_negative_factors(fired: list[tuple[dict, str, bool]], house: int
                            ) -> set[str]:
    """Factors targeted by a fired unfavorable-STRONG sutra — the SUTRA_GATE trigger
    (the doctrine-citable form of the A2 'besieged is broken' finding)."""
    out: set[str] = set()
    for rule, bucket, is_combo in fired:
        if novelty(rule, is_combination=is_combo) != "novel":
            continue
        c = rule["consequent"]
        if c["polarity"] == "unfavorable" and c.get("magnitude") == "strong":
            fac = target_factor(rule, bucket, house)
            if fac:
                out.add(fac)
    return out
