"""Smoke tests for the Argala+Drishti comparator."""

from __future__ import annotations

import json

import pytest

from app.integration.argala_drishti_compare import (
    ArgalaDrishtiComparisonReport,
    compare_argala_drishti,
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


class TestComparatorMechanics:
    def test_returns_report(self, bangalore_reading):
        report = compare_argala_drishti(bangalore_reading)
        assert isinstance(report, ArgalaDrishtiComparisonReport)

    def test_twelve_bhavas_covered(self, bangalore_reading):
        report = compare_argala_drishti(bangalore_reading)
        assert len(report.per_bhava) == 12
        bhavas = {entry.bhava for entry in report.per_bhava}
        assert bhavas == set(range(1, 13))


class TestPerBhavaShape:
    def test_planet_lists_are_sorted(self, bangalore_reading):
        report = compare_argala_drishti(bangalore_reading)
        for entry in report.per_bhava:
            assert entry.track_a_causing_planets == sorted(entry.track_a_causing_planets)
            assert entry.track_b_causing_planets == sorted(entry.track_b_causing_planets)

    def test_intersection_is_subset_of_both(self, bangalore_reading):
        report = compare_argala_drishti(bangalore_reading)
        for entry in report.per_bhava:
            a_set = set(entry.track_a_causing_planets)
            b_set = set(entry.track_b_causing_planets)
            assert set(entry.intersection).issubset(a_set & b_set)

    def test_only_in_a_disjoint_from_only_in_b(self, bangalore_reading):
        report = compare_argala_drishti(bangalore_reading)
        for entry in report.per_bhava:
            assert not (set(entry.only_in_a) & set(entry.only_in_b))


class TestTrackBStrict:
    """Track B always produces some argala output (every house has at least
    one source if any planet is in a 2/4/11/5 position relative to it)."""

    def test_track_b_emits_at_least_one_source_somewhere(self, bangalore_reading):
        report = compare_argala_drishti(bangalore_reading)
        total_b = sum(len(entry.track_b_causing_planets) for entry in report.per_bhava)
        assert total_b > 0, "Track B's argala_report produced no causing planets at all"


class TestAggregation:
    def test_counts_sum_to_twelve(self, bangalore_reading):
        report = compare_argala_drishti(bangalore_reading)
        assert report.agreement_count + report.disagreement_count == 12

    def test_verdict_summary_has_meaningful_content(self, bangalore_reading):
        report = compare_argala_drishti(bangalore_reading)
        assert (
            "FULL AGREEMENT" in report.verdict_summary
            or "agreements=" in report.verdict_summary
        )


class TestSerialization:
    def test_report_json_roundtrip(self, bangalore_reading):
        report = compare_argala_drishti(bangalore_reading)
        as_json = json.dumps(report.model_dump(mode="json"))
        revived = ArgalaDrishtiComparisonReport.model_validate(json.loads(as_json))
        assert revived.full_agreement == report.full_agreement
        assert len(revived.per_bhava) == 12
