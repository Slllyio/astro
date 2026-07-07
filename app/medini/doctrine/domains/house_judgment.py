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
from app.core.dignity import dignity_state, SIGN_RULERS
from app.core.drishti_argala import aspects_from_planet, planets_aspecting_bhava
from app.core.functional_roles import functional_roles
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

# What each house signifies, from the opening line of its HTJAH chapter (ch. IV-XV).
# A per-house descriptor + the traditional name of its karaka, for context.
HOUSE_SIGNIFICATIONS: Mapping[int, str] = {
    1: "body, appearance, health, temperament, longevity",
    2: "family, speech, vision (eyes), food, wealth",
    3: "brothers & sisters, courage, short journeys, communication",
    4: "mother, happiness, home, lands & vehicles, education",
    5: "children, intelligence, past merit (purva-punya), speculation",
    6: "enemies, disease, debts, litigation",
    7: "wife / spouse, marriage, partnerships, passion",
    8: "longevity & death, obstacles, legacies, the occult",
    9: "father, fortune, dharma, preceptor, long journeys",
    10: "profession, status, karma, authority, honour",
    11: "gains, elder siblings, fulfilment of desires",
    12: "loss & expenditure, exile, moksha, bed-comforts",
}
# A house's own HTJAH chapter — its rules are that house's doctrine regardless of
# the coarse topic-domain tag. Populated per house as each is deepened (house 1
# is deliberately absent so its reviewed output stays byte-stable).
HOUSE_CHAPTERS: Mapping[int, tuple[str, ...]] = {
    2: ("ch5", "5"),
    3: ("ch6", "6"),
    4: ("ch7", "7"),
    5: ("ch8", "8"),
    6: ("ch9", "9"),
    7: ("ch11", "11"),
    8: ("ch12", "12"),
    9: ("ch13", "13"),
    10: ("ch14", "14"),
    11: ("ch15", "15"),
    12: ("ch16", "16"),
}
KARAKA_NAMES: Mapping[int, str] = {
    1: "Thanukaraka (body)", 2: "Dhanakaraka (wealth)", 3: "Bhratrukaraka (siblings)",
    4: "Matrukaraka (mother)", 5: "Putrakaraka (children)", 6: "Satrukaraka (enemies)",
    7: "Kalatrakaraka (spouse)", 8: "Ayushkaraka (longevity)", 9: "Pitrukaraka (father)",
    10: "Karmakaraka (profession)", 11: "Labhakaraka (gains)", 12: "Vyayakaraka (loss)",
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


# Raman's MD x AD fructification tiers (HTJAH pp. 44-48, "Nature of the Results").
# Ordered strongest -> weakest so a UI can sort/colour them.
ACTIVATION_TIERS = ("par excellence", "predominant", "limited", "dormant")
_TIER_GLOSS = {
    "par excellence": "both lords influence the house AND are mutually associated",
    "predominant": "both the major and sub lords influence the house",
    "limited": "only one of the two lords influences the house",
    "dormant": "neither lord influences the house — no results of this house",
}


@dataclasses.dataclass(frozen=True)
class AntarWindow:
    lord: str
    start_age: float
    end_age: float
    influences: bool              # does the sub-lord influence the house (5 factors)?
    is_current: bool              # is this the running antardasha (bhukti)?
    associated_with_md: bool      # is the sub-lord associated with the major lord?
    tier: str                     # ACTIVATION_TIERS: this MD x AD fructification


@dataclasses.dataclass(frozen=True)
class DasaWindow:
    lord: str
    start_age: float
    end_age: float
    influences: bool              # is this planet a house influencer (5 factors)?
    is_current: bool              # is this the running mahadasha?
    antardashas: tuple[AntarWindow, ...] = ()


@dataclasses.dataclass(frozen=True)
class HouseTiming:
    influencers: tuple[str, ...]
    windows: tuple[DasaWindow, ...]
    current_md: str | None
    current_ad: str | None
    current_is_activator: bool
    current_tier: str | None            # ACTIVATION_TIERS for the running MD x AD
    influence_by_factor: Mapping[str, tuple[str, ...]]  # Raman's (a)-(e) grouping
    active_outcomes: tuple[FiredEvidence, ...]
    method_citation: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class Combination:
    """A named combination (yoga) Raman states for the house — a compound of two or
    more placements. Some manifest in a specific lord's dasa (``dasha_lord``)."""
    rule_id: str
    text: str
    polarity: str                # favorable | unfavorable | mixed
    magnitude: str | None
    book: str
    dasha_lord: str | None       # the period in which it fructifies, if dasa-timed
    active_now: bool             # is that period running?


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
    first_house: "FirstHouseTestimony | None" = None
    chandra: "ReferenceJudgment | None" = None
    combinations: tuple["Combination", ...] = ()

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


def _planets_named(node) -> set[str]:
    p = node.get("planet")
    return set(p) if isinstance(p, (list, tuple)) else ({p} if isinstance(p, str) else set())


# leaf ops that assert a placement / aspect / lordship — the building blocks of a yoga
_COMBO_ATOM_OPS = frozenset({
    "planet_in_house", "planet_aspects_house", "lord_of_house_in_house",
    "planet_is_lord_of", "planet_aspects_planet", "planet_conjunct_planet",
    "planet_in_sign", "planet_aspects_lord", "lagna_sign_is",
})


def _is_combination(rule: dict) -> bool:
    """A named yoga: a COMPOUND antecedent (all / n-of / none) that conjoins two or
    more placements on DIFFERENT houses, planets, or lordships — as opposed to a
    single-factor testimony. These are Raman's stated combinations (e.g. 'benefics
    in 1, 11, 12 with the lagna lord in a trikona', 'three malefics in the 1st')."""
    node = rule["antecedent"]
    if not isinstance(node, Mapping) or node.get("op") not in ("all", "n_of", "none", "any"):
        return False
    atoms = [n for n in _walk(node)
             if isinstance(n, Mapping) and n.get("op") in _COMBO_ATOM_OPS]
    if len(atoms) < 2:
        return False
    houses: set[int] = set()
    planets: set[str] = set()
    lordships: set[int] = set()
    for a in atoms:
        houses |= _houses_of(a)
        planets |= _planets_named(a)
        if "of_house" in a:
            lordships.add(int(a["of_house"]))
    return len(houses) >= 2 or len(planets) >= 2 or len(lordships) >= 2


def _classify(rule: dict, house: int) -> str:
    """Assign a fired rule to Raman's analytical bucket by its antecedent shape."""
    nodes = _walk(rule["antecedent"])
    ops = {n["op"] for n in nodes if isinstance(n, Mapping) and "op" in n}
    if _is_timing(rule, ops):
        return "timing"
    # Combinations (yogas): a compound multi-placement antecedent is recognised as a
    # named combination BEFORE the single-factor buckets, so a yoga that merely
    # mentions a planet in the house is not mis-filed under Occupants.
    if _is_combination(rule):
        return "combinations"
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


_DASHA_YEARS = dict(DASHA_LORDS)

# Raman's five influence factors (HTJAH p. 44), in his (a)-(e) order, mapped to
# the tags _influence_factors emits.
_FACTOR_LABELS = ("owns", "aspects house", "occupies", "aspects lord",
                  "conjoins lord", "lord from Moon")
FACTOR_DESCRIPTIONS = {
    "owns": "(a) lord of the house",
    "aspects house": "(b) aspects the house",
    "occupies": "(c) posited in the house",
    "aspects lord": "(d) aspects the lord of the house",
    "conjoins lord": "(e) in association with the lord",
    "lord from Moon": "(f) lord of the house from the Moon",
}


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


def _birth_elapsed_into_md(moon_lon: float) -> float:
    """Years already elapsed into the birth mahadasha (so its antardasha balance
    can be trimmed to start at birth)."""
    return calculate_vimshottari_mahadasha(moon_lon, birth_jd=0.0)["time_elapsed_years"]


def _antardasha_spans(md_lord: str, md_start: float, md_end: float,
                      elapsed_into_md: float = 0.0) -> list[tuple[str, float, float]]:
    """Vimshottari antardasha (bhukti) windows inside one mahadasha, as
    (lord, start_age, end_age). Each sub-lord Y's span within lord X's dasa is
    ``total_X * total_Y / 120`` years, in the DASHA_LORDS order beginning with X.
    For the partial birth mahadasha, the sub-periods elapsed before birth are
    dropped and the running one is clipped to start at birth (Raman, Chart 11)."""
    idx0 = next(i for i, (l, _) in enumerate(DASHA_LORDS) if l == md_lord)
    total_md = _DASHA_YEARS[md_lord]
    notional_start = md_start - elapsed_into_md   # where the MD would have begun
    out: list[tuple[str, float, float]] = []
    cursor = notional_start
    for k in range(9):
        lord, total_y = DASHA_LORDS[(idx0 + k) % 9]
        length = total_md * total_y / 120.0
        a_s, a_e = cursor, cursor + length
        cursor = a_e
        if a_e <= md_start + 1e-9:        # wholly elapsed before birth
            continue
        out.append((lord, round(max(a_s, md_start), 3), round(min(a_e, md_end), 3)))
    return out


def _associated(chart: RamanChart, p1: str, p2: str) -> bool:
    """Two planets are 'associated' (Raman) when conjoined or in mutual aspect —
    the relation that turns a doubly-influencing MD x AD into results par excellence."""
    if p1 == p2:
        return False
    d1 = _d1_houses(chart)
    if d1[p1] == d1[p2]:
        return True
    return (d1[p2] in aspects_from_planet(p1, d1[p1])
            or d1[p1] in aspects_from_planet(p2, d1[p2]))


def _pair_tier(chart: RamanChart, house: int, md_lord: str, ad_lord: str) -> str:
    """Raman's fructification tier for a (major, sub) lord pair on a house."""
    md_inf = bool(_influence_factors(chart, house, md_lord))
    ad_inf = bool(_influence_factors(chart, house, ad_lord))
    if md_inf and ad_inf:
        return "par excellence" if _associated(chart, md_lord, ad_lord) else "predominant"
    if md_inf or ad_inf:
        return "limited"
    return "dormant"


# ============================================================ strength assessor
# Raman's ch. IV method judges each of Lagna / Lord / Karaka to a graded strength
# verdict from his own criteria — aspects, dignity (friend/enemy sign, exalt/debil,
# neechabhanga), vargottama, placement, kartari — CROSS-CHECKED in Rasi and Navamsa.
#
# The weights + the combine rule are DECODED from Raman's worked horoscopes in ch. IV
# (Charts 12-14; scratchpad/htjah_h1_calibration.json), tuned so the assessor
# reproduces his stated per-factor verdicts within one grade (9/9). Decoded facts:
#   * the Navamsa is CO-EQUAL with the Rasi (Chart 12: the lord Saturn is bad on every
#     Rasi count yet "fairly good" because the Navamsa redeems it) — not a half-modifier;
#   * a PLANET strong in EITHER varga is strong -> optimistic combine max()+0.3*min();
#     the BHAVA is additive across vargas;
#   * vargottama is top-tier (a vargottama Lagna is "very powerful");
#   * neechabhanga cancels debility; exalted-conjunction and kartari are big.
# Computed from low-level chart primitives (dignity, drishti, D9 frame), NOT judge_bhava.

_CLASSICAL = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
# dignity weights (decoded): exalt/own strong, friend/enemy moderate, debil strong-neg
_DIGNITY_W = {"exalted": 1.6, "own": 1.2, "friendly": 0.8, "neutral": 0.0,
              "inimical": -0.8, "debilitated": -1.6}
_W = dict(dusthana=-1.0, kendra_trikona=1.2, vargottama=1.2, neechabhanga=0.2,
          kartari_subha=1.0, kartari_papa=-1.0, aspect=0.7, conjunct=0.7,
          conjunct_exalted=1.6, bhava_aspect_mul=0.5, dusthana_lord=-1.0)

# Consolidation (post-twelve-house-walk): diminishing returns on STACKED POSITIVES.
# The held-out audit of every strength-graded house (2-5, 7, 9, 11) showed the same
# dominant error -- a factor reaches "very strong / very powerful" from placement +
# dignity + a benefic conjunction/vargottama stacked additively, where Raman reserves
# the top grades (confirmed ~29x, sharpest on exaltation). So a factor's POSITIVE
# contributions saturate: past one strong dignity's worth (the knee = the exaltation
# weight, 1.6) extra positives compound only weakly. Applied to the positive side
# ONLY -- the negative side is already correct (every afflicted/dusthana factor and
# ch. VIII's childless charts matched), and the knee is set so no mid-range verdict
# and no ch. IV calibration anchor (Charts 12-14) shifts out of within-one.
_RESCUE_KNEE = 1.2      # a stronger frame at/above this "earns" the optimistic rescue
_RESCUE_W_WEAK = 0.9    # discount on a DEEPLY-afflicted weaker frame when rescuer is mild
_AFFLICT_FLOOR = -1.0   # a weaker frame below this is "deeply afflicted" (>1 malefic)
_BLEND_W = 0.3          # optimistic cross-varga blend: score = max + _BLEND_W*min
_POS_KNEE = 1.6
_POS_SLOPE = 0.1


def _cap_positive(total_pos: float) -> float:
    """Soft-cap the summed positive contributions of a frame (diminishing returns)."""
    if total_pos <= _POS_KNEE:
        return total_pos
    return _POS_KNEE + (total_pos - _POS_KNEE) * _POS_SLOPE

VERDICT_SCALE = ("afflicted", "weak", "moderate", "moderately good", "fairly good",
                 "fairly strong", "fairly powerful", "very strong", "very powerful")
_THRESH = ((2.4, "very powerful"), (1.75, "very strong"), (1.25, "fairly powerful"),
           (0.9, "fairly strong"), (0.55, "fairly good"), (0.25, "moderately good"),
           (-0.6, "moderate"), (-1.6, "weak"))


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
    label: str           # VERDICT_SCALE
    score: float         # combined (cross-varga) score
    findings: tuple[Finding, ...]
    rasi_score: float = 0.0
    navamsa_score: float = 0.0


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


@dataclasses.dataclass(frozen=True)
class ReferenceJudgment:
    """The house judged from a second reference ascendant. Raman does this from
    the Moon (Chandra Lagna) throughout HTJAH — same lines as the Lagna: the bhava
    reckoned from the Moon, and its lord (the lord of the house counted from the
    Moon) graded with functional nature read from Chandra Lagna."""
    reference: str               # "Chandra Lagna (from the Moon)"
    reference_sign: int
    lord_planet: str             # lord of the house counted from the reference
    bhava: FactorVerdict
    lord: FactorVerdict
    note: str


# Raman on the first house (HTJAH ch. IV, "Results of Different Signs Ascending",
# pp. 30-31): the rising SIGN's own nature is only a baseline "to be blended with
# those of planets rising or aspecting" — so the assessor does NOT score it. But
# two of the preamble's directions ARE weighed: mind by the Moon, health by Sun +
# Moon + Lagna. These are prose directions, not DSL records, so they are cited to
# the passage rather than to a method id.
_SIGNS_ASCENDING_CITE = ("How to Judge a Horoscope, Vol. I, ch. IV — "
                         "Results of Different Signs Ascending (pp. 30-31)")


@dataclasses.dataclass(frozen=True)
class FirstHouseTestimony:
    """The two first-house directions of the Signs-Ascending preamble that turn
    on luminaries rather than the rising sign's own nature."""
    mind_verdict: str            # "The mental disposition should always be judged
    mind_note: str               #  by reference to the Moon and his disposition."
    health_flag: bool            # Sun + Moon + Lagna each afflicted, >1 malefic
    health_note: str
    afflicting_malefics: tuple[str, ...]
    citation: str = _SIGNS_ASCENDING_CITE


def _planet_nature(chart: RamanChart, planet: str,
                   ref_sign: int | None = None) -> tuple[bool, str]:
    """Raman's TWO malefic kinds: natural AND reference-specific functional
    ('for Aries the Sun is good'; 'the Moon, a malefic in this case'). Returns
    (is_benefic, tag). Benefic if a natural benefic (Moon by waxing paksha) OR a
    functional benefic / yogakaraka for the reference ascendant. ``ref_sign``
    defaults to the Lagna; pass the Moon's sign to read functional nature 'from
    Chandra Lagna' (Raman: 'evil by virtue of the ... lordship from Chandra Lagna')."""
    ref = ref_sign if ref_sign is not None else chart.bundle.chart.asc_sign
    if planet == "Moon":
        lons = chart.bundle.chart.planet_lons
        nat_ben = 0.0 <= (lons["Moon"] - lons["Sun"]) % 360.0 < 180.0
    else:
        nat_ben = planet in _NATURAL_BENEFICS
    fr = functional_roles(ref).get(planet)
    yk = bool(fr and fr.is_yogakaraka)
    fb = bool(fr and fr.is_functional_benefic)
    fm = bool(fr and fr.is_functional_malefic)
    # Functional status is lagna-specific and takes precedence over the natural
    # nature: a yogakaraka / functional benefic is good even if a natural malefic
    # (Saturn for Libra); a functional malefic — a maraka/dusthana lord — is bad
    # even if a natural benefic (Venus, lord of 7 & 12, for Scorpio).
    if yk:
        return True, "yogakaraka"
    if fb:
        return True, "functional benefic"
    if fm:
        return False, "functional malefic"
    return nat_ben, ("benefic" if nat_ben else "malefic")


def _is_benefic(chart: RamanChart, planet: str, ref_sign: int | None = None) -> bool:
    return _planet_nature(chart, planet, ref_sign)[0]


def _d1_houses(chart: RamanChart) -> dict[str, int]:
    return dict(chart.bundle.kundali.planet_house)


def _d9_houses(chart: RamanChart) -> dict[str, int]:
    return {p: chart.house_of(p, "navamsa") for p in GRAHAS}


def _lord_of(chart: RamanChart, house: int) -> str:
    return chart.bundle.sign_lord_of_house(house, from_moon=False)


def _resolve_period_lord(chart: RamanChart, of: str | None) -> str | None:
    """Resolve a timing 'of' token ('lord_of_1', a planet name) to a planet."""
    if not of:
        return None
    if of.startswith("lord_of_"):
        try:
            return _lord_of(chart, int(of.rsplit("_", 1)[1]))
        except (ValueError, KeyError):
            return None
    return of if of in GRAHAS else None


_ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th",
             7: "7th", 8: "8th", 9: "9th", 10: "10th", 11: "11th", 12: "12th"}


