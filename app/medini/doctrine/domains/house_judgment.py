"""Raman's house-judgment *method*, executed — pure doctrine.

``domains/houses.py`` fires the compendium rules for a house and reduces them
to a flat polarity vote, and it drops every ``method`` record (they are
``antecedent:null``). This module instead runs *How to Judge a Horoscope*
ch. IV's stated procedure as an actual reasoning process:

  1. the Bhava (aspects on / sign of the house),
  2. its Lord (placement, dignity, the yogas it forms),
  3. its Occupants (planets in the house),
  4. its Karaka (the natural significator),
  then blends them (applying Raman's benefic/malefic · favourable-to-Lagna ·
  Rajayogakaraka-vs-Maraka modifier), and finally

  5. sequences the *timing* — the promise fructifies in the Dasa/Bhukti of the
     planets that **influence** the house (Raman's five factors, the
     ``planet_influences_house`` leaf), so the reading says *when* it activates.

Every step cites the ``method`` record that prescribes it, so the previously
inert prose becomes the executable spec. Strength enters ONLY through doctrine
rules whose antecedents use the DSL dignity/strength leaves — the BPHS
``judge_bhava`` scorer is deliberately NOT used (pure-doctrine constraint).
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence

from app.core.ephemeris_engine import DASHA_LORDS, calculate_vimshottari_mahadasha
from app.medini.doctrine.compendium import load_compendium
from app.medini.doctrine.domains.houses import HOUSE_DOMAIN, _POLARITY_SIGN
from app.medini.doctrine.engine.evaluate import evaluate_rule
from app.medini.doctrine.engine.predicates import (
    HOUSE_GROUPS, EvalContext, evaluate_predicate,
)
from app.medini.doctrine.raman_chart import RamanChart

GRAHAS: tuple[str, ...] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                           "Venus", "Saturn", "Rahu", "Ketu")

# Natural significator per bhava (BPHS Ch.6) — reference data, a lookup, not a
# scorer. Mirrors app/core/bhava_judge._BHAVA_KARAKAS (kept local to avoid
# coupling the doctrine reader to the framework engine).
BHAVA_KARAKAS: Mapping[int, tuple[str, ...]] = {
    1: ("Sun",), 2: ("Jupiter",), 3: ("Mars",), 4: ("Moon",), 5: ("Jupiter",),
    6: ("Mars", "Saturn"), 7: ("Venus",), 8: ("Saturn",), 9: ("Jupiter", "Sun"),
    10: ("Sun", "Mercury", "Jupiter", "Saturn"), 11: ("Jupiter",),
    12: ("Saturn", "Ketu"),
}

# Which method record prescribes which part of the procedure (cited, not dropped).
METHOD_CITATIONS = {
    "frame": "raman.htjah_vol1.ch4.judgment_elements",
    "bhava": "raman.htjah_vol1.ch4.judgment_elements",
    "lord": "raman.htjah_vol1.ch4.judgment_lord_position_aspects_yogas",
    "occupants": "raman.htjah_vol1.ch4.planets_in_first_reading_steps",
    "karaka": "raman.htjah_vol1.ch4.lagna_appearance_basis",
    "blend": "raman.htjah_vol1.ch4.nature_of_results_modifiers",
    "timing": ("raman.htjah_vol1.ch4.timing_five_factors",
               "raman.htjah_vol1.ch4.influence_definition"),
}

STEP_LABELS = {
    "bhava": "The Bhava (house sign & aspects on it)",
    "lord": "The Lord (its placement, dignity, yogas)",
    "occupants": "The Occupants (planets in the house)",
    "karaka": "The Karaka (natural significator)",
    "combinations": "Combinations (multi-factor yogas)",
}
STEP_ORDER = ("bhava", "lord", "occupants", "karaka", "combinations")


@dataclasses.dataclass(frozen=True)
class FiredEvidence:
    rule_id: str
    polarity: str
    text: str
    book: str
    magnitude: str | None


@dataclasses.dataclass(frozen=True)
class MethodStep:
    key: str
    label: str
    method_citation: str | None   # the method record prescribing this step
    evidence: tuple[FiredEvidence, ...]
    score: float                  # per-bucket polarity mean, [-1, +1]


@dataclasses.dataclass(frozen=True)
class DasaWindow:
    lord: str
    start_age: float
    end_age: float
    influences: bool              # is this planet a house influencer (5 factors)?
    is_current: bool              # is this the running mahadasha?


@dataclasses.dataclass(frozen=True)
class HouseTiming:
    influencers: tuple[str, ...]
    windows: tuple[DasaWindow, ...]
    current_md: str | None
    current_ad: str | None
    current_is_activator: bool
    active_outcomes: tuple[FiredEvidence, ...]
    method_citation: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class HouseJudgment:
    house: int
    domain: str
    frame_citation: str | None
    steps: tuple[MethodStep, ...]
    blend_score: float
    blend_label: str
    blend_modifier_citation: str | None
    timing: HouseTiming
    n_fired: int
    n_evaluable: int

    @property
    def method_records_cited(self) -> frozenset[str]:
        ids: set[str] = set()
        if self.frame_citation:
            ids.add(self.frame_citation)
        for s in self.steps:
            if s.method_citation:
                ids.add(s.method_citation)
        if self.blend_modifier_citation:
            ids.add(self.blend_modifier_citation)
        ids.update(self.timing.method_citation)
        return frozenset(ids)


# ------------------------------------------------------------------ helpers

def _walk(node) -> list[dict]:
    """Flatten a predicate tree into its leaf/op dict nodes."""
    if not isinstance(node, Mapping):
        return []
    out = [node]
    for key in ("args",):
        for child in node.get(key, ()):
            out.extend(_walk(child))
    if "arg" in node:
        out.extend(_walk(node["arg"]))
    return out


def _houses_of(node) -> set[int]:
    """Resolve a leaf's house spec (int / list / group name) to a house set."""
    spec = node.get("house", node.get("in_house"))
    if spec is None:
        return set()
    if isinstance(spec, str) and spec in HOUSE_GROUPS:
        return set(HOUSE_GROUPS[spec])
    if isinstance(spec, (list, tuple)):
        return {int(h) for h in spec}
    return {int(spec)}


