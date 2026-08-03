"""S3 tension narrator — both poles visible, guard-safe, rendered in the surfaces."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report, to_markdown
from app.raman_saab.tension_narrator import narrate_tensions

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


class TestTensionNarrator:
    def test_the_contested_house_sentence_names_both_poles(self, report):
        """PREC-3 narration: the headline verdict AND the witness split both appear —
        nothing suppressed (the user decision: narrate, never hide)."""
        recs = narrate_tensions(report)
        mc = report.preponderance.most_contested
        if mc is None:
            pytest.skip("no contested house on this chart")
        sent = next(s for s in recs if f"House {mc}" in s)
        ht = next(t for t in report.preponderance.houses if t.house == mc)
        assert ht.verdict in sent
        assert str(ht.favourable) in sent and str(ht.adverse) in sent
        assert "PREC-3" in sent

    def test_grain_sentences_name_both_verdicts(self, report):
        """PREC-1 narration: the matter verdict AND the house rollup both appear."""
        for s in narrate_tensions(report):
            if "PREC-1" in s:
                assert "favourable" in s and "afflicted" in s

    def test_every_sentence_passes_the_guard(self, report):
        from app.llm.report_explainer import _FORBIDDEN_RE
        for s in narrate_tensions(report):
            m = _FORBIDDEN_RE.search(s)
            assert m is None, f"{s!r} trips {m.group(0)!r}"

    def test_reconciliations_render_in_your_reading(self, report):
        assert report.plain_reading.reconciliations
        md = to_markdown(report)
        assert "Where readings pull in different directions" in md
        from app.raman_saab.report_html import to_html
        assert "Where readings pull in different directions" in to_html(report)
        from app.raman_saab.report_json import to_report_dict
        assert to_report_dict(report)["plain_reading"]["reconciliations"]

    def test_narration_is_deterministic(self, report):
        assert narrate_tensions(report) == narrate_tensions(report)


class TestTurningPoints:
    """S5 — MD boundaries where the Ishta/Kashta lean flips, on the Nichod."""

    def test_turning_points_are_lean_flips_only(self, report):
        tps = report.nichod.turning_points
        for _when, what in tps:
            assert "gives way to" in what and "lean changes" in what

    def test_turning_points_render_and_pass_the_guard(self, report):
        from app.llm.report_explainer import _FORBIDDEN_RE
        n = report.nichod
        if not n.turning_points:
            pytest.skip("no lean flip inside this chart's window")
        md = to_markdown(report)
        assert "Turning points" in md
        joined = "; ".join(f"{w}: {x}" for w, x in n.turning_points)
        assert _FORBIDDEN_RE.search(joined) is None