def _ordinal(n: int) -> str:
    return _ORDINALS.get(n, f"{n}th")


def _verdict_label(score: float) -> str:
    """Map a combined score to Raman's graded scale (decoded thresholds)."""
    for lo, lab in _THRESH:
        if score >= lo:
            return lab
    return "afflicted"


def _combine(findings: Sequence[Finding], *, additive: bool) -> tuple[float, float, float]:
    """Blend a factor's Rasi and Navamsa findings into one score.

    Decoded from Raman's worked charts: the BHAVA is additive across vargas,
    but a PLANET strong in EITHER varga is strong -> optimistic max()+0.3*min().
    Vargottama findings (frame 'both') count with the Rasi frame."""
    rasi_ds = [x.delta for x in findings if x.frame in ("Rasi", "both")]
    nav_ds = [x.delta for x in findings if x.frame == "Navamsa"]
    if additive:
        # BHAVA: additive across vargas; the positive contributions saturate together.
        allpos = _cap_positive(sum(d for d in rasi_ds + nav_ds if d > 0))
        allneg = sum(d for d in rasi_ds + nav_ds if d < 0)
        rasi = round(sum(rasi_ds), 3)
        nav = round(sum(nav_ds), 3)
        return round(allpos + allneg, 3), rasi, nav
    # PLANET: each varga's positive contributions saturate on their own, then the
    # optimistic max()+0.3*min() blend (a planet strong in EITHER varga is strong).
    rasi = round(_cap_positive(sum(d for d in rasi_ds if d > 0))
                 + sum(d for d in rasi_ds if d < 0), 3)
    nav = round(_cap_positive(sum(d for d in nav_ds if d > 0))
                + sum(d for d in nav_ds if d < 0), 3)
    # The optimistic blend rewards a planet strong in EITHER varga -- but only a
    # varga that was actually assessed. An UN-assessed frame is "no testimony", not
    # "neutral strength", so it must not stand in as a phantom 0 that rescues an
    # afflicted Rasi (Raman grades exalted-but-dusthana/papakartari Sun "afflicted",
    # not "moderate"). Blend only across frames that carry findings.
    if rasi_ds and nav_ds:
        hi, lo = (rasi, nav) if rasi >= nav else (nav, rasi)
        # Phase 2.5: the optimistic 30% discount on the weaker frame is EARNED only
        # when the stronger frame is genuinely strong (Chart 12: a Navamsa exaltation
        # rescues an afflicted Rasi). A merely-mild frame must NOT rescue a strongly
        # afflicted one -- there the affliction counts more (Raman grades such a
        # karaka "afflicted", not "moderately good"). The optimistic 30% discount is
        # withheld only from a DEEPLY-afflicted weaker frame (below _AFFLICT_FLOOR)
        # when the rescuer is itself mild -- a mild affliction is still rescued as
        # before, keeping the change narrow (house-1 Mars, lo -0.6, is untouched).
        w = (_RESCUE_W_WEAK if (lo < _AFFLICT_FLOOR and hi < _RESCUE_KNEE) else _BLEND_W)
        return round(hi + w * lo, 3), rasi, nav
    return (rasi if rasi_ds else nav), rasi, nav


