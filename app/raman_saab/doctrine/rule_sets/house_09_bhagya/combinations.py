"""House 9 (Bhagya / Dharma / Pitru Bhava — father / fortune / dharma / higher
learning / long journeys) — "Important Combinations".

Encodes the combination rule-atoms of the "Important Combinations" section of
``docs/raman_saab/methodology/house_09_bhagya.md`` (HTJAH-II:7406-9423), every
numbered rule across its four sub-sections:

* **A. Father** (from-Sun / pitru readings)  -> sig ``father``        (rules 1-20)
* **B. Fortune** (bhagya / raja-yoga-ish)     -> sig ``fortune``       (rules 21-32)
* **C. Dharma / religion / higher learning**  -> sig ``dharma`` /
  ``higher_learning``                                                  (rules 33-35)
* **D. Travel / pilgrimage**                  -> sig ``long_journeys`` /
  ``dharma``                                                           (rules 36-51)

Encoding policy (honest, atom by atom — mirrors H4/H5/H7/H8/H10):

* Existing predicates compose directly. Father combos route to ``father``;
  bhagya/raja-yoga combos to ``fortune``; religion/philosophy to ``dharma``;
  scholarship to ``higher_learning``; pilgrimage/foreign-travel to
  ``long_journeys``.
* The flat placement file (``house_09_bhagya.py``) already scores the
  ``LordIn(9,*)`` lord-in-house rows and the ``InRashiHouse(planet,9)``
  planet-in-9th rows, all under sig ``fortune``. To avoid double-counting, a
  combination that would reduce to one of those (same condition AND same sig)
  is either routed to a DIFFERENT fine key or kept ``kind="descriptive"`` with
  a note.
* Rules needing predicates not yet in the algebra — synastry (father's chart),
  D60 shashtyamsa, Mandi/Gulika, planet "strength/weak" gates, and Dasa-timing
  (Phase-F) — go in as ``kind="descriptive"`` with a ``TODO(predicate)`` note.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.bhangas import neecha_bhanga
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS)


# ── sign-class constants ──────────────────────────────────────────────────────
_MOVABLE: Final[frozenset[int]] = frozenset({1, 4, 7, 10})   # chara
_FIXED: Final[frozenset[int]] = frozenset({2, 5, 8, 11})     # sthira
_DUAL: Final[frozenset[int]] = frozenset({3, 6, 9, 12})      # dwiswabhava / common
_WATERY: Final[frozenset[int]] = frozenset({4, 8, 12})       # Cancer/Scorpio/Pisces
# Signs owned by a natural malefic (Sun, Mars, Saturn) — Raman's "malefic sign".
_MALEFIC_SIGNS: Final[frozenset[int]] = frozenset({1, 5, 8, 10, 11})
_KENDRA: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_FORTUNE_HOUSES: Final[frozenset[int]] = frozenset({1, 4, 5, 7, 9, 10, 11})  # trine/quadrant/11th


def _lord_of(house: int, chart: RamanChart) -> str:
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _sign_of_house(house: int, chart: RamanChart) -> int:
    """Sign occupying whole-sign `house` (1..12) counted from the Lagna."""
    return ((chart.asc_sign - 1) + (house - 1)) % 12 + 1


# ── local leaf predicates ─────────────────────────────────────────────────────

class _MoonAspectsHouse(C.Condition):
    """The Moon casts a whole-sign drishti on whole-sign `house`."""
    def __init__(self, house: int) -> None:
        self.house = house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return drishti.aspects_house("Moon", self.house, ctx.chart)


class _PlanetAspectsHouse(C.Condition):
    """`planet` casts a whole-sign drishti on whole-sign `house`."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return drishti.aspects_house(self.planet, self.house, ctx.chart)


class _ClassAspectsHouse(C.Condition):
    """Some natural planet of `klass` casts a whole-sign drishti on `house`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name in group and drishti.aspects_house(name, self.house, ctx.chart)
                   for name in ctx.chart.planets)


class _PlanetInHouseSigns(C.Condition):
    """`planet` sits in whole-sign `house`(s) AND that occupied SIGN is in `signs`."""
    def __init__(self, planet: str, houses: frozenset[int], signs: frozenset[int]) -> None:
        self.planet, self.houses, self.signs = planet, houses, signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.rasi_house in self.houses and p.sign in self.signs


class _PlanetInSignClass(C.Condition):
    """`planet`'s occupied sign is in `signs` (a sign-class set)."""
    def __init__(self, planet: str, signs: frozenset[int]) -> None:
        self.planet, self.signs = planet, signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.sign in self.signs


