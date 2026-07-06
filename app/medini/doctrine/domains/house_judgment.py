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

from app.core.bhava_judge import _NATURAL_BENEFICS, _NATURAL_MALEFICS
from app.core.dignity import dignity_state
from app.core.drishti_argala import aspects_from_planet, planets_aspecting_bhava
from app.core.ephemeris_engine import DASHA_LORDS, calculate_vimshottari_mahadasha
from app.medini.doctrine.compendium import load_compendium
from app.medini.doctrine.domains.houses import HOUSE_DOMAIN, _POLARITY_SIGN
from app.medini.doctrine.engine.evaluate import evaluate_rule
from app.medini.doctrine.engine.predicates import (
    HOUSE_GROUPS, EvalContext, evaluate_predicate,
)
from app.medini.doctrine.raman_chart import RamanChart

KENDRA = (1, 4, 7, 10)
TRIKONA = (1, 5, 9)
DUSTHANA = (6, 8, 12)

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
    lagna_verdict: "FactorVerdict"
    lord_verdict: "FactorVerdict"
    karaka_verdict: "FactorVerdict"
    conclusion: "Conclusion"

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


# ============================================================ strength assessor
# Raman's ch. IV method judges each of Lagna / Lord / Karaka to a graded
# strength verdict from his own criteria — aspects (benefic/malefic), dignity
# (friend/enemy sign, exaltation/debility, neechabhanga), vargottama, placement
# and kartari yogas — CROSS-CHECKED in the Rasi and the Navamsa. Computed from
# low-level chart primitives (dignity, drishti, D9 frame), NOT judge_bhava.
# The weights below are a transparent modelling choice (Raman states qualitative
# verdicts, not numbers); the FINDINGS are the faithful, cited part.

_CLASSICAL = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_DIGNITY_W = {"exalted": 2.0, "own": 1.5, "friendly": 1.0, "neutral": 0.0,
              "inimical": -1.0, "debilitated": -2.0}


@dataclasses.dataclass(frozen=True)
class Finding:
    text: str            # Raman-style observation
    delta: float         # signed contribution to the verdict
    frame: str           # "Rasi" | "Navamsa" | "both"
    criterion: str       # aspect | dignity | placement | conjunction | kartari | vargottama


@dataclasses.dataclass(frozen=True)
class FactorVerdict:
    role: str            # "Lagna" | "Lord" | "Karaka"
    subject: str         # the point judged (e.g. "house 1" or "Mars")
    label: str           # afflicted..powerful
    score: float
    findings: tuple[Finding, ...]


@dataclasses.dataclass(frozen=True)
class Influencer:
    planet: str
    factors: tuple[str, ...]     # which of the 5 factors it satisfies
    tier: str                    # "mostly" (>=2) | "moderate" (1)
    is_benefic: bool
    nature: str                  # blended-nature snippet from doctrine


@dataclasses.dataclass(frozen=True)
class Conclusion:
    label: str                   # headline verdict from Lagna+Lord+Karaka
    score: float
    influencers: tuple[Influencer, ...]
    synthesis: str               # prose blend of the influencing planets' natures
    afflicted_activators: tuple[str, ...]


def _is_benefic(chart: RamanChart, planet: str) -> bool:
    """Natural benefic/malefic with the waxing-Moon refinement Raman uses
    ('the Moon, a malefic in this case')."""
    if planet == "Moon":
        lons = chart.bundle.chart.planet_lons
        elong = (lons["Moon"] - lons["Sun"]) % 360.0
        return 0.0 <= elong < 180.0        # shukla paksha (waxing) -> benefic
    return planet in _NATURAL_BENEFICS


def _d1_houses(chart: RamanChart) -> dict[str, int]:
    return dict(chart.bundle.kundali.planet_house)


def _d9_houses(chart: RamanChart) -> dict[str, int]:
    return {p: chart.house_of(p, "navamsa") for p in GRAHAS}


def _lord_of(chart: RamanChart, house: int) -> str:
    return chart.bundle.sign_lord_of_house(house, from_moon=False)


_ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th",
             7: "7th", 8: "8th", 9: "9th", 10: "10th", 11: "11th", 12: "12th"}


def _ordinal(n: int) -> str:
    return _ORDINALS.get(n, f"{n}th")


def _verdict_label(score: float) -> str:
    if score >= 3.0:
        return "powerful"
    if score >= 1.5:
        return "good"
    if score >= 0.5:
        return "fairly good"
    if score > -0.5:
        return "moderate"
    if score >= -1.5:
        return "weak"
    return "afflicted"


def _neechabhanga(chart: RamanChart, planet: str, sign: int) -> bool:
    """Common neechabhanga: the dispositor of the debilitation sign sits in a
    kendra from the Lagna (a standard cancellation rule)."""
    from app.core.dignity import SIGN_RULERS
    dispositor = SIGN_RULERS.get(sign)
    if not dispositor:
        return False
    return chart.house_of(dispositor, "lagna") in KENDRA


