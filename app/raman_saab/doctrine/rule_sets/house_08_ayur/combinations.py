"""House 8 (Ayur / Randhra / Mrityu Bhava) — "Important Combinations".

Encodes the combination rule-atoms of the "Important Combinations" tables in
``docs/raman_saab/methodology/house_08_ayur.md`` (HTJAH-II:3084–3727, plus the
legacies/sudden-gains atoms at 3490–3574 and the place-of-death atoms at
3900–3908).

Encoding policy (honest, atom by atom — mirrors H2/H3):

* Existing condition-algebra predicates compose directly (``InRashiHouse``,
  ``Conjunct``, ``InSign``, ``CountInHouse``, ``HemmedBy``, ``MoonPhase``,
  ``Aspects``). Where a rule needs a refinement the algebra cannot express, the
  rasi-core fires and the refinement is kept in the result text (H2/H3 convention).
* Rules requiring predicates not yet in the algebra — the **22nd Drekkana** (D3)
  and its named-decanate grid, the **64th Navamsa from the Moon**, **Mandi/Gulika**
  position, planet "strength"/"weak" gates, the Navamsa-Lagna-lord place-of-death
  read — go in as ``kind="descriptive"`` with a ``TODO(predicate)`` note. Stage-5
  picks them up; the Stage-6 longevity sub-engine owns span/death timing.

LONGEVITY GUARD (methodology §1, §8): nature/cause/place/manner-of-death and the
chronic-disease atoms carry ``signification="death"`` (and the existing placements
carry ``"longevity"``) — both are clamped by ``LONGEVITY_GUARD`` until Phase E, so
an "afflicted" death verdict is *noted*, never pronounced here. The NON-guarded,
measurable matters are **legacies / inheritance** (``signification="legacies"``)
and **sudden gains** (``signification="sudden_gains"``); their significations were
re-tagged off the "longevity" bridge in ``significations.py`` so this layer can
move their verdicts. No rule double-counts a placement already fired by
``planets_in_8th`` / ``lord_in_12`` within the SAME signification (they route to
the distinct legacies/sudden_gains/death matters).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS)


# ── helpers ───────────────────────────────────────────────────────────────────

def _lord_of(house: int, chart: RamanChart) -> str:
    """Lord of whole-sign house `house` (1..12) counted from the Lagna."""
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _eighth_sign(chart: RamanChart) -> int:
    """The rashi (1..12) occupying the 8th whole-sign house."""
    return ((chart.asc_sign - 1) + 7) % 12 + 1


# Sign modality (chara/sthira/dwiswabhava) for the place-of-death rules.
_MOVABLE_SIGNS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})   # Ar Cn Li Cp
_FIXED_SIGNS: Final[frozenset[int]] = frozenset({2, 5, 8, 11})     # Ta Le Sc Aq
_COMMON_SIGNS: Final[frozenset[int]] = frozenset({3, 6, 9, 12})    # Ge Vi Sg Pi
_MODALITY: Final[dict[str, frozenset[int]]] = {
    "movable": _MOVABLE_SIGNS, "fixed": _FIXED_SIGNS, "common": _COMMON_SIGNS}


# ── local leaf predicates (conditions.py intentionally untouched) ─────────────

class _LagnaInSign(C.Condition):
    """The Ascendant rashi IS `sign` (1..12)."""
    def __init__(self, sign: int) -> None:
        self.sign = sign

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return ctx.chart.asc_sign == self.sign


class _EighthSignModality(C.Condition):
    """The sign in the 8th whole-sign house is movable / fixed / common."""
    def __init__(self, modality: str) -> None:
        self.modality = modality

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _eighth_sign(ctx.chart) in _MODALITY[self.modality]


class _PlanetInWaterySign(C.Condition):
    """`planet` occupies a watery rashi (Cancer/Scorpio/Pisces)."""
    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and C.SignIsWatery(p.sign)


class _ConjunctAnyMalefic(C.Condition):
    """A natural malefic (other than `planet` itself) shares `planet`'s house."""
    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        if p is None:
            return False
        return any(name != self.planet and name in NATURAL_MALEFICS
                   and q.rasi_house == p.rasi_house
                   for name, q in ctx.chart.planets.items())


