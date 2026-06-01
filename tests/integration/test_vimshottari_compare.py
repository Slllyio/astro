"""Smoke tests for the Vimshottari current-MD comparator.

Both engines compute current-MD from Moon's longitude + birth_jd using
the same nakshatra-floor math, so full agreement is expected.
"""

from __future__ import annotations

import json

import pytest

from app.integration.vimshottari_compare import (
    VimshottariCurrentMDReport,
    compare_vimshottari_current_md,
)
from app.reading.proforma import compute
from app.reading.schema import ChartInput


@pytest.fixture(scope="module")
def bangalore_reading() -> dict:
    """Real Bangalore baseline reading (Virgo lagna, 1990-07-15)."""
    ci = ChartInput(
        dob="1990-07-15", time="12:00", tz="+05:30",
        lat=12.97, lon=77.59,
    )
    return compute(ci, enrich=False)


def _extract_inputs(reading: dict) -> tuple[float, float]:
    """Pull moon_longitude + birth_jd from a reading."""
    chart = reading["chart"]
    return chart["planets"]["Moon"]["longitude"], chart["extras"]["birth_jd"]


class TestComparatorMechanics:
    def test_returns_report(self, bangalore_reading):
        moon_lon, birth_jd = _extract_inputs(bangalore_reading)
        report = compare_vimshottari_current_md(
            bangalore_reading, moon_longitude=moon_lon, birth_jd=birth_jd,
        )
        assert isinstance(report, VimshottariCurrentMDReport)

    def test_reading_without_md_judgments_raises(self):
        with pytest.raises(ValueError):
            compare_vimshottari_current_md(
                {"sequences": {"md_judgments": []}, "chart": {}},
                moon_longitude=88.0,
                birth_jd=2448088.0,
            )


class TestAgreementOnBangalore:
    """Both engines share the nakshatra-floor Vimshottari math — they MUST agree."""

    def test_md_lord_agrees(self, bangalore_reading):
        moon_lon, birth_jd = _extract_inputs(bangalore_reading)
        report = compare_vimshottari_current_md(
            bangalore_reading, moon_longitude=moon_lon, birth_jd=birth_jd,
        )
        assert report.md_lord_agrees, (
            f"MD lord diverges: A={report.track_a_md_lord}, B={report.track_b_md_lord}"
        )

    def test_md_dates_agree(self, bangalore_reading):
        moon_lon, birth_jd = _extract_inputs(bangalore_reading)
        report = compare_vimshottari_current_md(
            bangalore_reading, moon_longitude=moon_lon, birth_jd=birth_jd,
        )
        assert report.md_dates_agree, (
            f"Dates diverge: A={report.track_a_md_start}->{report.track_a_md_end}, "
            f"B={report.track_b_md_start}->{report.track_b_md_end}"
        )

    def test_duration_agrees(self, bangalore_reading):
        moon_lon, birth_jd = _extract_inputs(bangalore_reading)
        report = compare_vimshottari_current_md(
            bangalore_reading, moon_longitude=moon_lon, birth_jd=birth_jd,
        )
        assert report.duration_agrees

    def test_verdict_says_full_agreement(self, bangalore_reading):
        moon_lon, birth_jd = _extract_inputs(bangalore_reading)
        report = compare_vimshottari_current_md(
            bangalore_reading, moon_longitude=moon_lon, birth_jd=birth_jd,
        )
        assert "FULL AGREEMENT" in report.verdict_summary

    def test_md_lord_for_bangalore_is_mercury(self, bangalore_reading):
        """Bangalore 1990 baseline: Mercury MD per locked-decision lockfile."""
        moon_lon, birth_jd = _extract_inputs(bangalore_reading)
        report = compare_vimshottari_current_md(
            bangalore_reading, moon_longitude=moon_lon, birth_jd=birth_jd,
        )
        assert report.track_a_md_lord == "Mercury"
        assert report.track_b_md_lord == "Mercury"


class TestSerialization:
    def test_report_json_roundtrip(self, bangalore_reading):
        moon_lon, birth_jd = _extract_inputs(bangalore_reading)
        report = compare_vimshottari_current_md(
            bangalore_reading, moon_longitude=moon_lon, birth_jd=birth_jd,
        )
        as_json = json.dumps(report.model_dump(mode="json"))
        revived = VimshottariCurrentMDReport.model_validate(json.loads(as_json))
        assert revived.md_lord_agrees == report.md_lord_agrees