def _neechabhanga(chart: RamanChart, planet: str, sign: int) -> bool:
    """Common neechabhanga: the dispositor of the debilitation sign sits in a
    kendra from the Lagna (a standard cancellation rule)."""
    from app.core.dignity import SIGN_RULERS
    dispositor = SIGN_RULERS.get(sign)
    if not dispositor:
        return False
    return chart.house_of(dispositor, "lagna") in KENDRA


def _kartari(chart: RamanChart, house: int,
             houses: Mapping[str, int] | None = None,
             ref_sign: int | None = None
             ) -> tuple[str | None, list[str], list[str]]:
    """Papakartari / Subhakartari around a house: occupants of the 2nd AND the
    12th from it all malefic (papa) or all benefic (subha). ``houses`` defaults
    to the Rasi placement map; pass the D9 or from-Moon map for another frame.
    ``ref_sign`` selects the ascendant for functional benefic/malefic."""
    hm = houses if houses is not None else _d1_houses(chart)
    second = house % 12 + 1
    twelfth = (house - 2) % 12 + 1
    occ2 = [p for p in GRAHAS if hm[p] == second]
    occ12 = [p for p in GRAHAS if hm[p] == twelfth]
    if occ2 and occ12:
        if all(not _is_benefic(chart, p, ref_sign) for p in occ2 + occ12):
            return "papa", occ2, occ12
        if all(_is_benefic(chart, p, ref_sign) for p in occ2 + occ12):
            return "subha", occ2, occ12
    return None, occ2, occ12


