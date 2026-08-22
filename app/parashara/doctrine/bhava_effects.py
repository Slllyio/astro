"""Effects of the twelve houses (BPHS ch.12-23) — Parashara's per-bhava effect slokas, indexed.

Unlike ch.24 (a rigid lord x house grid), these twelve chapters are topical essays on each bhava's
significations — health and beauty for the 1st, wealth for the 2nd, co-born for the 3rd, and so on —
given as numbered slokas, some under ALL-CAPS topic headings ("COMBINATIONS FOR WEALTH"). This module
indexes each house-chapter by its numbered slokas IN PLACE (text read from the corpus, never
transcribed), so every sloka is citable to Parashara's own line, with its topic heading attached
where the OCR left one clean.

Honest scope: this archive.org scan's ch.12-23 carry heavier OCR damage than ch.24 — some sloka
numbers are mangled and a few topic headings are unreadable. The parser is robust (tolerant
separators, "N-M." ranges, strict-increasing numbers to reject noise) and captures what is cleanly
numbered; a sloka whose number the OCR destroyed is simply not indexed rather than mis-keyed. Per
`REPORT COMPLETENESS`, `coverage()` reports how many slokas each house yielded, so the partiality is
visible and never dressed up as complete. Making each conditional sloka fire on a chart is a later
rules-extraction pass; this is the faithful cited index it will build on.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Final, Mapping, Optional

from app.parashara.doctrine.sources import Citation, resolve_file

#: House H (1..12) is BPHS chapter H+11 (ch.12 = 1st house ... ch.23 = 12th house).
_FIRST_HOUSE_CHAPTER: Final[int] = 11
#: A numbered sloka start: "N." / "N-M." / "N)" etc., tolerant of OCR separators.
_SLOKA_RE: Final[re.Pattern] = re.compile(r"^\s*(\d+)(?:\s*-\s*\d+)?\s*[.\-):]\s")
#: A clean topic heading: mostly-caps words before a colon (rejects Devanagari-OCR garbage).
_TITLE_RE: Final[re.Pattern] = re.compile(r"^\s*\d+(?:\s*-\s*\d+)?\s*[.\-):]\s*([^:]{3,55}):")


@dataclass(frozen=True)
class BhavaEffect:
    """One numbered effect-sloka of a house-chapter, cited to its line (BPHS ch.12-23)."""
    house: int               # 1..12
    sloka: int               # the sloka number within the chapter
    topic: Optional[str]     # the ALL-CAPS heading, if the sloka opens a clean one
    text: str                # the sloka's effect prose, read verbatim (Notes/Devanagari stripped)
    source: Citation         # BPHS-(H+11) : the sloka's line


def _clean_title(line: str) -> Optional[str]:
    m = _TITLE_RE.match(line)
    if m is None:
        return None
    title = re.sub(r"\s+", " ", m.group(1)).strip()
    letters = [c for c in title if c.isalpha()]
    if len(letters) < 4 or len(title.split()) < 2:
        return None
    if sum(ord(c) < 128 for c in letters) / len(letters) < 0.85:
        return None                                  # too much non-ASCII = OCR garbage
    if sum(c.isupper() for c in letters) / len(letters) < 0.7:
        return None                                  # not a caps heading (e.g. ordinary prose)
    return title


def _clean_text(raw: list[str]) -> str:
    kept: list[str] = []
    for ln in raw:
        s = ln.strip()
        if not s:
            continue
        if re.match(r"note", s, re.I):
            break
        letters = [c for c in s if c.isalpha()]
        if letters and sum(ord(c) < 128 for c in letters) / len(letters) < 0.6:
            continue
        kept.append(s)
    text = " ".join(kept)
    text = re.sub(r"^\s*\d+(?:\s*-\s*\d+)?\s*[.\-):]?\s*", "", text)   # leading sloka number/range
    text = re.sub(r"^[A-Z][^:]{2,55}:\s*", "", text)                   # topic heading prefix
    text = re.sub(r"\s+", " ", text).strip()
    cut = text.rfind(".")
    return text[:cut + 1] if cut >= 20 else text


@lru_cache(maxsize=1)
def _index() -> dict[int, tuple[BhavaEffect, ...]]:
    out: dict[int, tuple[BhavaEffect, ...]] = {}
    for house in range(1, 13):
        path = resolve_file(f"BPHS-{house + _FIRST_HOUSE_CHAPTER}")
        if path is None:
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        # strict-increasing sloka starts (tolerant separators, "N-M." ranges); reject OCR noise.
        starts: list[tuple[int, int, Optional[str]]] = []
        last = 0
        for i, ln in enumerate(lines):
            m = _SLOKA_RE.match(ln)
            if not m:
                continue
            n = int(m.group(1))
            if last == 0 and 1 <= n <= 3:
                last = n - 1                         # allow the chapter to open at sloka 1..3
            if last < n <= last + 4:                 # strictly increasing; skip OCR-lost numbers
                starts.append((n, i, _clean_title(ln)))
                last = n
        effects: list[BhavaEffect] = []
        for k, (n, i0, title) in enumerate(starts):
            end = starts[k + 1][1] if k + 1 < len(starts) else len(lines)
            effects.append(BhavaEffect(house=house, sloka=n, topic=title,
                                       text=_clean_text(lines[i0:end]),
                                       source=Citation(f"BPHS-{house + _FIRST_HOUSE_CHAPTER}", i0 + 1)))
        out[house] = tuple(effects)
    return out


def effects_for_house(house: int) -> tuple[BhavaEffect, ...]:
    """Parashara's indexed effect-slokas for `house` (1..12), in chapter order (BPHS ch.12-23)."""
    if not (1 <= house <= 12):
        raise ValueError("house must be 1..12")
    return _index().get(house, ())


def all_bhava_effects() -> Mapping[int, tuple[BhavaEffect, ...]]:
    """{house: (effects...)} for all twelve house-chapters."""
    return dict(_index())


def coverage() -> Mapping[int, int]:
    """{house: number of slokas indexed} — surfaced so the partial OCR coverage stays honest."""
    return {h: len(v) for h, v in _index().items()}
