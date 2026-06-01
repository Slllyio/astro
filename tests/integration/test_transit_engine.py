"""M2 tests: transit_engine adapter wrapping app.core.gochara_engine."""

from __future__ import annotations

import pytest

from app.integration.transit_engine import (
    TransitReport,
    transit_at_now,
    transit_signs_at,
    transit_state_at,
)
from app.reading.proforma import compute as track_a_compute
from app.reading.schema import ChartInput


@pytest.fixture(scope="module")
def mainpuri_reading():
    return track_a_compute(
        ChartInput(dob="1989-10-12", time="10:02", tz="+05:30",
                   lat=27.23, lon=79.03),
        enrich=False,
    )


@pytest.fixture(scope="module")
def bangalore_reading():
    return track_a_compute(
        ChartInput(dob="1990-07-15", time="12:00", tz="+05:30",
                   lat=12.97, lon=77.59),
        enrich=False,
    )


# ---------------------------------------------------------------------------
# transit_signs_at
# ---------------------------------------------------------------------------

class TestTransitSignsAt:
    def test_returns_nine_planets(self):
        signs = transit_signs_at()
        assert set(signs.keys()) == {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        }

    def test_each_sign_in_range_1_to_12(self):
        signs = transit_signs_at()
        for planet, sign in signs.items():
            assert 1 <= sign <= 12, f"{planet}: sign {sign} out of range"

    def test_rahu_ketu_180_apart(self):
        signs = transit_signs_at()
        # Ketu is exactly 180° from Rahu, so 6 signs away (mod 12)
        diff = abs(signs["Ketu"] - signs["Rahu"])
        assert diff == 6, f"Rahu={signs['Rahu']}, Ketu={signs['Ketu']}"

    def test_specific_jd_deterministic(self):
        """Same JD must always produce same transit signs."""
        jd_2000 = 2451545.0  # 2000-01-01 12:00 UT
        a = transit_signs_at(target_jd=jd_2000)
        b = transit_signs_at(target_jd=jd_2000)
        assert a == b


# ---------------------------------------------------------------------------
# transit_state_at + transit_at_now
# ---------------------------------------------------------------------------

class TestTransitStateAt:
    def test_returns_transit_report(self, mainpuri_reading):
        report = transit_at_now(mainpuri_reading)
        assert isinstance(report, TransitReport)

    def test_twelve_bhavas_covered(self, mainpuri_reading):
        report = transit_at_now(mainpuri_reading)
        assert set(report.per_bhava.keys()) == set(range(1, 13))

    def test_transit_signs_propagated(self, mainpuri_reading):
        report = transit_at_now(mainpuri_reading)
        assert len(report.transit_signs) == 9

    def test_saturn_from_moon_in_range_1_to_12(self, mainpuri_reading):
        report = transit_at_now(mainpuri_reading)
        assert 1 <= report.saturn_from_moon <= 12


class TestMainpuriSpecificFlags:
    """Mainpuri 1989 native: Moon in Aquarius, Saturn currently in Aquarius
    (it's 2026), so Saturn-from-Moon = 1 -> Sade-Sati flag should fire."""

    def test_saturn_from_moon_for_mainpuri_2026(self, mainpuri_reading):
        report = transit_at_now(mainpuri_reading)
        # Saturn currently in late Aquarius/early Pisces. Moon in Aquarius.
        # So Saturn-from-Moon should be 1 or 2 (currently mid-Sade-Sati).
        assert report.saturn_from_moon in (1, 2, 12)

    def test_sade_sati_flag_consistent_with_saturn_from_moon(self, mainpuri_reading):
        """Sade-Sati doctrine: active when Saturn in 12H, 1H, or 2H from Moon."""
        report = transit_at_now(mainpuri_reading)
        if report.saturn_from_moon in (12, 1, 2):
            assert report.sade_sati_active
        else:
            assert not report.sade_sati_active


class TestSerialization:
    def test_transit_report_json_roundtrip(self, mainpuri_reading):
        import json
        report = transit_at_now(mainpuri_reading)
        as_json = json.dumps(report.model_dump(mode="json"))
        revived = TransitReport.model_validate(json.loads(as_json))
        assert revived.saturn_from_moon == report.saturn_from_moon
        assert len(revived.per_bhava) == 12


class TestBangaloreControl:
    def test_bangalore_runs_cleanly(self, bangalore_reading):
        report = transit_at_now(bangalore_reading)
        assert isinstance(report, TransitReport)
        assert len(report.per_bhava) == 12