class _AspectedByClass(C.Condition):
    """Some natural planet of `klass` ∈ {"malefic","benefic"} (other than `target`)
    casts a whole-sign drishti on `target`."""
    def __init__(self, target: str, klass: str) -> None:
        self.target, self.klass = target, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        if self.target not in ctx.chart.planets:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != self.target and name in group
                   and drishti.aspects_planet(name, self.target, ctx.chart)
                   for name in ctx.chart.planets)


class _PlanetWithHouseLord(C.Condition):
    """`planet` shares a house with the lord of house `house` (e.g. "Sun with the
    8th or 11th lord"). Identity (planet IS that lord) → False, by the LordsConjunct
    convention (a planet is not "with" itself)."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        if lord == self.planet:
            return False
        return C.Conjunct(self.planet, lord).evaluate(ctx)


class _LordsRelated(C.Condition):
    """Lords of houses `h1` and `h2` are "related": conjunction, mutual aspect, or
    parivartana (sign-exchange). Backs Raman's recurring "X and Y lords related"
    phrasing (rule 3: "6th & 8th lords related → death follows ill-health")."""
    def __init__(self, h1: int, h2: int) -> None:
        self.h1, self.h2 = h1, h2

    def evaluate(self, ctx: C.EvalContext) -> bool:
        l1, l2 = _lord_of(self.h1, ctx.chart), _lord_of(self.h2, ctx.chart)
        if l1 == l2:
            return True
        if C.LordsConjunct(self.h1, self.h2).evaluate(ctx):
            return True
        if drishti.mutual_aspect(l1, l2, ctx.chart):
            return True
        return C.Parivartana(self.h1, self.h2).evaluate(ctx)


def _all_in_house(planets: tuple[str, ...], house: int) -> C.Condition:
    """And(...) of `planets` each occupying whole-sign `house`."""
    return C.And(*(C.InRashiHouse(p, house) for p in planets))


# ── RULES ─────────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ===== Source & nature of death (HTJAH-II:3084–3090) — sig "death" (guarded) =====
    RuleRecord(
        id="H8.C.1", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.CountInHouse(8, 1, "malefic"),
        fortified=None,
        afflicted="malefics in the 8th → unnatural death (suicide, murder or accident)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3084)),
    RuleRecord(
        id="H8.C.2", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.CountInHouse(8, 1, "benefic"),
        fortified="benefic influence on the 8th → natural death (disease or old age)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3085)),
    RuleRecord(
        id="H8.C.3", house=8, signification="death", group="combination", kind="evaluable",
        condition=_LordsRelated(6, 8),
        fortified=None,
        afflicted="6th and 8th lords related → death follows a spell of ill-health",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3087)),
    RuleRecord(
        id="H8.C.4", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="6th and 8th houses severely afflicted → death after prolonged suffering "
                  "(chronic disease). TODO(predicate: affliction-grade aggregate)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3088)),
    RuleRecord(
        id="H8.C.5", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="a malefic in the 8th makes the death painful whether natural or violent "
                  "(refinement of H8.C.1 — not re-scored to avoid double-counting the "
                  "malefic-in-8th testimony)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3880)),
    RuleRecord(
        id="H8.C.6", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified="8th beneficially disposed → a sudden, quick end (refinement of H8.C.2)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3881)),

    # ===== Nature of death — Mandi/Navamsa entry points (descriptive — need Mandi) =====
    RuleRecord(
        id="H8.C.7", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified="benefic in the 7th from Mandi in the Navamsa → a happy death",
        afflicted="malefic in the 7th from Mandi in the Navamsa → a painful death; Saturn "
                  "there → death by snakes/thieves/supernatural beings; Mars → killed in a "
                  "fight; a luminary → death sentence / political death (Moon → mauled by an "
                  "aquatic animal). TODO(predicate: Mandi + 7th-from-Mandi in Navamsa)",
        frame="KARAKA", varga="D9", polarity="neutral", source=Citation("HTJAH-II", 3594)),

    # ===== Specific killer placements in the 8th — sig "death" (guarded) =====
    RuleRecord(
        id="H8.C.12", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(
            C.InRashiHouse("Moon", 8),
            C.Or(C.Conjunct("Moon", "Mars"), C.Conjunct("Moon", "Saturn"),
                 C.Conjunct("Moon", "Rahu"))),
        fortified=None,
        afflicted="Moon in the 8th with Mars, Saturn or Rahu → death by epilepsy",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3613)),
    RuleRecord(
        id="H8.C.13", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 8), C.Aspects("Saturn", "Moon")),
        fortified=None,
        afflicted="Moon in the 8th aspected by (strong) Saturn → surgery, or an anus / eye "
                  "ailment",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3616)),
    RuleRecord(
        id="H8.C.14", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="a waning Moon with Mars/Saturn/Rahu in the 8th → possession, drowning, "
                  "fire or weapon (refinement of H8.C.12 by Moon phase — not re-scored)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3618)),
    RuleRecord(
        id="H8.C.15", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mercury", 8), C.InRashiHouse("Venus", 8)),
        fortified=None,
        afflicted="Mercury and Venus in the 8th → dies while asleep",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3645)),
    RuleRecord(
        id="H8.C.16", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mercury", 8), C.InRashiHouse("Saturn", 8)),
        fortified=None,
        afflicted="Mercury and Saturn in the 8th → sentenced to the gallows",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3646)),
    RuleRecord(
        id="H8.C.17", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.Conjunct("Moon", "Mercury"),
                        C.Or(C.InRashiHouse("Moon", 6), C.InRashiHouse("Moon", 8))),
        fortified=None,
        afflicted="Moon and Mercury together in the 6th or 8th → poison the cause of death",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3647)),
    RuleRecord(
        id="H8.C.18", house=8, signification="death", group="combination", kind="evaluable",
        condition=_all_in_house(("Moon", "Mars", "Saturn"), 8),
        fortified=None,
        afflicted="Moon, Mars and Saturn together in the 8th → death by a weapon",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3650)),
    RuleRecord(
        id="H8.C.19", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="Mars and the Sun exchange signs and stand in a kendra to the 8th lord → "
                  "death-sentence by government. TODO(predicate: kendra-from-lord)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3662)),
    RuleRecord(
        id="H8.C.20", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="generic cause by the planet influencing the 8th — Sun→fire, Moon→water, "
                  "Mars→weapons, Mercury→fever, Jupiter→undiagnosable, Venus→excesses, "
                  "Saturn→starvation (use the 22nd-drekkana lord when the 8th is empty). "
                  "TODO(predicate: 22nd-drekkana lord lookup)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3884)),

    # ===== Nature-of-Death Killer Combinations (HTJAH-II:3620–3727) =====
    RuleRecord(
        id="H8.K.1", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.Or(_all_in_house(("Moon", "Sun", "Mars", "Saturn"), 8),
                       _all_in_house(("Moon", "Sun", "Mars", "Saturn"), 5),
                       _all_in_house(("Moon", "Sun", "Mars", "Saturn"), 9)),
        fortified=None,
        afflicted="Moon, Sun, Mars and Saturn together in the 8th, 5th or 9th → fall from a "
                  "height, drowning, or thunderstorm/lightning",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3620)),
    RuleRecord(
        id="H8.K.2", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 8), C.InRashiHouse("Mars", 9),
                        C.InRashiHouse("Sun", 1), C.InRashiHouse("Saturn", 5)),
        fortified=None,
        afflicted="Moon in 8th, Mars in 9th, Sun in Lagna, Saturn in 5th → thunderbolt or "
                  "the fall of a tree",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3623)),
    RuleRecord(
        id="H8.K.3", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.MoonPhase("waning"),
                        C.Or(C.InRashiHouse("Moon", 6), C.InRashiHouse("Moon", 8)),
                        C.CountInHouse(4, 1, "malefic"), C.CountInHouse(10, 1, "malefic")),
        fortified=None,
        afflicted="a waning Moon in the 6th/8th with malefics in the 4th and 10th → death "
                  "brought about through the scheming of an enemy",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3625)),
    RuleRecord(
        id="H8.K.4", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 8), C.InRashiHouse("Moon", 1),
                        C.InRashiHouse("Jupiter", 12), C.CountInHouse(4, 1, "malefic")),
        fortified=None,
        afflicted="Sun in 8th, Moon in Lagna, Jupiter in 12th, a malefic in 4th → dies as a "
                  "result of falling from a cot",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3629)),
    RuleRecord(
        id="H8.K.6", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 4), C.InRashiHouse("Moon", 10),
                        C.InRashiHouse("Saturn", 8)),
        fortified=None,
        afflicted="Sun in 4th, Moon in 10th, Saturn in 8th → hit accidentally by a log of "
                  "wood and dies",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3633)),
    RuleRecord(
        id="H8.K.7", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 7), C.InRashiHouse("Moon", 7),
                        C.InRashiHouse("Mercury", 7), C.InRashiHouse("Saturn", 1),
                        C.InRashiHouse("Mars", 12)),
        fortified="Sun+Moon+Mercury in 7th, Saturn in Lagna, Mars in 12th → a peaceful end in "
                  "tranquil surroundings, outside the country of birth",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3636)),
    RuleRecord(
        id="H8.K.8", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.Or(C.And(C.InRashiHouse("Sun", 8), C.InRashiHouse("Moon", 8)),
                       C.And(C.InRashiHouse("Sun", 6), C.InRashiHouse("Moon", 6))),
        fortified=None,
        afflicted="Sun and Moon together in the 8th or the 6th → killed by a ferocious animal",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3642)),
    RuleRecord(
        id="H8.K.10", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.Or(C.InSign("Moon", 1), C.InSign("Moon", 8)),
                        C.HemmedBy("Moon", "malefic")),
        fortified=None,
        afflicted="Moon in Aries or Scorpio hemmed between malefics → death through burns or "
                  "a weapon",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3655)),
    RuleRecord(
        id="H8.K.11", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 8), C.InRashiHouse("Mars", 10),
                        C.InRashiHouse("Saturn", 4), C.InRashiHouse("Sun", 1)),
        fortified=None,
        afflicted="Moon in 8th, Mars in 10th, Saturn in 4th, Sun in Lagna → death by a blunt "
                  "object (a club)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3657)),
    RuleRecord(
        id="H8.K.12", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 7), C.InRashiHouse("Moon", 1),
                        C.InRashiHouse("Saturn", 1)),
        fortified=None,
        afflicted="Mars in 7th, Moon and Saturn in Lagna → tortured to death",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3659)),
    RuleRecord(
        id="H8.K.18", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InSign("Venus", 1), C.InRashiHouse("Sun", 1),
                        C.InRashiHouse("Moon", 7), _ConjunctAnyMalefic("Moon")),
        fortified=None,
        afflicted="Venus in Aries, Sun in Lagna, Moon with a malefic in the 7th → a woman is "
                  "the cause of death",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3701)),
    # Corpus 3705-3708 gives food-poisoning TWO ways: (a) Moon+Saturn in 8th with
    # Mars-4/Sun-7, OR (b) Moon+Mercury in the 6th. Only branch (a) is encoded here:
    # branch (b) is the SAME Moon+Mercury-in-6th testimony already owned by H8.C.17
    # (poison, cite 3647) under the same "death" signification, so re-scoring it in
    # K.20 would double-count it. The omission is a deliberate de-dup, not a drop.
    RuleRecord(
        id="H8.K.20", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 8), C.InRashiHouse("Saturn", 8),
                        C.Or(C.InRashiHouse("Mars", 4), C.InRashiHouse("Sun", 7))),
        fortified=None,
        afflicted="Moon and Saturn in the 8th with Mars in the 4th or the Sun in the 7th → "
                  "death through food poisoning (the corpus's alternate Moon+Mercury-in-6th "
                  "branch is owned by H8.C.17 to avoid double-counting)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3705)),
    RuleRecord(
        id="H8.K.22", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 8), _PlanetInWaterySign("Moon")),
        fortified=None,
        afflicted="Moon in the 8th in a watery sign → consumption leads to death",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3712)),
    RuleRecord(
        id="H8.K.23", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InSign("Mercury", 5), _AspectedByClass("Mercury", "malefic")),
        fortified=None,
        afflicted="Mercury in Leo aspected by a malefic → death caused by fever",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3716)),
    RuleRecord(
        id="H8.K.24", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Venus", 8), _AspectedByClass("Venus", "malefic")),
        fortified=None,
        afflicted="Venus in the 8th aspected by a malefic → consumption, rheumatism or "
                  "diabetes",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3717)),
    RuleRecord(
        id="H8.K.25", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Jupiter", 8), _PlanetInWaterySign("Jupiter")),
        fortified=None,
        afflicted="Jupiter in the 8th in a watery sign → affection of the lungs",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3719)),
    RuleRecord(
        id="H8.K.26", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Rahu", 8), _AspectedByClass("Rahu", "malefic")),
        fortified=None,
        afflicted="Rahu in the 8th aspected by a malefic → small-pox, boils, snake-bite, a "
                  "fall or biliousness",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3720)),
    RuleRecord(
        id="H8.K.27", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 6), C.Aspects("Sun", "Mars")),
        fortified=None,
        afflicted="Mars in the 6th aspected by the Sun → diarrhoea",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3722)),
    RuleRecord(
        id="H8.K.28", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 8), C.InRashiHouse("Saturn", 8)),
        fortified=None,
        afflicted="Mars and Saturn together in the 8th → affliction to the aorta",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3724)),
    RuleRecord(
        id="H8.K.29", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mercury", 9), C.InRashiHouse("Venus", 9)),
        fortified=None,
        afflicted="Mercury and Venus in the 9th → heart disease",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3725)),
    RuleRecord(
        id="H8.K.30", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InSign("Moon", 6), C.HemmedBy("Moon", "malefic")),
        fortified=None,
        afflicted="Moon in Virgo hemmed between malefics → anaemia",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3726)),

    # ===== Suicide by hanging / poison (22nd drekkana + Navamsa — descriptive) =====
    RuleRecord(
        id="H8.C.21", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="5th/9th from Moon afflicted by a malefic AND a Sarpa/Nigada/Pasa/Ayudha "
                  "drekkana rises in the 8th Bhava (the 22nd drekkana) → suicide by hanging. "
                  "TODO(predicate: 22nd-drekkana named-decanate)",
        frame="LAGNA", varga="D3", polarity="malefic", source=Citation("HTJAH-II", 3684)),
    RuleRecord(
        id="H8.C.22", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="10th lord from Navamsa-Lagna with Rahu/Ketu → ends life by hanging; with "
                  "Saturn or in 6/8/12 → death by poisoning. TODO(predicate: Navamsa 10th lord)",
        frame="KARAKA", varga="D9", polarity="malefic", source=Citation("HTJAH-II", 3681)),

    # ===== Place of death (8th-sign modality, HTJAH-II:3900–3908) — sig "death" =====
    RuleRecord(
        id="H8.C.24", house=8, signification="death", group="combination", kind="evaluable",
        condition=_EighthSignModality("movable"),
        fortified=None,
        afflicted="the 8th is a movable sign → dies in a foreign country / far from birthplace",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3900)),
    RuleRecord(
        id="H8.C.25", house=8, signification="death", group="combination", kind="evaluable",
        condition=_EighthSignModality("fixed"),
        fortified="the 8th is a fixed sign → dies at the place of birth (drawn back to it)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3902)),
    RuleRecord(
        id="H8.C.26", house=8, signification="death", group="combination", kind="evaluable",
        condition=_EighthSignModality("common"),
        fortified=None,
        afflicted="the 8th is a common sign → dies while travelling / commuting",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3906)),
    RuleRecord(
        id="H8.C.27", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="place of death also read from the sign of the Navamsa-Lagna lord (or its "
                  "aspector / its Navamsa-sign lord). TODO(predicate: Navamsa-Lagna-lord sign)",
        frame="KARAKA", varga="D9", polarity="neutral", source=Citation("HTJAH-II", 3893)),

    # ===== Legacies / inheritance / unearned wealth — NON-GUARDED, measurable =====
    RuleRecord(
        id="H8.C.28", house=8, signification="legacies", group="combination", kind="evaluable",
        condition=C.InRashiHouse("Moon", 8),
        fortified="Moon in the 8th → acquires possessions easily through legacies or inheritance",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3502)),
    RuleRecord(
        id="H8.C.30", house=8, signification="legacies", group="combination", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 8),
        fortified="Mercury in the 8th → inherits as well as earns much wealth",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3525)),
    # Two-disjunct rule: Venus-in-8th (cite 3539) OR benefic-aspected Ketu-in-8th
    # (cite HTJAH-II:3574, "If Ketu in the 8th is aspected by a benefic, the native
    # enjoys much wealth and long life"). The record carries the Venus line per the
    # one-Citation-per-record convention; the Ketu branch's source is 3574.
    RuleRecord(
        id="H8.C.31", house=8, signification="legacies", group="combination", kind="evaluable",
        condition=C.Or(C.InRashiHouse("Venus", 8),
                       C.And(C.InRashiHouse("Ketu", 8), _AspectedByClass("Ketu", "benefic"))),
        fortified="Venus in the 8th (or a benefic-aspected Ketu in the 8th) → comes by much "
                  "wealth and long life",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3539)),
    RuleRecord(
        id="H8.C.29", house=8, signification="sudden_gains", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 8),
                        C.Or(_PlanetWithHouseLord("Sun", 8), _PlanetWithHouseLord("Sun", 11))),
        fortified="Sun in the 8th associated with the 8th or 11th lord → sudden monetary gain "
                  "via speculation",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3491)),
    RuleRecord(
        id="H8.C.32", house=8, signification="sudden_gains", group="combination", kind="evaluable",
        condition=C.LordIn(8, 10),
        fortified="8th lord in the 10th → unexpected gains via the death of superiors or elders",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3039)),

    # ===== Chronic / incurable disease (HTJAH-II:3583–3589) — sig "death" (guarded) =====
    RuleRecord(
        id="H8.D.1", house=8, signification="death", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 8),
                        C.Or(_ConjunctAnyMalefic("Saturn"), C.InRashiHouse("Rahu", 1))),
        fortified=None,
        afflicted="Saturn in the 8th with a malefic, or Rahu in the Lagna → stomach complaints",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3583)),
    RuleRecord(
        id="H8.D.2", house=8, signification="death", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="Lagna aspected by a malefic, the 8th lord weak, and the 8th aspected or "
                  "occupied by Saturn → a disease that prevents the intake of food (minor: "
                  "colds/mumps; serious: cancer, by affliction-grade). TODO(predicate: "
                  "8th-lord-weak gate)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3584)),
)
