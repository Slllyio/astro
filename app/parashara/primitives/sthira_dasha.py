"""Sthira dasha — a rasi dasha with fixed spans by sign modality (BPHS ch.46, slokas 168-173).

    "In this Dasa system 7 years, 8 years and 9 years are the Dasa spans of the movable, fixed and
     dual signs in that order. The Dasa of the 12 signs begins from the Brahma Grahashrit rasi. The
     Dasas are counted onwards from the odd signs and in the reverse order from the even signs."
     (BPHS-46:168-169)

Spans: movable 7, fixed 8, dual 9 -> full cycle 4x7 + 4x8 + 4x9 = **96 years**. Traversal and
direction come from the shared `rasi_dasha` framework (odd start -> forward, even -> reverse).

## The seed: Brahma Grahashrit rasi (delegated, and why)
The starting sign is the one occupied by the **Brahma Graha** (BPHS-46:170-173) — selected among the
lords of the 6th/8th/12th, the 8th lord in the 8th, planets in the 8th, Saturn/Rahu/Ketu, resolved
by STRENGTH and then by degrees. That selection needs a strength primitive (Shadbala) this engine
does not yet carry, and the degree/lordship criteria are multi-step. So `sthira_timeline` takes the
Brahma-Graha sign as an argument rather than a half-encoded guess — exactly as the nakshatra dashas
take `elapsed_fraction`. `brahma_graha_note()` records the rule verbatim for when strength lands.
This keeps the spans + direction fully faithful and testable now, with the one strength-dependent
input honestly delegated.
"""
from __future__ import annotations

from typing import Final

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.rasi_dasha import (
    RasiDashaPeriod, modality, rasi_timeline, total_years)

#: Dasa span (years) per sign modality (BPHS-46:168).
MODALITY_SPAN: Final[dict[str, int]] = {"movable": 7, "fixed": 8, "dual": 9}

SOURCE: Final[Citation] = Citation("BPHS-46", 4846)          # "Now I am going to describe the Sthira Dasa"
SEED_SOURCE: Final[Citation] = Citation("BPHS-46", 4873)     # Brahma Graha determination
TOTAL_YEARS: Final[int] = 96


def span_for(sign: int) -> int:
    """Sthira dasa span for a sign: 7 movable / 8 fixed / 9 dual (BPHS-46:168)."""
    return MODALITY_SPAN[modality(sign)]


def sthira_timeline(brahma_graha_sign: int) -> tuple[RasiDashaPeriod, ...]:
    """The Sthira mahadasha timeline, starting from the Brahma Graha's sign.

    Direction follows the start sign's parity (odd -> onwards, even -> reverse), per BPHS-46:169.
    """
    return rasi_timeline(brahma_graha_sign, span_for)


def brahma_graha_note() -> str:
    """The Brahma Graha selection rule (BPHS-46:170-173), for the record until strength is encoded."""
    return ("Brahma Graha = among the lords of the 6th/8th/12th, the strongest in the Ascendant or "
            "7th in an odd sign within 6 houses of the house concerned; or the 8th lord in the 8th; "
            "or a planet in the 8th; Saturn/Rahu/Ketu may qualify. Ties broken by degrees, then "
            "strength. Needs a Shadbala primitive not yet in this engine.")


assert total_years(span_for) == TOTAL_YEARS, "Sthira cycle must total 96 years"
