"""Book source text: citation parsing, numbered passages, OCR-normalised quote matching."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final

DEFAULT_SOURCES_ROOT: Final[Path] = Path("data/knowledge_library/sources")

#: Citation prefix -> source directory (same files the extractors read).
BOOK_DIRS: Final[dict[str, str]] = {
    "HTJAH-I": "how_to_judge_a_horoscope_raman",
    "HTJAH-II": "how_to_judge_horoscope_raman2",
    "NH": "notable_horoscopes_raman",
    "3HC": "three_hundred_combinations_raman",
}
_FILE: Final[str] = "chapter_001_full-text-unsplit.md"
_CITATION_RE: Final = re.compile(r"^\s*([A-Za-z0-9-]+):(\d+)(?:-(\d+))?\s*$")
MIN_QUOTE_WORDS: Final[int] = 4


def book_path(root: Path, book: str) -> Path:
    path = root / BOOK_DIRS[book] / _FILE
    if not path.is_file():
        raise FileNotFoundError(f"source text for {book} not found at {path} "
                                f"(gitignored; pass --sources-root)")
    return path


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def parse_citation(citation: str) -> tuple[str, int, int]:
    m = _CITATION_RE.match(citation)
    if not m:
        raise ValueError(f"unparseable citation: {citation!r}")
    start = int(m.group(2))
    end = int(m.group(3) or start)
    if end < start:
        raise ValueError(f"inverted range: {citation!r}")
    return m.group(1), start, end


def passage(lines: list[str], start: int, end: int, context: int = 40) -> str:
    """1-based inclusive span plus context, each line prefixed with its book line number."""
    lo, hi = max(1, start - context), min(len(lines), end + context)
    return "\n".join(f"{n}| {lines[n - 1]}" for n in range(lo, hi + 1))


def spans(item: dict) -> list[tuple[int, int]]:
    """All cited (start, end) spans of an item; older items carry only 'citation'."""
    return [parse_citation(c)[1:] for c in item.get("citations") or [item["citation"]]]


def passage_multi(lines: list[str], spans_: list[tuple[int, int]], context: int = 40) -> str:
    """Union of the ±context windows around every span; non-adjacent blocks split by '...'."""
    wins = sorted((max(1, s - context), min(len(lines), e + context)) for s, e in spans_)
    merged: list[list[int]] = []
    for lo, hi in wins:
        if merged and lo <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return "\n...\n".join("\n".join(f"{n}| {lines[n - 1]}" for n in range(lo, hi + 1))
                          for lo, hi in merged)


def normalise(text: str) -> str:
    text = re.sub(r"-\s*\n\s*", "", text)          # de-hyphenate across hard wraps
    text = re.sub(r"(?<=\w)-(?=\w)", "", text)    # compound words wrapped at their hyphen
    text = re.sub(r"[^\w]+", " ", text.lower())    # punctuation/quotes/dashes -> space
    return " ".join(text.split())


def quote_found(lines: list[str], quote: str, line: int, window: int = 60) -> bool:
    """True when `quote` occurs in the source within `window` lines of `line`."""
    q = normalise(quote)
    if len(q.split()) < MIN_QUOTE_WORDS:
        return False
    lo, hi = max(0, line - 1 - window), min(len(lines), line + window)
    return q in normalise("\n".join(lines[lo:hi]))
