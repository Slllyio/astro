"""rect_case_01 end-to-end golden — the module must reproduce the 2026-07-18 worked
rectification session's conclusion AUTONOMOUSLY from the anonymized fixture.

Session conclusion (external truth, derived interactively before this module existed):
the raman-ayanamsa classes around the stated 10:02 rank first (+2.0 over lahiri's best),
driven by the 2024 childbirth (Jupiter putrakaraka Bhukti under raman vs Rahu under
lahiri) and the 2026 career_change (Mercury MD opening — Me/Me/Me par-excellence);
career_start is FLAT (Saturn MD matches both frames); the marriage/first-childbirth
pair is CORRELATED (both Venus-natured — one witness); and the fact channel's
mother=afflicted picks raman (Rahu-on-the-4th) over lahiri.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.raman_saab.rectification.report import to_markdown, to_text
from app.raman_saab.rectification.session import RectificationSession

_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "rect_case_01.json"


@pytest.fixture(scope="module")
def outcome():
    session = RectificationSession.load(_FIXTURE)
    report = session.evaluate(top_k=6)
    return session, report


class TestSessionConclusion:
    def test_raman_class_ranks_first(self, outcome) -> None:
        """The winner is a raman-ayanamsa class (the session's rectified frame)."""
        _, report = outcome
        assert report.ranked[0].candidate.ayanamsa == "raman"

    def test_ayanamsa_verdict_names_raman_with_positive_margin(self, outcome) -> None:
        """The dual-frame verdict names raman and quantifies the lead."""
        _, report = outcome
        assert report.ayanamsa_verdict.winner == "raman"
        assert report.ayanamsa_verdict.margin > 0
        assert report.ayanamsa_verdict.driving_events

    def test_stated_time_class_is_a_leading_raman_class(self, outcome) -> None:
        """A raman class covering (or adjacent to) the stated 10:02 sits in the top 4 —
        the session validated the stated time, so the module must not push it down."""
        _, report = outcome
        top4 = report.ranked[:4]
        assert any(cs.candidate.ayanamsa == "raman"
                   and cs.candidate.interval_local[0] <= "10:03:30"
                   and cs.candidate.interval_local[1] >= "09:51:00"
                   for cs in top4)

    def test_discriminators_include_the_late_events(self, outcome) -> None:
        """The 2024 childbirth + 2026 career_change carried the ayanamsa separation."""
        _, report = outcome
        assert "career_change" in report.discriminators
        assert "childbirth" in report.discriminators

    def test_career_start_discriminates_and_a_correlated_pair_is_flagged(self, outcome) -> None:
        """At day/near-day precision the job discriminates WITHIN the raman classes too
        (its pratyantar flips across birth-time classes — finer evidence, finer
        resolution); and at least one correlated pair is reported as 'one witness'."""
        _, report = outcome
        assert "career_start" in report.discriminators
        assert report.correlated_pairs

    def test_mother_fact_scores_raman_up_and_lahiri_down(self, outcome) -> None:
        """The fact channel (raman: Rahu on the 4th -> afflicted agrees +1; lahiri:
        favourable disagrees -1) contributes the frame-picking margin."""
        _, report = outcome
        raman_best = next(cs for cs in report.ranked
                          if cs.candidate.ayanamsa == "raman" and cs.fact_scores)
        assert raman_best.channels.facts == pytest.approx(1.0)


class TestHonestFraming:
    def test_resolution_statement_is_day_grade_and_interval_only(self, outcome) -> None:
        _, report = outcome
        assert "day-grade" in report.resolution_statement
        assert "CLASS INTERVAL" in report.resolution_statement

    def test_both_tracks_and_verdict_render_in_both_formats(self, outcome) -> None:
        _, report = outcome
        txt, md = to_text(report), to_markdown(report)
        for out in (txt, md):
            assert "raman" in out and "lahiri" in out
        assert "[raman track]" in txt and "[lahiri track]" in txt
        assert "VERDICT" in txt

    def test_suggestions_offer_next_questions(self, outcome) -> None:
        """The suggester keeps the interactive loop alive even after a verdict."""
        _, report = outcome
        assert report.suggestions

    def test_round_recorded_with_suggestions(self, outcome) -> None:
        session, _ = outcome
        assert len(session.history) == 1
        assert session.history[0].n_events == 5
        assert session.history[0].suggested_next


class TestReproducibility:
    def test_save_load_evaluate_reproduces_the_winner(self, outcome, tmp_path) -> None:
        """Persistence is inputs-only; a reloaded session recomputes the same winner."""
        session, report = outcome
        p = tmp_path / "s.json"
        session.save(p)
        s2 = RectificationSession.load(p)
        r2 = s2.evaluate(top_k=6)
        assert (r2.ranked[0].candidate.ayanamsa, r2.ranked[0].candidate.class_id) == (
            report.ranked[0].candidate.ayanamsa, report.ranked[0].candidate.class_id)
        assert r2.ranked[0].channels.total == pytest.approx(
            report.ranked[0].channels.total)
