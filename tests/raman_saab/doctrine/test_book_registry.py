"""The book registry is the divergence firewall.

`live` books (Parashari-natal Raman) are citable; `catalog-only-out-of-scope` books (Jaimini /
horary / electional / annual) are present on disk but must NEVER resolve as a citation tag, so no
rule can pull a different system's doctrine into the engine.
"""
from __future__ import annotations

from app.raman_saab.doctrine import book_registry as br
from app.raman_saab.doctrine.sources import Citation, _CORPUS, _resolve_file, verify


def test_registry_status_values_valid():
    for b in br.BOOKS:
        assert b.status in ("live", "catalog-only-out-of-scope"), f"{b.tag}: bad status {b.status}"


def test_live_books_resolve_on_disk():
    """Every live book resolves to a real file (single-file via its tag; multi-chapter via a real
    chapter file under its folder)."""
    for b in br.BOOKS:
        if b.status != "live":
            continue
        if b.multi_chapter:
            folder = _CORPUS / b.slug
            assert folder.is_dir(), f"{b.tag}: folder {b.slug} missing"
            assert any(folder.glob("chapter_*.md")), f"{b.tag}: no chapter files in {b.slug}"
        else:
            f = _resolve_file(b.tag)
            assert f is not None and f.is_file(), f"{b.tag} does not resolve to a file"


def test_out_of_scope_books_are_non_citable():
    """The firewall: an out-of-scope book never resolves as a citation tag, and `verify` rejects
    any citation into it — so it cannot enter a RuleRecord."""
    for b in br.BOOKS:
        if b.status == "live":
            continue
        assert br.entry_for(b.tag) is None, f"{b.tag} (out-of-scope) leaked into entry_for"
        assert br.entry_for(f"{b.tag}-1") is None, f"{b.tag}-1 (out-of-scope) leaked into entry_for"
        assert _resolve_file(b.tag) is None, f"{b.tag} (out-of-scope) must NOT resolve to a file"
        assert _resolve_file(f"{b.tag}-1") is None
        assert verify(Citation(f"{b.tag}-1", 1)) is False, f"{b.tag} citation must NOT verify"


def test_registry_slugs_coupled_to_etl_bundle():
    """Every LIVE book's slug must also be known to the ingestion ETL (`_CLASSICAL_BUNDLE`), so the
    two registries can never drift on which folder a book lives in."""
    from app.medini.etl.import_archive_text import _CLASSICAL_BUNDLE
    bundle_slugs = {b.book_slug for b in _CLASSICAL_BUNDLE}
    for b in br.BOOKS:
        if b.status == "live":
            assert b.slug in bundle_slugs, f"live book {b.tag} ({b.slug}) missing from ETL bundle"
