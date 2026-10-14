"""Shared chart-fact helpers for the synthesis engines — the house/sign idioms, once.

Every synthesis engine needs the same handful of chart derivations: each body's sign, a house's sign
and its lord, who occupies or aspects a house. These are one-liners, but writing them once keeps the
whole-sign idiom (`((asc_sign - 1 + house - 1) % 12) + 1`) and the node-drishti convention in a
single place the tests can pin, rather than re-deriving them in five modules.
"""
from __future__ import annotations

from typing import Mapping

from app.parashara.chart.cast import ParasharaChart
from app.parashara.primitives.functional_nature import (
    FIXED_BENEFICS, FIXED_MALEFICS, natural_benefic)
from app.parashara.primitives.graha_drishti import aspects_sign
from app.parashara.primitives.relationships import SIGN_LORDS

#: Grahas that cast graha-drishti in this BPHS-root engine — the seven visible planets. The nodes
#: cast NO aspect: BPHS-26:47 assigns drishti to the seven planets only, and this engine encodes
#: Parashara's text. This is a DELIBERATE, SCOPED exception to the platform-wide locked convention
#: (Rahu/Ketu Jupiter-style 5/9, modern Sukra Nadi) — that lock governs the Raman engine; the
#: parashara engine's charter is fidelity to BPHS itself (user decision 2026-08-29). Nodes still
#: OCCUPY signs and can BE aspected.
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


def functioning_malefics(chart: ParasharaChart, *, signs: Mapping[str, int] | None = None
                         ) -> frozenset[str]:
    """The grahas acting as natural malefics IN THIS CHART (BPHS-3:187) — the affliction set.

    BPHS-3 sl.11 makes two of the malefics conditional, so a fixed set under-afflicts: the
    DECREASING Moon is a malefic (unless rescued by a benefic's company or aspect, BPHS-3:208 —
    translator's note), and Mercury turns malefic when he joins one. Delegates the doctrine to
    `functional_nature.natural_benefic`; this merely feeds it each graha's chart context
    (paksha, same-sign companions, a benefic's aspect).
    """
    signs = signs or planet_signs(chart)
    out = set(FIXED_MALEFICS)
    for planet in ("Moon", "Mercury"):
        if planet not in signs:
            continue
        companions = tuple(b for b, s in signs.items() if s == signs[planet] and b != planet)
        aspected = any(b in ASPECTING_GRAHAS and aspects_sign(b, signs[b], signs[planet])
                       for b in FIXED_BENEFICS if b in signs)
        if not natural_benefic(planet, moon_waxing=chart.moon_waxing,
                               companions=companions, aspected_by_benefic=aspected):
            out.add(planet)
    return frozenset(out)
