"""chunker + coverage: chapter chunks and auditable sweep manifests."""
import pytest

from app.medini.doctrine.tools.chunker import chunk_chapters
from app.medini.doctrine.tools.coverage import (
    init_chapters,
    load_manifest,
    mark,
    render_coverage_md,
    save_manifest,
)

TEXT = """\
front matter, not a chunk

CHAPTER I

The Zodiac

prose of chapter one
134

CHAPTER XVII

Key-Planets for Each Sign

per-lagna roles here

CHAPTER XXIU

Ocr-Mangled Roman Numeral chapter
"""


class TestChunker:
    def test_labels_and_order(self):
        chunks = chunk_chapters(TEXT)
        assert [c.label for c in chunks] == ["I", "XVII", "XXIU"]

    def test_titles_are_first_prose_line(self):
        chunks = chunk_chapters(TEXT)
        assert chunks[0].title == "The Zodiac"
        assert chunks[1].title == "Key-Planets for Each Sign"

    def test_chunks_tile_the_text(self):
        chunks = chunk_chapters(TEXT)
        assert chunks[-1].end == len(TEXT)
        for a, b in zip(chunks, chunks[1:]):
            assert a.end == b.start

    def test_slice_contains_body(self):
        chunks = chunk_chapters(TEXT)
        assert "per-lagna roles here" in chunks[1].slice(TEXT)
        assert "prose of chapter one" not in chunks[1].slice(TEXT)

    def test_custom_pattern(self):
        text = "1. Gajakesari Yoga\n\ndefinition\n\n2. Sunapha Yoga\n\nmore\n"
        chunks = chunk_chapters(text, pattern=r"^(\d{1,3})\.\s+[A-Z][a-z]+.*Yoga\s*$")
        assert [c.label for c in chunks] == ["1", "2"]


class TestCoverage:
    def test_init_and_mark_round_trip(self, tmp_path):
        chunks = chunk_chapters(TEXT)
        manifest = init_chapters("hpa", chunks, tmp_path)
        assert all(c["status"] == "pending" for c in manifest["chapters"])
        mark(manifest, "XVII", "swept", rule_count=12, sweep_id="s1")
        save_manifest(manifest, tmp_path)
        loaded = load_manifest("hpa", tmp_path)
        xvii = next(c for c in loaded["chapters"] if c["label"] == "XVII")
        assert xvii["status"] == "swept" and xvii["rule_count"] == 12

    def test_init_idempotent(self, tmp_path):
        chunks = chunk_chapters(TEXT)
        manifest = init_chapters("hpa", chunks, tmp_path)
        mark(manifest, "I", "skipped", notes="front matter only")
        save_manifest(manifest, tmp_path)
        again = init_chapters("hpa", chunk_chapters(TEXT), tmp_path)
        assert next(c for c in again["chapters"] if c["label"] == "I")["status"] == "skipped"

    def test_mark_unknown_chapter_raises(self, tmp_path):
        manifest = init_chapters("hpa", chunk_chapters(TEXT), tmp_path)
        with pytest.raises(KeyError):
            mark(manifest, "XCIX", "swept")

    def test_mark_bad_status_raises(self, tmp_path):
        manifest = init_chapters("hpa", chunk_chapters(TEXT), tmp_path)
        with pytest.raises(ValueError):
            mark(manifest, "I", "done")

    def test_render_md(self, tmp_path):
        manifest = init_chapters("hpa", chunk_chapters(TEXT), tmp_path)
        mark(manifest, "XVII", "swept", rule_count=12, sweep_id="s1")
        save_manifest(manifest, tmp_path)
        md = render_coverage_md(tmp_path)
        assert "hpa — 1/3 chapters swept" in md
        assert "| XVII | Key-Planets for Each Sign | swept | 12 | s1 |" in md
