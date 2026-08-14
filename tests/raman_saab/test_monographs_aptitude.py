"""v33 builder tests that run WITHOUT report_html and WITHOUT the corpus.

The contract tests (test_report_template_contract.py::TestAptitudeV33) exercise
the full four-surface render on CI's Python 3.12 with the vendored corpus. This
file is the local complement: it imports only monographs / detailed_report /
report_json — none of which need PEP 701 — and asserts the pure-re-read pins
that hold on any machine, corpus or not.
"""

from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.monographs import AptitudeProfile, build_aptitude_profile

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


class TestBuildAptitudeProfile:
    """The builder populates from already-judged material only."""

    def test_canonical_chart_builds_a_populated_profile(self, report):
        """The canonical Bangalore chart yields a non-None AptitudeProfile."""
        assert isinstance(report.aptitude, AptitudeProfile)

    def test_intellect_verdict_restates_the_h5_signification(self, report):
        """intellect_verdict is the H5 'intellect' verdict verbatim — a re-read."""
        ap = report.aptitude
        sv = next(s for s in report.proformas[4].significations
                  if s.signification == "intellect")
        assert ap.intellect_verdict == f"{sv.verdict} ({sv.degree})"

    def test_courage_verdict_restates_the_h3_signification(self, report):
        """courage_verdict is the H3 'courage' verdict verbatim — a re-read."""
        ap = report.aptitude
        sv = next(s for s in report.proformas[2].significations
                  if s.signification == "courage")
        assert ap.courage_verdict == f"{sv.verdict} ({sv.degree})"

    def test_mode_split_keys_are_h10_profession_significations(self, report):
        """The mode split re-reads only the four H10 profession keys."""
        allowed = {"profession_authority", "profession_trade",
                   "profession_learned", "profession_labour"}
        assert {k for k, _v in report.aptitude.mode_split} <= allowed

    def test_moon_mind_rules_match_the_moon_sign(self, report):
        """A fired H1.M.S<n> row must carry the chart's own Moon sign number."""
        moon_sign = report.chart.planets["Moon"].sign
        for rid, _text, _cite in report.aptitude.moon_mind_fired:
            assert rid.startswith("H1.M.")
            if rid.startswith("H1.M.S"):
                assert int(rid.removeprefix("H1.M.S")) == moon_sign

    def test_trade_indication_agrees_with_career_primitive(self, report):
        """trade_indication is career_indication(chart) verbatim, when present."""
        from app.raman_saab.primitives.career import career_indication
        assert report.aptitude.trade_indication == career_indication(report.chart)

    def test_style_modern_is_saturn_and_mars_themes(self, report):
        """The bannered modern tier carries exactly the Saturn/Mars keyword rows."""
        ap = report.aptitude
        assert len(ap.style_modern) == 2
        assert ap.style_modern[0].startswith("Saturn:")
        assert ap.style_modern[1].startswith("Mars:")

    def test_woven_names_the_governing_synthesis(self, report):
        """The composed prose defers trade questions to the v23 synthesis."""
        assert "synthesis governs" in report.aptitude.woven

    def test_sparse_chart_returns_none(self):
        """Fewer than ten judged houses → honest None, not a partial guess."""
        class _Sparse:
            proformas = ()
        assert build_aptitude_profile(_Sparse()) is None

    def test_report_json_carries_the_aptitude_key(self, report):
        """to_report_dict serialises the chapter (append-only JSON contract)."""
        from app.raman_saab.report_json import to_report_dict
        d = to_report_dict(report)
        assert d["aptitude"] is not None
        assert d["aptitude"]["mercury_state"]

    def test_markdown_renders_the_section(self, report):
        """to_markdown (3.11-safe, unlike report_html) emits the v33 marker."""
        from app.raman_saab.detailed_report import to_markdown
        md = to_markdown(report)
        assert "## Aptitude, intelligence & work style" in md
        assert "Mercury (buddhi)" in md
