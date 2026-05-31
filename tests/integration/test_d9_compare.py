"""Smoke tests for the D9 internal-consistency check."""

from __future__ import annotations

import json

import pytest

from app.integration.d9_compare import (
    D9ComparisonReport,
    PlanetD9Diff,
    compare_d9_signs,
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
        report = compare_d9_signs(bangalore_reading)
        assert isinstance(report, D9ComparisonReport)

    def test_per_planet_entries_are_valid(self, bangalore_reading):
        report = compare_d9_signs(bangalore_reading)
        for entry in report.per_planet:
            assert isinstance(entry, PlanetD9Diff)
            assert 1 <= entry.ephemeris_d9_sign <= 12
            assert 1 <= entry.shodashavarga_d9_sign <= 12


class TestInternalConsistency:
    """The two Track-B D9 implementations MUST agree for every planet."""

    def test_full_agreement(self, bangalore_reading):
        report = compare_d9_signs(bangalore_reading)
        assert report.full_agreement, (
            f"D9 sign disagreement: {report.verdict_summary}"
        )

    def test_no_disagreements(self, bangalore_reading):
        report = compare_d9_signs(bangalore_reading)
        assert report.disagreement_count == 0

    def test_every_planet_agrees(self, bangalore_reading):
        report = compare_d9_signs(bangalore_reading)
        for entry in report.per_planet:
            assert entry.agrees, (
                f"{entry.planet}: ephemeris D9={entry.ephemeris_d9_sign}, "
                f"shodashavarga D9={entry.shodashavarga_d9_sign}"
            )


class TestSerialization:
    def test_report_json_roundtrip(self, bangalore_reading):
        report = compare_d9_signs(bangalore_reading)
        as_json = json.dumps(report.model_dump(mode="json"))
        revived = D9ComparisonReport.model_validate(json.loads(as_json))
        assert revived.full_agreement == report.full_agreement
        assert len(revived.per_planet) == len(report.per_planet)