def _dignity_findings(chart, planet, sign, frame, scale=1.0) -> list[Finding]:
    if planet not in _CLASSICAL:
        return []
    dg = dignity_state(planet, sign)
    if dg == "debilitated" and _neechabhanga(chart, planet, sign):
        # cancellation lifts the debility to a mild positive (decoded 0.2), not -1.6.
        return [Finding(f"{planet} debilitated but neechabhanga (cancellation)",
                        round(_W["neechabhanga"] * scale, 2), frame, "dignity")]
    w = _DIGNITY_W.get(dg, 0.0) * scale
    if w == 0.0:
        return []
    return [Finding(f"{planet} in a {dg} sign", round(w, 2), frame, "dignity")]


def _aspect_findings(chart, houses, target_house, subject, frame, scale=1.0,
                     ref_sign=None, dignity_aware=False) -> list[Finding]:
    out: list[Finding] = []
    signs = (chart.bundle.chart.planet_signs if frame == "Rasi"
             else {p: chart.varga_signs[p][9] for p in GRAHAS}) if dignity_aware else None
    for a in planets_aspecting_bhava(target_house, houses):
        if a == subject:
            continue
        # An EXALTED planet aspecting a bhava strengthens it, whatever its
        # functional nature -- the same credit an exalted occupant/companion gets
        # (Raman, Chart 40: an exalted-Jupiter aspect helps make the 2nd "very
        # strongly situated"). dignity_aware is set only for bhava aspects.
        if (dignity_aware and a in _CLASSICAL
                and dignity_state(a, signs[a]) == "exalted"):
            out.append(Finding(f"aspected by {a} (exalted)",
                               round(_W["conjunct_exalted"] * scale, 2),
                               frame, "aspect"))
            continue
        ben, tag = _planet_nature(chart, a, ref_sign)
        w = (_W["aspect"] if ben else -_W["aspect"]) * scale
        out.append(Finding(f"aspected by {a} ({tag})", round(w, 2), frame, "aspect"))
    return out


