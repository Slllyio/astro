"""Nabhasa yogas (BPHS ch.35) — the 32 yogas of planetary distribution.

Parashara opens ch.35 with "32 Nabhasa yogas which have a total of 1800 varieties" in four families:
Asraya (3, by the modality all planets share), Dala (2, benefic/malefic in the kendras), Akriti (20,
by the geometric figure the occupied houses trace) and Sankhya (7, by the NUMBER of signs the seven
planets occupy). This module gives the faithful cited catalogue of all 32 (indexed from the chapter
in place) plus detectors for the two families that are computationally unambiguous — Asraya and
Sankhya — each citing Parashara's own defining sloka.

The two undetected families are not faked: Dala and the 20 Akriti figures need occupied-house pattern
matching that is a documented next step; `catalogue()` still carries their definitions and effects.
Per Parashara's own caveat (ch.35 sl.16-17) a Sankhya yoga "will not be operable if another Nabhasa
yoga is derivable", so `sankhya_yoga` returns that caveat rather than asserting operability the module
cannot yet confirm.

Nabhasa uses the seven visible grahas (Sun..Saturn); the nodes do not enter these yogas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Optional

from app.parashara.doctrine.corpus_index import Sloka, slokas_of
from app.parashara.doctrine.sources import Citation

_WORK: Final[str] = "BPHS-35"
#: The seven visible grahas — Nabhasa yogas exclude the nodes.
_SEVEN: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

#: Sign modality (BPHS: chara/sthira/dwiswabhava) by sign number 1..12.
_MOVABLE: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_FIXED: Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_DUAL: Final[frozenset[int]] = frozenset({3, 6, 9, 12})

#: Asraya yogas: all seven planets share one modality (ch.35 sl.7).
ASRAYA_SOURCE: Final[Citation] = Citation(_WORK, 67)
_ASRAYA: Final[Mapping[str, str]] = {"movable": "Rajju", "fixed": "Musala", "dual": "Nala"}

#: Sankhya yogas: by the number of distinct signs the seven occupy (ch.35 sl.16-17).
SANKHYA_SOURCE: Final[Citation] = Citation(_WORK, 148)
_SANKHYA: Final[Mapping[int, str]] = {
    1: "Gola", 2: "Yuga", 3: "Soola", 4: "Kedara", 5: "Pasa", 6: "Damini", 7: "Veena"}


@dataclass(frozen=True)
class NabhasaYoga:
    """A detected Nabhasa yoga: its name, family, why it formed, and Parashara's citation."""
    name: str
    family: str              # "asraya" | "sankhya"
    reason: str
    source: Citation
    operable: Optional[bool] = None   # None when precedence cannot yet be confirmed (Sankhya)


def _mode(sign: int) -> str:
    if sign in _MOVABLE:
        return "movable"
    if sign in _FIXED:
        return "fixed"
    return "dual"


def _signs(planet_signs: Mapping[str, int]) -> list[int]:
    return [planet_signs[p] for p in _SEVEN if p in planet_signs]


def asraya_yoga(planet_signs: Mapping[str, int]) -> Optional[NabhasaYoga]:
    """Rajju/Musala/Nala if all seven grahas share one modality, else None (BPHS-35 sl.7)."""
    signs = _signs(planet_signs)
    if len(signs) < 7:
        return None
    modes = {_mode(s) for s in signs}
    if len(modes) != 1:
        return None
    mode = modes.pop()
    return NabhasaYoga(name=_ASRAYA[mode], family="asraya",
                       reason=f"all seven grahas occupy {mode} signs", source=ASRAYA_SOURCE,
                       operable=True)


def sankhya_yoga(planet_signs: Mapping[str, int]) -> Optional[NabhasaYoga]:
    """The Sankhya yoga for the count of distinct signs the seven occupy (BPHS-35 sl.16-17).

    `operable` is left None: Parashara says a Sankhya yoga does not operate if another (Asraya/Dala/
    Akriti) Nabhasa yoga forms, and this module does not yet detect the Akriti figures — so operability
    is reported as unconfirmed rather than asserted. When `asraya_yoga` fires, that one is operable.
    """
    signs = _signs(planet_signs)
    if len(signs) < 7:
        return None
    count = len(set(signs))
    name = _SANKHYA.get(count)
    if name is None:
        return None
    return NabhasaYoga(name=name, family="sankhya",
                       reason=f"the seven grahas occupy {count} distinct sign(s)",
                       source=SANKHYA_SOURCE, operable=None)


def catalogue() -> tuple[Sloka, ...]:
    """The whole cited ch.35 — every Nabhasa definition and effect sloka, in order (all 32 families)."""
    return slokas_of(_WORK)
