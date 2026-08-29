"""Shared chart-fact helpers for the synthesis engines — the house/sign idioms, once.

Every synthesis engine needs the same handful of chart derivations: each body's sign, a house's sign
and its lord, who occupies or aspects a house. These are one-liners, but writing them once keeps the
whole-sign idiom (`((asc_sign - 1 + house - 1) % 12) + 1`) and the node-drishti convention in a
single place the tests can pin, rather than re-deriving them in five modules.
"""
from __future__ import annotations

from typing import Mapping

from app.parashara.chart.cast import ParasharaChart
from app.parashara.primitives.graha_drishti import aspects_sign
from app.parashara.primitives.relationships import SIGN_LORDS

#: Grahas that cast graha-drishti in this BPHS-root engine — the seven visible planets; the nodes
#: cast no aspect (BPHS ch.26), so they are excluded from aspect scans (they still OCCUPY signs).
ASPECTING_GRAHAS: frozenset[str] = frozenset(
    {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"})


def sign_of(longitude: float) -> int:
    """The rasi (1..12) a longitude falls in."""
    return int(longitude % 360.0 // 30) + 1


def planet_signs(chart: ParasharaChart) -> dict[str, int]:
    """Every body's sign (1..12), nodes included."""
    return {body: sign_of(lon) for body, lon in chart.longitudes.items()}


def house_sign(asc_sign: int, house: int) -> int:
    """The rasi (1..12) that is the `house`-th bhava for `asc_sign` (whole-sign)."""
    return ((asc_sign - 1 + house - 1) % 12) + 1


def house_of_sign(asc_sign: int, sign: int) -> int:
    """Which bhava (1..12) a given rasi is, for `asc_sign` (whole-sign)."""
    return ((sign - asc_sign) % 12) + 1


def house_lord(asc_sign: int, house: int) -> str:
    """The graha lording the `house`-th bhava's sign."""
    return SIGN_LORDS[house_sign(asc_sign, house)]


def occupants(chart: ParasharaChart, house: int, *, signs: Mapping[str, int] | None = None
              ) -> tuple[str, ...]:
    """The bodies (nodes included) occupying the `house`-th bhava."""
    signs = signs or planet_signs(chart)
    target = house_sign(chart.asc_sign, house)
    return tuple(b for b, s in signs.items() if s == target)


def aspectors(chart: ParasharaChart, house: int, *, signs: Mapping[str, int] | None = None
              ) -> tuple[str, ...]:
    """The grahas casting a full graha-drishti on the `house`-th bhava (nodes excluded — no drishti)."""
    signs = signs or planet_signs(chart)
    target = house_sign(chart.asc_sign, house)
    return tuple(g for g in ASPECTING_GRAHAS
                 if g in signs and aspects_sign(g, signs[g], target))
