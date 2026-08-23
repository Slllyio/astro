"""Pancha Mahapurusha yogas — the five "great men" yogas (BPHS ch.75, root).

BPHS DOES define these cleanly — the definition and all five effect descriptions are ch.75, which the
OCR had left stranded inside the ch.74 (Sudarshana Chakra) file; it was split out to
`chapter_075_*.md` so the root can be cited directly (2026-08-23). Parashara states them plainly:

    "When Mars, Mercury, Jupiter, Venus and Saturn being in their own sign or in their sign of
     exaltation, be in kendra to the Ascendant, they give rise to Ruchaka, Bhadra, Hamsa, Malavya
     and Sasa yogas respectively." (BPHS-75:34)

So each of the five non-luminaries, when it stands in its OWN or EXALTATION sign AND that sign is a
KENDRA from the ascendant, forms its Mahapurusha yoga: Mars->Ruchaka, Mercury->Bhadra, Jupiter->Hamsa,
Venus->Malavya, Saturn->Sasa. Chart-computable from dignity + house; the Sun, Moon and nodes do not
form these. Saravali-37:27 corroborates the same rule (allied).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import EXALTATION, SIGN_LORDS

_WORK: Final[str] = "BPHS-75"
DEF_SOURCE: Final[Citation] = Citation(_WORK, 34)          # sl.1-2 — the defining sloka
CORROBORATION: Final[Citation] = Citation("SARAVALI-37", 27)   # allied cross-ref (same rule)

#: planet -> (yoga name, effect-sloka line in BPHS ch.75).
_YOGA: Final[Mapping[str, tuple[str, int]]] = {
    "Mars": ("Ruchaka", 63), "Mercury": ("Bhadra", 98), "Jupiter": ("Hamsa", 127),
    "Venus": ("Malavya", 149), "Saturn": ("Sasa", 165)}
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
