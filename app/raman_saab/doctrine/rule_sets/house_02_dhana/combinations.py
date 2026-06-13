"""House 2 (Dhana — wealth) — "Important Combinations".

Encodes the 68 rule-atoms of the "Important Combinations" table in
``docs/raman_saab/methodology/house_02_dhana.md`` (HTJAH-I:2436–3318).

Encoding policy (honest, atom by atom):

* Existing condition-algebra predicates compose directly. Where the text
  specifies a D9/navamsa refinement, the rasi-core fires and the varga
  refinement is kept in the result text (same convention as H3).
* Rules requiring predicates not yet in the algebra (NavamsaDispositor,
  SignModality, ArudhaLagna, YogaDetection, Maraka-planet detection) are
  ``kind="descriptive"`` with a ``TODO(predicate)`` note.
* The "Source-of-Gain" list (#67) overlaps lord-in-12 rules and is encoded
  as descriptive to avoid double-counting.
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


def _second_lord(chart: RamanChart) -> str:
    return _lord_of(2, chart)


# ── local leaf predicates (conditions.py intentionally untouched) ─────────────

class _SecondLordConjunct(C.Condition):
    """The 2nd lord shares a whole-sign house with `planet`.  Identity → False."""
    def __init__(self, planet: str) -> None:
        self.planet = planet
    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _second_lord(ctx.chart)
        if lord == self.planet:
            return False
        return C.Conjunct(lord, self.planet).evaluate(ctx)


class _SecondLordHasDignity(C.Condition):
    """The 2nd lord's D1 compound dignity is one of `states`."""
    def __init__(self, states: set[str]) -> None:
        self.states = states
    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.HasDignity(_second_lord(ctx.chart), self.states).evaluate(ctx)


class _SecondLordIs(C.Condition):
    """The 2nd lord IS a specific planet (Lagna-dependent identity)."""
    def __init__(self, planet: str) -> None:
        self.planet = planet
    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _second_lord(ctx.chart) == self.planet


class _SecondLordAspectedByMalefic(C.Condition):
    """Any natural malefic casts whole-sign drishti on the 2nd lord."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _second_lord(ctx.chart)
        for name in NATURAL_MALEFICS:
            if name == lord or ctx.chart.planets.get(name) is None:
                continue
            if drishti.aspects_planet(name, lord, ctx.chart):
                return True
        return False


class _NotAspectedByMalefic(C.Condition):
    """No natural malefic casts whole-sign drishti on `planet`."""
    def __init__(self, planet: str) -> None:
        self.planet = planet
    def evaluate(self, ctx: C.EvalContext) -> bool:
        for name in NATURAL_MALEFICS:
            if name == self.planet or ctx.chart.planets.get(name) is None:
                continue
            if drishti.aspects_planet(name, self.planet, ctx.chart):
                return False
        return True


class _SecondLordNeechaBhanga(C.Condition):
    """The 2nd lord has NeechaBhanga (cancellation of debilitation)."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.NeechaBhanga(_second_lord(ctx.chart)).evaluate(ctx)


