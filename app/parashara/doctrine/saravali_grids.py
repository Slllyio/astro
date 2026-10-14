"""Saravali's effect grids — the planet-in-house / planet-in-sign / dignity doctrine BPHS lacks.

BPHS gives lords-in-houses (ch.24, encoded) but no clean 7-graha x 12-house or x 12-sign effect
grid; Saravali does, in prose so regular the ch.24 machinery reads it. This indexes those grids IN
PLACE — every cell is a numbered Saravali sloka, read verbatim and cited to its own line (allied
tier: citable where BPHS is silent, which here it is).

Each grid is a block of consecutive numbered slokas: within a chapter the blocks run in graha order
(Sun..Saturn), each block one graha's twelve houses/signs, so cell = start + block_index*12 +
(sub-1). Verified: Saravali ch.30 sl.2 = Sun-in-Ascendant .. sl.85 = Saturn-in-12th (sl.86-87 are the
closing rule, correctly outside the grid).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Final, Mapping, Optional

from app.parashara.doctrine.corpus_index import Sloka, slokas_of

_GRAHAS: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _arithmetic_grid(work: str, start: int, block: int,
                     keys: tuple[str, ...]) -> dict[tuple[str, int], Sloka]:
    """{(key, sub 1..block): Sloka} where sloka number = start + key_index*block + (sub-1)."""
    by_num = {s.number: s for s in slokas_of(work)}
    out: dict[tuple[str, int], Sloka] = {}
    for ki, key in enumerate(keys):
        for sub in range(1, block + 1):
            n = start + ki * block + (sub - 1)
            if n in by_num:
                out[(key, sub)] = by_num[n]
    return out


@lru_cache(maxsize=1)
def _house_grid() -> dict[tuple[str, int], Sloka]:
    # Saravali ch.30: sl.1 intro, then Sun sl.2-13, Moon 14-25, ... Saturn 74-85 (12 houses each).
    return _arithmetic_grid("SARAVALI-30", 2, 12, _GRAHAS)


def planet_in_house(planet: str, house: int) -> Optional[Sloka]:
    """Saravali's effect of `planet` in `house` (1..12 from the lagna), or None (SARAVALI-30)."""
    if planet not in _GRAHAS or not 1 <= house <= 12:
        raise ValueError("planet must be a graha (Sun..Saturn) and house 1..12")
    return _house_grid().get((planet, house))


def all_house_effects() -> Mapping[tuple[str, int], Sloka]:
    """The whole 7x12 planet-in-house grid (SARAVALI-30)."""
    return dict(_house_grid())


_ORD_WORD: Final[dict[int, str]] = {
    1: "Ascendant", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th",
    7: "7th", 8: "8th", 9: "9th", 10: "10th", 11: "11th", 12: "12th",
}


def normalize_house_phrase(text: str, house: int) -> str:
    """Repair only a leading house-ordinal token the OCR corrupted (e.g. Mars-8th prints "9h").

    The cell's house is authoritative by its position in Saravali's sequence (proven sequential and
    by effect content); some printed digits are OCR noise (6->0, 8->9, 5->3, destroyed->"?h"). We do
    NOT touch the substantive effect text or the stored `Sloka.text` (citation stays verbatim) — only
    the leading "...the <ordinal>," clause, and only when its digit disagrees with the true house.
    """
    head, sep, tail = text.partition(",")
    if not sep:
        return text
    low = head.lower()
    cut = max(low.rfind(" the "), low.rfind(" in "))
    if cut < 0:
        return text
    kw_end = cut + (5 if low[cut:cut + 5] == " the " else 4)
    current = head[kw_end:]
    if str(house) in current or (house == 1 and "ascend" in current.lower()):
        return text  # digit already right (or the "Ascendant" wording) — leave verbatim
    return head[:kw_end] + _ORD_WORD[house] + sep + tail
