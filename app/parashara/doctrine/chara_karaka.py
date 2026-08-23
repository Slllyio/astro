"""Chara (movable) karakas + Karakamsa — BPHS ch.32-33, the 7-karaka scheme Parashara states first.

## The 7-vs-8 fork, settled from the root text itself
BPHS ch.32 sl.1-2 declares the karakas are "obtainable from among the 7 planets viz the Sun to
Saturn" (BPHS-32:31) — that is Parashara's own primary statement. It then reports, as *"Some say ...
yet some say"*, an 8-karaka variant that adds Rahu with his degree deducted from 30 (BPHS-32:152).
The Notes name the primary as the "seven significators" school, which treats Matru and Putra karaka
as identical (BPHS-32:149).

This engine follows Parashara's primary 7-planet scheme and does NOT use the Rahu variant. This is
faithful to BPHS's own framing (7 is stated, 8 is "some say"), to the strict Jaimini reading, and it
matches the cross-platform lock the Raman engine carries: **the Atmakaraka can never be a node** —
here that is structural, the nodes are simply not in the ranked set.

## The rule
Each of the 7 visible planets is ranked by its degree WITHIN its sign, descending (BPHS-32:60 —
"whichever has traversed maximum number of degrees in a particular sign is called Atmakarka"); ties
break on minutes then seconds, which the float longitude already encodes. The seven roles in that
order: Atma, Amatya, Bhratri, Matri, Pitri, Gnati, Dara. Karakamsa (ch.33) is the navamsa sign the
Atmakaraka occupies — the lagna from which ch.33's effects are read.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.raman_saab.chart import varga as _varga          # substrate: division-sign arithmetic
from app.parashara.doctrine.sources import Citation

SOURCE: Final[Citation] = Citation("BPHS-32", 31)          # sl.1-2 — 7 planets, Sun..Saturn (primary)
AK_RULE_SOURCE: Final[Citation] = Citation("BPHS-32", 60)  # sl.3-8 — Atmakaraka = max degree-in-sign
ROLES_SOURCE: Final[Citation] = Citation("BPHS-32", 116)   # sl.13-17 — the karaka order
SEVEN_SCHOOL_SOURCE: Final[Citation] = Citation("BPHS-32", 149)   # the "seven significators" primary
EIGHTH_KARAKA_REJECTED: Final[Citation] = Citation("BPHS-32", 152)  # the "some say" Rahu variant, not used
KARAKAMSA_SOURCE: Final[Citation] = Citation("BPHS-33", 25)  # ch.33 sl.1 — effects of the Karakamsa

_SEVEN: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
#: descending-degree role order for the 7-karaka scheme (Putra merged into Matri, BPHS-32:149).
_ROLES: Final[tuple[str, ...]] = ("AK", "AmK", "BK", "MK", "PiK", "GK", "DK")
ROLE_NAMES: Final[Mapping[str, str]] = {
    "AK": "Atmakaraka", "AmK": "Amatyakaraka", "BK": "Bhratrikaraka", "MK": "Matrikaraka",
    "PiK": "Pitrikaraka", "GK": "Gnatikaraka", "DK": "Darakaraka",
}


def chara_karakas(longitudes: Mapping[str, float]) -> dict[str, str]:
    """{role: planet} for the 7 chara karakas, the visible planets ranked by degree-within-sign
    descending (BPHS-32). Nodes are never included, so the Atmakaraka is never Rahu/Ketu."""
    ranked = sorted((p for p in _SEVEN if p in longitudes),
                    key=lambda p: longitudes[p] % 30.0, reverse=True)
    return {role: planet for role, planet in zip(_ROLES, ranked)}


def atmakaraka(longitudes: Mapping[str, float]) -> str:
    """The Atmakaraka — the visible planet highest in degree-within-sign (BPHS-32:60)."""
    return chara_karakas(longitudes)["AK"]


def karakamsa(longitudes: Mapping[str, float]) -> int:
    """The Karakamsa: the navamsa sign (1..12) the Atmakaraka occupies — the ch.33 reading-lagna."""
    return _varga.navamsa_sign(longitudes[atmakaraka(longitudes)] % 360.0)
