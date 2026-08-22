"""Pancha Mahapurusha yogas — the five "great men" yogas (Saravali ch.37).

BPHS itself does not define these five yogas cleanly; the allied Parashari lineage does, and the
registry permits citing allied texts where the root is silent. Saravali states them plainly:

    "Venus, Mars, Saturn, Jupiter and Mercury remaining in their respective own Houses, or exaltation
     Signs, identical with Angles, cause Malavya, Ruchaka, Sasa, Hamsa and Bhadra (Yogas)."
     (SARAVALI-37:27)

So each of the five non-luminaries, when it stands in its OWN or EXALTATION sign AND that sign is a
KENDRA from the ascendant, forms its Mahapurusha yoga: Mars->Ruchaka, Mercury->Bhadra, Jupiter->Hamsa,
Venus->Malavya, Saturn->Sasa. Chart-computable from dignity + house; the Sun, Moon and nodes do not
form these.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import EXALTATION, SIGN_LORDS

_WORK: Final[str] = "SARAVALI-37"
DEF_SOURCE: Final[Citation] = Citation(_WORK, 27)      # sl.2 — the defining sloka

#: planet -> (yoga name, effect-sloka line in Saravali ch.37).
_YOGA: Final[Mapping[str, tuple[str, int]]] = {
    "Mars": ("Ruchaka", 41), "Mercury": ("Bhadra", 72), "Jupiter": ("Hamsa", 62),
    "Venus": ("Malavya", 32), "Saturn": ("Sasa", 54)}
_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})


@dataclass(frozen=True)
class MahapurushaYoga:
    name: str
    planet: str
    dignity: str             # "own" | "exaltation"
    house: int               # the kendra it occupies (1/4/7/10 from lagna)
    source: Citation         # the defining sloka
    effect: Citation         # the yoga's effect sloka


def _signs_owned(planet: str) -> tuple[int, ...]:
    return tuple(s for s, lord in SIGN_LORDS.items() if lord == planet)


def detect(planet_signs: Mapping[str, int], *, asc_sign: int) -> tuple[MahapurushaYoga, ...]:
    """Every Pancha Mahapurusha yoga present (Saravali-37): a non-luminary in own/exaltation, in a
    kendra from the ascendant."""
    out: list[MahapurushaYoga] = []
    for planet, (name, eff_line) in _YOGA.items():
        sign = planet_signs.get(planet)
        if sign is None:
            continue
        own = sign in _signs_owned(planet)
        exalt = sign == EXALTATION.get(planet)
        if not (own or exalt):
            continue
        house = ((sign - asc_sign) % 12) + 1
        if house in _KENDRAS:
            out.append(MahapurushaYoga(name=name, planet=planet,
                                       dignity="own" if own else "exaltation", house=house,
                                       source=DEF_SOURCE, effect=Citation(_WORK, eff_line)))
    return tuple(out)
