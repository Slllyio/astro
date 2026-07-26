"""Citation registry — maps a source tag to its on-disk corpus file and verifies
that a cited line actually exists. Every ``RuleRecord`` carries a ``Citation``;
a test (spec §5.4/§11) asserts every cited line resolves on disk.

Tags follow the methodology-overview §0 convention:
    HTJAH-I / HTJAH-II   — How to Judge a Horoscope, Vol I / II (chapter_001)
    HPA-NN               — Hindu Predictive Astrology, chapter NN
    GBB-N                — Graha & Bhava Balas, chapter N
    3HC                  — Three Hundred Important Combinations
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.raman_saab.doctrine import book_registry

_CORPUS: Path = (Path(__file__).resolve().parents[3]
                 / "data" / "knowledge_library" / "sources")


@dataclass(frozen=True)
class Citation:
    work: str   # e.g. "HTJAH-I", "HPA-14", "GBB-3"
    line: int


def _resolve_file(work: str) -> Path | None:
    """The on-disk file backing a source tag, via the unified `book_registry`. None if the tag
    is unknown OR points at an out-of-scope (non-citable) book — the divergence firewall."""
    entry = book_registry.entry_for(work)
    if entry is None:
        return None
    if entry.multi_chapter:
        return _glob_chapter(entry.slug, work.split("-", 1)[1])
    if entry.fixed_file is not None:
        return _CORPUS / entry.slug / entry.fixed_file
    return _first(_CORPUS / entry.slug)


def _glob_chapter(folder: str, num: str) -> Path | None:
    try:
        hits = sorted((_CORPUS / folder).glob(f"chapter_{int(num):03d}_*.md"))
    except (ValueError, OSError):
        return None
    return hits[0] if hits else None


def _first(folder: Path) -> Path | None:
    hits = sorted(folder.glob("*.md")) if folder.is_dir() else []
    return hits[0] if hits else None


@lru_cache(maxsize=256)
def _line_count(path: Path) -> int:
    try:
        with path.open(encoding="utf-8") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def verify(citation: Citation) -> bool:
    """True iff the cited file exists and has at least `line` lines (1-indexed)."""
    path = _resolve_file(citation.work)
    return (path is not None and path.is_file()
            and 1 <= citation.line <= _line_count(path))


#: A citation token: WORK:line or WORK:start-end (WORK may itself contain hyphens,
#: e.g. "HTJAH-I", "GBB-9", "BPHS-83-iii"; the line-spec is after the FINAL colon).
_CITE_RE = re.compile(r"^(?P<work>.+):(?P<start>\d+)(?:-(?P<end>\d+))?$")


def passage(cite: str, *, context: int = 0) -> Optional[dict]:
    """The verbatim source lines a citation token points to — the click-to-source backend.

    Returns ``{"work", "start", "end", "text"}`` or None. None when the token is malformed OR
    its work is outside the citable registry (the divergence firewall — CLASSICAL_NONCITABLE
    works like BPHS / Praśna Mārga are deliberately NOT resolved here; the caller shows a
    "classical corroboration, outside Raman's citable canon" note instead). `context` widens the
    returned window by N lines on each side for readability without changing the cited span."""
    m = _CITE_RE.match(cite.strip())
    if m is None:
        return None
    work = m.group("work")
    start = int(m.group("start"))
    end = int(m.group("end") or start)
    if end < start:
        start, end = end, start
    path = _resolve_file(work)
    if path is None or not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if start > len(lines):
        return None
    lo = max(1, start - context)
    hi = min(len(lines), end + context)
    return {"work": work, "start": start, "end": end,
            "text": "\n".join(lines[lo - 1:hi]).strip()}
