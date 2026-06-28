"""The condition algebra (Phase 2) — `doctrine/conditions.py`.

A ``Condition`` is a composable boolean predicate over a chart, evaluated via
``.evaluate(ctx)``. Combinators ``And`` / ``Or`` / ``Not`` / ``AtLeastN`` (also
``& | ~``); leaf predicates read the Phase-1 primitives + ``doctrine.drishti``.
RuleRecords (next) hold a ``Condition`` tree and fire it against a chart.

Predicate roadmap (predicate_audit §7). **Implemented:** combinators; absolute Lagna/D1
leaves; frame-relative `InHouseFrom` (C1: LAGNA/MOON/planet/house/"LORD_OF:n" origins);
`InHouseClass` (H6); `Parivartana`/`Exchange` (C6); `HemmedBy` (H1); `MutualAspect`;
`FunctionalNature` (C4); `InStarOf` (C3); `MoonPhase` (H4); `CountInHouse` (H10);
`Vargottama`/`NeechaBhanga`; varga overlays `InVargaHouseFrom`/`VargaDignity` (C2, D9);
Dwirdwadasha `PlanetPairIn2_12`/`AllPlanetsInDwirdwadasha` (H7); `LordsConjunct`;
sign-class data `SUSHKA_SIGNS`/`WATERY_SIGNS` (+ `SignIsSushka`/`SignIsWatery`).
**Still to add:** KARAKA / STRONGEST_OF / KARAKAMSA origins; `Strongest`/`Weakest`
(Shadbala aggregates); `TaraOf`; sphuta/Saham predicates; `ShashtiamsaClass`/
`VaiseshikamsaGrade` (H5).

Usage:
    from app.raman_saab.doctrine import conditions as C
    rule = C.And(C.InRashiHouse("Saturn", 7), C.Aspects("Mars", "Saturn"))
    rule.evaluate(C.EvalContext(chart))   # -> bool
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.varga import navamsa_sign as _navamsa_sign
from app.raman_saab.doctrine import drishti
from app.raman_saab.primitives import bhangas, nakshatra
from app.raman_saab.primitives import relationships as _rel
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS, Nature,
    compute_functional_nature, functional_nature, is_yogakaraka)
from app.raman_saab.primitives.bhangas import neecha_bhanga

# House classes (whole-sign, from the Lagna).
_HOUSE_CLASS: dict[str, frozenset[int]] = {
    "kendra": frozenset({1, 4, 7, 10}), "trikona": frozenset({1, 5, 9}),
    "dusthana": frozenset({6, 8, 12}), "upachaya": frozenset({3, 6, 10, 11}),
    "maraka": frozenset({2, 7})}


_LORD_OF_PREFIX = "LORD_OF:"


def _lord_of(house: int, chart: RamanChart) -> str:
    """Name of the D1 lord of whole-sign `house` (1..12) counted from the Lagna."""
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _parse_lord_of(origin: str) -> int:
    """House number out of a "LORD_OF:n" origin string, wrapped to 1..12 (mirrors the
    int-origin modulo). A malformed suffix is an encoding bug -> ValueError."""
    try:
        n = int(origin[len(_LORD_OF_PREFIX):])
    except ValueError as exc:
        raise ValueError(
            f"malformed LORD_OF origin {origin!r}; expected 'LORD_OF:<house 1..12>'"
        ) from exc
    return ((n - 1) % 12) + 1


def _resolve_planet(name: str, chart: RamanChart) -> str:
    """Resolve a SUBJECT-planet reference to an actual planet name. A static name passes
    through unchanged; a "LORD_OF:n" reference resolves to the D1 lord of house n (chart-
    dependent). This closes the G13 gap: varga predicates (InVargaHouseFrom / VargaDignity /
    Vargottama) can now take a dynamically-resolved house lord as their subject planet, not only
    as their origin — activating Raman's cited "Lagnadhipati in the 6/8/12 in the Navamsha"
    qualifier rules (HTJAH-I:1709-1789)."""
    if isinstance(name, str) and name.startswith(_LORD_OF_PREFIX):
        return _lord_of(_parse_lord_of(name), chart)
    return name


def _origin_house(origin: object, chart: RamanChart) -> int | None:
    """Resolve a frame origin to a whole-sign house (1..12). origin ∈ {"LAGNA","MOON",
    "LORD_OF:n", planet name, int house}. Returns None if a referenced planet is absent.

    "LORD_OF:n" (string form, e.g. "LORD_OF:2") resolves to the rasi-house of the D1
    lord of whole-sign house `n` counted from the Lagna; `n` wraps modulo 12 exactly
    like int origins. The string form keeps origins homogeneous (str | int) and
    serialisable in rule dumps."""
    if origin == "LAGNA":
        return 1
    if origin == "MOON":
        m = chart.planets.get("Moon")
        return m.rasi_house if m else None
    if isinstance(origin, int):
        return ((origin - 1) % 12) + 1
    if isinstance(origin, str) and origin.startswith(_LORD_OF_PREFIX):
        p = chart.planets.get(_lord_of(_parse_lord_of(origin), chart))
        return p.rasi_house if p else None
    p = chart.planets.get(origin)          # a planet name
    return p.rasi_house if p else None


def _origin_varga_sign(origin: object, chart: RamanChart) -> int | None:
    """The D9 mirror of `_origin_house`: resolve a frame origin to its NAVAMSA sign
    (1..12). "LAGNA" -> navamsa of the ascendant degree; "MOON"/planet name -> that
    planet's `navamsa_sign`; int n -> the nth sign from the navamsa Lagna;
    "LORD_OF:n" -> the navamsa sign held by the D1 lord of house n (Raman's "in the
    Navamsha from the sign held by the 2nd lord", HTJAH-I:1717-1718). Returns None
    if a referenced planet is absent (sparse Track-B charts)."""
    if origin == "LAGNA":
        return _navamsa_sign(chart.asc_lon)
    if origin == "MOON":
        m = chart.planets.get("Moon")
        return m.navamsa_sign if m else None
    if isinstance(origin, int):
        nav_lagna = _navamsa_sign(chart.asc_lon)
        return ((nav_lagna - 1) + (origin - 1)) % 12 + 1
    if isinstance(origin, str) and origin.startswith(_LORD_OF_PREFIX):
        p = chart.planets.get(_lord_of(_parse_lord_of(origin), chart))
        return p.navamsa_sign if p else None
    p = chart.planets.get(origin)          # a planet name
    return p.navamsa_sign if p else None


def _house_from(rasi_house: int, origin_house: int) -> int:
    """Whole-sign house of `rasi_house` counted from `origin_house` (1..12)."""
    return ((rasi_house - origin_house) % 12) + 1


@dataclass
class EvalContext:
    """The chart a condition is evaluated against. (Frame/varga overlays land here next.)

    ``chart`` is the only required constructor argument; it is read-only by convention.
    ``_cache`` is an internal memo store populated lazily via :meth:`get_or_compute` —
    do NOT access it directly.  Phase-added computed fields (functional nature,
    parivartana pairs, varga charts, sahams, longevity) should always go through
    ``get_or_compute`` so they are calculated at most once per context instance.
    """
    chart: RamanChart
    _cache: dict[str, Any] = field(default_factory=dict, compare=False, hash=False, repr=False)

    # A3 — lazy memo ----------------------------------------------------------
    def get_or_compute(self, key: str, compute_fn: Callable[[], Any]) -> Any:
        """Return the cached value for `key`, or call `compute_fn()`, cache, and return it.

        ``compute_fn`` must be a zero-argument callable.  Storing ``None`` is
        supported — a sentinel distinct from 'not yet computed' is used internally.
        """
        _MISSING = object.__new__(object)  # local sentinel type unused for check
        if key not in self._cache:
            self._cache[key] = compute_fn()
        return self._cache[key]

    # A2 — per-Lagna functional nature ----------------------------------------
    def functional_nature(self, planet: str) -> Nature:
        """Per-Lagna functional nature of `planet` for this chart's ascendant.

        Returns one of ``"benefic" | "malefic" | "neutral" | "yogakaraka" | "maraka"``.
        Result is memoised via :meth:`get_or_compute`.
        Source: HTJAH-I:523-604 + yogakaraka overlay.
        """
        return self.get_or_compute(
            f"_fn_{planet}",
            lambda: compute_functional_nature(self.chart.asc_sign, planet),
        )


class Condition(ABC):
    @abstractmethod
    def evaluate(self, ctx: EvalContext) -> bool: ...

    def __and__(self, other: "Condition") -> "Condition":
        return And(self, other)

    def __or__(self, other: "Condition") -> "Condition":
        return Or(self, other)

    def __invert__(self) -> "Condition":
        return Not(self)


# ── combinators ──────────────────────────────────────────────────────────────
class And(Condition):
    def __init__(self, *conds: Condition) -> None:
        self.conds: tuple[Condition, ...] = conds

    def evaluate(self, ctx: EvalContext) -> bool:
        return all(c.evaluate(ctx) for c in self.conds)


class Or(Condition):
    def __init__(self, *conds: Condition) -> None:
        self.conds: tuple[Condition, ...] = conds

    def evaluate(self, ctx: EvalContext) -> bool:
        return any(c.evaluate(ctx) for c in self.conds)


class Not(Condition):
    def __init__(self, cond: Condition) -> None:
        self.cond = cond

    def evaluate(self, ctx: EvalContext) -> bool:
        return not self.cond.evaluate(ctx)


class AtLeastN(Condition):
    def __init__(self, n: int, conds: Sequence[Condition]) -> None:
        self.n, self.conds = n, tuple(conds)

    def evaluate(self, ctx: EvalContext) -> bool:
        return sum(c.evaluate(ctx) for c in self.conds) >= self.n


# ── leaf predicates (absolute, Lagna-frame, D1) ──────────────────────────────
class InRashiHouse(Condition):
    """Planet occupies whole-sign house `house` (1..12 from the Lagna)."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.rasi_house == self.house


class InHouse(Condition):
    """Planet occupies Chalita bhava `house` (cusp-based — the result frame)."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.bhava == self.house


class InSign(Condition):
    def __init__(self, planet: str, sign: int) -> None:
        self.planet, self.sign = planet, sign

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.sign == self.sign


class LordIn(Condition):
    """The lord of whole-sign house `house` occupies whole-sign house `in_house`."""
    def __init__(self, house: int, in_house: int) -> None:
        self.house, self.in_house = house, in_house

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(_lord_of(self.house, ctx.chart))
        return p is not None and p.rasi_house == self.in_house


class Conjunct(Condition):
    """Two planets share a whole-sign house."""
    def __init__(self, a: str, b: str) -> None:
        self.a, self.b = a, b

    def evaluate(self, ctx: EvalContext) -> bool:
        pa, pb = ctx.chart.planets.get(self.a), ctx.chart.planets.get(self.b)
        return pa is not None and pb is not None and pa.rasi_house == pb.rasi_house


class Aspects(Condition):
    """Planet `a` casts a (whole-sign) aspect on planet `b` (drishti; nodes 7th-only)."""
    def __init__(self, a: str, b: str) -> None:
        self.a, self.b = a, b

    def evaluate(self, ctx: EvalContext) -> bool:
        return drishti.aspects_planet(self.a, self.b, ctx.chart)


class HasDignity(Condition):
    """Planet's compound dignity is one of `states` (e.g. {'exalt','own','moolatrikona'})."""
    def __init__(self, planet: str, states: set[str]) -> None:
        self.planet, self.states = planet, states

    def evaluate(self, ctx: EvalContext) -> bool:
        return self.planet in ctx.chart.planets and dignity(self.planet, ctx.chart) in self.states


class Retrograde(Condition):
    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.retrograde


class Combust(Condition):
    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: EvalContext) -> bool:
        # Substantially combust: combust_fraction >= 0.5 (within half the orb). One threshold for the
        # whole engine, matching the judge's affliction bar (_COMBUST_HARD_FRACTION / B7 doctrine) --
        # a planet barely inside its orb (e.g. ~13 deg from the Sun) is not treated as afflicted.
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.combust_fraction >= 0.5