def _conjunction_findings(chart, houses, planet, frame, scale=1.0,
                          ref_sign=None) -> list[Finding]:
    out: list[Finding] = []
    signs = (chart.bundle.chart.planet_signs if frame == "Rasi"
             else {p: chart.varga_signs[p][9] for p in GRAHAS})
    for c in GRAHAS:
        if c == planet or houses.get(c) != houses.get(planet):
            continue
        ben, tag = _planet_nature(chart, c, ref_sign)
        exalt = c in _CLASSICAL and dignity_state(c, signs[c]) == "exalted"
        if exalt:                          # an exalted companion is strongly good
            w = _W["conjunct_exalted"] * scale
            label = f"conjunct {c} (exalted)"
        else:
            w = (_W["conjunct"] if ben else -_W["conjunct"]) * scale
            label = f"conjunct {c} ({tag})"
        out.append(Finding(label, round(w, 2), frame, "conjunction"))
    return out


def _assess_planet(chart: RamanChart, planet: str, role: str, *,
                   ref_sign: int | None = None,
                   houses: Mapping[str, int] | None = None) -> FactorVerdict:
    """Grade a planet on Raman's criteria. Defaults reckon placement + functional
    nature from the Lagna; pass ``ref_sign`` (the Moon's sign) and ``houses`` (the
    from-Moon map) to grade the same planet 'from Chandra Lagna'. Dignity, aspects,
    conjunctions and vargottama are frame-invariant; only placement and functional
    benefic/malefic shift with the reference."""
    d1 = houses if houses is not None else _d1_houses(chart)
    d9 = _d9_houses(chart)
    sign1 = chart.bundle.chart.planet_signs[planet]
    sign9 = chart.varga_signs[planet][9]
    f: list[Finding] = []
    h = d1[planet]
    if h in DUSTHANA:
        f.append(Finding(f"placed in the {h}th (dusthana)", _W["dusthana"], "Rasi", "placement"))
    elif h in set(KENDRA) | set(TRIKONA):
        f.append(Finding(f"placed in the {h}th (kendra/trikona)",
                         _W["kendra_trikona"], "Rasi", "placement"))
    # Phase 2.4: a planet that OWNS a dusthana (6/8/12 from the Lagna) is a functional
    # malefic and thereby afflicted in itself (Raman, Chart 64: "the Moon owns the 6th
    # and hence afflicted"). The Lagna lord is exempt -- its ascendant lordship redeems
    # a coincidental dusthana ownership. Reckoned from the Lagna only (ref_sign None).
    if ref_sign is None:
        owned = [dh for dh in DUSTHANA if _lord_of(chart, dh) == planet]
        if owned and planet != _lord_of(chart, 1):
            f.append(Finding(
                f"owns the {owned[0]}th (dusthana lord → functional malefic)",
                _W["dusthana_lord"], "Rasi", "lordship"))
    # vargottama (same sign in both vargas) — decoded top-tier; counts with Rasi.
    if sign1 == sign9:
        f.append(Finding("vargottama (same sign in Rasi & Navamsa)",
                         _W["vargottama"], "both", "vargottama"))
    # Rasi frame — dignity, aspects, conjunctions, kartari (all co-equal weight).
    f += _dignity_findings(chart, planet, sign1, "Rasi")
    f += _aspect_findings(chart, d1, h, planet, "Rasi", ref_sign=ref_sign)
    f += _conjunction_findings(chart, d1, planet, "Rasi", ref_sign=ref_sign)
    kind, _o2, _o12 = _kartari(chart, h, d1, ref_sign)
    if kind == "subha":
        f.append(Finding("hemmed between benefics (Subhakartari)",
                         _W["kartari_subha"], "Rasi", "kartari"))
    elif kind == "papa":
        f.append(Finding("hemmed between malefics (Papakartari)",
                         _W["kartari_papa"], "Rasi", "kartari"))
    # Navamsa frame — CO-EQUAL (Chart 12: the Navamsa redeems a Rasi-afflicted lord).
    f += _dignity_findings(chart, planet, sign9, "Navamsa")
    f += _aspect_findings(chart, d9, d9[planet], planet, "Navamsa", ref_sign=ref_sign)
    f += _conjunction_findings(chart, d9, planet, "Navamsa", ref_sign=ref_sign)
    score, rasi, nav = _combine(f, additive=False)
    return FactorVerdict(role, planet, _verdict_label(score), score, tuple(f),
                         rasi_score=rasi, navamsa_score=nav)


