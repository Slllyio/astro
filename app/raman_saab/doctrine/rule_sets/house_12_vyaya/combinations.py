"""House 12 (Vyaya — loss / expenditure / moksha / foreign / bed-pleasures) —
"Important Combinations".

Encodes the combination rule-atoms of the "Important Combinations" tables in
``docs/raman_saab/methodology/house_12_vyaya.md`` (HTJAH-II:16244-16569, with the
movable-sign-travel modifier from the lord-in-12th close at 16230-16238).

Encoding policy (honest, atom by atom — mirrors H4/H5/H7/H8/H10):

* Existing predicates compose directly. Combos route to the FINE 12th-house sigs
  read from ``significations.py`` ``_H12``:
    - ``expenditure``      — how/where wealth is dissipated (Group A)
    - ``loss_moksha``      — generic loss matters: debts, poverty, bed-pleasure denial
                             (Groups B, C, E); the aggregate bridge tag of the house
    - ``incarceration``    — bandhana yoga / captivity (Group D)
    - ``moksha``           — after-death state, Final Emancipation, charity/piety
                             (Groups F, G, I)
    - ``foreign_residence``— travel / living abroad / wandering (Group H)
    - ``left_eye``         — eyes / defective vision / blindness (Group J: the only
                             eye-signification key, so right-eye and general-vision
                             rules also route here)
* The flat placement file ``house_12_vyaya.py`` already scores ``LordIn(12,*)``
  (H12.L.1..12) and ``InRashiHouse(planet,12)`` (H12.P.*), ALL under ``loss_moksha``.
  To avoid double-counting, combos that reuse one of those conditions route to a
  DIFFERENT fine key (e.g. Mars-in-12 -> ``expenditure``; 12th-lord-in-9 ->
  ``foreign_residence``), or carry a distinct condition tree.
* Rules needing predicates not yet in the algebra — Navamsa/shashtyamsa/drekkana/
  vaiseshikamsa/simhasanamsa varga overlays, karakamsa origin, Tara-from-Janma,
  planet "strength" gates, Mandi/Gulika, affliction-grade aggregates — go in as
  ``kind="descriptive"`` with a ``TODO(predicate)`` note.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS)


_MOVABLE_SIGNS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})  # Aries/Cancer/Libra/Cap
_VENUS_SIGNS: Final[frozenset[int]] = frozenset({2, 7})           # Taurus / Libra (Venus-lordship)
_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONA: Final[frozenset[int]] = frozenset({1, 5, 9})
_DUSTHANA: Final[frozenset[int]] = frozenset({6, 8, 12})


def _lord_of(house: int, chart: RamanChart) -> str:
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _twelfth_sign(chart: RamanChart) -> int:
    return ((chart.asc_sign - 1) + 11) % 12 + 1


# ── local leaf predicates ─────────────────────────────────────────────────────

class _LagnaInSigns(C.Condition):
    """The ascendant sign is one of `signs`."""
    def __init__(self, signs: frozenset[int]) -> None:
        self.signs = signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return ctx.chart.asc_sign in self.signs


class _TwelfthSignIn(C.Condition):
    """The sign on the 12th whole-sign house is one of `signs`."""
    def __init__(self, signs: frozenset[int]) -> None:
        self.signs = signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _twelfth_sign(ctx.chart) in self.signs


class _ClassAspectsHouse(C.Condition):
    """Some natural planet of `klass` casts a whole-sign drishti on whole-sign `house`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name in group and drishti.aspects_house(name, self.house, ctx.chart)
                   for name in ctx.chart.planets)


class _AspectedByClass(C.Condition):
    """`target` planet is aspected by some natural planet of `klass`."""
    def __init__(self, target: str, klass: str) -> None:
        self.target, self.klass = target, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        if self.target not in ctx.chart.planets:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != self.target and name in group
                   and drishti.aspects_planet(name, self.target, ctx.chart)
                   for name in ctx.chart.planets)


class _HouseHemmedBy(C.Condition):
    """Papakartari/Subhakartari on a whole-sign HOUSE: both the 11th and 1st
    (i.e. the houses immediately before and after) hold a planet of `klass`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        prev_h = ((self.house - 2) % 12) + 1
        next_h = (self.house % 12) + 1
        occupied = {prev_h: False, next_h: False}
        for name, p in ctx.chart.planets.items():
            if name in group and p.rasi_house in occupied:
                occupied[p.rasi_house] = True
        return all(occupied.values())


class _LordHemmedBy(C.Condition):
    """The lord of `house` is hemmed (2nd & 12th from it hold a planet of `klass`)."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.HemmedBy(_lord_of(self.house, ctx.chart), self.klass).evaluate(ctx)


class _LordConjunctClass(C.Condition):
    """The lord of `house` shares a whole-sign house with a natural planet of `klass`."""
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


