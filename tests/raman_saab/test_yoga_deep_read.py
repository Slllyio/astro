"""v21 yoga deep-read — quoted definitions, computation trees, measured strength."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report, to_markdown
from app.raman_saab.yoga_deep_read import NH_EXAMPLES, describe, participants

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


class TestWalkers:
    def test_describe_renders_combinators_readably(self):
        from app.raman_saab.doctrine import conditions as C
        cond = C.Or(C.Conjunct("Sun", "Mercury"), C.Not(C.InRashiHouse("Mars", 8)))
        s = describe(cond)
        assert " OR " in s and "NOT " in s and "Conjunct(a=Sun, b=Mercury)" in s

    def test_participants_collects_grahas_in_order(self):
        from app.raman_saab.doctrine import conditions as C
        cond = C.And(C.Conjunct("Sun", "Mercury"), C.Aspects("Jupiter", "Sun"))
        assert participants(cond) == ("Sun", "Mercury", "Jupiter")


class TestYogaDeepRead:
    def test_every_fired_yoga_gets_a_deep_read(self, report):
        assert report.yogas, "canonical chart fires yogas"
        assert len(report.yoga_deep) == len(report.yogas)

    def test_definitions_are_quoted_verbatim_with_resolving_cites(self, report):
        from app.raman_saab.doctrine.sources import Citation, verify
        for y in report.yoga_deep:
            assert y.definition_quote and len(y.definition_quote) > 30
            work, line = y.cite.rsplit(":", 1)
            assert verify(Citation(work, int(line))), y.cite

    def test_strength_is_measured_never_a_percentage(self, report):
        for y in report.yoga_deep:
            assert "%" not in y.strength_note
            assert "rupas" in y.strength_note or "unavailable" in y.strength_note

    def test_comparison_ranks_are_a_permutation(self, report):
        ranks = sorted(y.comparison_rank for y in report.yoga_deep)
        assert ranks == list(range(1, len(report.yoga_deep) + 1))

    def test_participants_carry_chart_facts(self, report):
        for y in report.yoga_deep:
            for f in y.participants:
                assert 1 <= f.house <= 12 and 1 <= f.sign <= 12
                assert f.dignity and f.effective_dignity

    def test_nh_example_cites_resolve(self):
        from app.raman_saab.doctrine.sources import Citation, verify
        for cites in NH_EXAMPLES.values():
            for cite in cites:
                work, line = cite.rsplit(":", 1)
                assert verify(Citation(work, int(line))), cite

    def test_section_renders_in_every_surface(self, report):
        from app.raman_saab.report_html import to_html
        from app.raman_saab.report_json import to_report_dict
        assert "## Yoga deep-read" in to_markdown(report)
        assert 'id="yoga-deep"' in to_html(report)
        assert to_report_dict(report)["yoga_deep"]