def _assess_bhava(chart: RamanChart, house: int) -> FactorVerdict:
    """The Bhava — additive across vargas; aspects on the house weigh half a
    planet's (decoded ``bhava_aspect_mul``). A vargottama Lagna is an override:
    Raman calls it 'very powerful' outright (Chart 14)."""
    d1 = _d1_houses(chart)
    amul = _W["bhava_aspect_mul"]
    f: list[Finding] = []
    # vargottama Lagna override — Rasi ascendant sign == Navamsa ascendant sign.
    lagna_vargottama = (house == 1
                        and chart.lagna_sign("navamsa") == chart.lagna_sign("lagna"))
    occ = [p for p in GRAHAS if d1[p] == house]
    rasi_signs = chart.bundle.chart.planet_signs
    for p in occ:
        ben, tag = _planet_nature(chart, p)
        # An occupant's DIGNITY colours the house, not just its benefic/malefic
        # nature (Raman, e.g. the 11th's exalted Mercury is a rajayoga, not a bare
        # malefic). Mirror the exalted-companion credit already in
        # _conjunction_findings; add own-sign / (cancelled) debility for the same
        # high-signal dignities. Friendly/neutral occupants stay on nature alone.
        dg = dignity_state(p, rasi_signs[p]) if p in _CLASSICAL else None
        if dg == "exalted":
            f.append(Finding(f"occupied by {p} (exalted)",
                             _W["conjunct_exalted"], "Rasi", "conjunction"))
            continue
        f.append(Finding(f"occupied by {p} ({tag})",
                         round((_W["conjunct"] if ben else -_W["conjunct"]), 2),
                         "Rasi", "conjunction"))
        if dg == "own":
            f.append(Finding(f"occupant {p} in own sign",
                             _DIGNITY_W["own"], "Rasi", "dignity"))
        elif dg == "debilitated":
            if _neechabhanga(chart, p, rasi_signs[p]):
                f.append(Finding(
                    f"occupant {p} debilitated but neechabhanga (cancellation)",
                    _W["neechabhanga"], "Rasi", "dignity"))
            else:
                f.append(Finding(f"occupant {p} in debilitated sign",
                                 _DIGNITY_W["debilitated"], "Rasi", "dignity"))
    if not occ:
        f.append(Finding("occupied by no planet", 0.0, "Rasi", "conjunction"))
    ra = _aspect_findings(chart, d1, house, None, "Rasi", amul, dignity_aware=True)
    f += ra
    if not ra:
        f.append(Finding("aspected by no planet", 0.0, "Rasi", "aspect"))
    kind, occ2, occ12 = _kartari(chart, house)
    if kind == "subha":
        f.append(Finding("hemmed between benefics (Subhakartari)",
                         _W["kartari_subha"], "Rasi", "kartari"))
    elif kind == "papa":
        f.append(Finding("hemmed between malefics (Papakartari)",
                         _W["kartari_papa"], "Rasi", "kartari"))
    if house == 1:                        # the Navamsa lagna: aspects on it (×0.5)
        d9 = _d9_houses(chart)
        na = _aspect_findings(chart, d9, 1, None, "Navamsa", amul, dignity_aware=True)
        f += na
        nk, _n2, _n12 = _kartari(chart, 1, d9)
        if nk == "subha":
            f.append(Finding("Navamsa lagna hemmed between benefics (Subhakartari)",
                             _W["kartari_subha"], "Navamsa", "kartari"))
        elif nk == "papa":
            f.append(Finding("Navamsa lagna hemmed between malefics (Papakartari)",
                             _W["kartari_papa"], "Navamsa", "kartari"))
    if lagna_vargottama:
        f.insert(0, Finding("Lagna vargottama (same sign in Rasi & Navamsa)",
                            _W["vargottama"], "both", "vargottama"))
        return FactorVerdict("Lagna", f"house {house}", "very powerful",
                             99.0, tuple(f), rasi_score=99.0, navamsa_score=0.0)
    score, rasi, nav = _combine(f, additive=True)
    return FactorVerdict("Lagna", f"house {house}", _verdict_label(score), score,
                         tuple(f), rasi_score=rasi, navamsa_score=nav)


def _assess_lagna(chart): return _assess_bhava(chart, 1)


def _assess_lord(chart, house):
    return _assess_planet(chart, _lord_of(chart, house), "Lord")


def _assess_karaka(chart, house):
    return _assess_planet(chart, BHAVA_KARAKAS[house][0], "Karaka")


def _moon_houses(chart: RamanChart) -> dict[str, int]:
    """Planet -> house counted from the Moon (Chandra Lagna frame)."""
    return {p: chart.house_of(p, "moon") for p in GRAHAS}


def _lord_from_moon(chart: RamanChart, house: int) -> str:
    """Lord of the house counted from the Moon (Raman's factor (f))."""
    moon_sign = chart.bundle.chart.planet_signs["Moon"]
    return SIGN_RULERS[((moon_sign + house - 2) % 12) + 1]


def _assess_bhava_reference(chart: RamanChart, house: int,
                            houses: Mapping[str, int], ref_sign: int,
                            ref_name: str, exclude: str | None = None) -> FactorVerdict:
    """The bhava reckoned from a second ascendant (the Moon). Additive, aspects on
    the house weigh half — same shape as the Lagna bhava, but no Lagna-only
    vargottama/Navamsa-lagna specials (those belong to the birth ascendant).
    ``exclude`` drops the reference luminary from its own occupant list (the Moon
    defines the Chandra Lagna; it is not an affliction of it)."""
    amul = _W["bhava_aspect_mul"]
    f: list[Finding] = []
    occ = [p for p in GRAHAS if houses[p] == house and p != exclude]
    for p in occ:
        ben, tag = _planet_nature(chart, p, ref_sign)
        f.append(Finding(f"occupied by {p} ({tag})",
                         round((_W["conjunct"] if ben else -_W["conjunct"]), 2),
                         "Rasi", "conjunction"))
    if not occ:
        f.append(Finding("occupied by no planet", 0.0, "Rasi", "conjunction"))
    ra = _aspect_findings(chart, houses, house, None, "Rasi", amul, ref_sign=ref_sign)
    f += ra
    if not ra:
        f.append(Finding("aspected by no planet", 0.0, "Rasi", "aspect"))
    kind, _o2, _o12 = _kartari(chart, house, houses, ref_sign)
    if kind == "subha":
        f.append(Finding("hemmed between benefics (Subhakartari)",
                         _W["kartari_subha"], "Rasi", "kartari"))
    elif kind == "papa":
        f.append(Finding("hemmed between malefics (Papakartari)",
                         _W["kartari_papa"], "Rasi", "kartari"))
    score, rasi, nav = _combine(f, additive=True)
    return FactorVerdict(ref_name, f"{_ordinal(house)} from {ref_name}",
                         _verdict_label(score), score, tuple(f),
                         rasi_score=rasi, navamsa_score=nav)


