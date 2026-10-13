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

    def test_inverted_range_raises(self):
        """A citation whose end precedes its start is rejected, not accepted."""
        with pytest.raises(ValueError):
            S.parse_citation("NH:20-10")


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

    def test_compound_word_wrapped_at_hyphen_matches(self):
        """A compound word OCR-wrapped at its hyphen still matches the true quote."""
        lines = ["The native was a well-", "known scholar of the sastras in his day."]
        assert S.quote_found(lines, "was a well-known scholar of the sastras", 1)

    def test_bad_byte_does_not_fuse_words(self, tmp_path):
        """An undecodable byte between words must not fuse them together."""
        p = tmp_path / "t.md"
        p.write_bytes(b"lost his\xffmother very early in life")
        assert S.quote_found(S.read_lines(p), "lost his mother very early", 1)


class TestBookPath:
    def test_unknown_book_raises(self):
        """Only books with a known source file are reviewable."""
        with pytest.raises(KeyError):
            S.book_path(Path("x"), "NOPE")

    def test_missing_file_raises(self, tmp_path):
        """A gitignored source that is absent fails loudly, naming the path."""
        with pytest.raises(FileNotFoundError):
            S.book_path(tmp_path, "NH")


def _book(n=400, at=None):
    lines = [f"filler line {k} about nothing" for k in range(1, n + 1)]
    for line_no, text in (at or {}).items():
        lines[line_no - 1] = text
    return lines


class TestLocate:
    def test_verbatim_prose_locates_its_own_line(self):
        """The prose's own words fix the window, whatever the stale citation says."""
        lines = _book(at={300: "Conclusion: the native lost his mother very ear-",
                          301: "ly in life and was raised by relatives."})
        item = {"book": "NH", "verdict_prose": "The native lost his mother very early in life "
                "and was raised by relatives.", "citations": ["NH:10"]}
        located, wins = S.locate(item, lines, {"id": "NH.chart_1"})
        assert located == "verbatim" and wins == [[260, 340]]

    def test_htjah_header_skips_cross_reference_decoy(self):
        """'as in Chart No. 5' is a mention, not the presentation; the block starts at 'Born'."""
        lines = _book(at={50: "This resembles the case as in Chart No. 5 above.",
                          100: "Chart No. 5.—Born on 7-5-1861 at 4-5 a.m. (L.T.)",
                          180: "Chart No. 6.—Born on 1-1-1900 at 6 a.m."})
        item = {"book": "HTJAH-I", "verdict_prose": "words that are nowhere in this book at all",
                "citations": ["HTJAH-I:50"]}
        rec = {"id": "HTJAH-I.x5", "name": "Chart 5 (extracted, DRAFT)",
               "birth": {"dt": "1861-05-07T04:05:00"}}
        assert S.locate(item, lines, rec) == ("chart_header", [[100, 179]])

    def test_htjah_birth_date_disambiguates_reused_number(self):
        """Two presentations share a number; the record's birth date picks its own."""
        lines = _book(at={100: "Chart No. 13.—Born on 2-11-1935 at 5-20 a.m.",
                          200: "Chart No. 13 .-Born 16-10-1918 at 2 p.m.",
                          300: "Chart No. 14.—Born 1-1-1920 at 2 p.m."})
        item = {"book": "HTJAH-I", "verdict_prose": "absent prose words here and there",
                "citations": ["HTJAH-I:1"]}
        rec = {"id": "HTJAH-I.x13", "name": "Chart 13", "birth": {"dt": "1918-10-16T14:00:00"}}
        assert S.locate(item, lines, rec) == ("chart_header", [[200, 299]])

    def test_nh_header_block_confirmed_by_name(self):
        """NH 'No. 38.- HENRY FORD' opens the block, capped at the next header."""
        lines = _book(at={100: "No. 37.— SAYAJI RAO III, GAEKWAR OF BARODA",
                          200: "No. 38.- HENRY FORD", 330: "No. 39— SIR ASHUTOSH MUKERJEE"})
        item = {"book": "NH", "verdict_prose": "absent prose words here and there",
                "citations": ["NH:120"]}
        assert S.locate(item, lines, {"id": "NH.chart_38", "name": "Henry Ford"}) == \
            ("chart_header", [[200, 329]])
        # a contradicting name is not this record's chart
        assert S.locate(item, lines, {"id": "NH.chart_38", "name": "Lord Tennyson"})[0] == \
            "NOT_LOCATED"

    def test_nothing_found_is_not_located(self):
        """No prose match and no header -> NOT_LOCATED with no windows."""
        item = {"book": "NH", "verdict_prose": "absent prose words here and there",
                "citations": ["NH:120"]}
        assert S.locate(item, _book(), {"id": "NH.chart_99"}) == ("NOT_LOCATED", [])