class _PlanetAspectsHouse(C.Condition):
    """A specific planet casts whole-sign drishti on house `house`."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house
    def evaluate(self, ctx: C.EvalContext) -> bool:
        return drishti.aspects_house(self.planet, self.house, ctx.chart)


class _LordAspectsHouse(C.Condition):
    """The lord of whole-sign house `lord_house` aspects house `target_house`."""
    def __init__(self, lord_house: int, target_house: int) -> None:
        self.lord_house, self.target_house = lord_house, target_house
    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.lord_house, ctx.chart)
        return drishti.aspects_house(lord, self.target_house, ctx.chart)


# ── dasha-result factory ─────────────────────────────────────────────────────

def _lord_with_lord_in(rule_id: str, other_h: int, fortified: str | None,
                       afflicted: str | None, line: int,
                       sig: str = "wealth", pol: str = "neutral") -> RuleRecord:
    """2nd lord with Nth-house lord in the Nth house (dasha-result family)."""
    return RuleRecord(
        id=rule_id, house=2, signification=sig, group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(2, other_h), C.LordIn(other_h, other_h)),
        fortified=fortified, afflicted=afflicted, frame="LAGNA", varga="D1",
        polarity=pol, source=Citation("HTJAH-I", line))


# ═══════════════════════════════════════════════════════════════════════════════
RULES: Final[tuple[RuleRecord, ...]] = (
    # ── A. OTHER IMPORTANT COMBINATIONS (HTJAH-I:2436–2512) ──────────────────

    # #1 — 2nd lord in 2nd with/aspected by evil planets → poor.
    RuleRecord(
        id="H2.C.1", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(2, 2),
                        C.Or(C.CountInHouse(2, 1, "malefic"),
                             _SecondLordAspectedByMalefic())),
        fortified=None,
        afflicted="2nd lord in 2nd with evil planets or aspected by them → poor",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2436)),

    # #2 — Saturn in 2nd aspected by Venus → ordinary wealth.
    RuleRecord(
        id="H2.C.2", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 2),
                        C.Aspects("Venus", "Saturn")),
        fortified="Saturn in 2nd aspected by Venus → ordinary wealth",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 2437)),

    # #3 — Moon+Mars in 2nd, Saturn aspecting → peculiar skin disease.
    RuleRecord(
        id="H2.C.3", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 2), C.InRashiHouse("Mars", 2),
                        _PlanetAspectsHouse("Saturn", 2)),
        fortified=None,
        afflicted="Moon and Mars in 2nd with Saturn aspecting → peculiar skin disease",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2437)),

    # #4 — Mercury in 2nd with evil planet, aspected by Moon → bad for saving.
    RuleRecord(
        id="H2.C.4", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Mercury", 2),
                        C.CountInHouse(2, 1, "malefic"),
                        C.Aspects("Moon", "Mercury")),
        fortified=None,
        afflicted="Mercury in 2nd with another evil planet, aspected by Moon → bad "
                  "for saving; even ancestral wealth wasted on extravagance",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2439)),

    # #5 — Sun in 2nd un-aspected by Saturn → steady fortune.
    RuleRecord(
        id="H2.C.5", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 2),
                        C.Not(C.Aspects("Saturn", "Sun"))),
        fortified="Sun in 2nd un-aspected by Saturn → favourable for steady fortune",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2440)),

    # #6 — 2nd lord is Jupiter OR Jupiter in 2nd un-aspected by malefic → much wealth.
    RuleRecord(
        id="H2.C.6", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.Or(_SecondLordIs("Jupiter"),
                       C.And(C.InRashiHouse("Jupiter", 2),
                             _NotAspectedByMalefic("Jupiter"),
                             C.Not(C.FunctionalNature("Jupiter", {"malefic"})))),
        fortified="2nd lord is Jupiter, or Jupiter in 2nd un-aspected by malefic → "
                  "much wealth",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2444)),

    # #7 — Mercury (aspected by Moon) in 2nd with Jupiter → loses wealth.
    RuleRecord(
        id="H2.C.7", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Mercury", 2),
                        C.InRashiHouse("Jupiter", 2),
                        C.Aspects("Moon", "Mercury")),
        fortified=None,
        afflicted="Mercury aspected by Moon contacts Jupiter in 2nd → loses wealth "
                  "(modifier of #6)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2445)),

    # #8 — Moon in 2nd aspected by Mercury → earns by self-exertion.
    RuleRecord(
        id="H2.C.8", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 2),
                        C.Aspects("Mercury", "Moon")),
        fortified="Moon in 2nd aspected by Mercury → earns by self-exertion",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 2446)),

    # #9 — Lords of 2nd & 11th interchange → pretty rich. Only the Parivartana
    #      path encoded; the "both in kendras with Mercury/Jupiter" alternative
    #      needs LordInHouseClass predicate → noted in result text.
    RuleRecord(
        id="H2.C.9", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.Parivartana(2, 11),
        fortified="lords of 2nd & 11th interchange → pretty rich (also if both in "
                  "kendras with Mercury/Jupiter aspect/conjunction — not yet encoded)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2447)),

    # #10 — Lords of 2nd & 3rd in the 6th with/aspected by evil → poor.
    RuleRecord(
        id="H2.C.10", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(2, 6), C.LordIn(3, 6)),
        fortified=None,
        afflicted="lords of 2nd and 3rd in the 6th, with or aspected by evil planets "
                  "→ poor",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2449)),

    # #11 — DESCRIPTIVE: lords of 2nd & 11th separate without evil → indigent.
    #       TODO(predicate): negative lord-separation + absence-of-malefic check.
    RuleRecord(
        id="H2.C.11", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="lords of 2nd & 11th remain separate, without evil "
                  "planets/aspects → always indigent",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2450)),

    # #12 — Jupiter in 11th, Venus in 2nd, 2nd lord with benefics → moral spending.
    RuleRecord(
        id="H2.C.12", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Jupiter", 11),
                        C.InRashiHouse("Venus", 2)),
        fortified="Jupiter in 11th, Venus in 2nd, 2nd lord with benefics → money "
                  "spent on moral purposes",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2451)),

    # #13 — DESCRIPTIVE: 2nd lord with good planets in kendra, or 2nd house all
    #       benefic → good terms with relatives.
    #       TODO(predicate): LordInHouseClass(2, "kendra") + benefic conjunction.
    RuleRecord(
        id="H2.C.13", house=2, signification="family", group="combination",
        kind="descriptive", condition=None,
        fortified="2nd lord with good planets in a kendra, or 2nd house has all good "
                  "association/aspects → good terms with relatives",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2452)),

    # #14 — Mars in 2nd with Moon or aspected by Mercury → good mathematician.
    RuleRecord(
        id="H2.C.14", house=2, signification="speech", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 2),
                        C.Or(C.InRashiHouse("Moon", 2),
                             C.Aspects("Mercury", "Mars"))),
        fortified="Mars in 2nd with Moon, or aspected by Mercury → good mathematician",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2456)),

    # #15 — DESCRIPTIVE: Jupiter in asc + Saturn in 8th; or Jupiter in quadrant +
    #       Lagna-lord/Mercury exalted → good mathematician.
    #       TODO(predicate): LagnaLordHasDignity + multi-path.
    RuleRecord(
        id="H2.C.15", house=2, signification="speech", group="combination",
        kind="descriptive", condition=None,
        fortified="Jupiter in ascendant + Saturn in 8th; or Jupiter in quadrant + "
                  "Lagna-lord/Mercury exalted → good mathematician",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2457)),

    # #16 — Sun or Moon aspected by Jupiter or Venus → able debater.
    RuleRecord(
        id="H2.C.16", house=2, signification="speech", group="combination",
        kind="evaluable",
        condition=C.Or(C.Aspects("Jupiter", "Sun"), C.Aspects("Venus", "Sun"),
                       C.Aspects("Jupiter", "Moon"), C.Aspects("Venus", "Moon")),
        fortified="Sun or Moon aspected by Jupiter or Venus → able debater",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2458)),

    # #17 — 2nd lord with Venus → the eye suffers.
    RuleRecord(
        id="H2.C.17", house=2, signification="vision", group="combination",
        kind="evaluable",
        condition=_SecondLordConjunct("Venus"),
        fortified=None,
        afflicted="2nd lord with Venus → the eye suffers",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2461)),

    # #18 — Sun & Moon in 2nd → night-blind.
    RuleRecord(
        id="H2.C.18", house=2, signification="vision", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 2), C.InRashiHouse("Moon", 2)),
        fortified=None,
        afflicted="Sun and Moon both in the 2nd → night-blind",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2461)),

    # #19 — Lords 2nd & 11th in 6/8/12, Mars in 11th, Rahu in 2nd → penalty.
    RuleRecord(
        id="H2.C.19", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(
            C.Or(C.LordIn(2, 6), C.LordIn(2, 8), C.LordIn(2, 12)),
            C.Or(C.LordIn(11, 6), C.LordIn(11, 8), C.LordIn(11, 12)),
            C.InRashiHouse("Mars", 11), C.InRashiHouse("Rahu", 2)),
        fortified=None,
        afflicted="lords of 2nd & 11th in 6/8/12, Mars in 11th, Rahu in 2nd → "
                  "penalty, false charges",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2462)),

    # #20 — 2nd lord in 6/8/12 → eye disease.
    RuleRecord(
        id="H2.C.20", house=2, signification="vision", group="combination",
        kind="evaluable",
        condition=C.Or(C.LordIn(2, 6), C.LordIn(2, 8), C.LordIn(2, 12)),
        fortified=None,
        afflicted="2nd lord in 6th, 8th or 12th → eye disease",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2464)),

    # #21 — 2nd lord strong → good eye-sight.
    RuleRecord(
        id="H2.C.21", house=2, signification="vision", group="combination",
        kind="evaluable",
        condition=_SecondLordHasDignity({"exalt", "own", "moolatrikona"}),
        fortified="2nd lord strong → good eye-sight",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2464)),

    # #22 — 2nd lord joins Saturn, Mars or Gulika → injured eye.
    #       Gulika not modelled → noted in result text.
    RuleRecord(
        id="H2.C.22", house=2, signification="vision", group="combination",
        kind="evaluable",
        condition=C.Or(_SecondLordConjunct("Saturn"),
                       _SecondLordConjunct("Mars")),
        fortified=None,
        afflicted="2nd lord joins Saturn, Mars or Gulika → injured eye (Gulika "
                  "not yet modelled)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2465)),

    # #23 — Saturn in 2nd → unfavourable for eye-sight.
    RuleRecord(
        id="H2.C.23", house=2, signification="vision", group="combination",
        kind="evaluable",
        condition=C.InRashiHouse("Saturn", 2),
        fortified=None,
        afflicted="Saturn in 2nd → unfavourable for eye-sight",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2466)),

    # #24 — 2nd lord in very weak position → helpless, wretched.
    #        Exempt if NeechaBhanga cancels the debilitation.
    RuleRecord(
        id="H2.C.24", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(_SecondLordHasDignity({"debil"}),
                        C.Not(_SecondLordNeechaBhanga())),
        fortified=None,
        afflicted="2nd lord in a very weak position (debilitated, no cancellation) → "
                  "helpless, wretched existence",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2466)),

    # #25 — 2nd lord debilitated, or in 2nd/8th with evil → stammers or dumb.
    #        Debilitation branch exempt if NeechaBhanga cancels it.
    RuleRecord(
        id="H2.C.25", house=2, signification="speech", group="combination",
        kind="evaluable",
        condition=C.Or(
            C.And(_SecondLordHasDignity({"debil"}),
                  C.Not(_SecondLordNeechaBhanga())),
            C.And(C.LordIn(2, 2), C.CountInHouse(2, 1, "malefic")),
            C.And(C.LordIn(2, 8), C.CountInHouse(8, 1, "malefic"))),
        fortified=None,
        afflicted="2nd lord debilitated, or in 2nd/8th with evil planets → "
                  "stammers or dumb",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2469)),

    # #26 — 12th lord in 2nd or 2nd lord in 12th → loses wealth under penalty.
    RuleRecord(
        id="H2.C.26", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.Or(C.LordIn(12, 2), C.LordIn(2, 12)),
        fortified=None,
        afflicted="12th lord in 2nd, or 2nd lord in 12th → loses wealth under penalty",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2472)),

    # #27 — 2nd lord in 8th with malefic → losses via govt fines.
    #       "In debility + Sun combining" refinement → result text.
    RuleRecord(
        id="H2.C.27", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(2, 8), C.CountInHouse(8, 1, "malefic")),
        fortified=None,
        afflicted="2nd lord in 8th with malefic (in debility + Sun combining) → "
                  "losses via government executions and fines",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2472)),

    # #28 — Lords of 2nd & 12th in the 2-12 axis → loses money offending authorities.
    #       "Aspected by Lagna-lord" refinement → result text.
    RuleRecord(
        id="H2.C.28", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.Or(C.LordIn(2, 2), C.LordIn(2, 12)),
                        C.Or(C.LordIn(12, 2), C.LordIn(12, 12))),
        fortified=None,
        afflicted="lords of 2nd and 12th remain in 2nd/12th, aspected by Lagna-lord "
                  "→ loses money offending authorities",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2474)),

    # #29 — Evil planets in 2nd, Lagna-lord in 12th → always in debt.
    #       "Aspected/joined by 10th or 11th lord" refinement → result text.
    RuleRecord(
        id="H2.C.29", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.CountInHouse(2, 1, "malefic"), C.LordIn(1, 12)),
        fortified=None,
        afflicted="evil planets in 2nd, Lagna-lord in 12th (aspected/joined by "
                  "10th or 11th lord) → always in debt",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2475)),

    # #30 — Jupiter/Venus/Mercury in 2nd, elevated → supports many men.
    RuleRecord(
        id="H2.C.30", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.Or(
            C.And(C.InRashiHouse("Jupiter", 2),
                  C.HasDignity("Jupiter", {"exalt", "own"})),
            C.And(C.InRashiHouse("Venus", 2),
                  C.HasDignity("Venus", {"exalt", "own"})),
            C.And(C.InRashiHouse("Mercury", 2),
                  C.HasDignity("Mercury", {"exalt", "own"}))),
        fortified="Jupiter, Venus or Mercury in 2nd elevated → supports many men",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2477)),

    # #31 — DESCRIPTIVE: 2nd lord elevated in kendra + strong Lagna-lord +
    #       dispositor in kendra → princely fortune.
    #       TODO(predicate): Dispositor + LordElevatedInKendra + LagnaLordStrong.
    RuleRecord(
        id="H2.C.31", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="2nd lord elevated in a kendra + strong Lagna-lord + dispositor of "
                  "2nd lord in a kendra → princely fortune",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2478)),

    # #32 — Lagna-lord in 2nd + 2nd lord in 11th, OR 11th lord in Lagna → great wealth.
    RuleRecord(
        id="H2.C.32", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.Or(C.And(C.LordIn(1, 2), C.LordIn(2, 11)),
                       C.LordIn(11, 1)),
        fortified="Lagna-lord in 2nd with 2nd lord in 11th, or 11th lord in "
                  "Lagna → great wealth",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2480)),

    # #33 — DESCRIPTIVE: navamsa-keyed dispositor check → rich in youth.
    #       TODO(predicate): NavamsaDispositor.
    RuleRecord(
        id="H2.C.33", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="2nd lord with 10th lord, aspected by navamsa-lord of Lagna-lord "
                  "→ rich in youth",
        afflicted=None,
        frame="LAGNA+D9", varga="D9", polarity="benefic",
        source=Citation("HTJAH-I", 2483)),

    # #34 — DESCRIPTIVE: 2nd lord in 10th aspected by Lagna-lord or navamsa Lagna-lord.
    #       TODO(predicate): NavamsaDispositor.
    RuleRecord(
        id="H2.C.34", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="2nd lord in 10th aspected by Lagna-lord or navamsa Lagna-lord "
                  "→ earns well in youth",
        afflicted=None,
        frame="LAGNA+D9", varga="D9", polarity="benefic",
        source=Citation("HTJAH-I", 2487)),

    # #35 — DESCRIPTIVE: 2nd & 11th lords with Lagna-lord in kendra having Kalabala.
    #       TODO(predicate): Kalabala (temporal strength).
    RuleRecord(
        id="H2.C.35", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="2nd & 11th lords associate with Lagna-lord in a kendra having "
                  "Kalabala → earns in middle life",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2489)),

    # #36 — DESCRIPTIVE: 3rd is common sign, lord there aspected by benefics.
    #       TODO(predicate): SignModality.
    RuleRecord(
        id="H2.C.36", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="3rd is a common sign, its lord there aspected by benefics → "
                  "wealth 'by thousands' in that planet's Dasha",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2492)),

    # #37 — DESCRIPTIVE: same but fixed sign → hundreds.
    RuleRecord(
        id="H2.C.37", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="same combination in a fixed sign → earnings 'by hundreds'",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2495)),

    # #38 — DESCRIPTIVE: same but movable sign → within two hundred.
    RuleRecord(
        id="H2.C.38", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="same combination in a movable sign → earns within two hundred",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2496)),

    # #39 — DESCRIPTIVE: Saturn/Mars debilitated in 11th from Arudha Lagna.
    #       TODO(predicate): ArudhaLagna.
    RuleRecord(
        id="H2.C.39", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="Saturn or Mars debilitated in 11th from Arudha Lagna → good earnings",
        afflicted=None,
        frame="ARUDHA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2497)),

    # #40 — DESCRIPTIVE: Arudha Lagna in 11/4/5/7 from Lagna → becomes rich.
    #       TODO(predicate): ArudhaLagna.
    RuleRecord(
        id="H2.C.40", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="Arudha Lagna in 11th, 4th, 5th or 7th from Lagna → becomes rich",
        afflicted=None,
        frame="ARUDHA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2498)),

    # ── B. POVERTY BLOCK (HTJAH-I:2526–2536) ─────────────────────────────────

    # #41 — DESCRIPTIVE: Lagna-lord in 12th with/aspected by Maraka → extreme poverty.
    #       TODO(predicate): MarakaDetection.
    RuleRecord(
        id="H2.C.41", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="Lagna-lord in 12th with/aspected by a Maraka planet → "
                  "extreme poverty",
        frame="LAGNA+MARAKA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2526)),

    # #42 — DESCRIPTIVE: exchange of 1st & 6th lords + Maraka involvement.
    #       TODO(predicate): MarakaDetection.
    RuleRecord(
        id="H2.C.42", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="exchange of 1st & 6th lords, either with/aspected by a Maraka "
                  "→ extreme poverty",
        frame="LAGNA+MARAKA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2527)),

    # #43 — DESCRIPTIVE: malefics (not 9/10 lords) in asc + Maraka → extremely poor.
    #       TODO(predicate): MarakaDetection + FunctionalNatureFilter.
    RuleRecord(
        id="H2.C.43", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="malefics (not owning 9th/10th) in ascendant with/aspected by "
                  "Maraka → extremely poor",
        frame="LAGNA+MARAKA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2528)),

    # #44 — Saturn in Lagna hemmed between malefics → fortune destroyed.
    RuleRecord(
        id="H2.C.44", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 1),
                        C.HemmedBy("Saturn", "malefic")),
        fortified=None,
        afflicted="Saturn in Lagna hemmed between malefics → fortune destroyed "
                  "(Jupiter's aspect/association counteracts)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2532)),

    # #45 — DESCRIPTIVE: movable-sign Lagna with Saturn/Ketu hemmed by malefics.
    #       TODO(predicate): SignModality.
    RuleRecord(
        id="H2.C.45", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="movable-sign Lagna with Saturn or Ketu, hemmed between malefics "
                  "→ poverty and deformed body",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2533)),

    # #46 — DESCRIPTIVE: 6/8/12 from Lagna becomes Arudha → poverty.
    #       TODO(predicate): ArudhaLagna.
    RuleRecord(
        id="H2.C.46", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="6th, 8th or 12th from Lagna becomes Arudha → suffers poverty",
        frame="ARUDHA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2535)),

    # ── C. DASHA-RESULT BLOCK (HTJAH-I:2637–2701) ────────────────────────────
    # Core = "2nd lord with Nth lord in Nth house." Navamsa modifier → result text.

    # #47 — 2nd lord well-fortified in 2nd → famous & wealthy.
    RuleRecord(
        id="H2.C.47", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(2, 2),
                        _SecondLordHasDignity({"exalt", "own", "moolatrikona"})),
        fortified="2nd lord well-fortified in 2nd → famous and wealthy (fame-no-wealth "
                  "if 2nd lord in 6/8/12 in navamsa; nil if Lagna-lord weak)",
        afflicted=None,
        frame="LAGNA+D9", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2637)),

    # #48 — 2nd lord with 3rd lord in 3rd.
    _lord_with_lord_in(
        "H2.C.48", 3,
        "prosperity; younger brothers help; fame & money if musician (opposite if "
        "2nd lord in 6/8/12 from 5th lord in navamsa)", None, 2642, pol="benefic"),

    # #49 — 2nd lord with 4th lord in 4th.
    _lord_with_lord_in(
        "H2.C.49", 4,
        "lands, cars, houses via literary/intellectual work; unexpected wealth "
        "(mining, lotteries); inheritance from mother/maternal grandfather", None,
        2648, pol="benefic"),

    # #50 — Venus as 2nd lord + Rahu, OR Mars as 2nd lord + Saturn → spouse astray.
    RuleRecord(
        id="H2.C.50", house=2, signification="family", group="combination",
        kind="evaluable",
        condition=C.Or(
            C.And(_SecondLordIs("Venus"), _SecondLordConjunct("Rahu")),
            C.And(_SecondLordIs("Mars"), _SecondLordConjunct("Saturn"))),
        fortified=None,
        afflicted="Venus as 2nd lord joined by Rahu, or Mars as 2nd lord joined by "
                  "Saturn → in its Dasha/Bhukti the wife (or husband) goes astray",
        frame="KARAKA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2652)),

    # #51 — 2nd lord with 5th lord in 5th.
    _lord_with_lord_in(
        "H2.C.51", 5,
        "children prosper & help financially; profitable intellectual pursuits",
        None, 2654, pol="benefic"),

    # #52 — 2nd lord with 6th lord in 6th.
    _lord_with_lord_in(
        "H2.C.52", 6, None,
        "maternal uncles prosper; native incurs enmity of moneyed people; if "
        "strong, wealth as physician; +Mars → stolen property/litigation earnings",
        2658, pol="neutral"),

    # #53 — 2nd lord with 7th lord in 7th.
    _lord_with_lord_in(
        "H2.C.53", 7,
        "good dowry/property from father-in-law; wealth only with other Dhana Yogas",
        "if 7th lord has maraka power → death of native or wife in this Dasha",
        2663, sig="family", pol="neutral"),

    # #54 — 2nd lord with 8th lord in 8th.
    _lord_with_lord_in(
        "H2.C.54", 8, None,
        "huge unpayable debts; danger of wife's death/disrepute; sorrow (worse "
        "if 2nd lord in 6/8/12 from 8th lord in navamsa)",
        2671, pol="malefic"),

    # #55 — 2nd lord with 9th lord in 9th.
    _lord_with_lord_in(
        "H2.C.55", 9,
        "immense wealth; father fortunate; earns righteously; friendship of "
        "learned men", None, 2677, pol="benefic"),

    # #56 — 2nd lord with 10th lord in 10th (+Raja-Yoga → result text).
    _lord_with_lord_in(
        "H2.C.56", 10,
        "high political/administrative office in this Dasha (malefics → abuse of "
        "office; businessman → huge profits); requires Lagna-lord in Raja-Yoga",
        None, 2681, pol="benefic"),

    # #57 — 2nd lord with 11th lord in 11th.
    _lord_with_lord_in(
        "H2.C.57", 11,
        "huge gains per 11th-lord karaka; happy relations with elder brother "
        "(malefic navamsa → reversals/losses)", None, 2688, pol="benefic"),

    # #58 — 2nd lord with 12th lord in 12th.
    _lord_with_lord_in(
        "H2.C.58", 12, None,
        "huge losses per 12th-lord karaka (small if both weak); domestic affairs "
        "sour", 2692, pol="malefic"),

    # #59 — 2nd lord in Lagna with Lagna-lord.
    RuleRecord(
        id="H2.C.59", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(2, 1), C.LordIn(1, 1)),
        fortified="2nd lord in Lagna with Lagna-lord → begets children, famous, "
                  "rich, charitable (meagre if 2nd lord weak)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2699)),

    # ── D. PERIOD-SELECTION BLOCK (HTJAH-I:2709–2716) ────────────────────────

    # #60 — Lords of 2nd & 5th, or 2nd & 11th, mutually exchanged → financial prosperity.
    RuleRecord(
        id="H2.C.60", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.Or(C.Parivartana(2, 5), C.Parivartana(2, 11)),
        fortified="lords of 2nd & 5th, or 2nd & 11th, mutually exchanged → "
                  "financial prosperity in their periods/sub-periods",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2709)),

    # #61 — Lords of 5th & 9th in 5th & 9th respectively → financial prosperity.
    RuleRecord(
        id="H2.C.61", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(5, 5), C.LordIn(9, 9)),
        fortified="lords of 5th & 9th in 5th & 9th respectively → financial "
                  "prosperity",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2710)),

    # #62 — 2nd lord associated with 12th lord → prosperity ordinary.
    RuleRecord(
        id="H2.C.62", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.LordsConjunct(2, 12),
        fortified=None,
        afflicted="2nd lord associated with 12th lord → prosperity in 2nd-lord "
                  "Dasha will be ordinary",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2710)),

    # #63 — Lords of Lagna, 4th & 9th in the 8th → financial losses.
    RuleRecord(
        id="H2.C.63", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 8), C.LordIn(4, 8), C.LordIn(9, 8)),
        fortified=None,
        afflicted="lords of Lagna, 4th and 9th in the 8th → financial losses in "
                  "their Dasha/Bhukti",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2714)),

    # #64 — 5th lord in 8th or vice-versa → financial losses.
    RuleRecord(
        id="H2.C.64", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.Or(C.LordIn(5, 8), C.LordIn(8, 5)),
        fortified=None,
        afflicted="5th lord in 8th or 8th lord in 5th → both lords give financial "
                  "losses",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2715)),

    # ── E. YOGA BLOCK (HTJAH-I:2879–2956) ────────────────────────────────────

    # #65 — Chandramangala Yoga (Moon+Mars conjunct/mutual aspect).
    #       Core condition evaluable; sign-dignity refinement in result text.
    RuleRecord(
        id="H2.C.65", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.Or(C.Conjunct("Moon", "Mars"), C.MutualAspect("Moon", "Mars")),
        fortified="Chandramangala Yoga (Moon+Mars conjunct/mutual aspect), dignified "
                  "in Taurus/Scorpio or Cancer/Capricorn, esp. in 2/9/10/11 → wealth "
                  "by above-board means (else Varahamihira's 'unscrupulous')",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2879)),

    # #65a — Mars and Moon in mutual Kendra (not already Chandramangala).
    #       InHouseFrom with kendra offsets {1,4,7,10} encodes "in kendra from".
    RuleRecord(
        id="H2.C.65a", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.And(
            C.Not(C.Conjunct("Moon", "Mars")),        # not already Chandramangala
            C.Not(C.MutualAspect("Moon", "Mars")),    # not already Chandramangala
            C.Or(C.InHouseFrom("Mars", "Moon", 1),    # Mars in kendra from Moon
                 C.InHouseFrom("Mars", "Moon", 4),
                 C.InHouseFrom("Mars", "Moon", 7),
                 C.InHouseFrom("Mars", "Moon", 10))),
        fortified="Mars and Moon in mutual Kendra → gives rise to something like "
                  "Chandramangala Yoga (a Chandramangala-grade wealth yoga from "
                  "angular disposition)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2945)),

    # #66 — Gajakesari Yoga (Jupiter in kendra from Moon).
    #       Core kendra-from-Moon condition evaluable; 6/8/12 refinement in text.
    RuleRecord(
        id="H2.C.66", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.Or(C.InHouseFrom("Jupiter", "Moon", 1),
                       C.InHouseFrom("Jupiter", "Moon", 4),
                       C.InHouseFrom("Jupiter", "Moon", 7),
                       C.InHouseFrom("Jupiter", "Moon", 10)),
        fortified="Gajakesari Yoga (Moon-Jupiter mutual kendra), with Jupiter "
                  "connected to 2nd → makes one earn well (but not if in 12/6/8 "
                  "from Lagna)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2948)),

    # #67 — DESCRIPTIVE: source-of-gain list (already covered by H2.L.1–L.12).
    RuleRecord(
        id="H2.C.67", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="2nd lord in 1-12 → source of gain varies by house (manual labour / "
                  "effortless / travels / mother / speculation / broker / marriage / "
                  "legacies / father / profession / various / servants); see lord-in-12 "
                  "rules H2.L.1–L.12 for individual encodings",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 2504)),

    # #68 — DESCRIPTIVE: Atma-Karaka + Arudha Lagna disposition.
    #       TODO(predicate): AtmaKaraka + ArudhaLagna.
    RuleRecord(
        id="H2.C.68", house=2, signification="wealth", group="combination",
        kind="descriptive", condition=None,
        fortified="Atma-Karaka + Arudha Lagna disposition; benefic/malefic in 11th "
                  "from Arudha decides just/unjust earning → strong bearing on "
                  "financial status and means of earning",
        afflicted=None,
        frame="ARUDHA/AK", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 2514)),

    # ── F. ACCURACY-FIX RULES (added for H2 golden accuracy) ───────────────

    # #69 — Chart-wide Dwirdwadasha web → wealth severely curtailed.
    #       Charts 42 & 44 cite Dwirdwadasha positions as key affliction.
    RuleRecord(
        id="H2.C.69", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=C.AllPlanetsInDwirdwadasha(),
        fortified=None,
        afflicted="Planets bound in Dwirdwadasha (2nd/12th) web throughout → wealth "
                  "severely curtailed (chart 42: 'ordinary man drawing Rs. 50-60/month'; "
                  "chart 44: 'lost all fortune, Rs. 50000 debt')",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2800)),

    # #70 — 6th lord aspects the 2nd house → wealth curtailed.
    #       Chart 48: "6th lord aspects house of finance."
    RuleRecord(
        id="H2.C.70", house=2, signification="wealth", group="combination",
        kind="evaluable",
        condition=_LordAspectsHouse(6, 2),
        fortified=None,
        afflicted="6th lord (debt/enemy) aspects the 2nd house → wealth curtailed, "
                  "acquired by hard labour",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2937)),
)