class IsYogaKaraka(Condition):
    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: EvalContext) -> bool:
        return is_yogakaraka(self.planet, ctx.chart.asc_sign)


class NeechaBhanga(Condition):
    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: EvalContext) -> bool:
        return neecha_bhanga(self.planet, ctx.chart)


class Vargottama(Condition):
    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(_resolve_planet(self.planet, ctx.chart))
        return p is not None and p.vargottama


# ── frame-relative (C1, the most-recurrent gap) ──────────────────────────────
class InHouseFrom(Condition):
    """Planet is in the `n`th whole-sign house counted from `origin`
    (origin ∈ {"LAGNA","MOON", planet name, int house})."""
    def __init__(self, planet: str, origin: object, n: int) -> None:
        self.planet, self.origin, self.n = planet, origin, n

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        oh = _origin_house(self.origin, ctx.chart)
        return p is not None and oh is not None and _house_from(p.rasi_house, oh) == self.n


class InHouseClass(Condition):
    """Planet sits in a house of class `klass` ∈ {kendra,trikona,dusthana,upachaya,maraka} (H6)."""
    def __init__(self, planet: str, klass: str) -> None:
        self.planet, self.klass = planet, klass

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.rasi_house in _HOUSE_CLASS[self.klass]


class ClassInHouseFrom(Condition):
    """Any planet of `klass` ∈ {"malefic","benefic"} sits in one of `houses` counted from
    `origin` (e.g. a malefic in the 4/8/12 from Venus). C1 + class quantifier."""
    def __init__(self, klass: str, origin: object, houses: set[int]) -> None:
        self.klass, self.origin, self.houses = klass, origin, houses

    def evaluate(self, ctx: EvalContext) -> bool:
        oh = _origin_house(self.origin, ctx.chart)
        if oh is None:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name in group and _house_from(p.rasi_house, oh) in self.houses
                   for name, p in ctx.chart.planets.items())


