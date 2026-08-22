"""A faithful numbered-sloka index for ANY corpus chapter (BPHS or allied), in place.

The classical texts are printed as numbered slokas, often under ALL-CAPS topic headings. This module
turns any chapter into a list of `Sloka(number, topic, text, source)` by parsing those numbers — the
text is read from the corpus file, never transcribed into code, so every sloka is citable to its own
line. It is the shared backbone the structured doctrine modules build on (ch.24's lord grid, the
house-effect index, the karakatwa and yoga tables): they add MEANING on top of this addressing.

Robustness (this is OCR): sloka numbers are matched with tolerant separators ("N." / "N-M." / "N)"),
accepted only when strictly increasing within a small forward gap (so OCR-lost numbers are skipped
and stray numbers inside Notes/lists are rejected), and topic headings are kept only when they read
as clean ASCII caps (Devanagari rendered as latin gibberish is dropped). A sloka whose number the OCR
destroyed is simply absent, never mis-keyed — coverage is honest, not faked.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Final, Optional

from app.parashara.doctrine.sources import Citation, resolve_file

#: A numbered sloka start: "N." / "N-M." / "N)" etc., tolerant of OCR separators.
_SLOKA_RE: Final[re.Pattern] = re.compile(r"^\s*(\d+)(?:\s*-\s*\d+)?\s*[.\-):]\s")
#: A topic heading candidate: the text before the first colon on a numbered line.
_TITLE_RE: Final[re.Pattern] = re.compile(r"^\s*\d+(?:\s*-\s*\d+)?\s*[.\-):]\s*([^:]{3,55}):")
#: Forward gap tolerated when a sloka number is OCR-lost (still strictly increasing).
_MAX_GAP: Final[int] = 4


@dataclass(frozen=True)
class Sloka:
    """One numbered sloka of a chapter, cited to its line."""
    work: str                # e.g. "BPHS-32"
    number: int              # the sloka number within the chapter
    topic: Optional[str]     # ALL-CAPS heading if the sloka opens a clean one, else None
    text: str                # the sloka's prose, read verbatim (Notes/Devanagari stripped)
    source: Citation


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
        return None                                  # not a caps heading
    return title


def _clean_text(raw: list[str]) -> str:
    kept: list[str] = []
    for ln in raw:
        s = ln.strip()
        if not s:
            continue
        if re.match(r"note", s, re.I):               # translator commentary -> sloka body ended
            break
        letters = [c for c in s if c.isalpha()]
        if letters and sum(ord(c) < 128 for c in letters) / len(letters) < 0.6:
            continue                                 # mostly-non-ASCII = Devanagari OCR garbage
        kept.append(s)
    text = " ".join(kept)
    text = re.sub(r"^\s*\d+(?:\s*-\s*\d+)?\s*[.\-):]?\s*", "", text)   # leading sloka number/range
    text = re.sub(r"^[A-Z][^:]{2,55}:\s*", "", text)                   # topic heading prefix
    text = re.sub(r"\s+", " ", text).strip()
    cut = text.rfind(".")
    return text[:cut + 1] if cut >= 20 else text


@lru_cache(maxsize=256)
def slokas_of(work: str) -> tuple[Sloka, ...]:
    """Every numbered sloka of `work` (e.g. ``"BPHS-32"``), in order, cited. Empty if unresolvable."""
    path = resolve_file(work)
    if path is None:
        return ()
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    starts: list[tuple[int, int, Optional[str]]] = []
    last = 0
    for i, ln in enumerate(lines):
        m = _SLOKA_RE.match(ln)
        if not m:
            continue
        n = int(m.group(1))
        if last == 0 and 1 <= n <= 3:
            last = n - 1                             # allow the chapter to open at sloka 1..3
        if last < n <= last + _MAX_GAP:
            starts.append((n, i, _clean_title(ln)))
            last = n
    out: list[Sloka] = []
    for k, (n, i0, title) in enumerate(starts):
        end = starts[k + 1][1] if k + 1 < len(starts) else len(lines)
        out.append(Sloka(work=work, number=n, topic=title,
                         text=_clean_text(lines[i0:end]), source=Citation(work, i0 + 1)))
    return tuple(out)


def find_slokas(work: str, pattern: str) -> tuple[Sloka, ...]:
    """The slokas of `work` whose text matches `pattern` (case-insensitive regex) — a cited grep."""
    rx = re.compile(pattern, re.I)
    return tuple(s for s in slokas_of(work) if rx.search(s.text))