def _is_timing(rule: dict, ops: set[str]) -> bool:
    return (rule["rule_type"] == "dasha_timing"
            or rule["consequent"].get("timing") is not None
            or "dasha_lord_is" in ops or "planet_influences_house" in ops)


def _classify(rule: dict, house: int) -> str:
    """Assign a fired rule to Raman's analytical bucket by its antecedent shape."""
    nodes = _walk(rule["antecedent"])
    ops = {n["op"] for n in nodes if isinstance(n, Mapping) and "op" in n}
    if _is_timing(rule, ops):
        return "timing"
    # Lord: a lordship leaf that concerns THIS house.
    for n in nodes:
        op = n.get("op")
        if op == "lord_of_house_in_house" and int(n.get("of_house", -1)) == house:
            return "lord"
        if op == "planet_is_lord_of" and int(n.get("house", -1)) == house:
            return "lord"
    # Occupants: a planet occupying this house.
    if any(n.get("op") == "planet_in_house" and house in _houses_of(n)
           for n in nodes):
        return "occupants"
    # Bhava: aspects on this house, or (H1) the rising sign.
    if any(n.get("op") == "planet_aspects_house" and house in _houses_of(n)
           for n in nodes):
        return "bhava"
    if any(n.get("op") == "lagna_sign_is" for n in nodes) and house == 1:
        return "bhava"
    # Karaka: references the house's natural significator.
    karakas = set(BHAVA_KARAKAS.get(house, ()))

    def _planets_of(n):
        p = n.get("planet")
        return set(p) if isinstance(p, (list, tuple)) else ({p} if isinstance(p, str) else set())
    if any(_planets_of(n) & karakas for n in nodes):
        return "karaka"
    return "combinations"


def _bucket_score(evidence: Sequence[FiredEvidence]) -> float:
    signed = [_POLARITY_SIGN[e.polarity] for e in evidence
              if e.polarity in ("favorable", "unfavorable")]
    return round(sum(signed) / len(signed), 4) if signed else 0.0


def _label(score: float) -> str:
    if score >= 0.34:
        return "favourable"
    if score <= -0.34:
        return "afflicted"
    return "mixed"