# ── varga overlays (C2, D9 only for now) ─────────────────────────────────────
_SUPPORTED_VARGAS = frozenset({"D9"})

# Varga dignity vocabulary. NOTE: 'moolatrikona' is deliberately absent — it is a
# D1 degree-range concept (sign + degree span, primitives.relationships.MOOLATRIKONA);
# a navamsa position carries no degree-within-sign, so it cannot be tested in a varga.
_VARGA_DIGNITY_STATES = frozenset({"exalt", "debil", "own", "friend", "neutral", "enemy"})


def _check_varga(varga: str) -> None:
    if varga not in _SUPPORTED_VARGAS:
        raise ValueError(f"unsupported varga {varga!r}; supported: {sorted(_SUPPORTED_VARGAS)}")


class InVargaHouseFrom(Condition):
    """Planet sits in one of `houses` counted IN the varga chart from the varga
    position of `origin` — BOTH endpoints are D9 positions. This is Raman's usage:
    "if he occupies 6th, 8th or 12th in the Navamsha from the sign held by the 2nd
    lord" (HTJAH-I:1714-1718) and "the lord of Lagna is in the 12th in the Navamsha"
    (HTJAH-I:1709-1712). Origins mirror `_origin_house`, resolved on the D9 side:
    "LAGNA" = the navamsa Lagna (navamsa of the ascendant degree); "MOON"/planet
    name = that planet's navamsa sign; int n = the nth sign from the navamsa Lagna;
    "LORD_OF:n" = the D1 lord of house n located by its navamsa sign. `houses` is a
    single int or an iterable of ints. Only varga="D9" is implemented (constructor
    raises for anything else)."""
    def __init__(self, planet: str, origin: object, houses: int | Sequence[int] | set[int],
                 varga: str = "D9") -> None:
        _check_varga(varga)
        self.planet, self.origin, self.varga = planet, origin, varga
        self.houses: frozenset[int] = (
            frozenset({houses}) if isinstance(houses, int) else frozenset(houses))

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(_resolve_planet(self.planet, ctx.chart))
        ov = _origin_varga_sign(self.origin, ctx.chart)
        return (p is not None and ov is not None
                and _house_from(p.navamsa_sign, ov) in self.houses)


