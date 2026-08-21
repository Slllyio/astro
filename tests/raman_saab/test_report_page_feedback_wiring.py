"""The feedback instrument is actually wired into the interactive page.

The page is a single 4,000-line template with no module system, so the couplings that break
silently are: a heading string that no longer matches its SEC_ID entry (the TOC and the explain
pill both go dead), a renderer that is defined but never called, and a `t('...')` string with no
Hindi entry (which renders English inside an otherwise Hindi page). Each is checked here.
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
    """Every key in the I18N_HI table, read from the source rather than executed."""
    block = page[page.index("const I18N_HI = {"):]
    block = block[:block.index("\n};")]
    return set(re.findall(r'^\s*"((?:[^"\\]|\\.)*)":', block, re.M))


class TestWiring:
    def test_the_section_is_rendered_on_the_colophon(self, page):
        """Defined-but-never-called is the failure mode a syntax check cannot see."""
        assert "function feedbackInstrument(inst)" in page
        assert "add(feedbackInstrument(R.feedback_instrument))" in page
        assert "add(H2('Your feedback'))" in page

    def test_the_heading_is_registered_so_the_toc_and_explain_pill_work(self, page):
        """H2 looks the label up in SEC_ID to find its section_meta; an unregistered heading
        renders bare — no subtitle, no reader-question, no jump target, no explain pill."""
        assert "'Your feedback':'feedback'" in page

    def test_the_invitation_is_offered_before_the_reading_not_after(self, page):
        """Part A is only evidence if it is answered blind. The section itself closes the
        report, so the OFFER has to be made at the top — above 'Your Reading'."""
        invite = page.index("add(feedbackInvite())")
        reading = page.index("add(H2('Your Reading'))")
        assert invite < reading

    def test_the_blind_claim_is_taken_back_when_the_reader_navigates_away(self, page):
        """Clicking the invitation claims 'before_reading'. Flipping to any other leaf means
        they went and read, and the claim must not survive that — a wrong before_reading label
        would put a satisfaction survey into the evidence column."""
        assert "function instWatchNavigation()" in page
        assert "if(n !== 12) INST_CONTEXT = 'after_reading';" in page

    def test_the_gate_keeps_the_later_parts_shut_until_part_a_is_done(self, page):
        assert "class:'fbi-locked'" in page
        assert ".fbi-locked{display:none}" in page
        assert ".fbi-locked.open{display:block}" in page

    def test_state_is_reset_between_charts(self, page):
        """A second cast in the same tab must not inherit the first chart's answers — the qids
        are identical across charts, so they would post as answers to the new nativity."""
        assert "INST_ANSWERS={}; INST_CONTEXT='after_reading';" in page

    def test_it_posts_to_the_instrument_endpoint_with_the_context(self, page):
        assert "'/report/feedback/instrument'" in page
        assert "context: INST_CONTEXT" in page

    def test_the_renderer_uses_safe_dom_only(self, page):
        """Project rule: createElement/textContent, never innerHTML."""
        block = page[page.index("function instText(o, field)"):
                     page.index("// ---- feedback card:")]
        assert "innerHTML" not in block
        assert "insertAdjacentHTML" not in block


class TestBothLanguages:
    def test_every_ui_string_the_instrument_adds_has_a_hindi_entry(self, page, i18n_keys):
        """A `t('...')` with no I18N_HI entry falls through to English, which is how a page
        ends up half-translated. Scoped to the instrument's own functions so this test fails
        for THIS feature's strings rather than reporting the page's whole backlog."""
        block = page[page.index("function instText(o, field)"):
                     page.index("// ---- feedback card:")]
        literals = set(re.findall(r"t\('((?:[^'\\]|\\.)*)'\)", block))
        missing = {s.replace("\\'", "'") for s in literals
                   if s.replace("\\'", "'") not in i18n_keys}
        assert not missing, f"no Hindi for: {sorted(missing)}"

    def test_the_multi_line_strings_are_registered_too(self, page, i18n_keys):
        """Two of the instrument's strings are written as concatenated fragments, so the regex
        above cannot see them whole. They are named here explicitly rather than left unchecked."""
        for s in ("Your answers are not scored back to you: knowing which option the chart "
                  "took would change how the next person answers.",
                  "Before you read: there are a few questions about your own life at the end "
                  "of this report. Answering them FIRST is what makes your feedback worth "
                  "anything — once you have read what the chart says, you can no longer "
                  "say what you would have said on your own."):
            assert s in i18n_keys, s[:60]

    def test_question_text_is_chosen_by_language_not_hardcoded(self, page):
        """The payload carries both languages; the page must pick, not default to English."""
        assert "return (LANG==='hi' ? o[field+'_hi'] : o[field+'_en'])" in page
        assert "LANG==='hi'?part.title_hi:part.title_en" in page
        assert "LANG==='hi'?inst.caveat_hi:inst.caveat_en" in page
