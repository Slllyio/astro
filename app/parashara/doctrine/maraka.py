"""Maraka — death-dealing planets (BPHS ch.44). The bridge from longevity to dasha timing.

    "The 2nd and 7th are Maraka houses ... the 2nd is a powerful Maraka (against the 7th). The lords
     of the 2nd and 7th, malefics in the 2nd and 7th, and malefics accompanying the 2nd and 7th lords
     are all known as Marakas. The major and sub periods of these planets will bring death on the
     native depending on whether he has a long, medium or short life." (BPHS-44:32,51)

So the maraka set is: the 2nd and 7th LORDS, natural malefics OCCUPYING the 2nd/7th, and natural
malefics CONJUNCT those lords. This module identifies them (with the reason each qualifies) so the
Vimshottari/bhukti timeline can flag the classically life-threatening periods — the natural companion
to the encoded Nisargayu longevity. The 2nd is the stronger maraka (it is both 12th-from-3rd and
7th-from-8th); this is noted on the 2nd-lord entry.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import SIGN_LORDS

SOURCE: Final[Citation] = Citation("BPHS-44", 51)          # sl.3 — the maraka planets
_MARAKA_HOUSES: Final[tuple[int, ...]] = (2, 7)
#: Natural malefics (the fixed set; nodes included).
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})


@dataclass(frozen=True)
class Maraka:
    planet: str
    reason: str
    source: Citation


def _house(asc_sign: int, sign: int) -> int:
    return ((sign - asc_sign) % 12) + 1


def maraka_planets(planet_signs: Mapping[str, int], *, asc_sign: int) -> tuple[Maraka, ...]:
    """The maraka (death-dealing) planets for the chart (BPHS-44), each with why it qualifies.

    `planet_signs` maps grahas -> sign (1..12); `asc_sign` is 1..12. A planet may qualify more than
    one way; the first-found reason (lord, then occupant, then companion) is reported once per planet.
    """
    found: dict[str, str] = {}

    # (1) the 2nd and 7th lords (the 2nd the stronger maraka).
    for house in _MARAKA_HOUSES:
        lord = SIGN_LORDS[((asc_sign - 1 + house - 1) % 12) + 1]
        note = " (the stronger maraka)" if house == 2 else ""
        found.setdefault(lord, f"lord of the {house}{'nd' if house == 2 else 'th'} house{note}")

    # (2) natural malefics occupying the 2nd or 7th.
    for p, s in planet_signs.items():
        if p in _MALEFICS and _house(asc_sign, s) in _MARAKA_HOUSES:
            found.setdefault(p, f"a malefic in the {_house(asc_sign, s)}th (maraka) house")

    # (3) natural malefics conjunct the 2nd or 7th lord.
    lord_signs = {SIGN_LORDS[((asc_sign - 1 + h - 1) % 12) + 1] for h in _MARAKA_HOUSES}
    lord_positions = {planet_signs[l] for l in lord_signs if l in planet_signs}
    for p, s in planet_signs.items():
        if p in _MALEFICS and s in lord_positions and p not in lord_signs:
            found.setdefault(p, "a malefic conjunct a maraka lord")

    order = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    return tuple(Maraka(p, found[p], SOURCE) for p in order if p in found)
