"""Session tests — JSON round-trip reproduces the ranking, history accumulates, the
engine fingerprint warns on mismatch, and discover mode's two-phase flow runs.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from app.raman_saab.rectification.events import LifeEvent, resolve_fact
from app.raman_saab.rectification.session import RectificationSession


def _seeded(tmp_path: Path) -> RectificationSession:
    s = RectificationSession.new(mode="rectify", date=(1989, 10, 12),
                                 lat=27.23, lon=79.03, tz=5.5, time=(10, 2),
                                 window_minutes=15)
    s.add_event(LifeEvent("marriage", 2017, 12, 4))
    s.add_event(LifeEvent("career_start", 2016, 2))
    return s


class TestEvaluate:
    def test_evaluate_ranks_and_records_history(self, tmp_path) -> None:
        """One evaluate() round ranks both ayanamsa tracks and appends a RoundRecord."""
        s = _seeded(tmp_path)
        report = s.evaluate(top_k=6)
        assert report.ranked
        assert {cs.candidate.ayanamsa for cs in report.ranked} == {"raman", "lahiri"}
        assert len(s.history) == 1
        assert s.history[0].n_events == 2
        assert s.history[0].n_candidates == report.n_candidates

    def test_facts_run_only_on_the_top_k(self, tmp_path) -> None:
        """The Tier-F fact channel is restricted to the event-score survivors."""
        s = _seeded(tmp_path)
        s.add_fact(resolve_fact("property", "favourable"))
        report = s.evaluate(top_k=2)
        with_facts = [cs for cs in report.ranked if cs.fact_scores]
        assert 0 < len(with_facts) <= 2


class TestPersistence:
    def test_json_round_trip_reproduces_the_ranking(self, tmp_path) -> None:
        """save -> load -> evaluate yields the same top candidate (scores are
        recomputed from inputs, never persisted)."""
        s = _seeded(tmp_path)
        r1 = s.evaluate()
        p = tmp_path / "s.json"
        s.save(p)
        s2 = RectificationSession.load(p)
        assert [e.event_type for e in s2.events] == [e.event_type for e in s.events]
        assert len(s2.history) == 1
        r2 = s2.evaluate()
        a, b = r1.ranked[0].candidate, r2.ranked[0].candidate
        assert (a.ayanamsa, a.class_id) == (b.ayanamsa, b.class_id)
        assert r1.ranked[0].channels.total == pytest.approx(r2.ranked[0].channels.total)

    def test_fingerprint_mismatch_warns(self, tmp_path) -> None:
        """A session saved under another engine version warns that history rankings
        may not reproduce."""
        s = _seeded(tmp_path)
        s.engine_fingerprint = "deadbeef0000"
        p = tmp_path / "s.json"
        s.save(p)
        with pytest.warns(UserWarning, match="may not reproduce"):
            RectificationSession.load(p)

    def test_current_fingerprint_loads_silently(self, tmp_path) -> None:
        """Same-engine load emits no warning."""
        s = _seeded(tmp_path)
        p = tmp_path / "s.json"
        s.save(p)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            RectificationSession.load(p)


class TestModes:
    def test_rectify_requires_a_stated_time(self) -> None:
        """rectify mode without a time is a data-entry error, not a silent discover."""
        with pytest.raises(ValueError, match="stated time"):
            RectificationSession.new(mode="rectify", date=(1989, 10, 12),
                                     lat=27.23, lon=79.03, tz=5.5)

    def test_discover_two_phase_flow_runs(self) -> None:
        """Discover mode walks the whole day coarse, then refines surviving lagna
        spans — and returns classes from more than one lagna only if they survive."""
        s = RectificationSession.new(mode="discover", date=(1989, 10, 12),
                                     lat=27.23, lon=79.03, tz=5.5)
        s.add_event(LifeEvent("marriage", 2017, 12, 4))
        report = s.evaluate(top_k=4)
        assert report.mode == "discover"
        assert report.ranked
        # the winner is reported as a class interval, never a point
        lo, hi = report.ranked[0].candidate.interval_local
        assert lo != hi
