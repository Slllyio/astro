"""Rasi drishti — Jaimini sign-to-sign aspects (as distinct from the Parashari graha drishti in
doctrine/drishti.py). Used by the Jaimini layer (Karakamsa, Arudha, Chara dasha), which reckons
aspects between SIGNS, not planets.

The rule (Jaimini Sutras 1.1):
  * a MOVABLE sign aspects the three FIXED signs EXCEPT the one adjacent to it (the next sign);
  * a FIXED sign aspects the three MOVABLE signs EXCEPT the one adjacent to it (the previous sign);
  * a DUAL (common) sign aspects the other three DUAL signs.
The relation is mutual (if A aspects B then B aspects A).

Usage:
    from app.raman_saab.primitives import rasi_drishti as rd
    rd.signs_aspected_by(1)            # {5, 8, 11}  (Aries -> Leo, Scorpio, Aquarius)
    rd.sign_aspects_sign(1, 5)         # True
    rd.planets_aspecting_sign(sign, chart)   # planets whose sign casts a rasi-drishti on `sign`
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.model import RamanChart

_MOVABLE: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_FIXED: Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_DUAL: Final[frozenset[int]] = frozenset({3, 6, 9, 12})


def signs_aspected_by(sign: int) -> frozenset[int]:
    """The set of signs (1..12) that `sign` casts a rasi-drishti upon."""
    m = (sign - 1) % 3
    if m == 0:                                      # movable -> fixed, except the adjacent (next) sign
        return frozenset(_FIXED - {(sign % 12) + 1})
    if m == 1:                                      # fixed -> movable, except the adjacent (prev) sign
        return frozenset(_MOVABLE - {((sign - 2) % 12) + 1})
    return frozenset(_DUAL - {sign})                # dual -> the other duals


def sign_aspects_sign(a: int, b: int) -> bool:
    """Does sign `a` cast a rasi-drishti on sign `b`?"""
    return b in signs_aspected_by(a)


def planets_aspecting_sign(sign: int, chart: RamanChart) -> list[str]:
    """Planets whose OCCUPIED sign casts a rasi-drishti on `sign` (a planet also rasi-aspects via the
    sign it sits in). Includes the nodes."""
    return [n for n, p in chart.planets.items() if sign_aspects_sign(p.sign, sign)]