def _kartari(chart: RamanChart, house: int) -> tuple[str | None, list[str], list[str]]:
    """Papakartari / Subhakartari around a house: occupants of the 2nd AND the
    12th from it all malefic (papa) or all benefic (subha)."""
    d1 = _d1_houses(chart)
    second = house % 12 + 1
    twelfth = (house - 2) % 12 + 1
    occ2 = [p for p in GRAHAS if d1[p] == second]
    occ12 = [p for p in GRAHAS if d1[p] == twelfth]
    if occ2 and occ12:
        if all(not _is_benefic(chart, p) for p in occ2 + occ12):
            return "papa", occ2, occ12
        if all(_is_benefic(chart, p) for p in occ2 + occ12):
            return "subha", occ2, occ12
    return None, occ2, occ12


def _dignity_findings(chart, planet, sign, frame, scale) -> list[Finding]:
    if planet not in _CLASSICAL:
        return []
    dg = dignity_state(planet, sign)
    if dg == "debilitated" and _neechabhanga(chart, planet, sign):
        return [Finding(f"{planet} debilitated but neechabhanga (cancellation)",
                        round(1.5 * scale, 2), frame, "dignity")]
    w = _DIGNITY_W.get(dg, 0.0) * scale
    if w == 0.0:
        return []
    return [Finding(f"{planet} in a {dg} sign", round(w, 2), frame, "dignity")]


def _aspect_findings(chart, houses, target_house, subject, frame, scale) -> list[Finding]:
    out: list[Finding] = []
    for a in planets_aspecting_bhava(target_house, houses):
        if a == subject:
            continue
        ben = _is_benefic(chart, a)
        out.append(Finding(f"aspected by {a} ({'benefic' if ben else 'malefic'})",
                           round((0.75 if ben else -0.75) * scale, 2), frame, "aspect"))
    return out


def _conjunction_findings(chart, houses, planet, frame, scale) -> list[Finding]:
    out: list[Finding] = []
    signs = (chart.bundle.chart.planet_signs if frame == "Rasi"
             else {p: chart.varga_signs[p][9] for p in GRAHAS})
    for c in GRAHAS:
        if c == planet or houses.get(c) != houses.get(planet):
            continue
        ben = _is_benefic(chart, c)
        exalt = c in _CLASSICAL and dignity_state(c, signs[c]) == "exalted"
        w = (0.75 if ben else -0.75) * scale + (0.5 * scale if exalt else 0.0)
        tag = "benefic" if ben else "malefic"
        out.append(Finding(f"conjunct {c} ({tag}{', exalted' if exalt else ''})",
                           round(w, 2), frame, "conjunction"))
    return out


def _assess_planet(chart: RamanChart, planet: str, role: str) -> FactorVerdict:
    d1, d9 = _d1_houses(chart), _d9_houses(chart)
    sign1 = chart.bundle.chart.planet_signs[planet]
    sign9 = chart.varga_signs[planet][9]
    f: list[Finding] = []
    h = d1[planet]
    if h in DUSTHANA:
        f.append(Finding(f"placed in the {h}th (dusthana)", -1.5, "Rasi", "placement"))
    elif h in set(KENDRA) | set(TRIKONA):
        f.append(Finding(f"placed in the {h}th (kendra/trikona)", 1.0, "Rasi", "placement"))
    f += _dignity_findings(chart, planet, sign1, "Rasi", 1.0)
    if sign1 == sign9:
        f.append(Finding("vargottama (same sign in Rasi & Navamsa)", 1.0, "both", "vargottama"))
    f += _aspect_findings(chart, d1, h, planet, "Rasi", 1.0)
    f += _conjunction_findings(chart, d1, planet, "Rasi", 1.0)
    f += _dignity_findings(chart, planet, sign9, "Navamsa", 0.5)
    f += _aspect_findings(chart, d9, d9[planet], planet, "Navamsa", 0.5)
    f += _conjunction_findings(chart, d9, planet, "Navamsa", 0.5)
    score = round(sum(x.delta for x in f), 3)
    return FactorVerdict(role, planet, _verdict_label(score), score, tuple(f))


def _assess_bhava(chart: RamanChart, house: int) -> FactorVerdict:
    d1 = _d1_houses(chart)
    f: list[Finding] = []
    occ = [p for p in GRAHAS if d1[p] == house]
    for p in occ:
        ben = _is_benefic(chart, p)
        f.append(Finding(f"occupied by {p} ({'benefic' if ben else 'malefic'})",
                         0.75 if ben else -0.75, "Rasi", "conjunction"))
    if not occ:
        f.append(Finding("occupied by no planet", 0.25, "Rasi", "conjunction"))
    f += _aspect_findings(chart, d1, house, None, "Rasi", 1.0)
    if not any(x.criterion == "aspect" for x in f):
        f.append(Finding("aspected by no planet", 0.25, "Rasi", "aspect"))
    kind, occ2, occ12 = _kartari(chart, house)
    if kind == "subha":
        f.append(Finding("hemmed between benefics (Subhakartari)", 1.0, "Rasi", "kartari"))
    elif kind == "papa":
        f.append(Finding("hemmed between malefics (Papakartari)", -1.0, "Rasi", "kartari"))
    if house == 1:                        # the Navamsa lagna
        d9 = _d9_houses(chart)
        f += _aspect_findings(chart, d9, 1, None, "Navamsa", 0.5)
    score = round(sum(x.delta for x in f), 3)
    return FactorVerdict("Lagna", f"house {house}", _verdict_label(score), score, tuple(f))