def _varga_dignity(planet: str, nav_sign: int) -> str:
    """Dignity from the D9 sign alone ∈ {exalt, debil, own, friend, neutral, enemy}.
    friend/neutral/enemy use the NAISARGIKA (natural) relation to the D9 sign's lord
    only — temporal friendship is a D1 rasi-house-distance concept and would smuggle
    D1 state into a varga predicate. Nodes are 'neutral' (Raman judges them by sign/
    conjunction, not dignity — mirrors primitives.dignity)."""
    if planet in ("Rahu", "Ketu"):
        return "neutral"
    if nav_sign == _rel.EXALTATION[planet][0]:
        return "exalt"
    if nav_sign == _rel.DEBILITATION[planet][0]:
        return "debil"
    lord = SIGN_LORDS[nav_sign]
    if lord == planet:
        return "own"
    return _rel.naisargika(planet, lord)


class VargaDignity(Condition):
    """Planet's D9-sign dignity is one of `states` ⊆ {exalt, debil, own, friend,
    neutral, enemy} (C2). 'moolatrikona' is rejected at construction — see
    `_varga_dignity`. Only varga="D9" is implemented."""
    def __init__(self, planet: str, varga: str, states: set[str]) -> None:
        _check_varga(varga)
        unknown = set(states) - _VARGA_DIGNITY_STATES
        if unknown:
            raise ValueError(f"unsupported varga dignity states {sorted(unknown)}; "
                             f"allowed: {sorted(_VARGA_DIGNITY_STATES)}")
        self.planet, self.varga, self.states = planet, varga, frozenset(states)

    def evaluate(self, ctx: EvalContext) -> bool:
        subj = _resolve_planet(self.planet, ctx.chart)
        p = ctx.chart.planets.get(subj)
        return p is not None and _varga_dignity(subj, p.navamsa_sign) in self.states


