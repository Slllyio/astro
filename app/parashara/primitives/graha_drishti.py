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


#: Graded (ordinary) rasi drishti value in virupas, by house-distance (BPHS-26:47, sl.2-5):
#: "on these places the aspects increase gradually in slabs of quarters i.e 1/4, 1/2, 3/4 and full"
#: -> 3rd/10th = 15, 5th/9th = 30, 4th/8th = 45, 7th = 60. This is Parashara's OWN sign-based
#: aspectual evaluation, distinct from the OCR-ambiguous degree-based Sphuta Drishti (sl.6-12).
_GRADED: Final[Mapping[int, float]] = {3: 15.0, 10: 15.0, 5: 30.0, 9: 30.0,
                                       4: 45.0, 8: 45.0, 7: 60.0}


def drishti_value(planet: str, planet_sign: int, target_sign: int) -> float:
    """The graded rasi drishti (virupas, 0..60) `planet` casts on `target_sign` (BPHS-26 sl.2-5).

    Every graha casts the graded value on 3/10, 5/9, 4/8, 7. A planet's SPECIAL houses get the FULL
    60 instead of the graded amount (Saturn 3/10, Jupiter 5/9, Mars 4/8) — that is what "special
    aspect" means. The nodes have no drishti in this BPHS-root engine, so they return 0.
    """
    if planet not in _SPECIAL and planet not in (
            "Sun", "Moon", "Mercury", "Venus"):     # e.g. Rahu/Ketu -> no drishti
        return 0.0
    distance = ((target_sign - planet_sign) % 12) + 1
    if distance in _SPECIAL.get(planet, frozenset()):
        return 60.0                                  # special aspect -> full
    return _GRADED.get(distance, 0.0)


def planets_aspecting_sign(target_sign: int,
                           planet_signs: Mapping[str, int]) -> tuple[str, ...]:
    """Every graha in `planet_signs` that casts a full aspect on `target_sign`.

    A planet does not aspect its own sign (distance 1 is never in any aspect set), so a graha
    sitting in the target is not counted as aspecting it — occupancy is a separate fact.
    """
    return tuple(p for p, s in planet_signs.items() if aspects_sign(p, s, target_sign))
