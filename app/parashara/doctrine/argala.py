"""Argala — planetary intervention (BPHS ch.31).

Argala ("bolt/impediment") is the leverage planets exert on a house or planet from specific places,
and the counter-leverage (virodhargala) that obstructs it:

    "Planets in the 4th, 2nd and the 11th (from a house or a planet) cause Argala while obstructors of
     the Argala will be those in the 10th, 12th and 3rd... The 5th is also an Argala place while the
     planet in the 9th will counteract such Argala. If the number of Argalas are more than the
     obstructing planets, then the Argala will prevail. If there are 3 or more malefics in the 3rd,
     they will cause Vipareeta Argala (more effective intervention) which will be very favourable."
     (BPHS-31:62)

The chapter's own table (BPHS-31, "4 2 11 5" over "10 12 3 9") fixes the pairing: the argala from the
2nd/4th/11th/5th is obstructed respectively by the 12th/10th/3rd/9th. This module computes, for a
target sign, each argala and whether it prevails (unobstructed, or its planets outnumber the
obstructors — the count rule the sloka states), plus the special Vipareeta argala.

Faithful scope: prevalence uses Parashara's stated COUNT rule; the alternative "stronger planet
prevails" rule (which needs Shadbala) and the nodes-count-in-reverse refinement are noted, not faked.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-31", 62)   # sl.2-9, "FORMATION OF ARGALA"

#: argala house (from the target) -> the house whose occupants obstruct it (BPHS-31 table).
_PAIRS: Final[Mapping[int, int]] = {2: 12, 4: 10, 11: 3, 5: 9}
#: Natural malefics — for the Vipareeta (3+ malefics in the 3rd) rule.
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})


@dataclass(frozen=True)
class Argala:
    """One argala on the target: the causing house/planets, its obstructor house/planets, verdict."""
    argala_house: int              # 2, 4, 11 or 5 from the target
    argala_planets: tuple[str, ...]
    obstructor_house: int          # 12, 10, 3 or 9 from the target
    obstructor_planets: tuple[str, ...]
    prevails: bool                 # unobstructed, or argala planets outnumber obstructors
    vipareeta: bool = False        # 3+ malefics in the 3rd -> special favourable argala


def _house(target_sign: int, sign: int) -> int:
    return ((sign - target_sign) % 12) + 1


def _planets_in_house(target_sign: int, house: int,
                      planet_signs: Mapping[str, int]) -> tuple[str, ...]:
    return tuple(p for p, s in planet_signs.items() if _house(target_sign, s) == house)


def argala_for(target_sign: int, planet_signs: Mapping[str, int]) -> tuple[Argala, ...]:
    """Every argala acting on `target_sign` (BPHS ch.31), each with its obstructor and verdict.

    Only argala houses that actually contain a planet are returned. `target_sign` and the values of
    `planet_signs` are 1..12.
    """
    if not 1 <= target_sign <= 12:
        raise ValueError("target_sign must be 1..12")
    third = _planets_in_house(target_sign, 3, planet_signs)
    third_malefics = [p for p in third if p in _MALEFICS]
    out: list[Argala] = []
    for a_house, o_house in _PAIRS.items():
        a_planets = _planets_in_house(target_sign, a_house, planet_signs)
        if not a_planets:
            continue
        o_planets = _planets_in_house(target_sign, o_house, planet_signs)
        # Vipareeta: 3+ malefics in the 3rd make that (the 11th's obstructor house) a favourable argala.
        vipareeta = a_house == 11 and len(third_malefics) >= 3
        prevails = vipareeta or len(a_planets) > len(o_planets)
        out.append(Argala(argala_house=a_house, argala_planets=a_planets,
                          obstructor_house=o_house, obstructor_planets=o_planets,
                          prevails=prevails, vipareeta=vipareeta))
    return tuple(out)
