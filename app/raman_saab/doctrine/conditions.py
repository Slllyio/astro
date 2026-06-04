"""The condition algebra (Phase 2) — `doctrine/conditions.py`.

A ``Condition`` is a composable boolean predicate over a chart, evaluated via
``.evaluate(ctx)``. Combinators ``And`` / ``Or`` / ``Not`` / ``AtLeastN`` (also
``& | ~``); leaf predicates read the Phase-1 primitives + ``doctrine.drishti``.
RuleRecords (next) hold a ``Condition`` tree and fire it against a chart.

Predicate roadmap (predicate_audit §7). **This module is the FIRST batch:**
absolute, Lagna-frame, D1 leaves. **Still to add (next sessions):**
- frame-relative origins — `FROM(origin)`, MOON / KARAKA / STRONGEST_OF (C1);
- varga overlays — `InVargaHouseFrom`, `VargaHouseDist` (C2);
- nakshatra (C3), aggregates `Strongest`/`CountInHouse` (H10), sphutas, `Parivartana`/
  `Exchange` (C6), `HemmedBy` (H1), `InHouseClass` (H6), MoonPhase (H4).

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
from app.raman_saab.primitives.bhangas import neecha_bhanga
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import is_yogakaraka


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
