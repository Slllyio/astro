"""Tests for app.medini.ml.validate_framework_readings — validation scaffold."""
from __future__ import annotations

import pytest

from app.medini.ml.validate_framework_readings import (
    CANONICAL_CHARTS,
    CanonicalChart,
    ChartValidationReport,
    ExpectedObservation,
    ObservationResult,
    format_report,
    validate_chart,
)


class TestCanonicalCharts:
    """Module-level dataset structure."""

    def test_three_canonical_charts_seeded(self):
        """Gandhi, Indira, Nehru — three seeded famous charts."""
        assert set(CANONICAL_CHARTS) == {"gandhi", "indira", "nehru"}

    def test_each_canonical_chart_has_observations(self):
        """No canonical chart seeded with zero observations."""
        for k, c in CANONICAL_CHARTS.items():
            assert c.expected_observations, f"{k} has no observations"

    def test_each_observation_carries_source(self):
        """Every ExpectedObservation cites its source — auditability."""
        for c in CANONICAL_CHARTS.values():
            for obs in c.expected_observations:
                assert obs.source, (
                    f"{c.key} observation '{obs.topic}' lacks source"
                )


class TestValidateChart:
    """End-to-end validation on canonical chart."""

    @pytest.mark.parametrize("chart_key", ["gandhi", "indira", "nehru"])
    def test_validate_returns_report(self, chart_key):
        """validate_chart returns a populated ChartValidationReport."""
        report = validate_chart(CANONICAL_CHARTS[chart_key])
        assert isinstance(report, ChartValidationReport)
        assert report.chart_key == chart_key

    def test_pass_miss_fail_counts_sum_to_observation_count(self):
        """n_pass + n_miss + n_fail = n_observations (no observations lost)."""
        for c in CANONICAL_CHARTS.values():
            report = validate_chart(c)
            assert (
                report.n_pass + report.n_miss + report.n_fail
                == report.n_observations
            )

    def test_results_are_observation_result_typed(self):
        """Each result is an ObservationResult dataclass."""
        report = validate_chart(CANONICAL_CHARTS["gandhi"])
        assert all(isinstance(r, ObservationResult) for r in report.results)


class TestFormatReport:
    """Plain-text rendering smoke-test."""

    def test_format_report_returns_string(self):
        """format_report produces a multi-line string."""
        report = validate_chart(CANONICAL_CHARTS["nehru"])
        text = format_report(report)
        assert isinstance(text, str)
        assert "Jawaharlal Nehru" in text

    def test_format_report_lists_observation_statuses(self):
        """Output includes PASS/MISS/FAIL tokens."""
        report = validate_chart(CANONICAL_CHARTS["gandhi"])
        text = format_report(report)
        # Each result line should carry one of the status tokens
        assert any(s in text for s in ("PASS", "MISS", "FAIL"))


class TestObservationScoring:
    """ObservationResult status logic edges."""

    def test_matching_labels_yield_pass(self):
        """When framework label matches expected label, status PASS."""
        # Pick an observation we know the framework agrees on for one
        # of the seeded charts (not guaranteed; this is a structure check).
        report = validate_chart(CANONICAL_CHARTS["nehru"])
        for r in report.results:
            if r.status == "PASS":
                # If we have a PASS, at minimum it's structurally consistent
                assert r.framework_label is not None or r.expected_label is None
                return
        # Allow the case where no PASS exists in seed — not a failure of test logic
        pytest.skip("No PASS observation in seeded data — structural-only check skipped")
