"""Upagraha house-effects — BPHS ch.25, the 5x12 grid for the Sun-derived sub-planets.

Where `primitives/upagrahas.py` COMPUTES the five Aprakasa grahas (Dhuma, Vyatipata, Parivesha,
Indrachapa, Upaketu — BPHS ch.3), this reads Parashara's effect for each of them in each of the 12
houses (BPHS ch.25). The chapter is regular: five blocks of twelve consecutive slokas, so
cell = start + block_index*12 + (house-1). Verified: Dhuma sl.2 (ascendant)..sl.13 (12th),
Vyatipata 14..25, Parivesha (Paridhi) 26..37, Indrachapa (Chapa/Kodanda) 38..49, Upaketu (Dhwaja/
Sikhi) 50..61. Each cell is a numbered sloka read verbatim and cited to its own line.

The engine names are Dhuma/Vyatipata/Parivesha/Indrachapa/Upaketu; ch.25 uses the synonyms Paridhi,
Chapa/Kodanda and Dhwaja/Sikhi for the last three — the same bodies (confirmed in the section heads).
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Final, Mapping, Optional

from app.parashara.doctrine.corpus_index import Sloka, slokas_of

_WORK: Final[str] = "BPHS-25"
#: engine name -> that upagraha's first sloka number (its ascendant/1st-house cell).
_BLOCK_START: Final[Mapping[str, int]] = {
    "Dhuma": 2, "Vyatipata": 14, "Parivesha": 26, "Indrachapa": 38, "Upaketu": 50,
}


@lru_cache(maxsize=1)
def _grid() -> dict[tuple[str, int], Sloka]:
    by_num = {s.number: s for s in slokas_of(_WORK)}
    out: dict[tuple[str, int], Sloka] = {}
    for name, start in _BLOCK_START.items():
        for house in range(1, 13):
            n = start + (house - 1)
            if n in by_num:
                out[(name, house)] = by_num[n]
    _recover_vyatipata_2nd(out, by_num)
    return out


def _recover_vyatipata_2nd(grid: dict[tuple[str, int], Sloka], by_num: dict[int, Sloka]) -> None:
    """Vyatipata's 2nd-house sloka (sl.15) had its number destroyed by OCR ("^ 1 H 5 -J7r ipata"),
    so `slokas_of` absorbed its text into the 1st-house cell (sl.14). The 2nd-house clause is legible
    after the mangled "the2nd" marker — recover it as its own cell (its number was lost, not its text,
    BPHS-25). The 1st-house cell is left verbatim (it still carries the merged clause honestly)."""
    if ("Vyatipata", 2) in grid or ("Vyatipata", 1) not in grid:
        return
    s1 = grid[("Vyatipata", 1)]
    m = re.search(r"2nd", s1.text)
    if m is None:
        return
    tail = re.sub(r"^[^A-Za-z]+", "", s1.text[m.end():]).strip()       # the 2nd-house effect
    if tail:
        grid[("Vyatipata", 2)] = Sloka(work=_WORK, number=15, topic="Vyatipata",
                                       text="If Vyatipata is in the 2nd, " + tail, source=s1.source)


def house_effect(upagraha: str, house: int) -> Optional[Sloka]:
    """BPHS ch.25's effect of `upagraha` in `house` (1..12 from the lagna), or None."""
    if upagraha not in _BLOCK_START or not 1 <= house <= 12:
        raise ValueError("upagraha must be one of the five Sun-derived; house 1..12")
    return _grid().get((upagraha, house))


def all_effects() -> Mapping[tuple[str, int], Sloka]:
    """The whole 5x12 upagraha house-effect grid (BPHS-25)."""
    return dict(_grid())
