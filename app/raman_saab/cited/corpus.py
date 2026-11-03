"""The shared source layer for the cited tools: which books exist, how a citation token is read
back as verbatim text, and where in his books Raman wrote each of his worked conclusions.

Book texts live under ``data/knowledge_library/sources`` (gitignored; on the project PC). Every
function here degrades to "text not on disk" rather than failing, so the tools still run, with
citation tokens only, on a clone without the books.

Citation tokens are the engine's own (``doctrine/sources.py``): ``HTJAH-I:1586``,
``HPA-20:65-70``. KP Readers use the KP engine's tags (``app/kp/citations.py``): ``KPR1`` ..
``KPR6``, cited by line of the library file here.

Scope labels say what a book may be used for, so the library never presents a Prasna Marga or
KP passage as Raman's natal doctrine:

* ``Raman, natal``           the books the natal engine cites
* ``Raman, Jaimini system``  Studies in Jaimini (a separate system, not used for natal verdicts)
* ``horary`` / ``electional`` / ``annual``  Raman's non-natal books and Prasna Marga
* ``classical, not Raman``   BPHS and Phaladeepika (corroboration only)
* ``Rao lineage, not citable``  B. Suryanarain Rao's books
* ``KP, a separate system``  Krishnamurti's Readers
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Optional

from app.raman_saab.doctrine import book_registry

ROOT: Path = Path(__file__).resolve().parents[3]
SOURCES: Path = ROOT / "data" / "knowledge_library" / "sources"
GOLDENS: Path = ROOT / "tests" / "fixtures" / "raman_goldens.jsonl"

_NATAL = {"HTJAH-I", "HTJAH-II", "3HC", "3HCC", "3HCH", "HPA", "GBB", "NH", "AFB", "ASP", "MANUAL"}
_SCOPE_BY_TAG = {"JAIMINI": "Raman, Jaimini system", "PRASNA": "horary", "PM1": "horary",
                 "PM2": "horary", "PM2F": "horary", "MUHURTHA": "electional", "VARSHA": "annual"}

#: KP Readers, by the KP engine's source tags (app/kp/citations.py PAGE_SOURCES + KPR3).
KP_BOOKS: tuple[tuple[str, str, str], ...] = (
    ("KPR1", "kp_reader1_casting", "KP Reader 1: Casting the Horoscope"),
    ("KPR2", "kp_reader2_fundamentals_scan", "KP Reader 2: Fundamental Principles"),
    ("KPR3", "kp_reader3_predictive", "KP Reader 3: Predictive Stellar Astrology"),
    ("KPR4", "kp_reader4_marriage", "KP Reader 4: Marriage, Married Life and Children"),
    ("KPR5", "kp_reader5_transits", "KP Reader 5: Transits"),
    ("KPR6", "kp_reader6_horary", "KP Reader 6: Horary Astrology"),
)
KP_SCOPE = "KP, a separate system"


@dataclass(frozen=True)
class BookFile:
    """One citable text file: ``prefix`` is the work part of its citation token."""
    prefix: str          # e.g. "HTJAH-I", "HPA-20", "KPR4"
    book: str            # registry tag, e.g. "HPA"
    title: str
    scope: str
    path: Path


def scope_of(tag: str, status: str) -> str:
    if status == "corroboration":
        return "classical, not Raman"
    if status == "lineage-catalog":
        return "Rao lineage, not citable"
    if tag in _NATAL:
        return "Raman, natal"
    return _SCOPE_BY_TAG.get(tag, "Raman, other")


def _chapter_no(p: Path) -> Optional[int]:
    m = re.match(r"chapter_(\d+)_", p.name)
    return int(m.group(1)) if m else None


def book_files(sources: Path = SOURCES) -> list[BookFile]:
    """Every book file on disk that a citation token can name, in registry order, KP last.

    Mirrors ``doctrine/sources._resolve_file``: a multi-chapter book contributes one file per
    chapter number (the first, as the resolver picks it); a single-file book its fixed file or
    its first ``*.md``."""
    out: list[BookFile] = []
    for b in book_registry.BOOKS:
        if b.status == "catalog-only-out-of-scope":
            continue
        folder = sources / b.slug
        if not folder.is_dir():
            continue
        scope = scope_of(b.tag, b.status)
        title = b.title or b.tag
        if b.multi_chapter:
            seen: set[int] = set()
            for p in sorted(folder.glob("chapter_*.md")):
                n = _chapter_no(p)
                if n is None or n in seen:
                    continue
                seen.add(n)
                out.append(BookFile(f"{b.tag}-{n}", b.tag, title, scope, p))
        else:
            p = folder / b.fixed_file if b.fixed_file else next(iter(sorted(folder.glob("*.md"))), None)
            if p is not None and p.is_file():
                out.append(BookFile(b.tag, b.tag, title, scope, p))
    for tag, slug, title in KP_BOOKS:
        p = sources / slug / "chapter_001_full-text-unsplit.md"
        if p.is_file():
            out.append(BookFile(tag, tag, title, KP_SCOPE, p))
    return out


@lru_cache(maxsize=1)
def _file_index() -> dict[str, BookFile]:
    return {f.prefix: f for f in book_files()}


@lru_cache(maxsize=64)
def lines_of(path: Path) -> tuple[str, ...]:
    try:
        return tuple(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return ()


_CITE_RE = re.compile(r"^(?P<work>.+):(?P<start>\d+)(?:-(?P<end>\d+))?$")


def parse_cite(cite: str) -> Optional[tuple[str, int, int]]:
    m = _CITE_RE.match(cite.strip())
    if m is None:
        return None
    s, e = int(m.group("start")), int(m.group("end") or m.group("start"))
    return m.group("work"), min(s, e), max(s, e)


def file_for(work: str) -> Optional[BookFile]:
    return _file_index().get(work)


def passage(cite: str, *, context: int = 0) -> Optional[dict[str, Any]]:
    """The verbatim lines a citation token names, widened by ``context`` lines each side.

    Returns ``{"cite", "work", "start", "end", "lo", "hi", "text", "title", "scope"}`` or None
    when the token is malformed, its book is unknown, or the text is not on this machine."""
    parsed = parse_cite(cite)
    if parsed is None:
        return None
    work, start, end = parsed
    f = file_for(work)
    if f is None:
        return None
    lines = lines_of(f.path)
    if not lines or start > len(lines):
        return None
    lo, hi = max(1, start - context), min(len(lines), end + context)
    return {"cite": cite, "work": work, "start": start, "end": end, "lo": lo, "hi": hi,
            "text": "\n".join(lines[lo - 1:hi]).strip(), "title": f.title, "scope": f.scope}


# -- Raman's worked examples ------------------------------------------------------------------

def worked_examples(path: Path = GOLDENS) -> list[dict[str, Any]]:
    """Every worked-example record in the golden fixture (synthetic self-tests left out)."""
    out = []
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if s and not s.startswith("#"):
            rec = json.loads(s)
            if rec.get("case_type") != "self_test":
                out.append(rec)
    return out


def example(record_id: str) -> dict[str, Any]:
    for rec in worked_examples():
        if rec.get("id") == record_id:
            return rec
    raise KeyError(record_id)


def is_confirmed(entry: dict[str, Any]) -> bool:
    """Scored only if reviewed CONFIRMED and not a bare DRAFT (as tests/raman_saab/test_goldens)."""
    return entry.get("verdict_review") == "CONFIRMED" and entry.get("verdict") != "DRAFT"


_WORD = re.compile(r"[a-z0-9]+")


def _norm_with_map(lines: tuple[str, ...]) -> tuple[str, list[int]]:
    """Lower-cased words of the file joined by single spaces, and for each character the
    1-based line it came from. Lets a sentence that wraps across lines be found."""
    buf: list[str] = []
    owner: list[int] = []
    for i, line in enumerate(lines, start=1):
        for w in _WORD.findall(line.lower()):
            if buf:
                buf.append(" ")
                owner.append(i)
            buf.append(w)
            owner.extend([i] * len(w))
    return "".join(buf), owner


@lru_cache(maxsize=16)
def _normed(path: Path) -> tuple[str, tuple[int, ...]]:
    text, owner = _norm_with_map(lines_of(path))
    return text, tuple(owner)


def _book_prefix(rec: dict[str, Any]) -> Optional[str]:
    for c in rec.get("citations") or ():
        p = parse_cite(c)
        if p is not None:
            return p[0]
    book = rec.get("book")
    return book if book and file_for(book) else None


def locate(prose: str, rec: dict[str, Any], *, window: int = 400) -> Optional[str]:
    """The citation token of the line where Raman wrote ``prose`` for this record, found by
    matching its words in the book text near the lines the record cites (within ``window``
    lines). None if the prose is a paraphrase (some labels are a reviewer's summary, not a
    quote), it is not found near this chart's write-up, or the book is not on disk. A wrong
    location is worse than none, so a match elsewhere in the book is never returned."""
    work = _book_prefix(rec)
    f = file_for(work) if work else None
    # labels elide with "...": search for the longest unbroken piece
    pieces = [_WORD.findall(x.lower()) for x in re.split(r"\.\.\.|\u2026", prose or "")]
    words = max(pieces, key=len) if pieces else []
    if f is None or len(words) < 6:
        return None
    text, owner = _normed(f.path)
    if not text:
        return None
    span = [p for p in (parse_cite(c) for c in rec.get("citations") or ()) if p and p[0] == work]
    lo = min(p[1] for p in span) - window if span else 1
    hi = max(p[2] for p in span) + window if span else len(owner) + 1
    full = " ".join(words)
    # the whole sentence first (gives its full line span), then ever shorter leading runs
    for probe in (full, *(" ".join(words[:n]) for n in (12, 8) if len(words) > n)):
        hits = [m.start() for m in re.finditer(re.escape(probe), text) if lo <= owner[m.start()] <= hi]
        if not hits:
            continue
        pos = hits[0]
        s, e = owner[pos], owner[min(len(owner) - 1, pos + len(probe) - 1)]
        return f"{work}:{s}" if s == e else f"{work}:{s}-{e}"
    return None


def discussion_span(rec: dict[str, Any], *, max_lines: int = 400) -> Optional[str]:
    """The span of Raman's own write-up of this chart: from the first to the last line the
    record cites, as a token. Capped at ``max_lines`` so a stray citation cannot pull in a book."""
    parsed = [p for p in (parse_cite(c) for c in rec.get("citations") or ()) if p]
    if not parsed:
        return None
    work = parsed[0][0]
    same = [p for p in parsed if p[0] == work]
    lo = min(p[1] for p in same)
    hi = max(p[2] for p in same)
    hi = min(hi, lo + max_lines)
    return f"{work}:{lo}" if lo == hi else f"{work}:{lo}-{hi}"


def iter_rules() -> Iterator[Any]:
    """Every RuleRecord in the rule store."""
    from app.raman_saab.doctrine.rule_sets import ALL_RULES
    yield from ALL_RULES


def rule_cite(rule: Any) -> str:
    src = rule.source
    return f"{src.work}:{src.line}" if hasattr(src, "work") else str(src)