class _HouseSignIn(C.Condition):
    """The SIGN occupying whole-sign `house` (from the Lagna) is in `signs`."""
    def __init__(self, house: int, signs: frozenset[int]) -> None:
        self.house, self.signs = house, signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _sign_of_house(self.house, ctx.chart) in self.signs


class _ThreeConjoinInSigns(C.Condition):
    """All three planets share ONE sign, and that common sign is in `signs`."""
    def __init__(self, a: str, b: str, c: str, signs: frozenset[int]) -> None:
        self.a, self.b, self.c, self.signs = a, b, c, signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        pa = ctx.chart.planets.get(self.a)
        pb = ctx.chart.planets.get(self.b)
        pc = ctx.chart.planets.get(self.c)
        if pa is None or pb is None or pc is None:
            return False
        return pa.sign == pb.sign == pc.sign and pa.sign in self.signs


class _PairConjoinInSignsFromPlanet(C.Condition):
    """`a` and `b` share ONE sign that is in `signs`, AND that sign is one of the
    `from_houses` counted from `origin`'s rasi-house (Raman: "5th, 7th or 9th
    from the Sun")."""
    def __init__(self, a: str, b: str, signs: frozenset[int], origin: str,
                 from_houses: frozenset[int]) -> None:
        self.a, self.b, self.signs = a, b, signs
        self.origin, self.from_houses = origin, from_houses

    def evaluate(self, ctx: C.EvalContext) -> bool:
        pa = ctx.chart.planets.get(self.a)
        pb = ctx.chart.planets.get(self.b)
        po = ctx.chart.planets.get(self.origin)
        if pa is None or pb is None or po is None:
            return False
        if pa.rasi_house != pb.rasi_house or pa.sign not in self.signs:
            return False
        dist = ((pa.rasi_house - po.rasi_house) % 12) + 1
        return dist in self.from_houses


class _ConjunctAnyClass(C.Condition):
    """`planet` shares a whole-sign house with a natural planet of `klass`."""
    def __init__(self, planet: str, klass: str) -> None:
        self.planet, self.klass = planet, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        if p is None:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != self.planet and name in group and q.rasi_house == p.rasi_house
                   for name, q in ctx.chart.planets.items())


class _AfflictedBy(C.Condition):
    """`planet` is conjunct-with OR aspected-by any of `afflictors`."""
    def __init__(self, planet: str, afflictors: tuple[str, ...]) -> None:
        self.planet, self.afflictors = planet, afflictors

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        if p is None:
            return False
        for af in self.afflictors:
            q = ctx.chart.planets.get(af)
            if q is None or af == self.planet:
                continue
            if q.rasi_house == p.rasi_house:
                return True
            if drishti.aspects_planet(af, self.planet, ctx.chart):
                return True
        return False


class _LordAfflictedBy(C.Condition):
    """The lord of `house` is conjunct-with OR aspected-by any of `afflictors`
    (a lord-aware version of ``_AfflictedBy`` — the 5th lord is dynamic, so it must
    be resolved per chart rather than hard-coded to a fixed planet)."""
    def __init__(self, house: int, afflictors: tuple[str, ...]) -> None:
        self.house, self.afflictors = house, afflictors

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _AfflictedBy(_lord_of(self.house, ctx.chart), self.afflictors).evaluate(ctx)


class _SunMoonTrineToMarsSaturn(C.Condition):
    """The Sun AND the Moon each stand in a trine (5th/9th, i.e. trikona distance)
    to Mars or to Saturn — Raman's "Sun and Moon in trine to Mars and Saturn"."""
    _TRINE: Final[frozenset[int]] = frozenset({5, 9})

    def evaluate(self, ctx: C.EvalContext) -> bool:
        sun = ctx.chart.planets.get("Sun")
        moon = ctx.chart.planets.get("Moon")
        mars = ctx.chart.planets.get("Mars")
        sat = ctx.chart.planets.get("Saturn")
        if sun is None or moon is None or mars is None or sat is None:
            return False
        targets = (mars.rasi_house, sat.rasi_house)

        def trines(lum_house: int) -> bool:
            return any(((t - lum_house) % 12) + 1 in self._TRINE for t in targets)
        return trines(sun.rasi_house) and trines(moon.rasi_house)


class _LordAspectsLord(C.Condition):
    """The lord of `h1` casts a whole-sign drishti on the lord of `h2` (identity
    → False)."""
    def __init__(self, h1: int, h2: int) -> None:
        self.h1, self.h2 = h1, h2

    def evaluate(self, ctx: C.EvalContext) -> bool:
        l1, l2 = _lord_of(self.h1, ctx.chart), _lord_of(self.h2, ctx.chart)
        return l1 != l2 and drishti.aspects_planet(l1, l2, ctx.chart)


