"""Citation resolution for the Parashara engine — the same apparatus, this engine's registry.

Every doctrine record carries a `Citation(work, line)` pointing at a REAL line in a REAL corpus
file. `verify()` checks the line exists; `passage()` returns the verbatim text (click-to-source).
A citation that does not resolve is a defect, not a stylistic preference — it is what separates
"faithfully encoded" from "plausibly worded".

Deliberately parallel to `app/raman_saab/doctrine/sources.py` in shape and behaviour, but bound to
`app.parashara.doctrine.book_registry` — so BPHS resolves as ROOT here, where the Raman engine
resolves it only as corroboration. Same tokens, same corpus, different authority.

Tokens:  ``BPHS-7:220``  ``BPHS-46:1120``  ``PHALA-3:112``  ``HTJAH-I:1586``
(the work may itself contain hyphens; the line-spec is after the FINAL colon).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.parashara.doctrine import book_registry

#: The shared corpus. Stream-agnostic on purpose: the TEXTS belong to no engine, only the
#: authority assigned to them does.
_CORPUS: Path = (Path(__file__).resolve().parents[3]
                 / "data" / "knowledge_library" / "sources")


@dataclass(frozen=True)
class Citation:
    """A pointer into the corpus: `work` tag + 1-indexed line."""
    work: str   # e.g. "BPHS-7", "PHALA-3", "SARAVALI-12"
    line: int


def _resolve_file(work: str) -> Optional[Path]:
    """The on-disk file backing a tag, or None when the tag is unknown / out-of-scope."""
    entry = book_registry.entry_for(work)
    if entry is None:
        return None
    if entry.multi_chapter:
        return _glob_chapter(entry.slug, work.split("-", 1)[1])
    if entry.fixed_file is not None:
        return _CORPUS / entry.slug / entry.fixed_file
    return _first(_CORPUS / entry.slug)


def resolve_file(work: str) -> Optional[Path]:
    """Public: the corpus file backing a work tag (e.g. ``"BPHS-24"``), or None.

    For doctrine modules that INDEX a whole chapter in place (rather than cite single lines) — they
    parse the file `resolve_file` returns, so effect text is never transcribed into code, only keyed.
    """
    return _resolve_file(work)


def _glob_chapter(folder: str, num: str) -> Optional[Path]:
    """chapter_NNN_*.md for a chapter number, tolerating 3-, 2- or 1-digit zero-padding on disk
    (the allied scrapes are inconsistent — Phaladeepika files are `chapter_05_`, BPHS `chapter_005_`)."""
    try:
        n = int(num)
    except ValueError:
        return None
    base = _CORPUS / folder
    for pat in (f"chapter_{n:03d}_*.md", f"chapter_{n:02d}_*.md", f"chapter_{n}_*.md"):
        try:
            hits = sorted(base.glob(pat))
        except OSError:
            return None
        if hits:
            return hits[0]
    return None


def _first(folder: Path) -> Optional[Path]:
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


#: WORK:line or WORK:start-end. WORK may contain hyphens, so the line-spec is after the LAST colon.
_CITE_RE = re.compile(r"^(?P<work>.+):(?P<start>\d+)(?:-(?P<end>\d+))?$")


def passage(cite: str, *, context: int = 0) -> Optional[dict]:
    """The verbatim source lines a citation token points to — the click-to-source backend.

    Returns ``{"work", "start", "end", "text", "status"}`` or None (malformed token, or a work
    outside the resolvable registry). ``status`` carries the registry tier so a reader can see at
    a glance whether a passage is Parashara's own word (`root`), the allied lineage, or merely
    corroboration. `context` widens the returned window without changing the cited span.
    """
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
            "text": "\n".join(lines[lo - 1:hi]).strip(),
            "status": book_registry.status_of(work)}
