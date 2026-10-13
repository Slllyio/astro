from __future__ import annotations

from pathlib import Path

import pytest

from tools.raman_saab.golden_pipeline import sources as S

EXCERPT = Path(__file__).parent / "fixtures" / "excerpt.md"


class TestParseCitation:
    def test_single_line_parses_to_equal_bounds(self):
        """A single-line citation is a one-line span."""
        assert S.parse_citation("NH:8530") == ("NH", 8530, 8530)

    def test_range_parses_to_both_bounds(self):
        """A range citation keeps both ends."""
        assert S.parse_citation("HTJAH-I:1177-1195") == ("HTJAH-I", 1177, 1195)

    def test_garbage_raises(self):
        """An unparseable citation fails loudly rather than guessing a line."""
        with pytest.raises(ValueError):
            S.parse_citation("Raman somewhere")


class TestPassage:
    def test_passage_is_line_numbered_with_context(self):
        """The packet passage carries real book line numbers so quote_line is checkable."""
        lines = S.read_lines(EXCERPT)
        out = S.passage(lines, 6, 7, context=1)
        assert out.splitlines()[0].startswith("5| Jupiter")
        assert out.splitlines()[-1].startswith("8| * A learned")


class TestQuoteFound:
    def test_quote_across_hyphenated_hard_wrap_matches(self):
        """OCR hard wraps and hyphenation must not reject a true quote."""
        lines = S.read_lines(EXCERPT)
        assert S.quote_found(lines, "lost his mother very early in life", 6)

    def test_case_and_punctuation_insensitive(self):
        """Curly quotes, dashes and case differ between OCR and a model's transcription."""
        lines = S.read_lines(EXCERPT)
        assert S.quote_found(lines, "CONCLUSION - the native lost his mother", 6)

    def test_fabricated_quote_is_rejected(self):
        """A quote absent from the source is not found."""
        lines = S.read_lines(EXCERPT)
        assert not S.quote_found(lines, "the native gained his mother late in life", 6)

    def test_quote_far_from_line_is_rejected(self):
        """A real quote cited at the wrong place does not pass."""
        lines = S.read_lines(EXCERPT)
        assert not S.quote_found(lines, "lost his mother very early", 500, window=5)

    def test_too_short_quote_is_rejected(self):
        """A 1-3 word quote matches anything and proves nothing."""
        lines = S.read_lines(EXCERPT)
        assert not S.quote_found(lines, "the native", 6)


class TestBookPath:
    def test_unknown_book_raises(self):
        """Only books with a known source file are reviewable."""
        with pytest.raises(KeyError):
            S.book_path(Path("x"), "NOPE")

    def test_missing_file_raises(self, tmp_path):
        """A gitignored source that is absent fails loudly, naming the path."""
        with pytest.raises(FileNotFoundError):
            S.book_path(tmp_path, "NH")