def _assess_lagna(chart): return _assess_bhava(chart, 1)


def _assess_lord(chart, house):
    return _assess_planet(chart, _lord_of(chart, house), "Lord")


def _assess_karaka(chart, house):
    return _assess_planet(chart, BHAVA_KARAKAS[house][0], "Karaka")


def _influence_factors(chart: RamanChart, house: int, planet: str) -> tuple[str, ...]:
    """Which of Raman's five factors the planet satisfies for the house."""
    d1 = _d1_houses(chart)
    lord = _lord_of(chart, house)
    facs: list[str] = []
    if planet == lord:
        facs.append("owns")
    if d1[planet] == house:
        facs.append("occupies")
    if house in aspects_from_planet(planet, d1[planet]):
        facs.append("aspects house")
    if planet != lord:
        if d1[lord] in aspects_from_planet(planet, d1[planet]):
            facs.append("aspects lord")
        if d1[planet] == d1[lord]:
            facs.append("conjoins lord")
    return tuple(facs)


def _nature_of(books, planet: str, lagna_sign: int) -> str:
    """The planet's own nature in the 1st, from the doctrine (planet-in-first)."""
    want = f".ch4.{planet.lower()}_in_first"
    for rules in books.values():
        for r in rules:
            if r["id"].endswith(want):
                txt = r["consequent"]["text"].split("—", 1)[-1]
                return " ".join(txt.replace("¬", "").split())[:180]
    return ""


def _build_conclusion(chart, house, books, lagna_v, lord_v, karaka_v,
                      influencers_tuple) -> Conclusion:
    lagna_sign = chart.bundle.chart.asc_sign
    ranked: list[Influencer] = []
    for p in influencers_tuple:
        facs = _influence_factors(chart, house, p)
        ranked.append(Influencer(
            planet=p, factors=facs,
            tier="mostly" if len(facs) >= 2 else "moderate",
            is_benefic=_is_benefic(chart, p),
            nature=_nature_of(books, p, lagna_sign)))
    ranked.sort(key=lambda i: (-len(i.factors), i.planet))
    # headline verdict: Raman bases it on the strength of Lagna + Lord + Karaka.
    score = round((lagna_v.score + lord_v.score + karaka_v.score) / 3.0, 3)
    mostly = [i.planet for i in ranked if i.tier == "mostly"]
    moderate = [i.planet for i in ranked if i.tier == "moderate"]
    if mostly and moderate:
        who = f"mostly {', '.join(mostly)}, and to a moderate extent {', '.join(moderate)}"
    elif mostly:
        who = ", ".join(mostly)
    else:
        who = ", ".join(moderate) + " (each by a single factor)"
    synthesis = (
        f"The planets influencing the {_ordinal(house)} house are {who}. The "
        f"native partakes of their blended natures, weighed by the "
        f"{lagna_v.label} Lagna, the {lord_v.label} lord and the "
        f"{karaka_v.label} karaka.")
    afflicted = tuple(i.planet for i in ranked if not i.is_benefic)
    return Conclusion(label=_verdict_label(score), score=score,
                      influencers=tuple(ranked), synthesis=synthesis,
                      afflicted_activators=afflicted)


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

    # ---- Raman's per-factor strength verdicts (Rasi + Navamsa) ----
    lagna_v = _assess_bhava(chart, house)
    lord_v = _assess_lord(chart, house)
    karaka_v = _assess_karaka(chart, house)
    conclusion = _build_conclusion(chart, house, books, lagna_v, lord_v, karaka_v,
                                   influencers)

    return HouseJudgment(
        house=house, domain=domain,
        frame_citation=METHOD_CITATIONS["frame"], steps=steps,
        blend_score=blend_score, blend_label=_label(blend_score),
        blend_modifier_citation=METHOD_CITATIONS["blend"], timing=timing,
        n_fired=n_fired, n_evaluable=evaluable,
        lagna_verdict=lagna_v, lord_verdict=lord_v, karaka_verdict=karaka_v,
        conclusion=conclusion,
    )


def judge_all_houses_doctrine(chart: RamanChart, *,
                              dasha: Mapping[str, str] | None = None
                              ) -> dict[int, HouseJudgment]:
    books = load_compendium()
    return {h: judge_house_doctrine(chart, h, books=books, dasha=dasha)
            for h in range(1, 13)}
