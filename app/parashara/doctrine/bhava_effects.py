"""Effects of the twelve houses (BPHS ch.12-23) — Parashara's per-bhava effect slokas, indexed.

Unlike ch.24 (a rigid lord x house grid), these twelve chapters are topical essays on each bhava's
significations — health and beauty for the 1st, wealth for the 2nd, co-born for the 3rd, and so on.
This module is a thin, house-keyed view over `corpus_index.slokas_of` (house H = chapter H+11), so
every sloka is citable to Parashara's own line, with its topic heading where the OCR left one clean.

Honest scope: this archive.org scan's ch.12-23 carry heavier OCR damage than ch.24, so the index is
PARTIAL — `coverage()` reports the per-house sloka count so the partiality stays visible and is never
dressed up as complete. Making each conditional sloka fire on a chart is a later rules-extraction
pass; this is the faithful cited index it will build on.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.corpus_index import Sloka, slokas_of

#: House H (1..12) is BPHS chapter H+11 (ch.12 = 1st house ... ch.23 = 12th house).
_FIRST_HOUSE_CHAPTER: Final[int] = 11

#: A house's effect-sloka is just a Sloka of its chapter — no separate type needed.
BhavaEffect = Sloka


def _work_for(house: int) -> str:
    return f"BPHS-{house + _FIRST_HOUSE_CHAPTER}"


def effects_for_house(house: int) -> tuple[Sloka, ...]:
    """Parashara's indexed effect-slokas for `house` (1..12), in chapter order (BPHS ch.12-23)."""
    if not (1 <= house <= 12):
        raise ValueError("house must be 1..12")
    return slokas_of(_work_for(house))


def all_bhava_effects() -> Mapping[int, tuple[Sloka, ...]]:
    """{house: (slokas...)} for all twelve house-chapters."""
    return {h: slokas_of(_work_for(h)) for h in range(1, 13)}


def coverage() -> Mapping[int, int]:
    """{house: number of slokas indexed} — surfaced so the partial OCR coverage stays honest."""
    return {h: len(slokas_of(_work_for(h))) for h in range(1, 13)}
