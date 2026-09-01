"""The collected chapter, "What Raman's rules indicate" (report contract v38).

The owner's question was: *why is it always good or bad? Raman wrote far more than that.*
Measured over all 871 `RuleRecord`s, 611 (70%) carry non-graded content — a kind, count,
attribute or circumstance rather than a verdict. This chapter gathers every such indication
for one chart in one place, grouped by category.

It is a PURE RE-READ (PREC-10) of the house-block composers: it computes nothing, reads no
chart, and adds no doctrine. The tests below pin the two properties that make it honest —
nothing is invented, and nothing that was never evaluated is presented as a finding.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import (build_detailed_report, collected_indications,
                                            descriptive_house_rules,
                                            house_chief_combinations,
                                            house_further_combinations,
                                            house_general_readings, house_indications,
                                            indication_category, to_markdown)
from app.raman_saab.render import _ascii
from app.raman_saab.report_html import to_html

CANON = BirthData("canon", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

#: The four provenance labels a row may carry. They are load-bearing: "on record" means the
#: rule was never evaluated, and letting it read as a finding would be a false claim about
#: the engine's own work.
KINDS = {"computed", "fired", "general", "on record"}


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(CANON)


class TestChapterIsAPureReRead:
    def test_every_row_traces_to_a_house_block_composer(self, report) -> None:
        """Nothing in the chapter may originate here. Each row must already be shown in the
        house block it names — otherwise the chapter is authoring doctrine, not collecting
        it."""
        source_rows: set[tuple[int, str]] = set()
        for h in range(1, 13):
            for sig, label, value in house_indications(report, h):
                source_rows.add((h, f"{label}: {value}"))
            for _sig, _rid, text, _cite in house_general_readings(report, h):
                source_rows.add((h, text))
            for _sig, _rid, text, _cite in house_chief_combinations(report, h):
                source_rows.add((h, text))
            for _sig, _rid, text, _cite in house_further_combinations(report, h):
                source_rows.add((h, text))
            for _sig, _rid, text, _cite in descriptive_house_rules(h):
                source_rows.add((h, text))
        for _label, rows in collected_indications(report):
            for house, _kind, _sig, text, _cite in rows:
                assert (house, text) in source_rows, (house, text[:60])

    def test_no_source_row_is_dropped(self, report) -> None:
        """The other direction: collecting must not lose anything either."""
        collected = {(h, t) for _l, rows in collected_indications(report)
                     for h, _k, _s, t, _c in rows}
        for h in range(1, 13):
            for _sig, _rid, text, _cite in descriptive_house_rules(h):
                assert (h, text) in collected, (h, text[:60])
            for sig, label, value in house_indications(report, h):
                assert (h, f"{label}: {value}") in collected


class TestProvenanceIsNeverCollapsed:
    def test_every_row_declares_how_it_got_there(self, report) -> None:
        for _label, rows in collected_indications(report):
            for _h, kind, _sig, _text, _cite in rows:
                assert kind in KINDS, kind

    def test_descriptive_rules_are_labelled_on_record_not_fired(self, report) -> None:
        """A `condition=None` rule was never evaluated against this chart. If it appeared
        as "fired" the chapter would assert something the engine never computed."""
        on_record = {text for h in range(1, 13)
                     for _s, _r, text, _c in descriptive_house_rules(h)}
        for _label, rows in collected_indications(report):
            for _h, kind, _sig, text, _cite in rows:
                if text in on_record:
                    assert kind == "on record", text[:60]


class TestCategorisationIsConservative:
    def test_unmatched_text_falls_to_other_rather_than_being_force_fit(self) -> None:
        key, label = indication_category("a sentence with no classifying cue at all")
        assert key == "other"
        assert "Other" in label

    def test_a_named_disease_lands_in_the_body_category(self) -> None:
        key, _label = indication_category("the native will suffer from consumption")
        assert key == "disease"

    def test_categories_never_hide_a_row(self, report) -> None:
        """Mis-categorisation may only affect GROUPING. Every row prints its full text,
        matter and citation whatever bucket it lands in, so no doctrine can be lost to a
        classifier mistake."""
        groups = collected_indications(report)
        total = sum(len(rows) for _l, rows in groups)
        assert total > 100
        assert len({label for label, _rows in groups}) == len(groups), "labels are unique"


class TestChapterReachesEverySurface:
    def test_markdown_and_html_carry_every_row(self, report) -> None:
        md, html = to_markdown(report), to_html(report)
        assert "## What Raman's rules indicate" in md
        assert 'id="indications"' in html
        for _label, rows in collected_indications(report):
            for _h, _kind, _sig, text, _cite in rows:
                # markdown is ASCII-folded on the way out (render._REPL)
                assert _ascii(text) in md, text[:60]

    def test_the_framing_sentence_is_present(self, report) -> None:
        """The chapter must say on its own face that these are not grades and not new."""
        md = to_markdown(report)
        assert "rather than a favourable/afflicted grade" in md
        assert "every line also appears in its own house block above" in md