class _LordAspectedByClass(C.Condition):
    """The lord of `house` is aspected by some natural planet of `klass` (the lord
    mirror of ``_AspectedByClass``). Encodes Raman's "the 12th lord is aspected by
    ... a malefic ... planet" (HTJAH-II:16252) for ALL malefics, not just the two
    with special aspects — under the Raman-Saab 7th-only node drishti the Sun and
    nodes contribute only their 7th, Mars/Saturn their full aspect set."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        if lord not in ctx.chart.planets:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != lord and name in group
                   and drishti.aspects_planet(name, lord, ctx.chart)
                   for name in ctx.chart.planets)


class _LordConjunctPlanet(C.Condition):
    """The lord of `house` shares a whole-sign house with `planet` (identity -> False)."""
    def __init__(self, house: int, planet: str) -> None:
        self.house, self.planet = house, planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        if lord == self.planet:
            return False
        return C.Conjunct(lord, self.planet).evaluate(ctx)


class _LordInClass(C.Condition):
    """The lord of `house` sits in a whole-sign house of class `signs`."""
    def __init__(self, house: int, signs: frozenset[int]) -> None:
        self.house, self.signs = house, signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(_lord_of(self.house, ctx.chart))
        return p is not None and p.rasi_house in self.signs


class _LordHasDignity(C.Condition):
    """The lord of `house` carries one of `states` as its compound dignity."""
    def __init__(self, house: int, states: frozenset[str]) -> None:
        self.house, self.states = house, states

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        return lord in ctx.chart.planets and dignity(lord, ctx.chart) in self.states


class _PlanetAspectsLord(C.Condition):
    """`planet` casts a whole-sign drishti on the lord of `house` (identity -> False)."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        return lord != self.planet and drishti.aspects_planet(self.planet, lord, ctx.chart)


class _LordAspectsPlanet(C.Condition):
    """The lord of `house` casts a whole-sign drishti on `planet` (identity -> False)."""
    def __init__(self, house: int, planet: str) -> None:
        self.house, self.planet = house, planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        return lord != self.planet and drishti.aspects_planet(lord, self.planet, ctx.chart)


class _PlanetIsLordOfIn(C.Condition):
    """`planet` is the lord of whole-sign house `house` AND occupies house `in_house`."""
    def __init__(self, planet: str, house: int, in_house: int) -> None:
        self.planet, self.house, self.in_house = planet, house, in_house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        if _lord_of(self.house, ctx.chart) != self.planet:
            return False
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.rasi_house == self.in_house


class _PlanetConjunctClassInHouse(C.Condition):
    """`planet` sits in whole-sign `house` together with a natural planet of `klass`."""
    def __init__(self, planet: str, house: int, klass: str) -> None:
        self.planet, self.house, self.klass = planet, house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        if p is None or p.rasi_house != self.house:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != self.planet and name in group and q.rasi_house == self.house
                   for name, q in ctx.chart.planets.items())


class _LordPlusNInClass(C.Condition):
    """The lord of `house` sits in a house of class `signs` that holds at least
    `extra` OTHER bodies (so the lord plus `extra` others — `extra`+1 planets in all)."""
    def __init__(self, house: int, extra: int, signs: frozenset[int]) -> None:
        self.house, self.extra, self.signs = house, extra, signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        p = ctx.chart.planets.get(lord)
        if p is None or p.rasi_house not in self.signs:
            return False
        others = sum(1 for name, q in ctx.chart.planets.items()
                     if name != lord and q.rasi_house == p.rasi_house)
        return others >= self.extra


