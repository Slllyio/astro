"""BPHS ch.33 — effects read from the Karakamsa, as a cited section catalogue.

The Karakamsa (the navamsa sign of the Atmakaraka, computed in `chara_karaka.py`) is a whole reading
lagna: ch.33 gives its effects by the sign it falls in, by planets tenanting it, and by each house
counted from it (2nd..12th from Karakamsa). The chapter is prose keyed by CAPS section headers, but
its per-sign sentences do not segment cleanly (mixed effect-before/after-name phrasing, OCR "etc."
boundaries), so — per "no silent approximation" — this indexes the chapter by its SECTIONS, each read
verbatim and cited to its own header line, rather than forcing a false 12-cell grid. It mirrors the
`yoga_catalogue` / `argala` pattern: a faithful queryable catalogue, applied on demand, not a
misattributed detector.

The Karakamsa-in-signs section (sl.2-8) is offered on its own so a reading can surface it beside the
chart's actual Karakamsa sign.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Final, Optional

from app.parashara.doctrine.sources import Citation, resolve_file

_WORK: Final[str] = "BPHS-33"
_HEADER = re.compile(r"^\s*(\d+(?:-\d+)?)\.\s*([A-Z][A-Z0-9 ,;:'/()-]{6,})")


@dataclass(frozen=True)
class KarakamsaSection:
    slokas: str          # the sloka range, e.g. "2-8"
    title: str           # the CAPS section title, cleaned
    text: str            # the section's English prose, read verbatim
    source: Citation     # the header line


def _english(raw: list[str]) -> str:
    """Join a section's lines, drop the Devanagari (non-ASCII) transliteration runs, collapse space."""
    joined = " ".join(raw)
    joined = re.sub(r"[^\x00-\x7f]+", " ", joined)         # strip Sanskrit
    joined = re.sub(r"\bBrihat Parasara[^.]*Sastra\b", " ", joined)   # running header
    joined = re.sub(r"\bChapter \d+\b", " ", joined)
    return re.sub(r"\s+", " ", joined).strip()


@lru_cache(maxsize=1)
def _sections() -> tuple[KarakamsaSection, ...]:
    path = resolve_file(_WORK)
    if path is None:
        return ()
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    heads: list[tuple[int, str, str]] = []
    for i, ln in enumerate(lines):
        m = _HEADER.match(ln)
        if m:
            # the CAPS run runs into the prose ("... KARAKAMSA : O Brahmin"); keep only the title.
            title = re.split(r"[;:]", m.group(2))[0]
            title = re.sub(r"\s+", " ", title).strip().rstrip(":;, ")
            heads.append((i, m.group(1), title))
    out: list[KarakamsaSection] = []
    for k, (i0, num, title) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        text = _english(lines[i0:end])
        out.append(KarakamsaSection(slokas=num, title=title, text=text,
                                    source=Citation(_WORK, i0 + 1)))
    return tuple(out)


def sections() -> tuple[KarakamsaSection, ...]:
    """Every cited CAPS section of ch.33 (Karakamsa-in-signs, planets-in-Karakamsa, Nth-from-...)."""
    return _sections()


def find(keyword: str) -> tuple[KarakamsaSection, ...]:
    """Sections whose title contains `keyword` (case-insensitive) — a cited grep over the chapter."""
    kw = keyword.upper()
    return tuple(s for s in _sections() if kw in s.title.upper())


def karakamsa_in_signs() -> Optional[KarakamsaSection]:
    """The sl.2-8 section giving the Atmakaraka's effect by the sign of its navamsa."""
    hits = [s for s in _sections() if "VARIOUS SIGNS" in s.title.upper()]
    return hits[0] if hits else None
