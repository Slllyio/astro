"""Whole-sign Drishti graph + Argala/Virodhargala — BPHS Ch.26, Jaimini Ch.4.

Phase 2 of the astrologer's-lens framework. Two related primitives:

## Drishti (Aspect) — whole-sign per BPHS Ch.26 (LOCKED in CLAUDE.md)

All 9 grahas aspect their **7th sign** (the 180° opposition by sign).
Beyond that, three planets carry special "extra" aspects:

* **Mars**: also aspects 4th and 8th from itself
* **Jupiter**: also aspects 5th and 9th from itself
* **Saturn**: also aspects 3rd and 10th from itself
* **Rahu/Ketu**: also aspect 5th and 9th (modern Sukra Nadi convention,
  locked in CLAUDE.md as Jupiter-style)

Sun/Moon/Mercury/Venus aspect ONLY the 7th. The orb is irrelevant for
whole-sign drishti — sign-membership is the test, not degree-proximity.

Output is a directed graph:
* planet → bhava: which bhavas a graha aspects
* planet → planet: which other grahas a graha aspects (whole-sign)

## Argala (Intervention) — Jaimini Ch.4

From any focal bhava (or planet) sitting in sign S, the houses at
distance 2, 4, 11 (primary) and 5 (secondary) from S can *intervene*
on the affairs of S — friendly if benefics occupy them, hostile if
malefics.

**Virodhargala** (counter-intervention) sits at distance 12, 10, 3
(primary blocks) and 9 (secondary block). If a counter-house holds a
planet of opposite disposition, it neutralises the argala from the
mirrored source.

The Bhava Judge (Phase 6) reads both layers: drishti gives WHO is
looking at a bhava; argala gives WHO is intervening on it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Sequence

# Whole-sign aspects from BPHS Ch.26. Distance is sign-count, not
# degree. 7 (opposition) is universal; planet-specific extras are:
_BASE_ASPECTS: Final[tuple[int, ...]] = (7,)
_PLANET_EXTRA_ASPECTS: Final[Mapping[str, tuple[int, ...]]] = {
    "Sun":     (),
    "Moon":    (),
    "Mercury": (),
    "Venus":   (),
    "Mars":    (4, 8),
    "Jupiter": (5, 9),
    "Saturn":  (3, 10),
    "Rahu":    (5, 9),   # Sukra Nadi modern (CLAUDE.md lock)
    "Ketu":    (5, 9),
}

_ALL_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
    "Saturn", "Rahu", "Ketu",
)

# Argala distances — Jaimini Ch.4. Primary causes vs counter-blocks.
_PRIMARY_ARGALA: Final[tuple[int, ...]] = (2, 4, 11)
_SECONDARY_ARGALA: Final[tuple[int, ...]] = (5,)

# Each argala distance has a paired Virodhargala (counter) distance.
# The pair (causer-distance, blocker-distance) is fixed in Jaimini:
#   2 ↔ 12, 4 ↔ 10, 11 ↔ 3, 5 ↔ 9
_VIRODHARGALA_PAIRS: Final[Mapping[int, int]] = {
    2: 12, 4: 10, 11: 3, 5: 9,
}


def _step(from_house: int, distance: int) -> int:
    """Move forward `distance` houses (1-indexed, wraps at 12).

    `from_house=1, distance=7 → 7` (opposition).
    `from_house=10, distance=4 → 1` (4 from 10 wraps to 2 — wait,
    Jaimini counting is *inclusive*: from 10, count "10, 11, 12, 1" =
    1. That's 4 houses inclusive ⇒ +3 in modulo. We use the inclusive
    convention throughout this module.
    """
    return ((from_house - 1 + distance - 1) % 12) + 1


def aspects_from_planet(planet: str, planet_house: int) -> tuple[int, ...]:
    """Which bhavas does this planet aspect (whole-sign)?

    Args:
        planet: One of the 9 grahas.
        planet_house: The natal house (1..12) the planet sits in.
    Returns:
        Sorted ascending tuple of bhava numbers the planet aspects.
    """
    if planet not in _PLANET_EXTRA_ASPECTS:
        return ()
    distances = _BASE_ASPECTS + _PLANET_EXTRA_ASPECTS[planet]
    return tuple(sorted({_step(planet_house, d) for d in distances}))


def aspect_graph(planet_houses: Mapping[str, int]) -> dict[str, tuple[int, ...]]:
    """Build the planet → bhava aspect graph for one chart.

    Args:
        planet_houses: e.g. ``{"Sun": 10, "Moon": 5, ...}``. Any
            missing planet is skipped (e.g. shadow planets in an
            engine that excludes them).
    """
    return {
        planet: aspects_from_planet(planet, h)
        for planet, h in planet_houses.items()
        if planet in _PLANET_EXTRA_ASPECTS
    }


def planets_aspecting_bhava(
    bhava: int, planet_houses: Mapping[str, int],
) -> tuple[str, ...]:
    """Reverse-lookup: which planets aspect the given bhava?

    This is what the Bhava Judge calls per-bhava. Sorted by name for
    stable output.
    """
    if not 1 <= bhava <= 12:
        raise ValueError(f"bhava must be 1..12, got {bhava}")
    out = [
        p for p, h in planet_houses.items()
        if p in _PLANET_EXTRA_ASPECTS and bhava in aspects_from_planet(p, h)
    ]
    return tuple(sorted(out))


# ─── Argala ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ArgalaSource:
    """One argala-causing relationship on a focal bhava.

    Attributes:
        focal_bhava: Where the intervention lands (1..12).
        argala_house: Which house contains the intervening planets.
        distance: 2/4/5/11 — the Jaimini distance label.
        kind: "primary" or "secondary".
        causing_planets: Planets sitting in argala_house.
        counter_house: The paired Virodhargala house.
        blocking_planets: Planets in counter_house (potential blockers).
        is_blocked: True iff Virodhargala has equal-or-greater planet
            count of opposite disposition. The "opposite disposition"
            check is deferred to Phase 6 which knows FB/FM per chart.
    """
    focal_bhava: int
    argala_house: int
    distance: int
    kind: str
    causing_planets: tuple[str, ...]
    counter_house: int
    blocking_planets: tuple[str, ...]
    is_blocked: bool


def _planets_in_house(
    house: int, planet_houses: Mapping[str, int],
) -> tuple[str, ...]:
    """All planets currently occupying the given house — sorted."""
    return tuple(sorted(p for p, h in planet_houses.items() if h == house))


def argala_for_bhava(
    focal_bhava: int, planet_houses: Mapping[str, int],
) -> tuple[ArgalaSource, ...]:
    """Enumerate every argala source on the given focal bhava.

    For each of the 4 argala distances (2, 4, 11, 5), build the source
    record. The simplest blocking criterion — pure count parity — is
    used here; Phase 6 will overlay benefic/malefic disposition.
    """
    if not 1 <= focal_bhava <= 12:
        raise ValueError(f"focal_bhava must be 1..12, got {focal_bhava}")

    sources: list[ArgalaSource] = []
    all_distances = [(d, "primary") for d in _PRIMARY_ARGALA] + \
                    [(d, "secondary") for d in _SECONDARY_ARGALA]
    for distance, kind in all_distances:
        argala_h = _step(focal_bhava, distance)
        counter_d = _VIRODHARGALA_PAIRS[distance]
        counter_h = _step(focal_bhava, counter_d)

        causing = _planets_in_house(argala_h, planet_houses)
        blocking = _planets_in_house(counter_h, planet_houses)
        if not causing and not blocking:
            continue
        # Simple disposition-agnostic block rule: equal-or-greater count
        # of blockers neutralises. Phase 6 overrides with FB/FM weighting.
        is_blocked = bool(blocking) and len(blocking) >= len(causing)

        sources.append(ArgalaSource(
            focal_bhava=focal_bhava,
            argala_house=argala_h,
            distance=distance,
            kind=kind,
            causing_planets=causing,
            counter_house=counter_h,
            blocking_planets=blocking,
            is_blocked=is_blocked,
        ))
    return tuple(sources)


def argala_report(
    planet_houses: Mapping[str, int], bhavas: Sequence[int] | None = None,
) -> dict[int, tuple[ArgalaSource, ...]]:
    """Build the full argala report for one chart.

    Args:
        planet_houses: planet → natal house mapping.
        bhavas: which focal bhavas to evaluate (default: all 12).

    Returns:
        bhava-number → tuple of argala sources active on it.
    """
    targets = range(1, 13) if bhavas is None else bhavas
    return {b: argala_for_bhava(b, planet_houses) for b in targets}
