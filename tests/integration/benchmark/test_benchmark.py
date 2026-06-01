"""Smoke tests for the famous-chart benchmark.

These tests run on a small subset of events (Einstein only) to keep
runtime under 2s. The full benchmark is exposed as a CLI / library API
for offline runs.
"""

from __future__ import annotations

import json

import pytest

from app.integration.benchmark import (
    BenchmarkReport,
    CHART_REGISTRY,
    EventOutcome,
    FAMOUS_EVENTS,
    FamousEvent,
    PerChartSummary,
    PerDomainSummary,
    run_benchmark,
    score_event,
)
from app.integration.benchmark.runner import (
    _classify_outcome,
    _find_active_md_at,
    _jd_from_iso,
)


@pytest.fixture(scope="module")
def einstein_events() -> list[FamousEvent]:
    """Just the 4 Einstein events for fast tests."""
    return [e for e in FAMOUS_EVENTS if e.chart_name == "einstein"]


@pytest.fixture(scope="module")
def einstein_chart():
    return CHART_REGISTRY["einstein"]


# ---------------------------------------------------------------------------
# Corpus integrity
# ---------------------------------------------------------------------------

class TestCorpusIntegrity:
    def test_every_event_references_known_chart(self):
        for event in FAMOUS_EVENTS:
            assert event.chart_name in CHART_REGISTRY, (
                f"Event {event.description!r} references unknown chart "
                f"{event.chart_name!r}"
            )

    def test_event_domains_are_valid(self):
        valid = {"career", "marriage", "children", "wealth", "health", "education"}
        for event in FAMOUS_EVENTS:
            assert event.domain in valid

    def test_event_polarities_are_valid(self):
        valid = {"positive", "negative", "mixed"}
        for event in FAMOUS_EVENTS:
            assert event.polarity in valid

    def test_event_dates_are_iso(self):
        for event in FAMOUS_EVENTS:
            # ISO YYYY-MM-DD must parse
            from datetime import date
            date.fromisoformat(event.event_date)


# ---------------------------------------------------------------------------
# JD math
# ---------------------------------------------------------------------------

class TestJDMath:
    def test_jd_for_known_date(self):
        """1900-01-01 12:00 UT = JD 2415021.0 (canonical)."""
        jd = _jd_from_iso("1900-01-01")
        assert abs(jd - 2415021.0) < 1.0  # tolerate ~1 day for our crude algo

    def test_jd_monotonic(self):
        jd1 = _jd_from_iso("2000-01-01")
        jd2 = _jd_from_iso("2000-01-02")
        assert jd2 > jd1


# ---------------------------------------------------------------------------
# Outcome classification
# ---------------------------------------------------------------------------

class TestOutcomeClassification:
    def test_positive_direction_positive_event_aligned(self):
        assert _classify_outcome("positive", "positive") == "aligned"

    def test_negative_direction_negative_event_aligned(self):
        assert _classify_outcome("negative", "negative") == "aligned"

    def test_positive_direction_negative_event_misaligned(self):
        assert _classify_outcome("positive", "negative") == "misaligned"

    def test_neutral_direction_is_neutral_outcome(self):
        assert _classify_outcome("neutral", "positive") == "neutral"
        assert _classify_outcome("neutral", "negative") == "neutral"

    def test_mixed_direction_is_mixed_outcome(self):
        assert _classify_outcome("mixed", "positive") == "mixed"

    def test_mixed_polarity_accepts_any_nonneutral_direction(self):
        assert _classify_outcome("positive", "mixed") == "aligned"
        assert _classify_outcome("negative", "mixed") == "aligned"

    def test_none_direction_skipped(self):
        assert _classify_outcome(None, "positive") == "skipped"


# ---------------------------------------------------------------------------
# Single-event scoring
# ---------------------------------------------------------------------------

class TestSingleEventScoring:
    def test_einstein_first_event_runs(self, einstein_chart, einstein_events):
        event = einstein_events[0]
        outcome = score_event(einstein_chart, event)
        assert isinstance(outcome, EventOutcome)
        assert outcome.chart_name == "einstein"
        assert outcome.event_date == event.event_date

    def test_outcome_has_md_lord_at_event_date(self, einstein_chart, einstein_events):
        """Active MD at event date should be populated."""
        event = einstein_events[0]
        outcome = score_event(einstein_chart, event)
        # MD lord should be present (or None if it's outside the natal Vimshottari cycle)
        if outcome.outcome != "skipped":
            # most lives fit within ~120y Vimshottari coverage
            assert outcome.active_md_lord_at_event is not None

    def test_outcome_is_valid_label(self, einstein_chart, einstein_events):
        for event in einstein_events:
            outcome = score_event(einstein_chart, event)
            assert outcome.outcome in (
                "aligned", "misaligned", "neutral", "mixed", "skipped",
            )


# ---------------------------------------------------------------------------
# Full benchmark (Einstein subset)
# ---------------------------------------------------------------------------

class TestFullBenchmark:
    def test_runs_on_einstein_subset(self, einstein_events):
        report = run_benchmark(events=einstein_events)
        assert isinstance(report, BenchmarkReport)
        assert report.total_events == len(einstein_events)

    def test_aggregates_sum_to_total(self, einstein_events):
        report = run_benchmark(events=einstein_events)
        total = (
            report.aligned + report.misaligned
            + report.neutral_or_mixed + report.skipped
        )
        assert total == report.total_events

    def test_per_domain_breakdown(self, einstein_events):
        report = run_benchmark(events=einstein_events)
        domains_in_report = {pd.domain for pd in report.per_domain}
        # Einstein has events in marriage + career
        assert "marriage" in domains_in_report
        assert "career" in domains_in_report

    def test_per_chart_breakdown(self, einstein_events):
        report = run_benchmark(events=einstein_events)
        chart_names = {pc.chart_name for pc in report.per_chart}
        assert chart_names == {"einstein"}

    def test_overall_alignment_rate_in_range(self, einstein_events):
        report = run_benchmark(events=einstein_events)
        assert 0.0 <= report.overall_alignment_rate <= 1.0


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_report_json_roundtrip(self, einstein_events):
        report = run_benchmark(events=einstein_events)
        as_json = json.dumps(report.model_dump(mode="json"))
        revived = BenchmarkReport.model_validate(json.loads(as_json))
        assert revived.total_events == report.total_events
        assert revived.overall_alignment_rate == report.overall_alignment_rate