class _PlanetAspectsLord(C.Condition):
    """`planet` casts a whole-sign drishti on the lord of `house` (identity → False)."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        return lord != self.planet and drishti.aspects_planet(self.planet, lord, ctx.chart)


class _LordAspectsPlanet(C.Condition):
    """The lord of `house` casts a whole-sign drishti on `planet` (identity → False).
    The directional mirror of ``_PlanetAspectsLord`` — needed because whole-sign
    Jupiter/Mars/Saturn aspects are NOT symmetric, so "aspected BY the Nth lord"
    (Raman, HTJAH-II:9388) must be encoded as lord → planet, not planet → lord."""
    def __init__(self, house: int, planet: str) -> None:
        self.house, self.planet = house, planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        return lord != self.planet and drishti.aspects_planet(lord, self.planet, ctx.chart)


class _PlanetConjunctLord(C.Condition):
    """`planet` shares a whole-sign house with the lord of `house` (identity → False)."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        if lord == self.planet:
            return False
        return C.Conjunct(self.planet, lord).evaluate(ctx)


class _LordAspectedByClass(C.Condition):
    """The lord of `house` is aspected by some natural planet of `klass`."""
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


class _LordDebilitated(C.Condition):
    """The lord of `house` holds a debilitated compound dignity in D1."""
    def __init__(self, house: int) -> None:
        self.house = house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        return lord in ctx.chart.planets and dignity(lord, ctx.chart) == "debil"


class _LordInWaterySignKendra(C.Condition):
    """The lord of `house` sits in a watery sign AND in a kendra (1/4/7/10)."""
    def __init__(self, house: int) -> None:
        self.house = house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(_lord_of(self.house, ctx.chart))
        return p is not None and p.sign in _WATERY and p.rasi_house in _KENDRA


class _MaleficInHouseDignified(C.Condition):
    """Some natural malefic occupies `house` with an exalted / own / friendly
    (compound) dignity — Raman's "malefic in 9th be exalted, own or friendly"."""
    _GOOD: Final[frozenset[str]] = frozenset({"exalt", "own", "moolatrikona", "friend"})

    def __init__(self, house: int) -> None:
        self.house = house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return any(name in NATURAL_MALEFICS and p.rasi_house == self.house
                   and dignity(name, ctx.chart) in self._GOOD
                   for name, p in ctx.chart.planets.items())


class _MaleficOrEclipsedOrDebilInHouse(C.Condition):
    """A malefic, an eclipsed (combust), or a debilitated planet occupies `house`."""
    def __init__(self, house: int) -> None:
        self.house = house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        for name, p in ctx.chart.planets.items():
            if p.rasi_house != self.house:
                continue
            if name in NATURAL_MALEFICS:
                return True
            if p.combust_fraction > 0.0:
                return True
            if dignity(name, ctx.chart) == "debil":
                return True
        return False


class _PlanetInHouseNotWith(C.Condition):
    """Some planet occupies `house` while NONE of `excluded` is in that house —
    Raman's "planets in the 9th not associated with Mercury and Jupiter"."""
    def __init__(self, house: int, excluded: tuple[str, ...]) -> None:
        self.house, self.excluded = house, excluded

    def evaluate(self, ctx: C.EvalContext) -> bool:
        occupants = [n for n, p in ctx.chart.planets.items() if p.rasi_house == self.house]
        if not occupants:
            return False
        return not any(ex in occupants for ex in self.excluded)


