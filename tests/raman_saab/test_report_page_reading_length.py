"""The reading-length toggle is wired into the interactive page.

Three things break silently in a 4,000-line template with no module system: a renderer that
is defined and never called, a `t('...')` with no Hindi entry (which renders English inside a
Hindi page), and — the one that matters most here — a mode a reader cannot get out of. Each
is checked.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_PAGE = (pathlib.Path(__file__).resolve().parents[2]
         / "app" / "medini" / "templates" / "report.html")


@pytest.fixture(scope="module")
def page() -> str:
    return _PAGE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def i18n_keys(page: str) -> set[str]:
    block = page[page.index("const I18N_HI = {"):]
    block = block[:block.index("\n};")]
    return set(re.findall(r'^\s*"((?:[^"\\]|\\.)*)":', block, re.M))


class TestTheDefaultIsFull:
    def test_the_page_starts_on_the_full_reading(self, page):
        """The completeness law's requirement: nothing is hidden unless a reader asks."""
        assert "let READ_LEN = 'full';" in page

    def test_switching_does_not_re_cast_the_chart(self, page):
        """Both readings ride in one payload; a toggle that refetched would double the wait
        and could return a different reference date."""
        assert "LAST_RENDER = [R, S, FQ];" in page
        block = page[page.index("function setReadingLength(v)"):
                     page.index("function readingLengthToggle()")]
        assert "fetch(" not in block


class TestWiring:
    def test_the_short_renderer_is_actually_called(self, page):
        assert "function shortReadingCard(sr)" in page
        assert "add(shortReadingCard(R.short_reading))" in page

    def test_the_toggle_is_offered_on_the_full_reading_too(self, page):
        """Otherwise the short reading is undiscoverable from where readers start."""
        # `page[page.index(x):].startswith("chapter(2);")` is true by construction once the
        # index call succeeds — the only real check was the ValueError it would otherwise raise.
        assert "chapter(2);\n  add(readingLengthToggle());" in page, \
            "the reading-length toggle no longer follows chapter(2) in the full reading"

    def test_every_folio_carries_the_way_back(self, page):
        """A mode you cannot find your way out of is a trap: in the short reading the other
        folios are where a reader looks for the switch, so it is on each of them."""
        block = page[page.index("if(READ_LEN==='short'){"):page.index("chapter(2);\n  add(readingLengthToggle());")]
        assert "for(let i=3;i<=11;i++)" in block
        assert block.count("add(readingLengthToggle());") >= 2

    def test_the_other_folios_are_explained_not_left_blank(self, page):
        assert "You are reading the short version." in page

    def test_feedback_still_renders_in_the_short_reading(self, page):
        """Shortening the reading must not quietly switch off the thing that measures how
        well it lands."""
        block = page[page.index("if(READ_LEN==='short'){"):page.index("chapter(2);\n  add(readingLengthToggle());")]
        assert "feedbackInstrument(R.feedback_instrument)" in block
        assert "feedbackCard(FQ)" in block

    def test_the_renderer_uses_safe_dom_only(self, page):
        block = page[page.index("function shortReadingCard(sr)"):
                     page.index("function render(R, S, FQ){")]
        assert "innerHTML" not in block and "insertAdjacentHTML" not in block

    def test_the_language_is_chosen_from_the_payload_not_translated(self, page):
        """Every sentence was composed at build time in both languages; `t()` cannot
        translate a runtime string, so the page must pick rather than translate."""
        block = page[page.index("function shortReadingCard(sr)"):
                     page.index("function render(R, S, FQ){")]
        assert "const pick=(o,f)=> (hi ? o[f+'_hi'] : o[f+'_en']) || '';" in block


class TestBothLanguages:
    def test_every_ui_string_the_toggle_adds_has_a_hindi_entry(self, page, i18n_keys):
        block = page[page.index("function setReadingLength(v)"):
                     page.index("function render(R, S, FQ){")]
        literals = {m.replace("\\'", "'") for m in re.findall(r"t\('((?:[^'\\]|\\.)*)'\)", block)}
        missing = sorted(s for s in literals if s not in i18n_keys)
        assert not missing, f"no Hindi for: {missing}"

    def test_the_short_mode_notice_is_translated(self, page, i18n_keys):
        """Written as a concatenated literal in the render branch, so the regex above cannot
        see it whole."""
        assert ("You are reading the short version. The rest of the book fills in when you "
                "switch to the full reading.") in i18n_keys
