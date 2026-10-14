"""Allied-lineage coverage through the shared corpus index (BPHS's Parashari lineage).

The same faithful numbered-sloka indexer spans the allied texts, not just BPHS. Saravali and Brihat
Jataka index richly; this pins that coverage and that allied citations resolve to real text (allied
tier, not frontmatter). It also guards the 2-/3-digit chapter-glob tolerance the allied scrapes need.

Honest scope: Phaladeepika, Uttara Kalamrita, Hora Sara and Jataka Parijata are sparsely imported or
heavily OCR-damaged in this corpus snapshot — a source-quality gap recorded, not papered over.
"""
from __future__ import annotations

from app.parashara.doctrine.corpus_index import slokas_of
from app.parashara.doctrine.sources import passage, resolve_file, verify

_FRONTMATTER = ("topics:", "classical_refs:", "content_type:", "scraped_at:")


class TestSaravali:
    def test_richly_indexed(self):
        total = sum(len(slokas_of(f"SARAVALI-{c}")) for c in range(1, 56))
        chapters = sum(1 for c in range(1, 56) if slokas_of(f"SARAVALI-{c}"))
        assert chapters >= 50
        assert total >= 900

    def test_citations_resolve_to_allied_text(self):
        s = slokas_of("SARAVALI-1")
        assert s and all(verify(x.source) for x in s)
        p = passage(f"{s[0].source.work}:{s[0].source.line}")
        assert p and p["status"] == "allied"
        assert not any(m in p["text"].lower() for m in _FRONTMATTER)


class TestBrihatJataka:
    def test_indexed(self):
        total = sum(len(slokas_of(f"BJ-{c}")) for c in range(1, 30))
        assert total >= 200


class TestChapterGlobTolerance:
    def test_two_digit_chapter_files_resolve(self):
        """Phaledeepika's files are `chapter_05_*` (2-digit); the resolver must still find them."""
        assert resolve_file("PHALA-5") is not None
