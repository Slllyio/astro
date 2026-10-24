"""The committed OCR corrections may only repair garbled words — never move or rewrite a passage.

`tools/raman_saab/ocr_corrections.json` carries line-level fixes to the git-ignored book corpus.
Every citation in the engine is a literal line number, so a correction that added a line, split
one, or changed a digit would silently move or alter what Raman is quoted as saying. These
checks pin that the file stays a list of word-level repairs, and (where the corpus is present)
that each entry still matches the book either before or after it was applied.
"""
from __future__ import annotations

import re

from corpus_presence import needs_corpus

from tools.raman_saab import apply_ocr_corrections as oc

_WORD = re.compile(r"[A-Za-z]+")


class TestCorrectionsAreWordRepairs:
    def test_entries_are_single_lines_with_a_real_change(self):
        """A correction is one line in, one line out, and actually differs."""
        for c in oc.load_corrections():
            assert "\n" not in c["before"] and "\n" not in c["after"], c
            assert "\r" not in c["before"] and "\r" not in c["after"], c
            assert c["before"] != c["after"], c
            assert c["line"] >= 1, c

    def test_repeated_lines_form_a_chain(self):
        """A line corrected by two passes must chain: each later entry starts from exactly the
        text the earlier one produced, so applying in file order is the only possible result."""
        last: dict[tuple[str, int], str] = {}
        for c in oc.load_corrections():
            key = (c["file"], c["line"])
            if key in last:
                assert c["before"] == last[key], c
            last[key] = c["after"]

    def test_digits_change_only_when_checked_against_the_page(self):
        """Degrees, dates, bindu counts and chart numbers cannot be recovered from context. A
        correction may touch a digit only when it records that the printed page was read."""
        for c in oc.load_corrections():
            if re.findall(r"\d+", c["before"]) != re.findall(r"\d+", c["after"]):
                assert "page" in c.get("verified", ""), c

    def test_changes_stay_word_sized(self):
        """Each entry repairs a few words; anything larger is a rewrite, not an OCR fix."""
        for c in oc.load_corrections():
            before, after = _WORD.findall(c["before"]), _WORD.findall(c["after"])
            changed = len(set(before) ^ set(after))
            assert changed <= 12, c


@needs_corpus
class TestCorrectionsMatchTheBooks:
    def test_every_entry_is_pending_or_applied(self):
        """An entry whose line matches neither text means the book changed under it; the tool
        leaves such lines alone, and this makes the drift visible."""
        status = oc.plan()
        assert not status["mismatch"], [f'{c["file"]}:{c["line"]}' for c in status["mismatch"]]
