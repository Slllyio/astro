"""Rasi drishti — sign aspects (BPHS ch.8, sl.1-3). The Jaimini aspect system, from Parashara.

    "Every movable sign aspects the 3 fixed signs leaving the fixed sign adjacent to it. Every fixed
     sign lends aspect to the 3 movable signs barring the adjacent movable sign. And a common sign
     aspects the other three common signs. The planet in a sign lends the same aspect as the sign."
     (BPHS-8:35)

So (worked example, sl.: Aries aspects Leo/Scorpio/Aquarius, not Taurus; Taurus aspects Cancer/Libra/
Capricorn, not Aries):
  * movable (Aries/Cancer/Libra/Capricorn) -> the three fixed signs except the next one (S+1);
  * fixed (Taurus/Leo/Scorpio/Aquarius) -> the three movable signs except the previous one (S-1);
  * dual (Gemini/Virgo/Sagittarius/Pisces) -> the other three dual signs.

This is the whole-sign aspect Jaimini techniques (Chara dasha, Karakamsa, rasi Argala) need, distinct
from the graha drishti of ch.26. A planet aspects a sign if its own sign does.
"""
from __future__ import annotations

from typing import Final

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-8", 35)

_MOVABLE: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_FIXED: Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_DUAL: Final[frozenset[int]] = frozenset({3, 6, 9, 12})


def rasi_aspects(from_sign: int) -> frozenset[int]:
    """The signs `from_sign` (1..12) casts a rasi aspect on (BPHS-8:35)."""
    if not 1 <= from_sign <= 12:
        raise ValueError("from_sign must be 1..12")
    if from_sign in _MOVABLE:
        return _FIXED - {from_sign + 1}                  # the fixed signs except the adjacent (next)
    if from_sign in _FIXED:
        return _MOVABLE - {from_sign - 1}                # the movable signs except the adjacent (prev)
    return _DUAL - {from_sign}                            # the other three dual signs


def aspects_sign(from_sign: int, to_sign: int) -> bool:
    """Does `from_sign` cast a rasi aspect on `to_sign`? (BPHS-8:35)"""
    return to_sign in rasi_aspects(from_sign)


def planets_aspecting_sign(target_sign: int, planet_signs) -> tuple[str, ...]:
    """Every graha whose sign casts a rasi aspect on `target_sign` (a planet aspects as its sign does)."""
    return tuple(p for p, s in planet_signs.items() if aspects_sign(s, target_sign))
