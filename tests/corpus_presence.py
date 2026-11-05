"""Skip guards for tests that need data deliberately kept outside git.

Two such classes exist (both are the CI-red "1165-failure class"):

* The Raman doctrine corpus (``data/knowledge_library/sources`` — copyrighted
  book text, gitignored). Every citation-resolution assertion needs it.
* Generated ML artifacts (``app/medini/data/*.parquet``, ``data/`` run outputs —
  large, reproducible, gitignored).

Tests that touch either skip cleanly where the data is absent (CI included) and
run in full wherever it is vendored — the same pattern
``tests/raman_saab/doctrine/test_source_lock.py`` already established. Import as
``from corpus_presence import needs_corpus`` (tests/ is on sys.path, same as
``bphs_compliance``).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.doctrine import source_lock

HAS_CORPUS = bool(source_lock.cited_files())

#: Skip marker for tests that resolve doctrine citations against the corpus.
needs_corpus = pytest.mark.skipif(
    not HAS_CORPUS, reason="corpus not present on this machine")


def needs_file(*paths: str) -> pytest.MarkDecorator:
    """Skip marker for tests that read gitignored data artifacts.

    Repo-root-relative paths; the test skips unless EVERY path exists.
    """
    missing = [p for p in paths if not (Path(__file__).resolve().parents[1] / p).exists()]
    return pytest.mark.skipif(
        bool(missing),
        reason=f"gitignored data not present on this machine: {', '.join(missing)}")

def vendored_books() -> set[str]:
    """Tags of live books that actually have text on this machine.

    `HAS_CORPUS` is all-or-nothing: truthy the moment ANY cited file resolves. That is right
    for CI, where nothing is vendored and everything skips, and wrong on a box that has most
    of the corpus but not all of it — one absent book turns into hard failures in tests that
    are really reporting "this scan is not on this machine".

    The concrete case is ASP (`ashtakavarga_system_raman`). It is the one live book with no
    archive.org source — the bundle records it as a local OCR of a user-supplied PDF — so it
    cannot be re-downloaded, and its folder exists but is empty here.
    """
    from app.raman_saab.doctrine import book_registry as br
    from app.raman_saab.doctrine.sources import _CORPUS, _resolve_file

    out = set()
    for b in br.BOOKS:
        if b.status != "live":
            continue
        if b.multi_chapter:
            if any((_CORPUS / b.slug).glob("chapter_*.md")):
                out.add(b.tag)
        else:
            f = _resolve_file(b.tag)
            if f is not None and f.is_file():
                out.add(b.tag)
    return out


def needs_book(*tags: str) -> pytest.MarkDecorator:
    """Skip unless EVERY named live book has text on this machine.

    Use where a test asserts about one book's content, so a book nobody can re-download does
    not read as a regression in unrelated doctrine.
    """
    have = vendored_books() if HAS_CORPUS else set()
    missing = [t for t in tags if t not in have]
    return pytest.mark.skipif(
        bool(missing), reason=f"book(s) not vendored on this machine: {', '.join(missing)}")