# ── RULES ─────────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ===== Group A — Expenditure / losses (HTJAH-II:16250-16371) — sig expenditure =====
    RuleRecord(
        id="H12.C.A1", house=12, signification="expenditure", group="combination",
        kind="descriptive", condition=None,
        fortified="12th lord in benefic vargas → spends wealth in honourable and approved "
                  "ways. TODO(predicate: benefic-varga / shashtyamsa gate of the lord)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 16250)),
    RuleRecord(
        id="H12.C.A2", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.Or(_LordConjunctClass(12, "malefic"),
                       _LordAspectedByClass(12, "malefic")),
        fortified=None,
        afflicted="12th lord with or aspected by a malefic / depressed / eclipsed planet → "
                  "spends money in illegal and questionable ways (wine, women, races, gambling, "
                  "per the afflicting planet)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16252)),
    RuleRecord(
        id="H12.C.A3", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.Or(C.CountInHouse(12, 1, "benefic"), _ClassAspectsHouse(12, "benefic")),
        fortified="benefics aspect or occupy the 12th → a good father funds his wants, can "
                  "spend freely",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16260)),
    RuleRecord(
        id="H12.C.A4", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=_ClassAspectsHouse(12, "malefic"),
        fortified=None,
        afflicted="malefics afflict the 12th → earnings get dissipated in many ways",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16262)),
    RuleRecord(
        id="H12.C.A5", house=12, signification="expenditure", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="6th or 8th lord in the 12th AND the 10th/2nd/11th houses and their lords "
                  "also afflicted → loss of prestige and money. TODO(predicate: multi-house "
                  "affliction-grade aggregate)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16263)),
    RuleRecord(
        id="H12.C.A6", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=_LordHasDignity(12, frozenset({"exalt", "own", "moolatrikona", "friend"})),
        fortified="12th lord exalted or in a friendly sign → the native is generous",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16268)),
    RuleRecord(
        id="H12.C.A7", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.CountInHouse(12, 1, "benefic"),
        fortified="a benefic in the 12th → makes one thrifty and careful with money",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16270)),
    RuleRecord(
        id="H12.C.A8", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 12), _AspectedByClass("Sun", "malefic")),
        fortified=None,
        afflicted="afflicted Sun in the 12th → wealth spent on fines or confiscated by the "
                  "Government",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16310)),
    RuleRecord(
        id="H12.C.A9", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.InRashiHouse("Mars", 12),
        fortified=None,
        afflicted="Mars in the 12th → expensive litigation and dangerous enemies; money lost "
                  "through ransom, cheating and swindlers",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16312)),
    RuleRecord(
        id="H12.C.A10", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.InRashiHouse("Mercury", 12),
        fortified=None,
        afflicted="Mercury in the 12th → reckless investment in shares, trade and business; "
                  "family litigation also dwindles wealth",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16314)),
    RuleRecord(
        id="H12.C.A11", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.InRashiHouse("Venus", 12),
        fortified=None,
        afflicted="Venus in the 12th → loss of money through women of ill-fame, scandals or "
                  "black-mail",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16316)),
    RuleRecord(
        id="H12.C.A12", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 12), C.InRashiHouse("Mars", 12)),
        fortified=None,
        afflicted="Saturn and Mars in the 12th → expenditure on account of co-borns",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16317)),
    RuleRecord(
        id="H12.C.A13", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 12), C.InRashiHouse("Rahu", 12)),
        fortified=None,
        afflicted="Saturn and Rahu in the 12th → heavy expenses on deaths and similar "
                  "calamities",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16318)),
    RuleRecord(
        id="H12.C.A14", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 12), C.LordIn(1, 12)),
        fortified=None,
        afflicted="the Moon and the Ascendant lord in the 12th → dissipation of money through "
                  "medical and hospital bills, sureties and bail-amounts",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16320)),
    RuleRecord(
        id="H12.C.A15", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.LordsConjunct(12, 4),
        fortified=None,
        afflicted="the afflicted 12th lord joins the 4th lord → the native's mother is "
                  "instrumental in his losing money",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16327)),
    RuleRecord(
        id="H12.C.A16", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.Or(C.LordsConjunct(12, 6), _LordConjunctPlanet(12, "Mars"),
                       _LordConjunctPlanet(12, "Venus"), C.LordsConjunct(12, 5),
                       C.LordsConjunct(12, 3), C.LordsConjunct(12, 7),
                       C.LordsConjunct(12, 10)),
        fortified=None,
        afflicted="12th lord connected with the 6th lord / Mars / Venus / 5th / 3rd / 7th / "
                  "10th lord → loss of money through their respective significations (enemies, "
                  "litigation, women, children, co-borns, married partner, father)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16328)),
    RuleRecord(
        id="H12.C.A17", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=_LordConjunctClass(12, "malefic"),
        fortified=None,
        afflicted="the 12th lord with a malefic → suggests embezzlement tendencies",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16337)),
    RuleRecord(
        id="H12.C.A18", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.And(C.Parivartana(2, 12), C.LordIn(1, 6)),
        fortified=None,
        afflicted="2nd↔12th lords exchange AND the Lagna lord afflicting in the 6th → criminal "
                  "proceedings leading to loss of wealth",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16338)),
    RuleRecord(
        id="H12.C.A19", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 12), C.InRashiHouse("Moon", 12)),
        fortified=None,
        afflicted="the luminaries occupy the 12th → loss of wealth through tax raids, "
                  "government enactments or confiscation",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16363)),
    RuleRecord(
        id="H12.C.A20", house=12, signification="expenditure", group="combination",
        kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 12),
        fortified="Jupiter in the 12th → makes one honest and pay taxes and tolls properly",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16370)),
    RuleRecord(
        id="H12.C.A21", house=12, signification="expenditure", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="the lord of the Navamsa occupied by the 2nd house, aspected by the Lagna "
                  "lord and in the 6th/8th/12th → expenditure on fines; also losses through "
                  "theft and fire. TODO(predicate: Navamsa-dispositor-of-house overlay)",
        frame="LAGNA", varga="D9", polarity="malefic", source=Citation("HTJAH-II", 16351)),
    RuleRecord(
        id="H12.C.A22", house=12, signification="expenditure", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="Mars aspecting the weak 2nd & 11th lords (in inimical malefic amsas, "
                  "malefic-afflicted) → theft, fire or fines lead to loss of wealth. "
                  "TODO(predicate: strength gate + amsa overlay)",
        frame="LAGNA", varga="D9", polarity="malefic", source=Citation("HTJAH-II", 16356)),
    RuleRecord(
        id="H12.C.A23", house=12, signification="expenditure", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="afflicted 10th lord in the 6th with the 2nd & 11th lords in an evil "
                  "shashtyamsa → public censure and thereby loss of wealth. TODO(predicate: "
                  "shashtyamsa class overlay)",
        frame="LAGNA", varga="D9", polarity="malefic", source=Citation("HTJAH-II", 16359)),

    # ===== Group B — Debts (HTJAH-II:16373-16393) — sig loss_moksha =====
    RuleRecord(
        id="H12.C.B1", house=12, signification="loss_moksha", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="lord of the Navamsa occupied by the 11th lord, with a benefic but in a "
                  "malefic shashtyamsa, in the 6th/8th/12th → plunged into debts. "
                  "TODO(predicate: Navamsa-dispositor + shashtyamsa overlay)",
        frame="LAGNA", varga="D9", polarity="malefic", source=Citation("HTJAH-II", 16373)),
    RuleRecord(
        id="H12.C.B2", house=12, signification="loss_moksha", group="combination",
        kind="evaluable",
        condition=C.And(C.LordsConjunct(10, 11), C.CountInHouse(2, 1, "malefic"),
                        C.LordIn(1, 12)),
        fortified=None,
        afflicted="10th lord conjoined the 11th lord, a malefic in the 2nd, and the Lagna lord "
                  "in the 12th → the native gets involved in debts",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16375)),
    RuleRecord(
        id="H12.C.B3", house=12, signification="loss_moksha", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="Lagna lord joining the 2nd, or the 7th lord eclipsed/debilitated/inimical in "
                  "a dusthana with the 9th lord unaspected by benefics (and variants) → debts. "
                  "TODO(predicate: eclipse/debility/combust + benefic-aspect gates)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16381)),
    RuleRecord(
        id="H12.C.B4", house=12, signification="loss_moksha", group="combination",
        kind="descriptive", condition=None,
        fortified="Nav-lords of the drekkana-rulers of the 2nd & 11th in vaiseshikamsa, in a "
                  "trine or quadrant → clears off debts during his lifetime (positive). "
                  "TODO(predicate: drekkana + vaiseshikamsa overlay)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 16390)),

    # ===== Group C — Poverty / penury (HTJAH-II:16395-16424) — sig loss_moksha =====
    RuleRecord(
        id="H12.C.C1", house=12, signification="loss_moksha", group="combination",
        kind="evaluable",
        condition=C.And(
            C.Or(C.InHouseFrom("Jupiter", "MOON", 12), C.InHouseFrom("Jupiter", "MOON", 6),
                 C.InHouseFrom("Jupiter", "MOON", 8)),
            C.InHouseClass("Moon", "kendra"),
            C.HasDignity("Moon", {"debil"})),
        fortified=None,
        afflicted="Jupiter in the 12th/6th/8th FROM the Moon, the Moon in a quadrant and "
                  "debilitated (or in an inimical varga) → poverty",
        frame="MOON", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16395)),
    RuleRecord(
        id="H12.C.C2", house=12, signification="loss_moksha", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 9), C.HasDignity("Sun", {"debil"}),
                        C.InRashiHouse("Mars", 8)),
        fortified=None,
        afflicted="the Sun in debility in the 9th and Mars in the 8th → appalling poverty",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16397)),
    RuleRecord(
        id="H12.C.C3", house=12, signification="loss_moksha", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="the Sun in Aries aspected by a malefic and debilitated in Navamsa; or Venus "
                  "in Virgo both in Rasi and Navamsa → a beggar is born. TODO(predicate: "
                  "Navamsa-debility overlay)",
        frame="LAGNA", varga="D9", polarity="malefic", source=Citation("HTJAH-II", 16398)),
    RuleRecord(
        id="H12.C.C4", house=12, signification="loss_moksha", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="Asc Sagittarius/Pisces/Leo/Taurus, Jupiter stronger than the 9th lord, and "
                  "the 11th lord weak & combust outside a kendra → indigent circumstances. "
                  "TODO(predicate: comparative strength + combust gate)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16401)),
    RuleRecord(
        id="H12.C.C5", house=12, signification="loss_moksha", group="combination",
        kind="evaluable",
        condition=C.ClassInHouseFrom("malefic", "Jupiter", {2, 4, 5}),
        fortified=None,
        afflicted="a malefic in the 2nd/4th/5th FROM Jupiter → the native will be poor",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16410)),
    RuleRecord(
        id="H12.C.C6", house=12, signification="loss_moksha", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 1), C.InRashiHouse("Moon", 1),
                        C.Or(C.LordIn(2, 1), C.LordIn(7, 1),
                             _LordAspectsPlanet(2, "Sun"), _LordAspectsPlanet(2, "Moon"),
                             _LordAspectsPlanet(7, "Sun"), _LordAspectsPlanet(7, "Moon"))),
        fortified=None,
        afflicted="the luminaries in the Lagna aspected by or associated with the 2nd or 7th "
                  "lord → the native will be poor",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16411)),
    RuleRecord(
        id="H12.C.C7", house=12, signification="loss_moksha", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 12), C.LordIn(12, 2), C.CountInHouse(3, 1, "malefic")),
        fortified=None,
        afflicted="the 9th lord in the 12th, the 12th lord in the 2nd and malefics in the 3rd "
                  "→ penury and suffering",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16413)),
    RuleRecord(
        id="H12.C.C8", house=12, signification="loss_moksha", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 8), C.LordIn(8, 1),
                        C.Or(C.LordIn(2, 1), C.LordIn(7, 1))),
        fortified=None,
        afflicted="the Lagna lord in the 8th while the 8th lord joins the 2nd or 7th lord in "
                  "Lagna → never earns enough for even bare subsistence",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16416)),
    RuleRecord(
        id="H12.C.C9", house=12, signification="loss_moksha", group="combination",
        kind="evaluable",
        condition=C.Or(
            C.And(C.CountInHouse(10, 1, "benefic"), C.CountInHouse(2, 1, "malefic")),
            C.And(C.InHouseClass("Moon", "kendra"), C.InHouseClass("Jupiter", "kendra"),
                  C.InHouseClass("Saturn", "kendra"),
                  C.Or(C.InRashiHouse("Mars", 5), C.InRashiHouse("Mars", 8),
                       C.InRashiHouse("Mars", 12)))),
        fortified=None,
        afflicted="benefics in the 10th with malefics in the 2nd; or the Moon, Jupiter & Saturn "
                  "in quadrants with Mars (or Mandi) in the 5th/8th/12th → poverty "
                  "(slum-dweller class). TODO(predicate: Mandi placement)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16418)),

    # ===== Group D — Confinement / imprisonment, Bandhana Yoga (16426-16448) — incarceration =====
    RuleRecord(
        id="H12.C.D1", house=12, signification="incarceration", group="combination",
        kind="evaluable",
        condition=_LordHemmedBy(1, "malefic"),
        fortified=None,
        afflicted="the Ascendant, its lord and planets in papakartari yoga → usually gives "
                  "rise to imprisonment",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16426)),
    RuleRecord(
        id="H12.C.D2", house=12, signification="incarceration", group="combination",
        kind="evaluable",
        condition=C.And(C.LordsConjunct(1, 6), _LordConjunctPlanet(1, "Saturn"),
                        C.Or(_LordInClass(1, _KENDRA), _LordInClass(1, _TRIKONA))),
        fortified=None,
        afflicted="the Lagna and 6th lords combining with Saturn in a kendra or kona → the "
                  "native suffers imprisonment",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16427)),
    RuleRecord(
        id="H12.C.D3", house=12, signification="incarceration", group="combination",
        kind="evaluable",
        condition=C.And(C.CountInHouse(2, 1, "malefic"), C.CountInHouse(5, 1, "malefic"),
                        C.CountInHouse(9, 1, "malefic"), C.CountInHouse(12, 1, "malefic")),
        fortified=None,
        afflicted="malefics in the 2nd, 5th, 9th and 12th houses → captivity (exact mode set "
                  "by the rising sign)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16429)),
    RuleRecord(
        id="H12.C.D3a", house=12, signification="incarceration", group="combination",
        kind="evaluable",
        condition=C.And(C.CountInHouse(2, 1, "malefic"), C.CountInHouse(5, 1, "malefic"),
                        C.CountInHouse(9, 1, "malefic"), C.CountInHouse(12, 1, "malefic"),
                        _LagnaInSigns(frozenset({1, 2, 9}))),
        fortified=None,
        afflicted="(D3) with Aries/Taurus/Sagittarius rising → the native is bound by ropes",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16431)),
    RuleRecord(
        id="H12.C.D3b", house=12, signification="incarceration", group="combination",
        kind="evaluable",
        condition=C.And(C.CountInHouse(2, 1, "malefic"), C.CountInHouse(5, 1, "malefic"),
                        C.CountInHouse(9, 1, "malefic"), C.CountInHouse(12, 1, "malefic"),
                        _LagnaInSigns(frozenset({8}))),
        fortified=None,
        afflicted="(D3) with Scorpio rising → the native is thrown into an underground cell",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16433)),
    RuleRecord(
        id="H12.C.D3c", house=12, signification="incarceration", group="combination",
        kind="evaluable",
        condition=C.And(C.CountInHouse(2, 1, "malefic"), C.CountInHouse(5, 1, "malefic"),
                        C.CountInHouse(9, 1, "malefic"), C.CountInHouse(12, 1, "malefic"),
                        _LagnaInSigns(frozenset({3, 7, 6}))),
        fortified=None,
        afflicted="(D3) with Gemini/Libra/Virgo rising → one may be put in fetters",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16434)),
    RuleRecord(
        id="H12.C.D3d", house=12, signification="incarceration", group="combination",
        kind="evaluable",
        condition=C.And(C.CountInHouse(2, 1, "malefic"), C.CountInHouse(5, 1, "malefic"),
                        C.CountInHouse(9, 1, "malefic"), C.CountInHouse(12, 1, "malefic"),
                        _LagnaInSigns(frozenset({12, 4, 10}))),
        fortified=None,
        afflicted="(D3) with Pisces/Cancer/Capricorn rising → imprisonment in a large "
                  "protected building",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16435)),
    RuleRecord(
        id="H12.C.D4", house=12, signification="incarceration", group="combination",
        kind="evaluable",
        condition=C.And(C.LordsConjunct(1, 6),
                        C.Or(_LordConjunctPlanet(1, "Rahu"), _LordConjunctPlanet(1, "Ketu")),
                        C.Or(_LordInClass(1, _KENDRA), _LordInClass(1, _TRIKONA))),
        fortified=None,
        afflicted="the 6th and Lagna lords in a trine or quadrant, joining Rahu or Ketu → "
                  "incarceration",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16438)),
    RuleRecord(
        id="H12.C.D5", house=12, signification="incarceration", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 10), C.InRashiHouse("Mars", 9),
                        C.InRashiHouse("Saturn", 1), C.InRashiHouse("Sun", 5)),
        fortified=None,
        afflicted="the Moon, Mars, Saturn and Sun in the 10th, 9th, 1st and 5th respectively → "
                  "death in captivity",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16439)),
    RuleRecord(
        id="H12.C.D6", house=12, signification="incarceration", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="rulers of (2&12)/(5&9)/(6&12)/(3&11)/(4&10) equal in strength → criminal "
                  "action (absent other mitigation). TODO(predicate: equal-strength gate)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16444)),

    # ===== Group E — Bed-pleasures / sayana-sukha (16289-16305) — sig loss_moksha =====
    RuleRecord(
        id="H12.C.E1", house=12, signification="loss_moksha", group="combination",
        kind="descriptive", condition=None,
        fortified="the 12th house AND Venus both beneficially disposed → bed-comforts wherever "
                  "he resides. TODO(predicate: 'beneficially disposed' strength gate)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16289)),
    RuleRecord(
        id="H12.C.E2", house=12, signification="loss_moksha", group="combination",
        kind="descriptive", condition=None,
        fortified="the 12th lord conjoined with or aspected by a benefic and occupying a "
                  "benefic varga → enjoys pleasures of the couch. TODO(predicate: benefic-varga "
                  "gate of the lord)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 16291)),
    RuleRecord(
        id="H12.C.E3", house=12, signification="loss_moksha", group="combination",
        kind="evaluable",
        condition=C.Or(_LordInClass(1, _DUSTHANA), _LordHasDignity(1, frozenset({"debil"})),
                       _LordConjunctPlanet(1, "Saturn"), _LordConjunctPlanet(1, "Rahu"),
                       _LordConjunctClass(12, "malefic")),
        fortified=None,
        afflicted="the Lagna lord in the 6th/8th/12th; or the Lagna lord debilitated or with "
                  "Saturn/Mandi/Rahu; or the 12th lord malefic-afflicted → denial or "
                  "deprivation of bed-pleasures. TODO(predicate: Mandi placement)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16299)),

    # ===== Group F — After-death state of the soul (16491-16523) — sig moksha =====
    RuleRecord(
        id="H12.C.F1", house=12, signification="moksha", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="the 12th aspected/occupied by Saturn or Mandi AND the 12th lord in a Vipat "
                  "(3rd)/Pratyak (5th)/Naidhana (7th) constellation from Janma Nakshatra → "
                  "calamities, vicious conduct, goes to hell after death. TODO(predicate: "
                  "Tara-from-Janma + Mandi)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16491)),
    RuleRecord(
        id="H12.C.F2", house=12, signification="moksha", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="a malefic in combustion/debilitation/eclipse afflicting the 12th → may go "
                  "to lower planes such as hell after death. TODO(predicate: combust/debil/"
                  "eclipse state of the afflicting planet)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16498)),
    RuleRecord(
        id="H12.C.F3", house=12, signification="moksha", group="combination",
        kind="descriptive", condition=None,
        fortified=None,
        afflicted="the 12th lord in a malefic shashtyamsa aspected by a malefic; or Rahu in the "
                  "12th with Mandi and the 8th lord aspected by the 6th lord → descends into "
                  "the infernal regions after death. TODO(predicate: shashtyamsa + Mandi)",
        frame="LAGNA", varga="D9", polarity="malefic", source=Citation("HTJAH-II", 16500)),
    RuleRecord(
        id="H12.C.F4", house=12, signification="moksha", group="combination",
        kind="evaluable",
        condition=C.Or(C.CountInHouse(12, 1, "benefic"), _HouseHemmedBy(12, "benefic")),
        fortified="the 12th occupied by a benefic or subject to a shubhakartari yoga → the "
                  "native goes to heaven",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16506)),
    RuleRecord(
        id="H12.C.F5", house=12, signification="moksha", group="combination",
        kind="evaluable",
        condition=C.Or(_PlanetIsLordOfIn("Jupiter", 10, 12),
                       C.And(C.InRashiHouse("Jupiter", 12),
                             C.Or(C.Aspects("Venus", "Jupiter"),
                                  C.And(C.Aspects("Moon", "Jupiter"), C.MoonPhase("waning"))))),
        fortified="Jupiter as the 10th lord in the 12th, or Jupiter in the 12th aspected by "
                  "Venus / waning Moon / well-placed Sun → becomes a celestial after death",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16509)),
    RuleRecord(
        id="H12.C.F6", house=12, signification="moksha", group="combination",
        kind="descriptive", condition=None,
        fortified="a benefic planet in strength in the 12th in benefic vargas, aspected both by "
                  "benefics and malefics → becomes a celestial after death. TODO(predicate: "
                  "strength + benefic-varga gate)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 16515)),
    RuleRecord(
        id="H12.C.F7", house=12, signification="moksha", group="combination",
        kind="descriptive", condition=None,
        fortified="powerful Jupiter in Cancer and its moolatrikona sign in Navamsa, with 3-4 "
                  "planets in kendras → attains Brahmaloka after death. TODO(predicate: Navamsa "
                  "moolatrikona + strength gate)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 16517)),

    # ===== Group G — Moksha / Final Emancipation (16524-16531) — sig moksha =====
    RuleRecord(
        id="H12.C.G1", house=12, signification="moksha", group="combination",
        kind="descriptive", condition=None,
        fortified="Asc Sagittarius, Navamsa-Lagna Aries, Venus in the 7th in Gemini and the "
                  "Moon in Virgo → attains Liberation (Moksha) after death. TODO(predicate: "
                  "Navamsa-Lagna overlay)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 16524)),
    RuleRecord(
        id="H12.C.G2", house=12, signification="moksha", group="combination",
        kind="descriptive", condition=None,
        fortified="Ketu in the 12th FROM karakamsa → gives Kaivalya / Final Emancipation. "
                  "TODO(predicate: karakamsa origin / Atmakaraka-Navamsa frame)",
        afflicted=None,
        frame="KARAKA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 16527)),
    RuleRecord(
        id="H12.C.G3", house=12, signification="moksha", group="combination",
        kind="evaluable",
        condition=C.Or(_LordPlusNInClass(10, 4, _TRIKONA), _LordPlusNInClass(10, 4, _KENDRA)),
        fortified="the 10th lord joining 4 other planets in a trine or quadrant → the native "
                  "attains Final Liberation",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16528)),
    RuleRecord(
        id="H12.C.G4", house=12, signification="moksha", group="combination",
        kind="evaluable",
        condition=C.And(_LagnaInSigns(frozenset({3})), C.InSign("Mars", 12),
                        C.InSign("Mercury", 12)),
        fortified="Mars and Mercury in Pisces with Gemini as the Ascendant → gives Moksha",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16530)),

    # ===== Group H — Foreign residence / wandering (16201-16238) — sig foreign_residence =====
    RuleRecord(
        id="H12.C.H1", house=12, signification="foreign_residence", group="combination",
        kind="evaluable",
        condition=C.And(_TwelfthSignIn(_MOVABLE_SIGNS),
                        C.Or(C.InRashiHouse("Moon", 12), C.InRashiHouse("Mercury", 12))),
        fortified="the 12th a movable sign containing the Moon or Mercury → lot of travelling; "
                  "benefic aspect → residence abroad, delightful journeys, good fortune",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16232)),
    RuleRecord(
        id="H12.C.H2", house=12, signification="foreign_residence", group="combination",
        kind="evaluable",
        condition=C.Or(_HouseHemmedBy(12, "malefic"), _ClassAspectsHouse(12, "malefic")),
        fortified=None,
        afflicted="malefics afflicting the 12th by papakartari yoga or aspect → the native may "
                  "leave the country for fear of the law or life, and live a vagrant incognito "
                  "life",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16236)),
    RuleRecord(
        id="H12.C.H3", house=12, signification="foreign_residence", group="combination",
        kind="evaluable",
        condition=C.LordIn(12, 9),
        fortified="the 12th lord in the 9th → residence abroad, acquires foreign property and "
                  "prosperity",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16201)),
    RuleRecord(
        id="H12.C.H4", house=12, signification="foreign_residence", group="combination",
        kind="evaluable",
        condition=C.LordIn(12, 4),
        fortified=None,
        afflicted="the 12th lord in the 4th → living abroad (among the results of this "
                  "placement)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16161)),

    # ===== Group I — Charity / piety (positive expenditure) (16271-16287) — sig moksha =====
    RuleRecord(
        id="H12.C.I1", house=12, signification="moksha", group="combination",
        kind="evaluable",
        condition=C.And(_PlanetAspectsLord("Jupiter", 12), C.LordIn(9, 4),
                        _LordInClass(10, _KENDRA)),
        fortified="the 12th lord aspected by Jupiter, the 9th lord in the 4th, and the 10th "
                  "lord in a kendra → a charitable disposition",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16271)),
    RuleRecord(
        id="H12.C.I2", house=12, signification="moksha", group="combination",
        kind="evaluable",
        condition=C.Parivartana(1, 9),
        fortified="the Ascendant and the 9th lords in parivartana → engages in charitable and "
                  "virtuous deeds",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16272)),
    RuleRecord(
        id="H12.C.I3", house=12, signification="moksha", group="combination",
        kind="evaluable",
        condition=C.LordIn(9, 12),
        fortified="the 9th lord in the 12th → keen on pilgrimages and charitably disposed",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16275)),
    RuleRecord(
        id="H12.C.I4", house=12, signification="moksha", group="combination",
        kind="descriptive", condition=None,
        fortified="the 9th lord occupying a benefic sign in Navamsa with a benefic planet → "
                  "spends lavishly on charity. TODO(predicate: Navamsa-sign of the lord overlay)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 16276)),
    RuleRecord(
        id="H12.C.I5", house=12, signification="moksha", group="combination",
        kind="evaluable",
        condition=C.And(C.HasDignity("Mercury", {"exalt"}),
                        C.Or(C.InHouseClass("Mercury", "kendra"), C.InRashiHouse("Mercury", 11)),
                        _LordAspectsPlanet(9, "Mercury")),
        fortified="exalted Mercury in a quadrant or the 11th, aspected by the 9th lord → makes "
                  "one a philanthropist",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 16278)),
    RuleRecord(
        id="H12.C.I6", house=12, signification="moksha", group="combination",
        kind="descriptive", condition=None,
        fortified="the 9th lord in simhasanamsa aspected by the Lagna & 10th lords (variants) → "
                  "spends large sums on charity (out of ostentation if the 9th lord is in a "
                  "malefic Navamsa/shashtyamsa). TODO(predicate: simhasanamsa / amsa-repeat "
                  "overlay)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 16281)),

    # ===== Group J — Eyes / defective vision / blindness (16450-16474) — sig left_eye =====
    RuleRecord(
        id="H12.C.J1", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(_LagnaInSigns(_VENUS_SIGNS), C.LordIn(1, 6)),
        fortified=None,
        afflicted="Lagna-lord Venus in the 6th → diseases in the left eye",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16450)),
    RuleRecord(
        id="H12.C.J2", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(_LordConjunctPlanet(2, "Venus"), _LordConjunctPlanet(12, "Venus"),
                        _LordInClass(1, _DUSTHANA)),
        fortified=None,
        afflicted="the 2nd & 12th lords conjoining Venus and the Lagna lord in a dusthana "
                  "(6/8/12) → born blind",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16451)),
    RuleRecord(
        id="H12.C.J3", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(_LordConjunctPlanet(1, "Sun"), _LordConjunctPlanet(1, "Venus")),
        fortified=None,
        afflicted="a combination of the Lagna lord, the Sun and Venus → born blind",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16453)),
    RuleRecord(
        id="H12.C.J4", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(_AspectedByClass("Moon", "malefic"), C.InRashiHouse("Venus", 2)),
        fortified=None,
        afflicted="the Moon afflicted by a malefic and Venus in the 2nd → loss of vision",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16454)),
    RuleRecord(
        id="H12.C.J5", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(C.InHouseClass("Moon", "dusthana"), C.InHouseClass("Venus", "dusthana")),
        fortified=None,
        afflicted="the Moon and Venus in the 6th/8th/12th → night-blindness",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16460)),
    RuleRecord(
        id="H12.C.J6", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(C.MoonPhase("waning"), C.Aspects("Saturn", "Moon")),
        fortified=None,
        afflicted="the waning Moon aspected by Saturn → weak vision",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16461)),
    RuleRecord(
        id="H12.C.J7", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(C.InSign("Moon", 4), _AspectedByClass("Moon", "malefic")),
        fortified=None,
        afflicted="the Moon in Cancer aspected by malefics (from the 7th or 10th) → weak "
                  "vision",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16462)),
    RuleRecord(
        id="H12.C.J8", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(C.Or(C.InRashiHouse("Venus", 1), C.InRashiHouse("Venus", 8)),
                        _AspectedByClass("Venus", "malefic")),
        fortified=None,
        afflicted="Venus in the Lagna or the 8th afflicted by malefics → eye troubles foreseen",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16463)),
    RuleRecord(
        id="H12.C.J9", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(C.Or(C.InRashiHouse("Sun", 12), C.InHouseClass("Sun", "trikona")),
                        C.Or(C.Aspects("Mars", "Sun"), C.Aspects("Saturn", "Sun"),
                             C.Conjunct("Rahu", "Sun"), C.Aspects("Rahu", "Sun"))),
        fortified=None,
        afflicted="the Sun aspected by Mars/Saturn or afflicted by Rahu, in the 12th or any "
                  "trine → defective vision",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16465)),
    RuleRecord(
        id="H12.C.J10", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(_LordInClass(1, _DUSTHANA), _LordInClass(2, _DUSTHANA)),
        fortified=None,
        afflicted="the Lagna and 2nd lords in the 6th/8th/12th → one's eye-sight may be "
                  "affected",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16469)),
    RuleRecord(
        id="H12.C.J11", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.InRashiHouse("Mars", 12),
        fortified=None,
        afflicted="Mars in the 12th → injures the right eye",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16470)),
    RuleRecord(
        id="H12.C.J12", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 6), C.InRashiHouse("Moon", 12)),
        fortified=None,
        afflicted="the Sun and the Moon in the 6th and the 12th from Lagna → one may lose one "
                  "of his eyes",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16471)),
    RuleRecord(
        id="H12.C.J13", house=12, signification="left_eye", group="combination",
        kind="evaluable",
        condition=C.Or(C.And(C.InRashiHouse("Moon", 12), C.InRashiHouse("Venus", 12)),
                       _PlanetConjunctClassInHouse("Venus", 12, "malefic")),
        fortified=None,
        afflicted="the Moon and Venus in the 12th, or Venus with a malefic in the 12th → the "
                  "left eye is affected",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 16473)),
)