def _assess_from_moon(chart: RamanChart, house: int) -> ReferenceJudgment:
    """Judge the house from the Moon (Chandra Lagna) on the same lines as the
    Lagna — Raman does this throughout HTJAH (82 'from the Moon' references)."""
    moon_sign = chart.bundle.chart.planet_signs["Moon"]
    mh = _moon_houses(chart)
    lord = _lord_from_moon(chart, house)
    bhava_v = _assess_bhava_reference(chart, house, mh, moon_sign, "Chandra Lagna",
                                      exclude="Moon")
    lord_v = _assess_planet(chart, lord, "Lord from Moon",
                            ref_sign=moon_sign, houses=mh)
    note = (
        f"Reckoned from the Moon, the {_ordinal(house)} bhava is {bhava_v.label} "
        f"and its lord {lord} is {lord_v.label}. Raman weighs this Chandra-Lagna "
        f"view alongside the Lagna (its lord is also his sixth influence factor).")
    return ReferenceJudgment(
        reference="Chandra Lagna (from the Moon)", reference_sign=moon_sign,
        lord_planet=lord, bhava=bhava_v, lord=lord_v, note=note)


def _malefic_afflictions(chart: RamanChart, house: int) -> list[str]:
    """Malefics (natural OR functional, per Raman's two-malefic rule) that afflict
    a house — those aspecting it or occupying it. Returns their names."""
    d1 = _d1_houses(chart)
    out: list[str] = []
    for p in planets_aspecting_bhava(house, d1):
        if not _is_benefic(chart, p):
            out.append(p)
    for p in GRAHAS:
        if d1[p] == house and not _is_benefic(chart, p) and p not in out:
            out.append(p)
    return out


def _first_house_testimony(chart: RamanChart) -> FirstHouseTestimony:
    """Mind by the Moon; health by Sun + Moon + Lagna (Signs-Ascending preamble)."""
    moon_v = _assess_planet(chart, "Moon", "Karaka")
    mind_note = (
        "The mental disposition is judged by the Moon and his disposition: the "
        f"Moon is {moon_v.label} here, colouring the native's mind accordingly.")
    d1 = _d1_houses(chart)
    lagna_af = _malefic_afflictions(chart, 1)
    sun_af = _malefic_afflictions(chart, d1["Sun"])
    moon_af = _malefic_afflictions(chart, d1["Moon"])
    # "When the Sun, the Moon and the ascendant are afflicted by more than one of
    # the malefics" — each of the three afflicted, and more than one malefic across.
    union = sorted(set(lagna_af) | set(sun_af) | set(moon_af))
    flag = bool(lagna_af and sun_af and moon_af and len(union) > 1)
    if flag:
        health_note = (
            "The Sun, the Moon and the ascendant are each afflicted by malefics "
            f"({', '.join(union)}) — Raman flags a liability to accidents or a "
            "violent/sudden turn of health (confirm from the 6th & 8th).")
    else:
        health_note = ("The Sun, Moon and ascendant are not jointly afflicted by "
                       "more than one malefic — no special accident liability flagged.")
    return FirstHouseTestimony(
        mind_verdict=moon_v.label, mind_note=mind_note,
        health_flag=flag, health_note=health_note,
        afflicting_malefics=tuple(union))


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
    # (f) Raman's sixth factor: the lord of the house counted from the Moon.
    if planet == _lord_from_moon(chart, house) and "owns" not in facs:
        facs.append("lord from Moon")
    return tuple(facs)


_HOUSE_WORDS = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
                6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth",
                11: "eleventh", 12: "twelfth"}


def _nature_of(books, planet: str, house: int) -> str:
    """The planet's effect in THIS house, from the doctrine (planet-in-Nth), if a
    record exists. Falls back to the empty string when the compendium has none."""
    word = _HOUSE_WORDS.get(house, "first")
    wants = (f"_{planet.lower()}_in_{word}", f".{planet.lower()}_in_{word}")
    for rules in books.values():
        for r in rules:
            if r["id"].endswith(wants[0]) or r["id"].endswith(wants[1]):
                txt = r["consequent"]["text"].split("—", 1)[-1]
                return " ".join(txt.replace("¬", "").split())[:180]
    return ""


