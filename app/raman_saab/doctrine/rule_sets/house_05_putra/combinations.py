"""House 5 (Putra — children / intellect / poorvapunya) — "Important Combinations".

Encodes the combination rule-atoms of the "Important Combinations" tables in
``docs/raman_saab/methodology/house_05_putra.md`` (HTJAH-I:5183-5228, 5271).

Encoding policy (honest, atom by atom — mirrors H2/H3/H4/H7/H8/H10):

* Existing predicates compose directly. Children/sex/count/adoption/obedience rules
  route to ``children``; brain/intellect rules route to ``intellect`` (its sig
  rule_tags was extended to ("intellect","children") so it aggregates the shared
  placements AND its own combos).
* Children/progeny verdicts pass through the Beeja/Kshetra **fertility gate**
  (``_fertility_gate``, house_template.py) — the begetting pre-pass; these combos
  feed that matter.
* Rules needing predicates not yet in the algebra — **Navamsa**/**Drekkana** lord
  overlays, the Beeja/Kshetra **sphuta**, planet strength gates, native-sex
  determination, and from-5th-lord frames — go in as ``kind="descriptive"`` with a
  ``TODO(predicate)`` note.
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


_COMMON_EX_SAG: Final[frozenset[int]] = frozenset({3, 6, 12})  # dual signs minus Sagittarius
# Signs owned by a natural malefic (Sun, Mars, Saturn): Ar Le Sc Cp Aq (Raman's "malefic Rashi").
_MALEFIC_SIGNS: Final[frozenset[int]] = frozenset({1, 5, 8, 10, 11})


def _lord_of(house: int, chart: RamanChart) -> str:
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _fifth_sign(chart: RamanChart) -> int:
    return ((chart.asc_sign - 1) + 4) % 12 + 1


# ── local leaf predicates ─────────────────────────────────────────────────────

class _LagnaInSigns(C.Condition):
    def __init__(self, signs: frozenset[int]) -> None:
        self.signs = signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return ctx.chart.asc_sign in self.signs


class _FifthSignIn(C.Condition):
    def __init__(self, signs: frozenset[int]) -> None:
        self.signs = signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _fifth_sign(ctx.chart) in self.signs


class _PlanetInSigns(C.Condition):
    def __init__(self, planet: str, signs: frozenset[int]) -> None:
        self.planet, self.signs = planet, signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.sign in self.signs


class _ClassAspectsHouse(C.Condition):
    """Some natural planet of `klass` casts a whole-sign drishti on whole-sign `house`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name in group and drishti.aspects_house(name, self.house, ctx.chart)
                   for name in ctx.chart.planets)


class _AspectedByClass(C.Condition):
    def __init__(self, target: str, klass: str) -> None:
        self.target, self.klass = target, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        if self.target not in ctx.chart.planets:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != self.target and name in group
                   and drishti.aspects_planet(name, self.target, ctx.chart)
                   for name in ctx.chart.planets)


class _FifthFromMoonMaleficConvergence(C.Condition):
    """>= 2 distinct natural malefics occupy or cast whole-sign drishti on the 5th sign
    counted from the Moon (Chandra Lagna). Occupation and aspect count once per planet;
    the drishti module supplies the project convention (nodes 7th-only in raman_saab).
    H5.C.39's predicate — see the rule's comment block for the five citations, the >= 2
    vocabulary gradient, and the Victoria documented limit."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        moon = chart.planets.get("Moon")
        if moon is None:
            return False
        cl5_sign = ((moon.sign - 1 + 4) % 12) + 1
        cl5_house = ((cl5_sign - chart.asc_sign) % 12) + 1
        count = 0
        for name in ("Sun", "Mars", "Saturn", "Rahu", "Ketu"):
            p = chart.planets.get(name)
            if p is None:
                continue
            if p.sign == cl5_sign or drishti.aspects_house(name, cl5_house, chart):
                count += 1
        return count >= 2


class _PutraKarakaDoublyAfflicted(C.Condition):
    """>= 2 of the first-rate malefics {Mars, Saturn, Rahu, Ketu} contact the PutraKaraka
    Jupiter — conjunction (same sign) or whole-sign drishti (nodes 7th-only via the drishti
    module). H5.C.40's predicate; the Sun is deliberately excluded (see the rule's comment)."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        jup = chart.planets.get("Jupiter")
        if jup is None:
            return False
        count = 0
        for name in ("Mars", "Saturn", "Rahu", "Ketu"):
            p = chart.planets.get(name)
            if p is None:
                continue
            if p.sign == jup.sign or drishti.aspects_planet(name, "Jupiter", chart):
                count += 1
        return count >= 2


