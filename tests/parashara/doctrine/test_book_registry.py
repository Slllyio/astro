"""Book-registry vs on-disk corpus guard — no false coverage claims.

Every registered book must have its corpus folder on disk, and a note may only claim "Complete" if
the folder is actually populated. This catches the class of bug where PHALA's note said "Complete"
while a single chapter was on disk (fixed 2026-08-24), and any future registry/corpus drift.
"""
from __future__ import annotations

from app.parashara.doctrine.book_registry import BOOKS
from app.parashara.doctrine.sources import _CORPUS


def _md_count(slug: str) -> int:
    folder = _CORPUS / slug
    return len(list(folder.glob("*.md"))) if folder.is_dir() else -1


def test_every_book_folder_exists():
    missing = [e.tag for e in BOOKS if _md_count(e.slug) < 0]
    assert not missing, f"registry entries with no corpus folder on disk: {missing}"


def test_every_book_folder_has_files():
    empty = [e.tag for e in BOOKS if _md_count(e.slug) == 0]
    assert not empty, f"registry entries whose corpus folder is empty: {empty}"


def test_complete_claims_are_truthful():
    """A note may say 'Complete' only if the folder is genuinely populated (guards the PHALA bug)."""
    liars = [(e.tag, _md_count(e.slug)) for e in BOOKS
             if e.note and "complete" in e.note.lower() and "incomplete" not in e.note.lower()
             and _md_count(e.slug) < 2]
    assert not liars, f"entries claiming 'Complete' with <2 files on disk: {liars}"