# ── relations (C6, H1, mutual) ───────────────────────────────────────────────
class MutualAspect(Condition):
    def __init__(self, a: str, b: str) -> None:
        self.a, self.b = a, b

    def evaluate(self, ctx: EvalContext) -> bool:
        return drishti.mutual_aspect(self.a, self.b, ctx.chart)


class Parivartana(Condition):
    """Exchange between the lords of houses h1 and h2 (C6)."""
    def __init__(self, h1: int, h2: int) -> None:
        self.h1, self.h2 = h1, h2

    def evaluate(self, ctx: EvalContext) -> bool:
        return bhangas.parivartana(self.h1, self.h2, ctx.chart)


class Exchange(Condition):
    """Two planets each occupy a sign owned by the other (C6)."""
    def __init__(self, a: str, b: str) -> None:
        self.a, self.b = a, b

    def evaluate(self, ctx: EvalContext) -> bool:
        return bhangas.exchange(self.a, self.b, ctx.chart)


def _in_2_12(h1: int, h2: int) -> bool:
    """Mutual Dwirdwadasha: `h1` is 2nd or 12th counted from `h2` (symmetric)."""
    return _house_from(h1, h2) in (2, 12)


class PlanetPairIn2_12(Condition):
    """`p1` and `p2` sit 2nd/12th from each other by rasi house — the Dwirdwadasha
    pair (H7). Symmetric by construction (one is always 2nd and the other 12th).
    Nodes count as placed. Source: HTJAH-I:1139-1140 ("DwirdwaDasha positions
    (12th and 2nd from each other)")."""
    def __init__(self, p1: str, p2: str) -> None:
        self.p1, self.p2 = p1, p2

    def evaluate(self, ctx: EvalContext) -> bool:
        a, b = ctx.chart.planets.get(self.p1), ctx.chart.planets.get(self.p2)
        return a is not None and b is not None and _in_2_12(a.rasi_house, b.rasi_house)