def _maha_sequence(moon_lon: float) -> list[tuple[str, float, float]]:
    """Full Vimshottari mahadasha windows as (lord, start_age, end_age) from
    birth, using the running-dasha balance + the DASHA_LORDS order."""
    birth = calculate_vimshottari_mahadasha(moon_lon, birth_jd=0.0)
    lord0 = birth["mahadasha_lord"]
    remaining = birth["years_remaining"]
    idx0 = next(i for i, (l, _) in enumerate(DASHA_LORDS) if l == lord0)
    seq: list[tuple[str, float, float]] = [(lord0, 0.0, remaining)]
    cursor = remaining
    for step in range(1, 9):
        lord, years = DASHA_LORDS[(idx0 + step) % 9]
        seq.append((lord, cursor, cursor + years))
        cursor += years
    return seq


# ------------------------------------------------------------------ main

def judge_house_doctrine(chart: RamanChart, house: int, *,
                         books: Mapping[str, list[dict]] | None = None,
                         dasha: Mapping[str, str] | None = None) -> HouseJudgment:
    """Execute Raman's HTJAH ch. IV judgment procedure for one house (pure doctrine)."""
    if not 1 <= house <= 12:
        raise ValueError(f"house must be 1..12, got {house}")
    books = books or load_compendium()
    by_domain: dict[str, list[dict]] = {}
    for rules in books.values():
        for r in rules:
            by_domain.setdefault(r["domain"], []).append(r)
    domain = HOUSE_DOMAIN[house]

    ctx = EvalContext(chart=chart, dasha=dasha)
    buckets: dict[str, list[FiredEvidence]] = {k: [] for k in STEP_ORDER}
    timing_fired: list[tuple[FiredEvidence, dict]] = []
    n_fired = evaluable = 0
    seen: set[str] = set()
    for rule in by_domain.get(domain, ()):
        if rule["antecedent"] is None or rule["id"] in seen:
            continue
        seen.add(rule["id"])
        outcome = evaluate_rule(rule, ctx)
        if not outcome.evaluable:
            continue
        evaluable += 1
        if not outcome.fired:
            continue
        n_fired += 1
        ev = FiredEvidence(rule["id"], rule["consequent"]["polarity"],
                           rule["consequent"]["text"], rule["book"],
                           rule["consequent"].get("magnitude"))
        bucket = _classify(rule, house)
        if bucket == "timing":
            timing_fired.append((ev, rule))
        else:
            buckets[bucket].append(ev)

    steps = tuple(
        MethodStep(key=k, label=STEP_LABELS[k],
                   method_citation=METHOD_CITATIONS.get(k),
                   evidence=tuple(buckets[k]), score=_bucket_score(buckets[k]))
        for k in STEP_ORDER
    )

    # blend: overall polarity mean across all non-timing evidence
    all_ev = [e for k in STEP_ORDER for e in buckets[k]]
    blend_score = _bucket_score(all_ev)

    # ---- timing sub-verdict (five factors -> dasha windows -> activation) ----
    influencers = tuple(
        p for p in GRAHAS
        if evaluate_predicate(
            {"op": "planet_influences_house", "planet": p, "house": house}, ctx)
    )
    infl_set = set(influencers)
    md = dasha.get("md") if dasha else None
    ad = dasha.get("ad") if dasha else None
    moon_lon = chart.bundle.chart.planet_lons["Moon"]
    windows = tuple(
        DasaWindow(lord=l, start_age=round(s, 2), end_age=round(e, 2),
                   influences=l in infl_set, is_current=(l == md))
        for l, s, e in _maha_sequence(moon_lon)
    )
    current_is_activator = md in infl_set if md else False
    active_outcomes = tuple(
        ev for ev, rule in timing_fired
        if (rule["consequent"].get("timing") or {}).get("of") == md
    )
    timing = HouseTiming(
        influencers=influencers, windows=windows, current_md=md, current_ad=ad,
        current_is_activator=current_is_activator, active_outcomes=active_outcomes,
        method_citation=METHOD_CITATIONS["timing"],
    )

    return HouseJudgment(
        house=house, domain=domain,
        frame_citation=METHOD_CITATIONS["frame"], steps=steps,
        blend_score=blend_score, blend_label=_label(blend_score),
        blend_modifier_citation=METHOD_CITATIONS["blend"], timing=timing,
        n_fired=n_fired, n_evaluable=evaluable,
    )


def judge_all_houses_doctrine(chart: RamanChart, *,
                              dasha: Mapping[str, str] | None = None
                              ) -> dict[int, HouseJudgment]:
    books = load_compendium()
    return {h: judge_house_doctrine(chart, h, books=books, dasha=dasha)
            for h in range(1, 13)}
