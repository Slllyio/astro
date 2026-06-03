"""Drishti (planetary aspects) — Raman Saab doctrine.

Whole-sign Vedic aspects (CLAUDE.md lock): an aspect fires by SIGN membership
(the planet's rasi-house to the target's rasi-house); orb only sets ``is_exact``.
Every planet aspects the 7th. Special aspects: Mars 4th & 8th, Jupiter 5th & 9th,
Saturn 3rd & 10th.

**Raman Saab divergence (methodology §9 D3):** Rahu/Ketu cast **only the 7th**
aspect — NO special 5/9. This intentionally differs from `app/core/drishti_argala.py`
(which gives the nodes a Jupiter-style 5/9 per Bhasin/Nadi). Guard test enforces it.

Usage:
    from app.raman_saab.doctrine import drishti
    drishti.aspects_planet("Saturn", "Sun", chart)   # bool
    drishti.aspecting_planets("Sun", chart)          # which planets aspect the Sun
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.model import RamanChart

# Aspect houses (counted from the aspecting planet, whole-sign). All include the 7th.
# Nodes are 7th-ONLY (Raman Saab divergence — do not add 5/9).
ASPECT_HOUSES: Final[dict[str, frozenset[int]]] = {
    "Sun": frozenset({7}), "Moon": frozenset({7}),
    "Mercury": frozenset({7}), "Venus": frozenset({7}),
    "Mars": frozenset({4, 7, 8}),
    "Jupiter": frozenset({5, 7, 9}),
    "Saturn": frozenset({3, 7, 10}),
    "Rahu": frozenset({7}), "Ketu": frozenset({7}),
}


def _house_distance(from_house: int, to_house: int) -> int:
    """Whole-sign distance (1..12) from one rasi-house to another."""
    return ((to_house - from_house) % 12) + 1


def aspects_house(planet: str, house: int, chart: RamanChart) -> bool:
    """Does `planet` cast a (whole-sign) aspect on rasi-house `house` (1..12)?"""
    if planet not in chart.planets or planet not in ASPECT_HOUSES:
        return False
    dist = _house_distance(chart.planets[planet].rasi_house, house)
    return dist in ASPECT_HOUSES[planet]


def aspects_planet(a: str, b: str, chart: RamanChart) -> bool:
    """Does planet `a` aspect planet `b` (by whole-sign rasi-house)?"""
    if a == b or a not in chart.planets or b not in chart.planets:
        return False
    return aspects_house(a, chart.planets[b].rasi_house, chart)


def mutual_aspect(a: str, b: str, chart: RamanChart) -> bool:
    """Do `a` and `b` aspect each other?"""
    return aspects_planet(a, b, chart) and aspects_planet(b, a, chart)


def aspecting_planets(target: str, chart: RamanChart) -> list[str]:
    """All planets (in chart order) that aspect the `target` planet."""
    if target not in chart.planets:
        return []
    return [p for p in chart.planets if p != target and aspects_planet(p, target, chart)]


def aspecting_house(house: int, chart: RamanChart) -> list[str]:
    """All planets that aspect rasi-house `house`."""
    return [p for p in chart.planets if aspects_house(p, house, chart)]