class AllPlanetsInDwirdwadasha(Condition):
    """Chart-wide Dwirdwadasha web — the rule #34 aggregate (the AFFLICTION form).

    Raman, HTJAH-I:1137-1140: "that horoscope is a fortunate one in which planets
    are not disposed in DwirdwaDasha positions (12th and 2nd from each other)." His
    worked usage never demands a literal EVERY-planet web: he diagnoses the
    affliction when *"almost all"* / *"most of the planets"* fall in mutual 2/12
    (Chart 18, HTJAH-I:1981: "almost all planets are disposed in DwirdwaDasha ...";
    Chart 31, HTJAH-I:2223: "all the planets are disposed in the 2nd and 12th ...
    indicate ... lack of happiness"). A single isolated planet must NOT exonerate
    an otherwise web-bound chart — under the literal "every planet" reading the
    fortunate negation ``~AllPlanetsInDwirdwadasha`` was almost always True (one
    lone planet breaks the strict web), so it carried no information.

    Encoded as the corpus "almost all" threshold: True iff the chart holds at least
    two placed bodies (nodes included as placed) AND at MOST ONE planet lacks a 2/12
    partner — i.e. >= N-1 of the N planets each sit 2nd/12th from at least one other.
    Rule #34's fortunate form is the negation; the stricter zero-pair reading stays
    composable from ``PlanetPairIn2_12``.
    Fewer than two planets (sparse Track-B) -> False."""
    def evaluate(self, ctx: EvalContext) -> bool:
        houses = [p.rasi_house for p in ctx.chart.planets.values()]
        n = len(houses)
        if n < 2:
            return False
        unpaired = sum(
            0 if any(_in_2_12(h, other) for j, other in enumerate(houses) if j != i)
            else 1
            for i, h in enumerate(houses))
        # "Almost all": the web binds the chart when at most one planet is isolated.
        return unpaired <= 1


class LordsConjunct(Condition):
    """The D1 lord of house `h1` and the lord of house `h2` (both counted whole-sign
    from the Lagna) occupy the same rasi. Backs rule #1 ("lord of birth with the
    lord of 6, 8 or 12") and the #40-#65 lords-conjunct family. If ONE planet lords
    both houses (e.g. Venus for houses 1 and 6 of a Taurus Lagna) that is identity
    lordship, not a conjunction of two lords -> False by convention (rules that
    care about dual lordship need a dedicated predicate). Missing lords on sparse
    Track-B charts -> False."""
    def __init__(self, h1: int, h2: int) -> None:
        self.h1, self.h2 = h1, h2

    def evaluate(self, ctx: EvalContext) -> bool:
        l1, l2 = _lord_of(self.h1, ctx.chart), _lord_of(self.h2, ctx.chart)
        if l1 == l2:
            return False
        p1, p2 = ctx.chart.planets.get(l1), ctx.chart.planets.get(l2)
        return p1 is not None and p2 is not None and p1.sign == p2.sign


class HemmedBy(Condition):
    """Papakartari/Subhakartari: both the 2nd and 12th from `target` hold a planet of
    `klass` ∈ {"malefic","benefic"} (H1)."""
    def __init__(self, target: str, klass: str) -> None:
        self.target, self.klass = target, klass

    def evaluate(self, ctx: EvalContext) -> bool:
        t = ctx.chart.planets.get(self.target)
        if t is None:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        second = (t.rasi_house % 12) + 1
        twelfth = ((t.rasi_house - 2) % 12) + 1
        houses = {n: False for n in (second, twelfth)}
        for name, p in ctx.chart.planets.items():
            if name != self.target and name in group and p.rasi_house in houses:
                houses[p.rasi_house] = True
        return all(houses.values())


