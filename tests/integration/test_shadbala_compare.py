"""Smoke tests for the Shadbala comparator."""

from __future__ import annotations

import json

import pytest

from app.integration.shadbala_compare import (
    ShadbalaComparisonReport,
    compare_shadbala,
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
        report = compare_shadbala(bangalore_reading)
        assert isinstance(report, ShadbalaComparisonReport)

    def test_seven_classical_planets_in_per_planet(self, bangalore_reading):
        """Track A's Phase 1 + Track B both cover the 7 classical planets only."""
        report = compare_shadbala(bangalore_reading)
        assert len(report.per_planet) == 7
        planets = {entry.planet for entry in report.per_planet}
        assert planets == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}

    def test_track_b_has_strongest_and_weakest(self, bangalore_reading):
        report = compare_shadbala(bangalore_reading)
        assert report.track_b_strongest is not None
        assert report.track_b_weakest is not None
        assert report.track_b_strongest in {p.planet for p in report.per_planet}


class TestPerPlanetShape:
    def test_track_b_total_virupa_is_nonneg_when_present(self, bangalore_reading):
        report = compare_shadbala(bangalore_reading)
        for entry in report.per_planet:
            if entry.track_b_total_virupa is not None:
                assert entry.track_b_total_virupa >= 0

    def test_classification_aligns_is_bool_or_none(self, bangalore_reading):
        report = compare_shadbala(bangalore_reading)
        for entry in report.per_planet:
            assert entry.classification_aligns in (True, False, None)


class TestAggregation:
    def test_alignment_counts_add_up(self, bangalore_reading):
        report = compare_shadbala(bangalore_reading)
        agreed_plus_misagreed = (
            report.classifications_in_agreement + report.classifications_in_disagreement
        )
        # Each comparable planet contributes to exactly one of the two counts
        comparable = sum(
            1 for entry in report.per_planet
            if entry.classification_aligns is not None
        )
        assert agreed_plus_misagreed == comparable

    def test_strong_lists_are_subsets_of_classical_7(self, bangalore_reading):
        report = compare_shadbala(bangalore_reading)
        classical = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert set(report.track_a_strong_planets).issubset(classical)
        assert set(report.track_b_strong_planets).issubset(classical)


class TestSerialization:
    def test_report_json_roundtrip(self, bangalore_reading):
        report = compare_shadbala(bangalore_reading)
        as_json = json.dumps(report.model_dump(mode="json"))
        revived = ShadbalaComparisonReport.model_validate(json.loads(as_json))
        assert len(revived.per_planet) == 7
