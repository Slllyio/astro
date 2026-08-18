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
from app.raman_saab.monographs import (AptitudeProfile, PsychProfile,
                                       build_aptitude_profile, build_psych_profile)

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


class TestPsychProfileWithoutCorpus:
    """P0 fix (REPORT_CRITIQUE_2026-08-17): the psych chapter must NEVER vanish just
    because the HPA-18 verbatim pull is empty — the Moon state, temperament, nature
    stamp and AK are all computed. The quote field carries an honest-absence line."""

    def test_empty_pull_still_builds_a_renderable_profile(self, report, monkeypatch):
        """passage() returning None (corpus absent) yields a full PsychProfile, not None."""
        import app.raman_saab.monographs as mono
        monkeypatch.setattr(mono, "passage", lambda *a, **k: None)
        ps = build_psych_profile(report)
        assert isinstance(ps, PsychProfile)
        # all COMPUTED rows still present
        assert ps.moon_state
        assert ps.woven
        assert ps.atmakaraka in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                 "Venus", "Saturn")

    def test_absence_line_reuses_the_existing_citation(self, report, monkeypatch):
        """The absence line names the per-lagna HPA-18 anchor already in the code —
        never an invented line number — and flows through the quote field so no
        renderer needs a change."""
        import app.raman_saab.monographs as mono
        from app.raman_saab.monographs import LAGNA_BLOCKS
        monkeypatch.setattr(mono, "passage", lambda *a, **k: None)
        ps = build_psych_profile(report)
        cite = f"HPA-18:{LAGNA_BLOCKS[report.chart.asc_sign][0]}"
        assert ps.lagna_quote == (
            f"lagna portrait at {cite} - corpus not mounted on this machine", cite)

    def test_real_quote_still_wins_when_the_corpus_is_present(self, report, monkeypatch):
        """A non-empty pull renders verbatim — the absence line is the fallback only."""
        import app.raman_saab.monographs as mono
        monkeypatch.setattr(
            mono, "passage",
            lambda cite, **k: {"work": "HPA-18", "start": 1, "end": 2,
                               "text": "The native is of noble bearing."})
        ps = build_psych_profile(report)
        assert ps.lagna_quote[0] == "The native is of noble bearing."
        assert "corpus not mounted" not in ps.lagna_quote[0]


class TestPsychMindStack:
    """Wave-2 foundation additions (REPORT_CRITIQUE_2026-08-17): the Moon-in-sign
    mental disposition (re-read of the fired H1.M.* rule, HTJAH-I:1452), the Mercury
    (buddhi) condition line, and the cross-reference to Deeptadi's Moon row."""

    def test_moon_mind_rereads_the_fired_h1m_rule(self, report):
        """Canonical pin: Moon in Pisces fires H1.M.S12 (HTJAH-I:1452) — the SAME
        fired row the Aptitude chapter shows, re-read here, never re-judged."""
        ps = report.psych
        assert ps is not None and ps.moon_mind
        rid, text, cite = ps.moon_mind[0]
        assert rid == "H1.M.S12"
        assert cite == "HTJAH-I:1452"
        assert ps.moon_mind == report.aptitude.moon_mind_fired

    def test_mercury_buddhi_line_is_composed_from_computed_condition(self, report):
        """Manas-and-buddhi framing over Mercury's computed house/dignity/avastha and
        the drishti it receives (canonical: H11, enemy, Deena; Mars + Rahu aspect)."""
        ps = report.psych
        assert "manas" in ps.mercury_line and "buddhi" in ps.mercury_line
        assert "in house 11, dignity enemy, avastha Deena" in ps.mercury_line
        assert "aspected by Mars, Rahu" in ps.mercury_line

    def test_deeptadi_moon_cross_reference(self, report):
        """The psych chapter points at the Deeptadi section's Moon row with Raman's
        own result phrase (HPA Ch.7:46-83) — canonical: Moon Muditha."""
        ps = report.psych
        assert ps.deeptadi_moon.startswith("Moon Muditha")
        assert "HPA Ch.7:46-83" in ps.deeptadi_moon
        assert "Deeptadi avasthas section" in ps.deeptadi_moon

    def test_mind_stack_renders_in_markdown(self, report):
        """The three new rows appear inside the Psychological profile section."""
        from app.raman_saab.detailed_report import to_markdown
        md = to_markdown(report)
        i = md.find("## Psychological profile")
        sec = md[i:md.find("## Planetary positions")]
        assert "**The Moon's sign (mental disposition)** [H1.M.S12]" in sec
        assert "**Mercury (buddhi)**" in sec
        assert "**The Moon's avastha (cross-reference)**" in sec

    def test_mind_stack_prose_passes_the_guard(self, report):
        """Descriptive idiom only on every new psych field."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        ps = report.psych
        for text in (ps.mercury_line, ps.deeptadi_moon,
                     *(t for _rid, t, _c in ps.moon_mind)):
            m = _FORBIDDEN_RE.search(text)
            assert m is None, m and m.group(0)
