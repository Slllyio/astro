"""The condition algebra (Phase 2) — `doctrine/conditions.py`.

A ``Condition`` is a composable boolean predicate over a chart, evaluated via
``.evaluate(ctx)``. Combinators ``And`` / ``Or`` / ``Not`` / ``AtLeastN`` (also
``& | ~``); leaf predicates read the Phase-1 primitives + ``doctrine.drishti``.
RuleRecords (next) hold a ``Condition`` tree and fire it against a chart.

Predicate roadmap (predicate_audit §7). **Implemented:** combinators; absolute Lagna/D1
leaves; frame-relative `InHouseFrom` (C1: LAGNA/MOON/planet/house origins); `InHouseClass`
(H6); `Parivartana`/`Exchange` (C6); `HemmedBy` (H1); `MutualAspect`; `FunctionalNature`
(C4); `InStarOf` (C3); `MoonPhase` (H4); `CountInHouse` (H10); `Vargottama`/`NeechaBhanga`.
**Still to add:** varga overlays `InVargaHouseFrom`/`VargaHouseDist` (C2); KARAKA /
STRONGEST_OF / KARAKAMSA origins; `Strongest`/`Weakest` (Shadbala aggregates); `TaraOf`;
sphuta/Saham predicates; `ShashtiamsaClass`/`VaiseshikamsaGrade` (H5).

Usage:
    from app.raman_saab.doctrine import conditions as C
    rule = C.And(C.InRashiHouse("Saturn", 7), C.Aspects("Mars", "Saturn"))
    rule.evaluate(C.EvalContext(chart))   # -> bool
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti
from app.raman_saab.primitives import bhangas, nakshatra
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS, functional_nature, is_yogakaraka)
from app.raman_saab.primitives.bhangas import neecha_bhanga

# House classes (whole-sign, from the Lagna).
_HOUSE_CLASS: dict[str, frozenset[int]] = {
    "kendra": frozenset({1, 4, 7, 10}), "trikona": frozenset({1, 5, 9}),
    "dusthana": frozenset({6, 8, 12}), "upachaya": frozenset({3, 6, 10, 11}),
    "maraka": frozenset({2, 7})}


def _origin_house(origin: object, chart: RamanChart) -> int | None:
    """Resolve a frame origin to a whole-sign house (1..12). origin ∈ {"LAGNA","MOON",
    planet name, int house}. Returns None if a referenced planet is absent."""
    if origin == "LAGNA":
        return 1
    if origin == "MOON":
        m = chart.planets.get("Moon")
        return m.rasi_house if m else None
    if isinstance(origin, int):
        return ((origin - 1) % 12) + 1
    p = chart.planets.get(origin)          # a planet name
    return p.rasi_house if p else None


def _house_from(rasi_house: int, origin_house: int) -> int:
    """Whole-sign house of `rasi_house` counted from `origin_house` (1..12)."""
    return ((rasi_house - origin_house) % 12) + 1


@dataclass(frozen=True)
class EvalContext:
    """The chart a condition is evaluated against. (Frame/varga overlays land here next.)"""
    chart: RamanChart


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
        lord = SIGN_LORDS[((ctx.chart.asc_sign - 1) + (self.house - 1)) % 12 + 1]
        p = ctx.chart.planets.get(lord)
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
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.combust_fraction > 0.0


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
        p = ctx.chart.planets.get(self.planet)
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