# ── functional nature (C4) & nakshatra (C3) ──────────────────────────────────
class FunctionalNature(Condition):
    """Planet's per-Lagna functional nature ∈ `natures` (e.g. {"benefic","yogakaraka"})."""
    def __init__(self, planet: str, natures: set[str]) -> None:
        self.planet, self.natures = planet, natures

    def evaluate(self, ctx: EvalContext) -> bool:
        return (self.planet in ctx.chart.planets
                and functional_nature(self.planet, ctx.chart) in self.natures)


class InStarOf(Condition):
    """Planet occupies a nakshatra ruled by `lord` (C3)."""
    def __init__(self, planet: str, lord: str) -> None:
        self.planet, self.lord = planet, lord

    def evaluate(self, ctx: EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and nakshatra.nakshatra_lord(p.nakshatra) == self.lord


# ── luminary (H4) & aggregates (H10) ─────────────────────────────────────────
class MoonPhase(Condition):
    """Moon is waxing (Sukla, Moon−Sun < 180) or waning (Krishna). `phase` ∈ {waxing,waning}."""
    def __init__(self, phase: str) -> None:
        self.phase = phase

    def evaluate(self, ctx: EvalContext) -> bool:
        moon, sun = ctx.chart.planets.get("Moon"), ctx.chart.planets.get("Sun")
        if moon is None or sun is None:
            return False
        waxing = (moon.lon - sun.lon) % 360.0 < 180.0
        return waxing if self.phase == "waxing" else not waxing


class CountInHouse(Condition):
    """At least `n` planets sit in whole-sign house `house`, optionally filtered to
    `klass` ∈ {"malefic","benefic", None} (H10)."""
    def __init__(self, house: int, n: int, klass: str | None = None) -> None:
        self.house, self.n, self.klass = house, n, klass

    def evaluate(self, ctx: EvalContext) -> bool:
        group = (NATURAL_MALEFICS if self.klass == "malefic"
                 else NATURAL_BENEFICS if self.klass == "benefic" else None)
        count = sum(1 for name, p in ctx.chart.planets.items()
                    if p.rasi_house == self.house and (group is None or name in group))
        return count >= self.n


# ── sign-class data (constitution rules, HTJAH-I:1105-1114) ──────────────────
# Raman's lean/stout constitution passage: "Sushka planets are the Sun, Mars and
# Saturn" (HTJAH-I:1105-1106); "Sushka Rashis (signs owned by Mars, Saturn and the
# Sun)" = Aries, Leo, Scorpio, Capricorn, Aquarius (HTJAH-I:1106-1107); corpulence
# "if ascendant be Cancer, Scorpio, or Pisces with good planets" (HTJAH-I:1109);
# "watery planet (Venus and the Moon)" (HTJAH-I:1109-1110).
# NOTE: Scorpio (8) belongs to BOTH sets — Sushka by Mars-ownership, watery by element.
SUSHKA_PLANETS: frozenset[str] = frozenset({"Sun", "Mars", "Saturn"})
SUSHKA_SIGNS: frozenset[int] = frozenset({1, 5, 8, 10, 11})
WATERY_PLANETS: frozenset[str] = frozenset({"Venus", "Moon"})
WATERY_SIGNS: frozenset[int] = frozenset({4, 8, 12})


def SignIsSushka(sign: int) -> bool:  # noqa: N802 — predicate-namespace naming
    """`sign` (1..12) is a Sushka (dry) rashi — owned by Mars, Saturn or the Sun
    (HTJAH-I:1106-1107). Plain accessor, not a Condition: constitution rules test
    the ascendant sign, which is available directly on the chart."""
    return sign in SUSHKA_SIGNS


def SignIsWatery(sign: int) -> bool:  # noqa: N802 — predicate-namespace naming
    """`sign` (1..12) is a watery rashi — Cancer, Scorpio or Pisces (HTJAH-I:1109)."""
    return sign in WATERY_SIGNS
