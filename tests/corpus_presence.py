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
