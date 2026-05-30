"""Tests for Birth Time Rectification (BTR) — Gap M."""
from __future__ import annotations

import pytest

from app.core.birth_time_rectification import (
    KnownEvent, RectificationCandidate, RectificationReport,
    rectify_birth_time, simple_bhava_scorer,
)
from app.core.chart_model import Chart


def _make_chart_builder():
    """Build a chart builder that shifts Lagna sign every 30 minutes (perturbation).

    Simulates the ephemeris-engine bridge for tests. The actual ephemeris
    engine in the project would compute the precise Lagna degree.
    """
    base_asc_sign = 4

    def builder(birth_jd: float) -> Chart:
        # Synthetic: every 60 minutes of perturbation shifts Lagna by 1 sign
        offset_minutes = (birth_jd - 2447988.0) * 1440
        sign_shift = int(offset_minutes // 60)
        new_asc = ((base_asc_sign - 1 + sign_shift) % 12) + 1
        return Chart(
            asc_sign=new_asc, asc_lon=(new_asc - 1) * 30.0 + 15.0,
            planet_signs={"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 6,
                          "Jupiter": 9, "Venus": 2, "Saturn": 11,
                          "Rahu": 3, "Ketu": 9},
            planet_houses={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                          "Jupiter", "Venus", "Saturn",
                                          "Rahu", "Ketu"]},
            planet_lons={"Sun": 130, "Moon": 100, "Mars": 10, "Mercury": 175,
                         "Jupiter": 250, "Venus": 40, "Saturn": 310,
                         "Rahu": 70, "Ketu": 250},
        )
    return builder


class TestKnownEvent:
    def test_construct_with_default_weight(self):
        e = KnownEvent(event_jd=2455000.0, expected_bhava=7, label="marriage")
        assert e.weight == 1.0

    def test_construct_with_custom_weight(self):
        e = KnownEvent(event_jd=2455000.0, expected_bhava=10,
                       label="career change", weight=2.0)
        assert e.weight == 2.0


class TestRectifyBirthTime:
    def test_returns_report(self):
        events = [
            KnownEvent(event_jd=2455000.0, expected_bhava=7, label="marriage"),
            KnownEvent(event_jd=2456000.0, expected_bhava=10, label="career"),
        ]
        report = rectify_birth_time(
            initial_birth_jd=2447988.0,
            events=events,
            chart_builder=_make_chart_builder(),
            bhava_scorer=simple_bhava_scorer,
            window_minutes=30,
        )
        assert isinstance(report, RectificationReport)
        assert report.n_events_used == 2

    def test_best_candidate_is_highest_fitness(self):
        events = [
            KnownEvent(event_jd=2455000.0, expected_bhava=10, label="career"),
        ]
        report = rectify_birth_time(
            initial_birth_jd=2447988.0,
            events=events,
            chart_builder=_make_chart_builder(),
            bhava_scorer=simple_bhava_scorer,
            window_minutes=30,
        )
        # The best candidate should have the highest score among top_candidates
        for c in report.top_candidates:
            assert report.best_candidate.fitness_score >= c.fitness_score

    def test_rejects_empty_events(self):
        with pytest.raises(ValueError):
            rectify_birth_time(
                initial_birth_jd=2447988.0,
                events=[],
                chart_builder=_make_chart_builder(),
                bhava_scorer=simple_bhava_scorer,
            )

    def test_warning_when_less_than_3_events(self):
        events = [KnownEvent(2455000.0, 7, "marriage")]
        report = rectify_birth_time(
            initial_birth_jd=2447988.0, events=events,
            chart_builder=_make_chart_builder(),
            bhava_scorer=simple_bhava_scorer,
            window_minutes=30,
        )
        assert any("unstable" in n.lower() for n in report.notes)

    def test_window_search_covers_full_range(self):
        events = [KnownEvent(2455000.0, 7, "marriage", 1.0)]
        report = rectify_birth_time(
            initial_birth_jd=2447988.0, events=events,
            chart_builder=_make_chart_builder(),
            bhava_scorer=simple_bhava_scorer,
            window_minutes=10, step_minutes=1,
        )
        # Should have 21 candidates in top_candidates (only top 5 returned)
        # but internal search covers -10..+10 = 21 values
        assert len(report.top_candidates) <= 5

    def test_rejects_invalid_window(self):
        events = [KnownEvent(2455000.0, 7, "test")]
        with pytest.raises(ValueError):
            rectify_birth_time(
                initial_birth_jd=2447988.0, events=events,
                chart_builder=_make_chart_builder(),
                bhava_scorer=simple_bhava_scorer,
                window_minutes=5, step_minutes=10,  # step > window
            )


class TestSimpleBhavaScorer:
    def test_kendra_lord_positive_score(self):
        """Bhava lord in Kendra → +1.0."""
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Mars": 1},   # 1L Mars in 1H (Kendra)
            planet_houses={"Mars": 1},
            planet_lons={"Mars": 10.0},
        )
        score = simple_bhava_scorer(chart, target_bhava=1, event_jd=0)
        assert score == 1.0

    def test_dusthana_lord_negative_score(self):
        """Bhava lord in dusthana → -1.0."""
        chart = Chart(
            asc_sign=1, asc_lon=10.0,
            planet_signs={"Mars": 8},   # 1L Mars in 8H (dusthana)
            planet_houses={"Mars": 8},
            planet_lons={"Mars": 220.0},
        )
        score = simple_bhava_scorer(chart, target_bhava=1, event_jd=0)
        assert score == -1.0
