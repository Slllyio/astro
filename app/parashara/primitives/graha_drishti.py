"""Graha drishti — planetary aspects (BPHS ch.26, slokas 2-5).

    "All planets aspect the 7th fully. Saturn, Jupiter and Mars have special aspects respectively
     on 3rd and 10th, 5th and 9th, and 4th and 8th." (BPHS-26:47)

Full aspects (the boolean "does X aspect Y", which is what bhava judgment needs):
  * every graha  -> the 7th house from itself
  * Saturn       -> additionally the 3rd and 10th
  * Jupiter      -> additionally the 5th and 9th
  * Mars         -> additionally the 4th and 8th

Counted by SIGN (rasi drishti), Parashara's whole-sign distance — the same convention the platform
uses elsewhere, and stream-agnostic as arithmetic; the DOCTRINE here is which houses each graha
special-aspects, which is BPHS's, not shared. The graded quarter/half/three-quarter aspects
(BPHS-26:53) are a strength refinement for later; a bhava is "aspected by" a graha when the graha
casts a FULL aspect on it.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

#: Extra full-aspect house-distances beyond the universal 7th (BPHS-26:47).
_SPECIAL: Final[Mapping[str, frozenset[int]]] = {
    "Saturn": frozenset({3, 10}),
    "Jupiter": frozenset({5, 9}),
    "Mars": frozenset({4, 8}),
}
#: Every graha aspects the 7th.
_UNIVERSAL: Final[int] = 7

SOURCE: Final[Citation] = Citation("BPHS-26", 47)


def full_aspect_distances(planet: str) -> frozenset[int]:
    """The set of house-distances (1-indexed, planet's own sign = 1) `planet` FULLY aspects."""
    return frozenset({_UNIVERSAL}) | _SPECIAL.get(planet, frozenset())


def aspects_sign(planet: str, planet_sign: int, target_sign: int) -> bool:
    """Does `planet` (in `planet_sign`) cast a full aspect on `target_sign`? (1=Aries..12=Pisces)"""
    distance = ((target_sign - planet_sign) % 12) + 1
    return distance in full_aspect_distances(planet)


def planets_aspecting_sign(target_sign: int,
                           planet_signs: Mapping[str, int]) -> tuple[str, ...]:
    """Every graha in `planet_signs` that casts a full aspect on `target_sign`.

    A planet does not aspect its own sign (distance 1 is never in any aspect set), so a graha
    sitting in the target is not counted as aspecting it — occupancy is a separate fact.
    """
    return tuple(p for p, s in planet_signs.items() if aspects_sign(p, s, target_sign))