def _build_conclusion(chart, house, books, lagna_v, lord_v, karaka_v,
                      influencers_tuple) -> Conclusion:
    ranked: list[Influencer] = []
    for p in influencers_tuple:
        facs = _influence_factors(chart, house, p)
        ranked.append(Influencer(
            planet=p, factors=facs,
            tier="mostly" if len(facs) >= 2 else "moderate",
            is_benefic=_is_benefic(chart, p),
            nature=_nature_of(books, p, house)))
    ranked.sort(key=lambda i: (-len(i.factors), i.planet))
    # headline verdict: decoded from Raman's own priority — "if the strength of the
    # lord is full there will be a good influence on the house": the Lord dominates,
    # then the Bhava, then the Karaka. (Cap the vargottama sentinel to its grade.)
    cap = _THRESH[0][0]                    # "very powerful" magnitude
    lagna_s = min(lagna_v.score, cap)
    score = round(0.5 * lord_v.score + 0.3 * lagna_s + 0.2 * karaka_v.score, 3)
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

    # Candidate rules: the house's primary domain, PLUS every rule from that
    # house's own HTJAH chapter (ch. IV = 1, ch. V = 2, ...; houses 7-12 live in
    # vol. two, ch. XI = 7, ..., ch. XVI = 12). A chapter's rules ARE that house's
    # doctrine irrespective of the coarse topic-domain tag, so e.g. the 2nd house
    # reads its eye / speech / learning sutras (tagged health_body / education),
    # and the 7th reads its career-tagged 7th-lord-in-10th sutra, that the
    # single-domain sweep would miss.
    candidates: list[dict] = list(by_domain.get(domain, ()))
    chapters = HOUSE_CHAPTERS.get(house, ())
    if chapters:
        cand_ids = {r["id"] for r in candidates}
        for book_name in ("htjah_vol1", "htjah_vol2"):
            for r in books.get(book_name, ()):
                if (r.get("provenance", {}).get("chapter") in chapters
                        and r["id"] not in cand_ids):
                    candidates.append(r)
                    cand_ids.add(r["id"])

    ctx = EvalContext(chart=chart, dasha=dasha)
    buckets: dict[str, list[FiredEvidence]] = {k: [] for k in STEP_ORDER}
    timing_fired: list[tuple[FiredEvidence, dict]] = []
    combos_fired: list[tuple[FiredEvidence, dict]] = []
    n_fired = evaluable = 0
    seen: set[str] = set()
    for rule in candidates:
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
        # a named yoga is surfaced as a Combination even when it is dasa-timed
        # (Raman's 'Lagna lord joins the Nth lord in the Nth' set) — collected here
        # in addition to its bucket so both the step vote and the yoga list see it.
        if _is_combination(rule):
            combos_fired.append((ev, rule))
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
    # the DSL five-factor influencers, PLUS Raman's sixth: the lord of the house
    # counted from the Moon (factor (f)).
    dsl_infl = {
        p for p in GRAHAS
        if evaluate_predicate(
            {"op": "planet_influences_house", "planet": p, "house": house}, ctx)
    }
    dsl_infl.add(_lord_from_moon(chart, house))
    influencers = tuple(p for p in GRAHAS if p in dsl_infl)
    infl_set = set(influencers)
    md = dasha.get("md") if dasha else None
    ad = dasha.get("ad") if dasha else None
    moon_lon = chart.bundle.chart.planet_lons["Moon"]
    # Raman's (a)-(e) grouping of the planets that influence this house.
    factor_map: dict[str, list[str]] = {f: [] for f in _FACTOR_LABELS}
    for p in GRAHAS:
        for fac in _influence_factors(chart, house, p):
            factor_map[fac].append(p)
    influence_by_factor = {f: tuple(v) for f, v in factor_map.items() if v}
    # mahadasha windows, each with its nested antardasha (bhukti) sub-periods and
    # the MD x AD fructification tier Raman assigns to the pair.
    seq = _maha_sequence(moon_lon)
    elapsed0 = _birth_elapsed_into_md(moon_lon)
    windows_l: list[DasaWindow] = []
    for i, (l, s, e) in enumerate(seq):
        elapsed = elapsed0 if i == 0 else 0.0
        antars = tuple(
            AntarWindow(
                lord=al, start_age=as_, end_age=ae_,
                influences=al in infl_set, is_current=(l == md and al == ad),
                associated_with_md=_associated(chart, l, al),
                tier=_pair_tier(chart, house, l, al))
            for al, as_, ae_ in _antardasha_spans(l, s, e, elapsed)
        )
        windows_l.append(DasaWindow(
            lord=l, start_age=round(s, 2), end_age=round(e, 2),
            influences=l in infl_set, is_current=(l == md), antardashas=antars))
    windows = tuple(windows_l)
    current_is_activator = md in infl_set if md else False
    current_tier = _pair_tier(chart, house, md, ad) if md and ad else None
    active_outcomes = tuple(
        ev for ev, rule in timing_fired
        if (rule["consequent"].get("timing") or {}).get("of") == md
    )
    timing = HouseTiming(
        influencers=influencers, windows=windows, current_md=md, current_ad=ad,
        current_is_activator=current_is_activator, current_tier=current_tier,
        influence_by_factor=influence_by_factor, active_outcomes=active_outcomes,
        method_citation=METHOD_CITATIONS["timing"],
    )

    # ---- Raman's per-factor strength verdicts (Rasi + Navamsa) ----
    lagna_v = _assess_bhava(chart, house)
    lord_v = _assess_lord(chart, house)
    karaka_v = _assess_karaka(chart, house)
    conclusion = _build_conclusion(chart, house, books, lagna_v, lord_v, karaka_v,
                                   influencers)
    first_house = _first_house_testimony(chart) if house == 1 else None
    chandra = _assess_from_moon(chart, house)

    # ---- named combinations (yogas) that fired for this house ----
    combos: list[Combination] = []
    for ev, rule in combos_fired:
        of = (rule["consequent"].get("timing") or {}).get("of")
        dl = _resolve_period_lord(chart, of)
        combos.append(Combination(
            rule_id=ev.rule_id, text=ev.text, polarity=ev.polarity,
            magnitude=ev.magnitude, book=ev.book, dasha_lord=dl,
            active_now=(dl is not None and dl == md)))
    # strongest / most specific first: favourable+unfavourable before mixed, then by text
    _pol_rank = {"unfavorable": 0, "favorable": 0, "mixed": 1}
    combos.sort(key=lambda c: (_pol_rank.get(c.polarity, 2), c.rule_id))

    return HouseJudgment(
        house=house, domain=domain,
        frame_citation=METHOD_CITATIONS["frame"], steps=steps,
        blend_score=blend_score, blend_label=_label(blend_score),
        blend_modifier_citation=METHOD_CITATIONS["blend"], timing=timing,
        n_fired=n_fired, n_evaluable=evaluable,
        lagna_verdict=lagna_v, lord_verdict=lord_v, karaka_verdict=karaka_v,
        conclusion=conclusion, first_house=first_house, chandra=chandra,
        combinations=tuple(combos),
    )


def judge_all_houses_doctrine(chart: RamanChart, *,
                              dasha: Mapping[str, str] | None = None
                              ) -> dict[int, HouseJudgment]:
    books = load_compendium()
    return {h: judge_house_doctrine(chart, h, books=books, dasha=dasha)
            for h in range(1, 13)}
