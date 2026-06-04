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

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_CORPUS: Path = (Path(__file__).resolve().parents[3]
                 / "data" / "knowledge_library" / "sources")


@dataclass(frozen=True)
class Citation:
    work: str   # e.g. "HTJAH-I", "HPA-14", "GBB-3"
    line: int


def _resolve_file(work: str) -> Path | None:
    """The on-disk file backing a source tag (None if the tag is unknown)."""
    if work == "HTJAH-I":
        return _CORPUS / "how_to_judge_a_horoscope_raman" / "chapter_001_full-text-unsplit.md"
    if work == "HTJAH-II":
        return _CORPUS / "how_to_judge_horoscope_raman2" / "chapter_001_full-text-unsplit.md"
    if work.startswith("HPA-"):
        return _glob_chapter("hindu_predictive_astrology_raman", work.split("-", 1)[1])
    if work.startswith("GBB-"):
        return _glob_chapter("graha_bhava_balas_raman", work.split("-", 1)[1])
    if work == "3HC":
        return _first(_CORPUS / "three_hundred_combinations_raman")
    return None


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