class _LordHemmedBy(C.Condition):
    """The lord of `house` is hemmed (2nd & 12th from it hold a planet of `klass`)."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.HemmedBy(_lord_of(self.house, ctx.chart), self.klass).evaluate(ctx)


class _LordConjunctClass(C.Condition):
    """The lord of `house` shares a house with a natural planet of `klass`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        p = ctx.chart.planets.get(lord)
        if p is None:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != lord and name in group and q.rasi_house == p.rasi_house
                   for name, q in ctx.chart.planets.items())


class _LordConjunctPlanet(C.Condition):
    """The lord of `house` shares a house with `planet` (identity → False)."""
    def __init__(self, house: int, planet: str) -> None:
        self.house, self.planet = house, planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        if lord == self.planet:
            return False
        return C.Conjunct(lord, self.planet).evaluate(ctx)


class _LordsMutualAspect(C.Condition):
    """The lords of houses `h1` and `h2` mutually aspect (identity → False)."""
    def __init__(self, h1: int, h2: int) -> None:
        self.h1, self.h2 = h1, h2

    def evaluate(self, ctx: C.EvalContext) -> bool:
        l1, l2 = _lord_of(self.h1, ctx.chart), _lord_of(self.h2, ctx.chart)
        return l1 != l2 and drishti.mutual_aspect(l1, l2, ctx.chart)


class _PlanetAspectsLord(C.Condition):
    """`planet` casts a whole-sign drishti on the lord of `house` (identity → False)."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        return lord != self.planet and drishti.aspects_planet(self.planet, lord, ctx.chart)


class _JupiterStrong5thLordAspectedByLagnaLord(C.Condition):
    """Jupiter IS the 5th lord (Scorpio/Leo lagna), B1-strong (band 'strong', not decisively
    weak), and the Lagna lord casts a whole-sign drishti on it (HTJAH-I:5185, rasi core)."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.primitives.effective_strength import effective_strength
        if _lord_of(5, ctx.chart) != "Jupiter" or "Jupiter" not in ctx.chart.planets:
            return False
        es = effective_strength("Jupiter", ctx.chart)
        if es.band != "strong" or es.decisively_weak:
            return False
        lagna_lord = _lord_of(1, ctx.chart)
        return (lagna_lord != "Jupiter"
                and drishti.aspects_planet(lagna_lord, "Jupiter", ctx.chart))


