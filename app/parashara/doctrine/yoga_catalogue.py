"""A cited catalogue of Parashara's yoga chapters (BPHS ch.35-42).

Some yoga families have clean, chart-computable detectors (Nabhasa ch.35, lunar ch.37, solar ch.38,
Gaja-Kesari ch.36 — encoded in their own modules). Others — the Raja yogas (ch.39, largely
Karakamsa/Jaimini-based), the royal-association yogas (ch.40), the wealth yogas (ch.41) and the
penury yogas (ch.42) — Parashara gives as MANY bespoke specific combinations, not general rules with
a single citable principle. Synthesizing a general detector for those would misattribute doctrine, so
they are preserved faithfully as a CITED CATALOGUE instead: every yoga sloka, indexed in place from
the corpus, keyed by its chapter, each traceable to its own line.

`catalogue()` returns {chapter label: slokas}; `find(pattern)` is a cited grep across all yoga
chapters. This is the honest home for the yogas that resist a faithful detector — a reference, not a
verdict engine.
"""
from __future__ import annotations

from typing import Final, Mapping

from app.parashara.doctrine.corpus_index import Sloka, find_slokas, slokas_of

#: The yoga chapters and their subjects (BPHS ch.35-42).
YOGA_CHAPTERS: Final[Mapping[int, str]] = {
    35: "Nabhasa yogas", 36: "Other yogas", 37: "Lunar yogas", 38: "Solar yogas",
    39: "Raja yogas", 40: "Yogas for royal association", 41: "Dhana (wealth) yogas",
    42: "Combinations for penury"}


def catalogue() -> dict[str, tuple[Sloka, ...]]:
    """{chapter label: (slokas...)} across all yoga chapters, each sloka cited to its own line."""
    return {label: slokas_of(f"BPHS-{ch}") for ch, label in YOGA_CHAPTERS.items()}


def slokas_for(chapter: int) -> tuple[Sloka, ...]:
    """The indexed yoga slokas of one yoga chapter (35..42)."""
    if chapter not in YOGA_CHAPTERS:
        raise ValueError(f"chapter {chapter} is not a yoga chapter {tuple(YOGA_CHAPTERS)}")
    return slokas_of(f"BPHS-{chapter}")


def find(pattern: str) -> tuple[Sloka, ...]:
    """A cited grep across every yoga chapter — the yoga slokas whose text matches `pattern`."""
    out: list[Sloka] = []
    for ch in YOGA_CHAPTERS:
        out.extend(find_slokas(f"BPHS-{ch}", pattern))
    return tuple(out)
