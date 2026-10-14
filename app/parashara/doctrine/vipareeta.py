"""Vipareeta (reversal) yogas — Harsha, Sarala, Vimala: good FROM the dusthanas (BPHS-48).

    "(1) If the 6th house is occupied or aspected by malefics and the lord of the 6th is in
     Dusthana (6th, 8th or 12th), such a disposition produces Harsha yoga ... will overcome his
     enemies. (2) If the lord of the 8th house is placed in the 6th, the 8th or the 12th, the yoga
     caused is known as Sarala Yoga ... long-lived, resolute ... (3) If the lord of the 12th be in
     a Dusthana and be aspected by or associated with malefics, the Yoga so produced is called
     Vimala Yoga ... will spend little and save much money." (BPHS-48:124-145)

PROVENANCE — labeled, per the honesty rule: this passage is the translator's quotation of
**Mantreswara's Phaladeepika ch.VI** inside the BPHS volume (BPHS-48:120 names him). It is allied
doctrine carried by the root text's own pages, not Parashara's voice; every consumer must say so.
It matters because it is the corpus's one polarity-resolver for the dusthanas: adversity TO the
houses of adversity favours the native.

Malefics here are the natural set (Sun/Mars/Saturn + nodes for occupancy; nodes cast no drishti in
this engine, BPHS-26). Whole-sign throughout.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.functional_nature import FIXED_MALEFICS
from app.parashara.primitives.graha_drishti import aspects_sign
from app.parashara.primitives.relationships import SIGN_LORDS

ATTRIBUTION_SOURCE: Final[Citation] = Citation("BPHS-48", 120)   # "Mantreswara's Phaladeepika"
HARSHA_SOURCE: Final[Citation] = Citation("BPHS-48", 124)
SARALA_SOURCE: Final[Citation] = Citation("BPHS-48", 133)
VIMALA_SOURCE: Final[Citation] = Citation("BPHS-48", 140)

#: The provenance sentence every consumer carries beside these yogas.
PROVENANCE: Final[str] = ("translator's quotation of Mantreswara's Phaladeepika ch.VI "
                          "(BPHS-48:120) — allied doctrine, not Parashara's own voice")

_DUSTHANAS: Final[tuple[int, ...]] = (6, 8, 12)
#: Malefics that can cast the drishti these conditions need (nodes cast none in this engine).
_ASPECTING_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn"})


@dataclass(frozen=True)
class VipareetaYoga:
    name: str        # Harsha | Sarala | Vimala
    house: int       # the dusthana it redeems: 6 | 8 | 12
    reason: str
    source: Citation


def _sign_of(lon: float) -> int:
    return int(lon % 360.0 // 30) + 1


def detect(longitudes: Mapping[str, float], *, asc_sign: int) -> tuple[VipareetaYoga, ...]:
    """The vipareeta yogas present in the chart (whole-sign; conditions verbatim from BPHS-48)."""
    signs = {p: _sign_of(lon) for p, lon in longitudes.items()}
    house_signs = {h: ((asc_sign - 1 + h - 1) % 12) + 1 for h in _DUSTHANAS}
    dusthana_signs = frozenset(house_signs.values())

    def malefic_on_or_aspecting(target_sign: int) -> bool:
        occupied = any(p in FIXED_MALEFICS and s == target_sign for p, s in signs.items())
        aspected = any(p in _ASPECTING_MALEFICS and p in signs
                       and aspects_sign(p, signs[p], target_sign) for p in _ASPECTING_MALEFICS)
        return occupied or aspected

    out: list[VipareetaYoga] = []

    lord6 = SIGN_LORDS[house_signs[6]]
    if (signs.get(lord6) in dusthana_signs and malefic_on_or_aspecting(house_signs[6])):
        out.append(VipareetaYoga(
            "Harsha", 6,
            f"the 6th is touched by malefics and its lord {lord6} sits in a dusthana — "
            "'will overcome his enemies'", HARSHA_SOURCE))

    lord8 = SIGN_LORDS[house_signs[8]]
    if signs.get(lord8) in dusthana_signs:
        out.append(VipareetaYoga(
            "Sarala", 8,
            f"the 8th lord {lord8} sits in a dusthana — 'long-lived, resolute ... prosperous'",
            SARALA_SOURCE))

    lord12 = SIGN_LORDS[house_signs[12]]
    l12_sign = signs.get(lord12)
    if l12_sign in dusthana_signs:
        with_malefic = any(p in FIXED_MALEFICS and s == l12_sign and p != lord12
                           for p, s in signs.items())
        aspected = any(p in _ASPECTING_MALEFICS and p in signs and p != lord12
                       and aspects_sign(p, signs[p], l12_sign) for p in _ASPECTING_MALEFICS)
        if with_malefic or aspected:
            out.append(VipareetaYoga(
                "Vimala", 12,
                f"the 12th lord {lord12} sits in a dusthana under malefic contact — "
                "'will spend little and save much'", VIMALA_SOURCE))
    return tuple(out)
