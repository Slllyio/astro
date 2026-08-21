"""The source content-lock guards every cited corpus file against silent line-shift.

`sources.verify` checks a cited line EXISTS; this checks the file's IDENTITY is unchanged, so a
re-import / re-OCR that shifts line numbers is caught loudly instead of rotting ~1769 citations.
"""
from __future__ import annotations

import os

import pytest

from app.raman_saab.doctrine import source_lock

# The corpus lives outside git (data/ is ignored); skip cleanly where it isn't present.
_HAS_CORPUS = bool(source_lock.cited_files())
_needs_corpus = pytest.mark.skipif(not _HAS_CORPUS, reason="corpus not present on this machine")


@_needs_corpus
def test_source_lock_matches_disk():
    """Every locked file's sha256 + line_count is unchanged. A failure means a CITED source file
    changed since it was locked — its line numbers may have shifted, so every citation into it
    must be re-validated against the new text before re-locking with UPDATE_SOURCE_LOCK=1."""
    if os.environ.get("UPDATE_SOURCE_LOCK"):
        source_lock.write_lock()
        pytest.skip("SOURCE_LOCK.json regenerated (UPDATE_SOURCE_LOCK=1)")
    stored = source_lock.load_lock()
    assert stored, "SOURCE_LOCK.json missing or empty — run UPDATE_SOURCE_LOCK=1 to create it"
    current = source_lock.compute_lock()
    on_disk = set(source_lock.cited_files())
    changed = sorted(k for k in on_disk & set(stored) if current.get(k) != stored[k])
    assert not changed, (
        f"{len(changed)} cited corpus file(s) changed since they were locked — citations into "
        f"them may have shifted, and `verify` cannot see it because a stale line number is "
        f"still a line number. Re-validate every citation into them against the new text, fix "
        f"what moved, and only then re-lock with UPDATE_SOURCE_LOCK=1: {changed}")


@_needs_corpus
def test_every_cited_file_is_locked():
    """No citation may resolve to a file the lock does not cover — a new book's first citation
    must be locked in the same change."""
    stored = source_lock.load_lock()
    for key in source_lock.cited_files():
        assert key in stored, (
            f"cited source {key} is not in SOURCE_LOCK.json — lock it with UPDATE_SOURCE_LOCK=1")


@_needs_corpus
def test_lock_covers_only_cited_files():
    """The lock is scoped to cited files only (it must not silently freeze the whole corpus).

    Locked-but-absent entries are allowed and are not "extra": a machine missing one book
    still holds that book's record, which is what lets the next machine — the one that HAS it
    — check it. What is forbidden is the other direction, a locked file nothing cites, since
    that is the lock quietly freezing corpus it has no business freezing.
    """
    cited = set(source_lock.cited_files())
    locked = set(source_lock.load_lock())
    from app.raman_saab.doctrine.sources import _CORPUS
    unexplained = {k for k in locked - cited if (_CORPUS / k).is_file()}
    assert not unexplained, (
        f"locked file(s) nothing cites: {sorted(unexplained)} — the lock must not freeze "
        f"corpus beyond what the engine actually cites")
    assert cited <= locked, f"cited but unlocked: {sorted(cited - locked)}"
