"""Source content-lock guard — every cited corpus file's sha256 is frozen (BPHS + allied).

`sources.verify()` checks a cited LINE exists; this checks the cited FILE's IDENTITY. A re-import /
re-OCR that shifts line numbers would keep verify() green while rotting every citation — this test
fails loudly instead. Re-lock deliberately with UPDATE_SOURCE_LOCK=1 (only after re-validating the
affected citations against the new text).
"""
from __future__ import annotations

import os

from app.parashara.doctrine import source_lock


def test_lock_file_exists_and_is_populated():
    lock = source_lock.load_lock()
    assert lock and len(lock) >= 40, "source_lock.json missing or too small"


def test_every_cited_file_is_locked_and_unchanged():
    if os.environ.get("UPDATE_SOURCE_LOCK") == "1":
        source_lock.write_lock()          # deliberate re-lock, human-gated
        return

    stored = source_lock.load_lock()
    current = source_lock.compute_lock()

    missing = sorted(set(current) - set(stored))
    assert not missing, ("cited files not covered by the lock (a new citation into a new file?):\n"
                         + "\n".join(missing) + "\n-> re-lock with UPDATE_SOURCE_LOCK=1")

    changed = [k for k in current if k in stored and current[k] != stored[k]]
    assert not changed, ("cited corpus files changed content since the lock (re-OCR/line drift?):\n"
                         + "\n".join(changed)
                         + "\n-> re-validate the affected citations, then UPDATE_SOURCE_LOCK=1")


def test_enumeration_is_not_vacuous():
    # guard the guard: the citation walk must actually find the many cited files
    assert len(source_lock.cited_files()) >= 40
