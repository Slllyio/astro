"""BPHS ch.33 — Karakamsa effects section catalogue.

Pins that the chapter's CAPS sections are indexed completely, each cites a real BPHS-33 line, titles
are clean (no OCR prose trailer), the sign-effects section is findable, and find() greps titles. The
catalogue is deliberately section-level, not a per-sign grid (the prose does not segment cleanly).
"""
from __future__ import annotations

from app.parashara.doctrine.karakamsa_effects import (
    find,
    karakamsa_in_signs,
    sections,
)
from app.parashara.doctrine.sources import verify


class TestCatalogue:
    def test_indexes_the_chapter_sections(self):
        ss = sections()
        assert len(ss) >= 15                       # ~17 CAPS sections in ch.33

    def test_every_section_cites_a_real_bphs33_line(self):
        for s in sections():
            assert s.source.work == "BPHS-33" and verify(s.source), s.title

    def test_every_section_has_english_text(self):
        for s in sections():
            assert len(s.text) > 20, s.title

    def test_titles_have_no_prose_trailer(self):
        # the cut at ';'/':' must drop the "... KARAKAMSA : O Brahmin" run
        for s in sections():
            assert ";" not in s.title and ":" not in s.title
            assert "Brahmin" not in s.title

    def test_the_nth_from_karakamsa_houses_are_present(self):
        titles = " | ".join(s.title for s in sections()).upper()
        for ordinal in ("2ND", "9TH", "12TH"):
            assert f"{ordinal} FROM KARAKAMSA" in titles


class TestQueries:
    def test_karakamsa_in_signs_is_the_sl2_8_section(self):
        ks = karakamsa_in_signs()
        assert ks is not None and ks.slokas == "2-8"
        assert "Aries" in ks.text and "Pisces" in ks.text   # spans all twelve

    def test_find_greps_titles(self):
        assert any("PLANETS" in s.title.upper() for s in find("planets"))
        assert find("nonexistent-section") == ()
