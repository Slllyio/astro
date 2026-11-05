"""Technical terms are named in plain words the first time the markdown uses them.

The standalone HTML (`_apply_glossary_abbrs`) and the interactive page (`glossWalk`) both
mark first occurrences already, and a hover shows the gloss. Markdown has no hover, so its
reader met every term cold with the plain-terms chapter a thousand lines away.

The pass runs over a FINISHED document, which is exactly the kind of substitution that
quietly corrupts things it was never meant to touch. Every guard it carries is pinned here,
because each of them stands for a real way the naive version broke the report.
"""
from __future__ import annotations

import re

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import _gloss_first_use, build_detailed_report, to_markdown
from app.raman_saab.plain_terms import TERM_GLOSS

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def markdown() -> str:
    return to_markdown(build_detailed_report(_CANONICAL))


class TestItActuallyGlosses:
    def test_a_plain_sentence_gets_the_gloss_once(self):
        out = _gloss_first_use("The Shadbala figure is high.\nShadbala again here.")
        assert out.splitlines()[0] == "The Shadbala (planetary strength) figure is high."
        assert out.splitlines()[1] == "Shadbala again here."

    def test_the_real_report_glosses_a_useful_number_of_terms(self, markdown):
        glossed = [t for t, g in TERM_GLOSS.items()
                   if f"{t} ({re.sub(r'[ ]*\([^)]*\)', '', g.plain).strip(' ,-')})" in markdown]
        assert len(glossed) >= 12, glossed


class TestTheGuards:
    def test_a_hyphenated_compound_is_left_alone(self):
        """"Kashta-dominant" must not become "Kashta (hard-yield potential)-dominant"."""
        assert _gloss_first_use("It is Kashta-dominant here.") == "It is Kashta-dominant here."

    def test_a_bold_row_label_is_left_alone(self):
        """`**Karaka**` is a structural field name; glossing it renames the field."""
        assert _gloss_first_use("- **Karaka** - Jupiter") == "- **Karaka** - Jupiter"

    def test_a_term_already_inside_a_parenthetical_is_left_alone(self):
        """Nesting reads worse than the jargon: "(Kashta 11 over Ishta (…) 7)"."""
        assert _gloss_first_use("(Kashta 11 over Ishta 7)") == "(Kashta 11 over Ishta 7)"

    def test_a_term_that_already_explains_itself_is_left_alone(self):
        assert _gloss_first_use("Shadbala (six-fold strength)") == "Shadbala (six-fold strength)"

    def test_a_heading_is_never_touched(self):
        """Headings anchor jumpLink, SCOPE and the digest; they stay byte-identical."""
        assert _gloss_first_use("## Shadbala") == "## Shadbala"
        assert _gloss_first_use("### Vedha") == "### Vedha"

    def test_a_table_row_is_never_touched(self):
        assert _gloss_first_use("| Shadbala | 8.7 |") == "| Shadbala | 8.7 |"

    def test_a_quotation_is_never_touched(self):
        """Raman's own words are verbatim; an editorial parenthesis inside a quote is a
        falsified quotation."""
        line = 'He writes "the Shadbala of the lord decides".'
        assert _gloss_first_use(line) == line

    def test_the_plain_terms_chapter_is_never_touched(self):
        """It defines these words; glossing them there is noise on top of the definition."""
        block = "### In plain terms (every technical word, with why it matters)\n" \
                "- **Shadbala** - planetary strength."
        assert _gloss_first_use(block) == block

    def test_a_nested_parenthetical_in_the_gloss_is_flattened(self, markdown):
        """TERM_GLOSS['Atmakaraka'].plain carries its own '(highest-degree planet)'."""
        assert "Atmakaraka (the soul significator)" in markdown
        assert "(the soul significator (highest-degree planet))" not in markdown


class TestNothingElseMoved:
    def test_every_section_heading_survives(self, markdown):
        from app.raman_saab.detailed_report import SECTION_CONTRACT
        for spec in SECTION_CONTRACT:
            if spec.md_marker:
                assert spec.md_marker in markdown, spec.md_marker
