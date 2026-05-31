"""Smoke tests for the yoga detection comparator."""

from __future__ import annotations

import json

import pytest

from app.integration.yoga_compare import (
    YogaComparisonReport,
    _normalise,
    compare_yoga_detection,
)
from app.reading.proforma import compute
from app.reading.schema import ChartInput


@pytest.fixture(scope="module")
def bangalore_reading() -> dict:
    ci = ChartInput(
        dob="1990-07-15", time="12:00", tz="+05:30",
        lat=12.97, lon=77.59,
    )
    return compute(ci, enrich=False)


class TestNormalisation:
    """Name normalisation maps both engines' names to canonical form."""

    def test_strips_namespace_prefix(self):
        assert _normalise("yogas_extended.lakshmi") == "lakshmi"
        assert _normalise("foundation.gajakesari") == "gajakesari"

    def test_lowercases_titlecase(self):
        assert _normalise("Lakshmi") == "lakshmi"
        assert _normalise("Gajakesari") == "gajakesari"

    def test_replaces_underscore_with_space(self):
        assert _normalise("vipareeta_raja") == "vipareeta raja"

    def test_strips_trailing_yoga_suffix(self):
        assert _normalise("Lakshmi Yoga") == "lakshmi"
        assert _normalise("vipareeta_raja_yoga") == "vipareeta raja"

    def test_strips_trailing_dosha_suffix(self):
        assert _normalise("Mangal Dosha") == "mangal"

    def test_track_a_and_track_b_lakshmi_canonical(self):
        """The two engines must produce the SAME canonical name for the same yoga."""
        assert _normalise("yogas_extended.lakshmi") == _normalise("Lakshmi")


class TestComparatorMechanics:
    def test_returns_report(self, bangalore_reading):
        report = compare_yoga_detection(bangalore_reading)
        assert isinstance(report, YogaComparisonReport)

    def test_track_a_yoga_count_is_nonzero(self, bangalore_reading):
        """Bangalore Virgo chart triggers SOME Track-A yogas."""
        report = compare_yoga_detection(bangalore_reading)
        assert report.track_a_yoga_count > 0

    def test_track_b_yoga_count_is_nonzero(self, bangalore_reading):
        """Track B's yoga_library detects at least one yoga for Bangalore."""
        report = compare_yoga_detection(bangalore_reading)
        assert report.track_b_yoga_count > 0


class TestSymmetricDiff:
    def test_per_yoga_partitioning_is_complete(self, bangalore_reading):
        """Every yoga in per_yoga is exactly one of: both, track_a_only, track_b_only."""
        report = compare_yoga_detection(bangalore_reading)
        for entry in report.per_yoga:
            assert entry.detected_by in ("both", "track_a_only", "track_b_only")

    def test_both_set_is_consistent_with_per_yoga(self, bangalore_reading):
        report = compare_yoga_detection(bangalore_reading)
        both_per_yoga = {e.canonical_name for e in report.per_yoga if e.detected_by == "both"}
        assert set(report.both) == both_per_yoga

    def test_intersection_count_matches_both_list(self, bangalore_reading):
        report = compare_yoga_detection(bangalore_reading)
        assert report.intersection_count == len(report.both)

    def test_track_b_only_entries_have_no_track_a_names(self, bangalore_reading):
        report = compare_yoga_detection(bangalore_reading)
        for entry in report.per_yoga:
            if entry.detected_by == "track_b_only":
                assert entry.track_a_names == []
                assert entry.track_b_name is not None


class TestSerialization:
    def test_report_json_roundtrip(self, bangalore_reading):
        report = compare_yoga_detection(bangalore_reading)
        as_json = json.dumps(report.model_dump(mode="json"))
        revived = YogaComparisonReport.model_validate(json.loads(as_json))
        assert revived.intersection_count == report.intersection_count
        assert set(revived.both) == set(report.both)


class TestVerdictSummary:
    def test_verdict_includes_counts(self, bangalore_reading):
        report = compare_yoga_detection(bangalore_reading)
        # Verdict format: "both=N, track_a_only=N, track_b_only=N"
        for label in ("both=", "track_a_only=", "track_b_only="):
            assert label in report.verdict_summary