class _LordOfTwelfthFromLordWatery(C.Condition):
    """The lord of the 12th sign counted FROM the sign held by the Lagna-lord
    occupies a watery sign — Raman's "lord of the 12th from the sign occupied by
    the Lagna lord is (in) a watery sign" (HTJAH-II:7505-7507)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lagna_lord = ctx.chart.planets.get(_lord_of(1, ctx.chart))
        if lagna_lord is None:
            return False
        twelfth_sign = ((lagna_lord.sign - 1 + 11) % 12) + 1
        sub_lord = ctx.chart.planets.get(SIGN_LORDS[twelfth_sign])
        return sub_lord is not None and sub_lord.sign in _WATERY


class _BeneficInHouseFromMoon(C.Condition):
    """A natural benefic occupies the `n`th whole-sign house counted from the Moon."""
    def __init__(self, n: int) -> None:
        self.n = n

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.ClassInHouseFrom("benefic", "MOON", {self.n}).evaluate(ctx)


class _LordInHouseClassFromMoon(C.Condition):
    """The lord of `house` sits in one of `from_houses` counted from the Moon."""
    def __init__(self, house: int, from_houses: frozenset[int]) -> None:
        self.house, self.from_houses = house, from_houses

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        moon = ctx.chart.planets.get("Moon")
        p = ctx.chart.planets.get(lord)
        if moon is None or p is None:
            return False
        return (((p.rasi_house - moon.rasi_house) % 12) + 1) in self.from_houses


class _SunPitrukarakaAfflicted(C.Condition):
    """The Sun (Pitru-karaka) cast into a dusthana {6,8,12} AND hemmed by papakartari (a
    natural malefic in BOTH the 2nd- and 12th-from-Sun), UNCANCELLED by neecha-bhanga ->
    early death of the father.

    Raman (HTJAH-II:7916): "Afflictions to the Sun or his occupation of malefic houses results
    in early death of father. If the 9th lord is in a kendra or the 11th... or fortified, the
    father lives long." Chart 97 (h9_13) conclusion HTJAH-II:8580: "the karaka and 9th lord Sun
    are in a dusthana ... afflicted by the papakartari yoga caused by Rahu and Saturn ... the
    father of the native died." The H9-father twin of the decisive vaidhavya rules H7.C.84/85
    (karaka cast into an evil house + a malefic aggravator). EXALTATION is NOT a relief -- Raman
    curtails an exalted-Sun-under-papakartari father too (h9_02/h9_05), so the only relief kept
    is neecha-bhanga (HTJAH-II:8157, which flips a deprivation to protection). bphs-doctrine-
    reviewer SOUND-WITH-CAVEAT (the backwards exalted-Sun guard was dropped)."""

    _DUS: Final[frozenset[int]] = frozenset({6, 8, 12})

    def evaluate(self, ctx: C.EvalContext) -> bool:
        sun = ctx.chart.planets.get("Sun")
        if sun is None or sun.rasi_house not in self._DUS:
            return False
        if not C.HemmedBy("Sun", "malefic").evaluate(ctx):
            return False
        if dignity("Sun", ctx.chart) == "debil" and neecha_bhanga("Sun", ctx.chart):
            return False
        return True


# ── RULES ─────────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ===== A. Father — from-Sun / pitru readings (HTJAH-II:7411-7456) — sig father =====
    RuleRecord(
        id="H9.A.1", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.And(_PlanetInHouseSigns("Sun", frozenset({8, 9, 11, 12}), _FIXED),
                        C.Not(_MoonAspectsHouse(1))),
        fortified=None,
        afflicted="the Sun in the 9th/8th/11th/12th in a fixed sign with the Lagna un-aspected "
                  "by the Moon → father not present at the birth (he is in his own town)",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7411)),
    RuleRecord(
        id="H9.A.2", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.And(_PlanetInHouseSigns("Sun", frozenset({8, 9, 11, 12}), _MOVABLE),
                        C.Not(_MoonAspectsHouse(1))),
        fortified=None,
        afflicted="the same Sun-position but in a movable sign → father away in a foreign "
                  "country at the birth",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7414)),
    RuleRecord(
        id="H9.A.3", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.Or(
            C.And(C.InRashiHouse("Sun", 4), C.InRashiHouse("Mars", 4), C.InRashiHouse("Saturn", 4)),
            C.And(C.InRashiHouse("Sun", 10), C.InRashiHouse("Mars", 10), C.InRashiHouse("Saturn", 10))),
        fortified=None,
        afflicted="the Sun, Mars and Saturn combining in the 4th or the 10th → a posthumous child",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7416)),
    RuleRecord(
        id="H9.A.4", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.Or(_PlanetInHouseSigns("Sun", frozenset({5}), _MALEFIC_SIGNS),
                       _PlanetInHouseSigns("Sun", frozenset({9}), _MALEFIC_SIGNS)),
        fortified=None,
        afflicted="the 5th or 9th from Lagna being a malefic sign occupied by the Sun → father "
                  "dies soon",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7420)),
    RuleRecord(
        id="H9.A.5", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.And(C.InHouseFrom("Sun", "MOON", 10),
                        C.ClassInHouseFrom("malefic", "MOON", {10})),
        fortified=None,
        afflicted="the Sun and malefics in the 10th from the Moon → early death of father",
        frame="MOON", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7425)),
    RuleRecord(
        id="H9.A.6", house=9, signification="father", group="combination", kind="evaluable",
        condition=_PairConjoinInSignsFromPlanet(
            "Saturn", "Mars", frozenset({1, 5, 11}), "Sun", frozenset({5, 7, 9})),
        fortified=None,
        afflicted="Saturn and Mars conjoining in Aries/Leo/Aquarius which is the 5th/7th/9th from "
                  "the Sun → father in some sort of captivity at the birth",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7426)),
    RuleRecord(
        id="H9.A.7", house=9, signification="father", group="combination", kind="evaluable",
        condition=_ConjunctAnyClass("Sun", "malefic"),
        fortified=None,
        afflicted="the Sun afflicted by conjunction with malefics → father's life adversely "
                  "influenced",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7429)),
    RuleRecord(
        id="H9.A.8", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.And(C.Conjunct("Moon", "Mars"), C.Conjunct("Mars", "Mercury"),
                        C.Conjunct("Mercury", "Saturn")),
        fortified=None,
        afflicted="the Moon, Mars, Mercury and Saturn together → two fathers and two mothers "
                  "(taken in adoption)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7431)),
    RuleRecord(
        id="H9.A.9", house=9, signification="father", group="combination", kind="evaluable",
        condition=_PlanetAspectsHouse("Sun", 1),
        fortified="the Sun aspecting the Ascendant → native inherits wealth from his father",
        afflicted=None,
        frame="KARAKA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7433)),
    RuleRecord(
        id="H9.A.10", house=9, signification="father", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="the 9th house OR 9th lord in a movable sign, conjunct with or aspected by "
                  "Saturn, AND the 12th lord strong → native adopted by another. Kept descriptive: "
                  "the 'strong 12th lord' clause needs a strength gate. "
                  "TODO(predicate: planet-strength gate)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7435)),
    RuleRecord(
        id="H9.A.11", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(4, 6), C.LordIn(9, 6)),
        fortified=None,
        afflicted="the 4th lord conjoining the 9th lord in the 6th → native's father a profligate",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7440)),
    RuleRecord(
        id="H9.A.12", house=9, signification="father", group="combination", kind="descriptive",
        condition=None,
        fortified="the 5th lord a benefic AND the Sun beneficially disposed → native gives "
                  "happiness to the father. Kept descriptive: 'benefic / beneficially disposed' is "
                  "a strength/disposition gate. TODO(predicate: beneficial-disposition gate)",
        afflicted=None,
        frame="KARAKA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7441)),
    RuleRecord(
        id="H9.A.13", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.Or(_AfflictedBy("Sun", ("Saturn", "Rahu")),
                       _LordAfflictedBy(5, ("Saturn", "Rahu"))),
        fortified=None,
        afflicted="the 5th lord OR the Sun afflicted by Saturn / Rahu / Mandi → native a source "
                  "of misery to the father. The 5th-lord arm is encoded faithfully via the "
                  "per-chart 5th lord (not a hard-coded planet); the Mandi/Gulika afflictor is "
                  "deferred. TODO(predicate: Mandi/Gulika)",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7443)),
    RuleRecord(
        id="H9.A.14", house=9, signification="father", group="combination", kind="descriptive",
        condition=None,
        fortified="the native's Ascendant being the same sign as that rising in the father's 10th "
                  "→ a dutiful son. Kept descriptive: requires the father's chart (synastry). "
                  "TODO(predicate: cross-chart / synastry)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7445)),
    RuleRecord(
        id="H9.A.15", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Jupiter", 9),
                        C.VargaDignity("Jupiter", "D9", {"own"})),
        fortified="Jupiter in the 9th occupying his own Navamsa → high sense of filial duty",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 7447)),
    RuleRecord(
        id="H9.A.16", house=9, signification="father", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="the Ascendants of native and father mutually in the 6th and 8th → the pair "
                  "always at variance. Kept descriptive: requires the father's chart (synastry). "
                  "TODO(predicate: cross-chart / synastry)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7449)),
    RuleRecord(
        id="H9.A.17", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.HasDignity("Sun", {"enemy"}),
        fortified=None,
        afflicted="the Sun in an inimical sign → native studiously causes pain to his father",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7450)),
    RuleRecord(
        id="H9.A.18", house=9, signification="father", group="combination", kind="evaluable",
        condition=_SunMoonTrineToMarsSaturn(),
        fortified=None,
        afflicted="the Sun and Moon in trine to Mars and Saturn → child abandoned by both parents",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7452)),
    RuleRecord(
        id="H9.A.19", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.Or(
            C.And(C.InRashiHouse("Saturn", 11), C.InRashiHouse("Mars", 11), C.InRashiHouse("Rahu", 11)),
            C.And(C.InRashiHouse("Saturn", 9), C.InRashiHouse("Mars", 9), C.InRashiHouse("Rahu", 9))),
        fortified=None,
        afflicted="Saturn, Mars and Rahu in the 11th or the 9th from Lagna → father's death",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7453)),
    RuleRecord(
        id="H9.A.20", house=9, signification="father", group="combination", kind="evaluable",
        condition=C.Or(C.And(C.InHouseClass("Sun", "kendra"), _PlanetInSignClass("Sun", _MOVABLE)),
                       C.And(C.InHouseClass("Moon", "kendra"), _PlanetInSignClass("Moon", _MOVABLE))),
        fortified=None,
        afflicted="the Sun or the Moon in a kendra in a movable sign → native will not perform "
                  "the father's last rites",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7455)),
    # DECISIVE (father): the Sun (Pitru-karaka) cast into a dusthana {6,8,12} AND hemmed by
    # papakartari (malefics flanking it), uncancelled by neecha-bhanga -> early death of the
    # father. HTJAH-II:7916; Chart-97/h9_13 conclusion HTJAH-II:8580. The H9-father twin of the
    # decisive vaidhavya rules H7.C.84/85; `father` is BIDIRECTIONAL (not an AFFLICTION_MATTER),
    # so the decisive flag is the only lever that carries the verdict past _decide's strong-
    # pillar favourable preponderance. Fires on h9_13 (target) + h9_05 (already afflicted) across
    # the H9 goldens; spares every favourable/mixed twin (zero over-fire). EXALTATION is NOT a
    # relief (h9_02/h9_05 are exalted-Sun fathers Raman still curtails). h9_02 (exalted Sun in
    # the 9th, papakartari-on-bhava + karaka-in-9th) is a distinct mechanism, deferred.
    RuleRecord(
        id="H9.A.20a", house=9, signification="father", group="combination", kind="evaluable",
        condition=_SunPitrukarakaAfflicted(),
        fortified=None,
        afflicted="the Sun (Pitru-karaka) cast into a dusthana (6th/8th/12th) and hemmed by "
                  "papakartari (malefics flanking it), uncancelled by neecha-bhanga -> the "
                  "father's longevity is curtailed; early death of the father",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7916)),

    # ===== B. Fortune / raja-yoga-ish (HTJAH-II:7460-7484) — sig fortune =====
    RuleRecord(
        id="H9.B.21", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.CountInHouse(9, 1, "benefic"),
        fortified="a benefic occupying the 9th → native is lucky",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7460)),
    RuleRecord(
        id="H9.B.22", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(9, 6), _LordAspectedByClass(9, "malefic")),
        fortified=None,
        afflicted="the 9th lord in the 6th aspected by a malefic/inimical/debilitated planet → "
                  "the person suffers in every respect",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7461)),
    RuleRecord(
        id="H9.B.23", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.Or(_LordDebilitated(9), C.CountInHouse(9, 1, "malefic")),
        fortified=None,
        afflicted="the 9th lord debilitated (in sign or Navamsa) / weak / in a malefic shashtyamsa, "
                  "OR malefics occupying the 9th → unfortunate in life. Encoded on D1 9th-lord "
                  "debility and malefics-in-9th; the malefic-shashtyamsa (D60), the 'weak' gate, "
                  "and 9th-lord-Navamsa-debility (needs a lord-aware VargaDignity not yet in the "
                  "algebra) are deferred. TODO(predicate: D60 shashtyamsa, planet-strength gate, "
                  "9th-lord-Navamsa-debility)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7463)),
    RuleRecord(
        id="H9.B.24", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=_MaleficOrEclipsedOrDebilInHouse(9),
        fortified=None,
        afflicted="a malefic, eclipsed (combust) or debilitated planet in the 9th → luckless, "
                  "poor or unprincipled",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7467)),
    RuleRecord(
        id="H9.B.25", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=_MaleficInHouseDignified(9),
        fortified="but a malefic in the 9th if exalted, in its own or a friendly sign → the "
                  "opposite (good) results",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7468)),
    RuleRecord(
        id="H9.B.26", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 9), _LordAspectsLord(10, 11)),
        fortified="the 11th lord in the 9th influenced by the 10th lord → lucky wherever he goes",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7472)),
    RuleRecord(
        id="H9.B.27", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(9, 2), _LordAspectsLord(10, 9)),
        fortified="the 9th lord in the 2nd aspected by the 10th lord → lucky wherever he goes",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7473)),
    RuleRecord(
        id="H9.B.28", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(2, 11), C.LordIn(11, 9), C.LordIn(9, 2)),
        fortified="the 2nd lord in the 11th, the 11th lord in the 9th and the 9th lord in the 2nd "
                  "→ extremely fortunate, earns well",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7474)),
    RuleRecord(
        id="H9.B.29", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.LordsConjunct(3, 9),
        fortified="the 3rd and 9th lords joining (or aspected by benefics / in benefic "
                  "signs-Navamsas) → fortune advanced through a brother. Encoded on the conjunction; "
                  "the benefic-aspect/benefic-Navamsa alternatives are deferred. "
                  "TODO(predicate: benefic-Navamsa gate)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7477)),
    RuleRecord(
        id="H9.B.30", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.LordsConjunct(5, 9),
        fortified="the 5th and 9th lords combining (or beneficially disposed by aspect/association) "
                  "→ children bring prosperity. Encoded on the conjunction; the beneficial-aspect "
                  "alternative is deferred. TODO(predicate: beneficial-disposition gate)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7479)),
    RuleRecord(
        id="H9.B.31", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.Or(_PlanetAspectsLord("Venus", 9), _PlanetAspectsLord("Jupiter", 9)),
        fortified="Venus or Jupiter in the 9th, or aspecting the 9th lord → a fortunate life. "
                  "The 'in the 9th' disjunct is already scored as the Venus/Jupiter placements "
                  "(H9.P.Venus/H9.P.Jupiter, sig fortune); this combo encodes ONLY the distinct "
                  "aspect-the-9th-lord arm (a different condition from the in-the-9th placements), "
                  "so routing it to its true matter (fortune / 'a fortunate life') is not a "
                  "double-count.",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7481)),
    RuleRecord(
        id="H9.B.32", house=9, signification="fortune", group="combination", kind="evaluable",
        condition=C.Parivartana(1, 9),
        fortified="mutual exchange of houses between the Lagna lord and the 9th lord → every kind "
                  "of fortune",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7482)),

    # ===== C. Dharma / religion / higher learning (HTJAH-II:7496-7509) =====
    RuleRecord(
        id="H9.C.33", house=9, signification="dharma", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Jupiter", 9),
                        C.Aspects("Saturn", "Moon"), C.Aspects("Saturn", "Jupiter"),
                        _PlanetAspectsHouse("Saturn", 1)),
        fortified="Jupiter in the 9th with the Moon, Jupiter and the Ascendant all aspected by "
                  "Saturn → founder of a system of philosophical thought",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7496)),
    RuleRecord(
        id="H9.C.34", house=9, signification="higher_learning", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Jupiter", 9), C.InRashiHouse("Sun", 9),
                        C.InRashiHouse("Mercury", 9)),
        fortified="Jupiter, the Sun and Mercury occupying the 9th → highly learned and wealthy",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7498)),
    RuleRecord(
        id="H9.C.35", house=9, signification="higher_learning", group="combination", kind="evaluable",
        condition=_PlanetInHouseNotWith(9, ("Mercury", "Jupiter")),
        fortified=None,
        afflicted="planets in the 9th not associated with Mercury and Jupiter → diseased, forlorn, "
                  "captivity and misery",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7507)),

    # ===== D. Travel / pilgrimage (HTJAH-II:7486-7507, 8648, 9388-9418) =====
    RuleRecord(
        id="H9.D.36", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=C.And(_LordInWaterySignKendra(9), _LordAspectedByClass(9, "benefic")),
        fortified="the 9th lord in a watery sign in a quadrant, aspected by a benefic → pilgrimage "
                  "and a dip in a sacred river",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7486)),
    RuleRecord(
        id="H9.D.37", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=_PlanetAspectsHouse("Jupiter", 9),
        fortified="Jupiter aspecting the 9th house → travels to many holy spots and religious "
                  "centres. (The 'OR the 9th and 10th lords combining' arm of HTJAH-II:7488 is "
                  "separately scored as H9.D.48, same sig long_journeys, so it is dropped here to "
                  "avoid a same-signification double-count.)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7488)),
    RuleRecord(
        id="H9.D.38", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=C.And(_BeneficInHouseFromMoon(9), _ClassAspectsHouse(9, "benefic")),
        fortified="the 9th from the Moon beneficially aspected and occupied by a benefic → a long "
                  "pilgrimage. (From-Moon occupancy encoded exactly; the 'beneficial aspect' arm "
                  "is approximated by a benefic aspect on the radical 9th. "
                  "TODO(predicate: benefic-aspect-of-house-from-Moon))",
        afflicted=None,
        frame="MOON", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7490)),
    RuleRecord(
        id="H9.D.39", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(1, 12), C.InRashiHouse("Moon", 10), C.InRashiHouse("Mars", 10),
                        _HouseSignIn(10, _MALEFIC_SIGNS)),
        fortified=None,
        afflicted="the Lagna lord in the 12th with the Moon and Mars conjoining in the 10th (a "
                  "malefic sign) → goes abroad but good fortune evades him",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7501)),
    RuleRecord(
        id="H9.D.40", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=C.And(C.Conjunct("Sun", "Moon"), C.Conjunct("Moon", "Saturn")),
        fortified=None,
        afflicted="the Sun, the Moon and Saturn in the same sign → wicked and deceitful, tries to "
                  "travel abroad",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7503)),
    RuleRecord(
        id="H9.D.41", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=_LordOfTwelfthFromLordWatery(),
        fortified="the lord of the 12th from the sign occupied by the Lagna lord being in a watery "
                  "sign → prosperous in foreign lands",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7505)),
    RuleRecord(
        id="H9.D.42", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=C.Or(_HouseSignIn(9, _DUAL), _HouseSignIn(9, _MOVABLE), _HouseSignIn(9, _WATERY)),
        fortified="common/movable signs (and watery signs) on the 9th → more capable of giving "
                  "foreign journeys (fixed signs less so)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 8648)),
    RuleRecord(
        id="H9.D.43", house=9, signification="dharma", group="combination", kind="evaluable",
        condition=C.Or(_PlanetConjunctLord("Jupiter", 10), _LordAspectsPlanet(10, "Jupiter")),
        fortified="Jupiter combined with or aspected by the 10th lord → leads one to acts of piety",
        afflicted=None,
        frame="KARAKA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9388)),
    RuleRecord(
        id="H9.D.44", house=9, signification="long_journeys", group="combination", kind="descriptive",
        condition=None,
        fortified="the 7th, 5th, 9th, 10th lords AND Jupiter combining in a watery sign → dips in "
                  "rivers as sacred as the Ganges in Jupiter Dasa. Kept descriptive: the verdict is "
                  "gated on the running Jupiter Dasa (Phase-F timing). "
                  "TODO(predicate: Dasa timing)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9389)),
    RuleRecord(
        id="H9.D.45", house=9, signification="dharma", group="combination", kind="descriptive",
        condition=None,
        fortified="in the Dasas of the 5th and 7th lords the native does NOT go on pilgrimages but "
                  "devotes time to the study of sacred lore (especially stories of Maha Vishnu). "
                  "Kept descriptive: a Dasa-timing rule (Phase-F). TODO(predicate: Dasa timing)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9393)),
    RuleRecord(
        id="H9.D.46", house=9, signification="long_journeys", group="combination", kind="descriptive",
        condition=None,
        fortified="the Dasa of the 4th lord gives pilgrimages to many holy spots. Kept descriptive: "
                  "a Dasa-timing rule (Phase-F). TODO(predicate: Dasa timing)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9396)),
    RuleRecord(
        id="H9.D.47", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=C.And(C.CountInHouse(10, 1, "malefic"), C.CountInHouse(4, 1, "malefic")),
        fortified=None,
        afflicted="malefics occupying the 10th and 4th from Lagna → native dies during his "
                  "pilgrimage to a sacred shrine",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9396)),
    RuleRecord(
        id="H9.D.48", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=C.LordsConjunct(9, 10),
        fortified="the lords of the 9th and 10th combining → a long pilgrimage",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9398)),
    RuleRecord(
        id="H9.D.49", house=9, signification="dharma", group="combination", kind="evaluable",
        condition=_PlanetAspectsHouse("Jupiter", 9),
        fortified="Jupiter's aspect on the 9th house → the good fortune of bathing in the Ganges",
        afflicted=None,
        frame="KARAKA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9400)),
    RuleRecord(
        id="H9.D.50", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=C.And(_ClassAspectsHouse(9, "benefic"),
                        C.Or(C.LordIn(9, 1), C.LordIn(9, 4), C.LordIn(9, 5), C.LordIn(9, 7),
                             C.LordIn(9, 9), C.LordIn(9, 10), C.LordIn(9, 11))),
        fortified="benefics aspecting the 9th AND the 9th lord in a trine / quadrant / 11th → a "
                  "big pilgrimage",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9415)),
    RuleRecord(
        id="H9.D.51", house=9, signification="long_journeys", group="combination", kind="evaluable",
        condition=_LordInHouseClassFromMoon(9, _KENDRA),
        fortified="the 9th lord from the Moon in a kendra → native goes to many holy spots",
        afflicted=None,
        frame="MOON", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9416)),
)