# ── RULES ─────────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ===== A. Birth / presence of children (HTJAH-I:5183-5190) — sig children =====
    RuleRecord(
        id="H5.C.1", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.Or(C.CountInHouse(5, 1, "benefic"), _ClassAspectsHouse(5, "benefic")),
        fortified="benefic associations or aspects on the 5th → there will be children",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5183)),
    RuleRecord(
        id="H5.C.2", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.Or(C.LordIn(1, 5), C.Parivartana(1, 5)),
        fortified="Lagna-lord in the 5th (with a strong 5th lord), or 1st-5th lord exchange → "
                  "favours birth of children",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5184)),
    RuleRecord(
        id="H5.C.4", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(2, 5), _PlanetAspectsLord("Jupiter", 2)),
        fortified="a strong 2nd lord in the 5th aspected by Jupiter → birth of children",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5186)),
    # C.3 — the "strength gate" TODO was stale (B1 effective_strength); the rasi core is
    #       encoded on it, the Navamsa-dispositor overlays stay deferred in the result text
    #       (the H9.B.29 encode-the-core precedent). Encoded 2026-08-23.
    RuleRecord(
        id="H5.C.3", house=5, signification="children", group="combination", kind="evaluable",
        condition=_JupiterStrong5thLordAspectedByLagnaLord(),
        fortified="Jupiter as a strong 5th lord aspected by the Lagna lord → many issues. "
                  "The source's following sentence ('Birth of children is ALSO indicated "
                  "when...' — 5th-lord-Navamsa-dispositor benefic / 5th lord in benefic amsa / "
                  "that dispositor in Lagna Bhava) lists three INDEPENDENT combinations, not "
                  "overlays on this rule — when encoded they belong as separate rule(s), never "
                  "as an And-gate here",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-I", 5185)),

    # ===== B. Death / early loss of children (HTJAH-I:5192-5211) — sig children =====
    RuleRecord(
        id="H5.C.8", house=5, signification="children", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="5th lord in the 3rd/6th/12th (aspected by no benefic) → children die early. "
                  "Kept descriptive: the lord-in-3/6/12 condition is already scored by the "
                  "lord_in_12 placements (H5.L.3/L.6/L.12) under the same `children` matter; "
                  "encoding it again would double-count. TODO(predicate: no-benefic-aspect gate "
                  "to distinguish the death reading)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5192)),
    RuleRecord(
        id="H5.C.9", house=5, signification="children", group="combination", kind="evaluable",
        condition=_LordHemmedBy(5, "malefic"),
        fortified=None,
        afflicted="5th lord hemmed between malefics (papakartari) → children die early",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5193)),
    RuleRecord(
        id="H5.C.10", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(_ClassAspectsHouse(5, "malefic"), _LordConjunctClass(5, "malefic")),
        fortified=None,
        afflicted="5th aspected by a malefic AND the 5th lord joining an evil planet → children "
                  "die early",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5193)),
    RuleRecord(
        id="H5.C.13", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Rahu", 5), C.Aspects("Mars", "Rahu")),
        fortified=None,
        afflicted="Rahu occupying the 5th aspected by Mars → children die early",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5199)),
    RuleRecord(
        id="H5.C.14", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 5), C.Aspects("Moon", "Saturn"),
                        _LordConjunctPlanet(5, "Rahu")),
        fortified=None,
        afflicted="Saturn (aspected by the Moon) in the 5th AND the 5th lord joining Rahu → "
                  "children die early",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5199)),
    # #15 — the un-numbered clause between C.14 and the extinction group, found 2026-08-29 by
    #       the per-chart error programme (the NH.chart_57 trail led back to this list and two
    #       of its clauses turned out never to have been encoded — the id sequence skips 15/16).
    #       "children will die early ... when Rahu and lord of Lagna are associated with the
    #       5th lord or occupy the 5th" (HTJAH-I:5200-5201). Two disjuncts as written: BOTH
    #       Rahu and the lagna lord joined to the 5th lord, OR both occupying the 5th itself.
    #       "Associated" is read as conjunction — the settled module idiom (H2.C.62 and H11.C.21
    #       encode Raman's identical "associated with <lord>" as LordsConjunct; the wider
    #       conjunction-OR-aspect reading is reserved for where he writes "aspect or association",
    #       cf. H1 _LordsInContact, and in THIS paragraph he says "aspected by" four times when he
    #       means aspect). The COLLECTIVE parse is deliberate: one compound subject governs both
    #       verbs, so a mixed configuration (Rahu with the 5th lord while the lagna lord sits in
    #       the 5th) is a documented floor, not covered — reviewer-confirmed 2026-08-29.
    RuleRecord(
        id="H5.C.15", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.Or(
            C.And(_LordConjunctPlanet(5, "Rahu"), C.LordsConjunct(1, 5)),
            C.And(C.InRashiHouse("Rahu", 5), C.LordIn(1, 5))),
        fortified=None,
        afflicted="Rahu and the Lagna lord associated with the 5th lord, or both occupying "
                  "the 5th → children die early",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5200)),
    # #16 — the first extinction clause, likewise never encoded: "The family is extinguished
    #       when the lord of Lagna is in the 5th, and Lagna and the Moon have evil
    #       associations" (HTJAH-I:5203-5204). Lagna's evil association is a malefic in the
    #       Lagna (C.17's reading of the same phrase one sentence later); the Moon's is a
    #       malefic sharing its rasi.
    RuleRecord(
        id="H5.C.16", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(1, 5), C.CountInHouse(1, 1, "malefic"),
                        C.Or(C.Conjunct("Moon", "Sun"), C.Conjunct("Moon", "Mars"),
                             C.Conjunct("Moon", "Saturn"), C.Conjunct("Moon", "Rahu"),
                             C.Conjunct("Moon", "Ketu"))),
        fortified=None,
        afflicted="Lagna lord in the 5th with Lagna and the Moon both under evil association "
                  "→ family extinguished",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5203)),
    RuleRecord(
        id="H5.C.25", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 5),
                        C.Or(C.Aspects("Jupiter", "Mars"), C.Aspects("Venus", "Mars"))),
        fortified=None,
        afflicted="Mars in the 5th aspected by Jupiter or Venus → the first child dies",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5210)),
    RuleRecord(
        id="H5.C.11", house=5, signification="children", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="5th lord in a cruel & debilitated Navamsa; the Drekkana/Navamsa-dispositor of "
                  "the 5th lord joined by the 12th lord aspecting the 5th lord → children die "
                  "early. TODO(predicate: Navamsa/Drekkana overlay). (The Rahu+Lagna-lord clause "
                  "formerly bundled here is HTJAH-I:5200's first disjunct and is evaluably owned "
                  "by H5.C.15 since 2026-08-29.)",
        frame="LAGNA", varga="D9", polarity="malefic", source=Citation("HTJAH-I", 5194)),

    # ===== C. Extinction of family / denial of issue (HTJAH-I:5203-5209) — children =====
    RuleRecord(
        id="H5.C.17", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mercury", 5), C.CountInHouse(1, 1, "malefic")),
        fortified=None,
        afflicted="the 5th occupied by Mercury AND the Lagna by a malefic → family extinguished",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5204)),
    RuleRecord(
        id="H5.C.18", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.CountInHouse(1, 1, "malefic"), C.CountInHouse(5, 1, "malefic"),
                        C.CountInHouse(8, 1, "malefic"), C.CountInHouse(12, 1, "malefic")),
        fortified=None,
        afflicted="malefics occupying the 1st, 5th, 8th and 12th → family extinguished",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5205)),
    RuleRecord(
        id="H5.C.19", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 1), C.InRashiHouse("Saturn", 8),
                        C.InRashiHouse("Sun", 5)),
        fortified=None,
        afflicted="Mars, Saturn and Sun occupying the 1st, 8th and 5th respectively → family "
                  "extinguished",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5206)),

    # ===== D. Sex of first child (HTJAH-I:5206-5220) — sig children (neutral) =====
    RuleRecord(
        id="H5.C.21", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.Or(C.LordIn(5, 1), C.LordIn(5, 2), C.LordIn(5, 3)),
        fortified="5th lord in the 1st, 2nd or 3rd → the first child will be male",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5206)),
    RuleRecord(
        id="H5.C.22", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(_PlanetInSigns("Mars", _COMMON_EX_SAG),
                        _PlanetInSigns("Venus", _COMMON_EX_SAG),
                        _PlanetInSigns("Moon", _COMMON_EX_SAG)),
        fortified="Mars, Venus and the Moon in common signs (Sagittarius excepted) → first child male",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5207)),
    RuleRecord(
        id="H5.C.24", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.CountInHouse(11, 1, "malefic"), C.InRashiHouse("Moon", 5),
                        C.InRashiHouse("Venus", 5)),
        fortified=None,
        afflicted="a malefic in the 11th AND Moon & Venus in the 5th → the first-born is a daughter",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5219)),

    # ===== E. Count / timing of children (HTJAH-I:5211-5222) — sig children =====
    RuleRecord(
        id="H5.C.26", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Jupiter", 5), _LordConjunctPlanet(5, "Venus")),
        fortified="Jupiter in the 5th AND the 5th lord with Venus → gets a child in the 32nd year",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5211)),
    RuleRecord(
        id="H5.C.28", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.Or(C.And(C.InRashiHouse("Sun", 5), _AspectedByClass("Sun", "benefic")),
                       C.And(_LagnaInSigns(frozenset({6})), C.InRashiHouse("Saturn", 5))),
        fortified="Sun (benefic-aspected) in the 5th, or Virgo Lagna with Saturn in the 5th → "
                  "three children",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5220)),
    RuleRecord(
        id="H5.C.29", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(_LagnaInSigns(frozenset({7})), C.InRashiHouse("Saturn", 5)),
        fortified="Libra Lagna with Saturn in the 5th → five children",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5222)),
    RuleRecord(
        id="H5.C.27", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(_LagnaInSigns(frozenset({1, 8})), C.InRashiHouse("Sun", 5),
                        C.InRashiHouse("Saturn", 8)),
        fortified="Aries/Scorpio Lagna + Sun in the 5th & Saturn in the 8th (benefic-influenced) "
                  "→ children late in life",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5216)),

    # ===== F. Adoption / "purchase" of a son (HTJAH-I:5218-5224) — children (neutral) =====
    RuleRecord(
        id="H5.C.30", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(_FifthSignIn(frozenset({3, 6, 10, 11})), C.InRashiHouse("Saturn", 5)),
        fortified=None,
        afflicted="the 5th in Gemini/Virgo/Capricorn/Aquarius with Saturn (or Mandi) → an "
                  "adopted son",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5218)),
    RuleRecord(
        id="H5.C.31", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 5), C.InRashiHouse("Mercury", 5),
                        C.InRashiHouse("Moon", 5)),
        fortified=None,
        afflicted="Saturn, Mercury and the Moon in the 5th → 'purchases' a son for the family's "
                  "continuance",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5223)),

    # ===== G. Obedience of child (HTJAH-I:5214-5223) — sig children =====
    RuleRecord(
        id="H5.C.32", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(5, 1), C.LordIn(1, 5)),
        fortified="the 5th lord in the Lagna AND the Lagna lord in the 5th → an obedient child",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5214)),
    RuleRecord(
        id="H5.C.34", house=5, signification="children", group="combination", kind="evaluable",
        condition=_LordsMutualAspect(1, 5),
        fortified="the lords of the 1st and 5th aspecting each other → the son is obedient to "
                  "the father",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5222)),

    # ===== H. Brain / intellect (HTJAH-I:5226-5272) — sig intellect =====
    RuleRecord(
        id="H5.C.35", house=5, signification="intellect", group="combination", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 5),
        fortified="Jupiter in the 5th → good intellect and memory",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5226)),
    RuleRecord(
        id="H5.C.36", house=5, signification="intellect", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Rahu", 5), C.InRashiHouse("Saturn", 5)),
        fortified=None,
        afflicted="Rahu and Saturn in the 5th → makes one dull and stupid",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5228)),
    RuleRecord(
        id="H5.C.37", house=5, signification="intellect", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="Saturn as the afflicting planet on the 5th → fear of brain derangement "
                  "(an affliction-grade modifier). TODO(predicate: affliction-grade gate)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5271)),
    # DECISIVE (children): the PutraKaraka Jupiter hemmed by papakartari (a malefic in BOTH the
    # 2nd- and 12th-from-Jupiter) AND occupying a malefic rashi (Sun/Mars/Saturn-owned) -> the
    # karaka of children is BLEMISHED -> progeny denied. HTJAH-I:5619-5620 verbatim
    # "Jupiter, the Karaka for children ... is subject to Papakarthari Yoga and occupies
    # a malefic Rashi, he is also blemished" (Chart 91/h5_01); the h5_07/Chart-97 leg at
    # HTJAH-I:5733/5746 "all three factors considerably afflicted, 5th house spoilt; no issue".
    # The H5 twin of the decisive karaka-papakartari rules H9.A.20a (Sun) / H7.C.84-85. The
    # malefic-rashi conjunct is LOAD-BEARING (Charts 93/95 have a papakartari'd Jupiter Raman does
    # NOT let drive the denial). NO neecha-bhanga guard: per the H3.C.40 organ-affliction split,
    # bhanga restores prosperity/status but NOT the papakartari blemish (h5_16's Jupiter has
    # neecha-bhanga yet Raman still reads child-loss). `children` is bidirectional (not
    # AFFLICTION_MATTER), so the decisive flag carries it past the favourable preponderance.
    # Fires on h5_01 + h5_07 across the H5/children goldens; spares the favourable twin h5_16.
    # bphs-doctrine-reviewer SOUND-WITH-CAVEAT (HIGH). h5_05/10/12 (no Jupiter papakartari) are a
    # distinct single-weak-sphuta mechanism, deferred.
    RuleRecord(
        id="H5.C.38", house=5, signification="children", group="combination", kind="evaluable",
        condition=C.And(C.HemmedBy("Jupiter", "malefic"),
                        _PlanetInSigns("Jupiter", _MALEFIC_SIGNS)),
        fortified=None,
        afflicted="the PutraKaraka Jupiter hemmed by papakartari and occupying a malefic rashi "
                  "→ the karaka of children is blemished; progeny is denied",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5619)),

    # #39 — CL-5th malefic convergence: >= 2 distinct natural malefics occupy or aspect the
    # 5th FROM CHANDRA LAGNA -> the children matter is blemished. STRONG TESTIMONY, deliberately
    # NOT decisive — the bphs-doctrine-reviewer's amendment (SHIP-WITH-AMENDMENTS, HIGH,
    # 2026-08-30): Victoria (NH:6764-6770) is a PRINTED counterexample where Raman sees the
    # three-malefic convergence and still rules "prolific motherhood" via a rescue stack he
    # never reduces to rule, and even in the condemned charts the CL testimony never stands
    # alone. FIVE explicit citations: Chart 101 HTJAH-I:5826-5829 ("occupied by the malefic
    # Saturn and aspected by another malefic Mars ... strongly blemished"), Chart 98
    # HTJAH-I:5750-5752, Chart 108 HTJAH-I:5956-5958 ("Saturn—Ketu association is a clear case
    # of the spoiling of the 5th house"), Goethe NH:5494-5497 ("completely spoiled when viewed
    # from Chandra Lagna"), Wadiyar IV NH:11061-11064 (Raman's second influence there is MANDI,
    # which this predicate does not model — the engine's second is Saturn's aspect; recorded).
    # The >= 2 bar is his own vocabulary gradient: one malefic aspect alone rates only
    # "nominally or feebly strong" (Chart 100, HTJAH-I:5804-5806); two or more rate "strongly
    # blemished" / "clear case of the spoiling" / "completely spoiled". Defeasibility clause
    # HTJAH-I:5876-5878 ("in the absence of any relief from beneficial sources") — the
    # benefic-relief guard FAILED enumeration (Jupiter aspects the CL 5th in condemned Charts
    # 101/Shaw exactly as in Victoria), so there is NO encodable guard and Victoria stays a
    # documented limit. NO Moon-strength gate: HTJAH-I:7094's "in this case as he is strong"
    # is a per-chart weighting remark, and the gate would rescue nothing in the fire set.
    # Fires (7th-only node drishti) on 8 afflicted + 2 mixed (h5_13/h5_14, already
    # engine-afflicted) + Victoria across the 35 H5-children goldens.
    RuleRecord(
        id="H5.C.39", house=5, signification="children", group="combination", kind="evaluable",
        condition=_FifthFromMoonMaleficConvergence(),
        fortified=None,
        afflicted="two or more natural malefics occupy or aspect the 5th from Chandra Lagna "
                  "→ the house of children is strongly blemished from the Moon",
        frame="CHANDRA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5826)),

    # #40 — the PutraKaraka under the COMBINED influence of two first-rate malefics -> sorrow
    # through children. Chart 99 verbatim (HTJAH-I:5795-5799): "as PutraKaraka has the combined
    # influences of two first-rate malefic, Mars ... and Saturn, the Karaka for sorrow ...
    # the native has to experience sorrow on account of the 5th house" — pronounced even though
    # "the disposition of 5th house and the 5th lord indicates the birth of children" and the
    # PK sits in his OWN sign (dignity does not relieve contact-affliction; the same lesson as
    # H9.A.20a's dropped exalted-Sun guard). Second strong citation: Chart 95 HTJAH-I:5701-5713
    # ("his association with Rahu and the combined aspects of Mars and Saturn ... rendered him
    # highly malefic ... no issues born"). Corroborated by Shaw NH:7320-7323 ("Putrakaraka
    # being associated with Rahu" — and per NH:7302-7303 Saturn also aspects it, a genuine
    # two-contact chart), Marie Antoinette NH:5834-5836 (PK "further afflicted by Rahu"), Bose
    # NH:14001-14003 (PK "plus the influence of Mars and Saturn").
    # CONTACT SET = {Mars, Saturn, Rahu, Ketu}. The Sun's exclusion is an EMPIRICAL DOCUMENTED
    # LIMIT of the printed PK-contact corpus (no PK condemnation ever names the Sun as the
    # contact), NOT Raman's vocabulary — his "first-rate malefic" idiom explicitly includes
    # the Sun elsewhere (HTJAH-I:5673 "three first-rate malefic, viz., the Sun, Saturn and
    # Rahu"; NH:10543; NH:18035). Reviewer-corrected reading, 2026-08-30.
    # NON-decisive testimony, same status and reasoning as C.39: Chart 99's own house/lord
    # "indicate birth", so the PK blemish grades the outcome rather than overriding everything;
    # the Dhana-Yoga chart (chart_67, NH:13766-13774) keeps a double-contact PK chart "fairly
    # well disposed" with only an abortion warning — decisive would misread it. chart_67's fire
    # is directionally faithful but a MECHANISM MISMATCH (Raman's stated driver there is the
    # 5th-lord Mars aspected by Saturn, never the PK) — not a validation chart.
    # Distinct from C.38 (papakartari + malefic rashi — a HEMMING predicate); this is CONTACT
    # (conjunction / whole-sign drishti, nodes 7th-only per the raman_saab lock); fire sets are
    # disjoint in the goldens, and Chart 97 (HTJAH-I:5733-5747) counts hemming and focussed
    # evil as SEPARATE blemishes on the same Jupiter, so stacking would be faithful anyway.
    # Fires on 9 afflicted + 1 mixed (chart_67) + 0 favourable across the 35 H5-children
    # goldens — the h5_15/chart_74 favourable twins carry exactly ONE first-rate contact and
    # are spared by the >= 2 bar; Raman's own gradient: one contact = "moderately blemished"
    # (Chart 92 :5641-5644) / "feebly weak" (Chart 98 :5760-5762), two = sorrow, three =
    # "most baneful" (Chart 95). No printed chart condemns on a single PK contact alone.
    RuleRecord(
        id="H5.C.40", house=5, signification="children", group="combination", kind="evaluable",
        condition=_PutraKarakaDoublyAfflicted(),
        fortified=None,
        afflicted="the PutraKaraka Jupiter carries the combined influences of two or more "
                  "first-rate malefics → sorrow on account of the house of children",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5791)),
)
