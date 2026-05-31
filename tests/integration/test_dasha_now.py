"""Tests for the MD-at-any-JD helper (v1.0.1 fix for the 'current MD' label bug)."""

from __future__ import annotations

import pytest

from app.integration.dasha_now import (
    MDLookup,
    _iso_from_jd,
    md_at_birth,
    md_at_jd,
    md_at_now,
)
from app.reading.proforma import compute as track_a_compute
from app.reading.schema import ChartInput


@pytest.fixture(scope="module")
def mainpuri_reading():
    """Mainpuri chart used in the bug report: 1989-10-12 10:02 IST, lat 27.23 lon 79.03."""
    ci = ChartInput(
        dob="1989-10-12", time="10:02", tz="+05:30",
        lat=27.23, lon=79.03,
    )
    return track_a_compute(ci, enrich=False)


class TestMDAtBirth:
    """md_at_birth returns the MD covering birth_jd."""

    def test_returns_mdlookup(self, mainpuri_reading):
        lookup = md_at_birth(mainpuri_reading)
        assert isinstance(lookup, MDLookup)

    def test_is_at_birth_flag_true(self, mainpuri_reading):
        lookup = md_at_birth(mainpuri_reading)
        assert lookup.is_at_birth is True

    def test_mainpuri_md_at_birth_is_rahu(self, mainpuri_reading):
        """The 1989 native was born inside Rahu MD (1974-1992)."""
        lookup = md_at_birth(mainpuri_reading)
        assert lookup.md_lord == "Rahu"

    def test_age_at_start_is_negative(self, mainpuri_reading):
        """Rahu MD started before birth, so age_at_start < 0."""
        lookup = md_at_birth(mainpuri_reading)
        assert lookup.age_at_start_years < 0

    def test_age_at_end_is_positive_under_three(self, mainpuri_reading):
        """Rahu MD ends ~age 3 (1992 - 1989)."""
        lookup = md_at_birth(mainpuri_reading)
        assert 2.0 < lookup.age_at_end_years < 4.0


class TestMDAtNow:
    """md_at_now returns the MD covering the current UTC moment."""

    def test_returns_mdlookup(self, mainpuri_reading):
        lookup = md_at_now(mainpuri_reading)
        assert isinstance(lookup, MDLookup)

    def test_is_at_birth_flag_false(self, mainpuri_reading):
        lookup = md_at_now(mainpuri_reading)
        assert lookup.is_at_birth is False

    def test_mainpuri_md_at_2026_is_saturn(self, mainpuri_reading):
        """1989 native at age ~37 in 2026 should be in Saturn MD
        (Rahu ended 1992, Jupiter ran 1992-2008 (16y), Saturn started 2008)."""
        lookup = md_at_now(mainpuri_reading)
        assert lookup.md_lord == "Saturn"

    def test_age_now_in_mid_thirties(self, mainpuri_reading):
        """Native born 1989-10-12, current age in 2026 is ~36."""
        lookup = md_at_now(mainpuri_reading)
        assert 35.0 < lookup.age_now_years < 40.0


class TestMDAtAnyJD:
    """md_at_jd accepts an arbitrary target_jd."""

    def test_target_at_age_10_lands_in_jupiter(self, mainpuri_reading):
        """Age 10 = ~1999, native is in Jupiter MD (1992-2008)."""
        birth_jd = mainpuri_reading["chart"]["extras"]["birth_jd"]
        target = birth_jd + 10 * 365.2425
        lookup = md_at_jd(mainpuri_reading, target_jd=target)
        assert lookup.md_lord == "Jupiter"
        assert 9.5 < lookup.age_now_years < 10.5

    def test_target_at_age_25_lands_in_saturn(self, mainpuri_reading):
        """Age 25 = ~2014, native is in Saturn MD (2008-2027)."""
        birth_jd = mainpuri_reading["chart"]["extras"]["birth_jd"]
        target = birth_jd + 25 * 365.2425
        lookup = md_at_jd(mainpuri_reading, target_jd=target)
        assert lookup.md_lord == "Saturn"

    def test_target_outside_cycle_raises(self, mainpuri_reading):
        """Target JD past the natal cycle (~120 years) raises ValueError."""
        birth_jd = mainpuri_reading["chart"]["extras"]["birth_jd"]
        target = birth_jd + 130 * 365.2425
        with pytest.raises(ValueError, match="natal Vimshottari"):
            md_at_jd(mainpuri_reading, target_jd=target)

    def test_empty_reading_raises(self):
        with pytest.raises(ValueError, match="missing or empty"):
            md_at_jd({}, target_jd=2460000.0)


class TestISOConversion:
    def test_known_jd_roundtrip(self):
        """2000-01-01 12:00 UT = JD 2451545.0."""
        iso = _iso_from_jd(2451545.0)
        # Allow ±1 day tolerance because of the .5 rounding in the inverse algo
        assert iso in ("1999-12-31", "2000-01-01", "2000-01-02")
