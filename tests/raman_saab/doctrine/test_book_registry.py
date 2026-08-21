"""The book registry is the divergence firewall.

`live` books are citable; `catalog-only-out-of-scope` books (annual / different systems) are
present on disk but must NEVER resolve as a citation tag, so no rule can pull a different
system's doctrine into the engine. PRASNA/MUHURTHA are live for their own walled subsystems only.

`corroboration` books (BPHS, Phaladeepika — added 2026-08-21 for the varga module) split the two
predicates that used to be one: they RESOLVE (click-to-source) but are NOT natal-citable. The
strictly-Raman house engine no longer relies on "non-live => non-resolvable"; it relies on the
natal-only citation guard (`test_natal_citations_are_raman_only`).
"""
from __future__ import annotations

from app.raman_saab.doctrine import book_registry as br
from app.raman_saab.doctrine.sources import Citation, _CORPUS, _resolve_file, verify


def test_registry_status_values_valid():
    for b in br.BOOKS:
        # "lineage-catalog" (2026-08-08): the Suryanarain Rao shelf — findable, non-resolvable.
        # "corroboration" (2026-08-21): classical, resolvable but not natal-citable.
        assert b.status in (
            "live", "corroboration", "catalog-only-out-of-scope", "lineage-catalog"), (
            f"{b.tag}: bad status {b.status}")


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
    """The firewall: an out-of-scope / lineage book never resolves as a citation tag, and `verify`
    rejects any citation into it — so it cannot enter a RuleRecord. (Corroboration books DO resolve;
    they are covered by the separate test below.)"""
    for b in br.BOOKS:
        if b.status in ("live", "corroboration"):
            continue
        assert br.entry_for(b.tag) is None, f"{b.tag} (out-of-scope) leaked into entry_for"
        assert br.entry_for(f"{b.tag}-1") is None, f"{b.tag}-1 (out-of-scope) leaked into entry_for"
        assert _resolve_file(b.tag) is None, f"{b.tag} (out-of-scope) must NOT resolve to a file"
        assert _resolve_file(f"{b.tag}-1") is None
        assert verify(Citation(f"{b.tag}-1", 1)) is False, f"{b.tag} citation must NOT verify"


def test_corroboration_books_resolve_but_are_not_natal_citable():
    """Corroboration books (BPHS, Phaladeepika) RESOLVE — click-to-source works — but are barred
    from the natal registry: `is_natal_citable` is False for every one. This is the 2026-08-21
    split of resolution from natal-citability; the strictly-Raman guarantee moves to the
    natal-only citation guard, not the resolution firewall."""
    corr = [b for b in br.BOOKS if b.status == "corroboration"]
    assert corr, "expected at least one corroboration book (BPHS / Phaladeepika)"
    for b in corr:
        # resolves to real on-disk text
        if b.multi_chapter:
            folder = _CORPUS / b.slug
            assert folder.is_dir() and any(folder.glob("chapter_*.md")), (
                f"{b.tag}: corroboration folder {b.slug} has no chapter files")
        else:
            assert _resolve_file(b.tag) is not None, f"{b.tag}: corroboration must resolve"
        # resolvable, yet NOT natal-citable
        probe = f"{b.tag}-7" if b.multi_chapter else b.tag
        assert br.entry_for(probe) is not None, f"{b.tag}: should resolve via entry_for"
        assert br.is_natal_citable(probe) is False, (
            f"{b.tag}: corroboration must NOT be natal-citable")


def test_registry_slugs_coupled_to_etl_bundle():
    """Every LIVE book's slug must also be known to the ingestion ETL (`_CLASSICAL_BUNDLE`), so the
    two registries can never drift on which folder a book lives in."""
    from app.medini.etl.import_archive_text import _CLASSICAL_BUNDLE
    bundle_slugs = {b.book_slug for b in _CLASSICAL_BUNDLE}
    for b in br.BOOKS:
        if b.status == "live":
            assert b.slug in bundle_slugs, f"live book {b.tag} ({b.slug}) missing from ETL bundle"
