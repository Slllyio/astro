"""Feature-bank construction and the screening cohort filter.

Exercised on a handful of real charts rather than mocks — the banks are thin
enough that mocking the ephemeris would test nothing. What matters here is that
the banks stay separated, that undefined houses surface as NaN rather than a
substituted value, and that flagged rows are excluded from the cohort by an
explicit filter rather than by luck.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from app.empirical.tournament.build_feature_banks import (
    BANKS,
    ChartRow,
    _chartless_features,
    _day_of_year,
    bank_columns,
    build_banks,
)
from app.empirical.tournament.run_screening import _cohort


def _row(**overrides) -> ChartRow:
    base = dict(
        person_id="p1", year=1900, month=6, day=15, ut_hour=12.0,
        latitude=48.85, longitude=2.35, label="scientist",
        time_tier="A", data_quality="ok",
    )
    base.update(overrides)
    return ChartRow(**base)


class TestDayOfYear:
    """Tolerant of the source's impossible dates, correct on real ones."""

    def test_january_first(self):
        """Day 1 of the year."""
        assert _day_of_year(1900, 1, 1) == 1

    def test_march_first_in_a_common_year(self):
        """31 + 28 + 1 = 60."""
        assert _day_of_year(1901, 3, 1) == 60

    def test_march_first_in_a_leap_year(self):
        """A leap day shifts everything after February by one."""
        assert _day_of_year(1904, 3, 1) == 61

    def test_1900_is_not_a_leap_year(self):
        """Divisible by 100 but not 400 — the Gregorian exception."""
        assert _day_of_year(1900, 3, 1) == 60

    def test_impossible_date_does_not_raise(self):
        """CURA publishes 1869-02-29 and 1888-06-31; the builder must not crash.

        Those rows are flagged at import and excluded from cohorts, but they
        still need a row in the matrix so the flag stays visible downstream.
        """
        assert _day_of_year(1869, 2, 29) > 0
        assert _day_of_year(1888, 6, 31) > 0

    def test_out_of_range_month_is_survivable(self):
        """A corrupt month falls back rather than throwing."""
        assert _day_of_year(1900, 13, 1) == 1


class TestChartlessBank:
    """The bar every chart bank must beat."""

    def test_carries_era_and_geography(self):
        """Birth year, latitude, longitude — the AUC-0.744 ingredients."""
        features = _chartless_features(_row())
        assert features["cl_birth_year"] == 1900.0
        assert features["cl_latitude"] == pytest.approx(48.85)
        assert features["cl_longitude"] == pytest.approx(2.35)

    def test_carries_full_date_precision_not_just_the_year(self):
        """The bar must know the date, or a chart bank beats it on date alone.

        The slow planets pin the birth epoch to within days. A twin holding only
        the integer year leaves sub-year precision uncontrolled, and every chart
        bank then "wins" by knowing when the person was born more exactly — which
        is not astrology.
        """
        january = _chartless_features(_row(month=1, day=1))
        december = _chartless_features(_row(month=12, day=31))
        assert january["cl_birth_decimal_year"] < december["cl_birth_decimal_year"]
        assert december["cl_birth_decimal_year"] - january["cl_birth_decimal_year"] > 0.9

    def test_decimal_year_orders_across_years(self):
        """Dec 1899 must sort before Jan 1900."""
        earlier = _chartless_features(_row(year=1899, month=12, day=31))
        later = _chartless_features(_row(year=1900, month=1, day=1))
        assert earlier["cl_birth_decimal_year"] < later["cl_birth_decimal_year"]

    def test_season_is_circular(self):
        """December and January are adjacent, so season enters as sin/cos.

        A raw day-of-year would make 31 Dec and 1 Jan maximally distant.
        """
        december = _chartless_features(_row(month=12, day=31))
        january = _chartless_features(_row(month=1, day=1))
        distance = math.hypot(
            december["cl_season_sin"] - january["cl_season_sin"],
            december["cl_season_cos"] - january["cl_season_cos"],
        )
        assert distance < 0.05


class TestBankSeparation:
    """A scoring run must not be able to mix banks by accident."""

    def test_every_declared_bank_yields_columns(self):
        """All three banks are populated for a real chart."""
        frame, columns = build_banks([_row()], progress_every=0)
        for bank in BANKS:
            assert columns[bank], f"{bank} produced no features"

    def test_bank_prefixes_do_not_overlap(self):
        """No column belongs to two banks."""
        frame, _ = build_banks([_row()], progress_every=0)
        groups = [set(bank_columns(frame, b)) for b in BANKS]
        for i, first in enumerate(groups):
            for second in groups[i + 1:]:
                assert not (first & second)

    def test_unknown_bank_rejected(self):
        """A typo must not silently return an empty feature list."""
        frame, _ = build_banks([_row()], progress_every=0)
        with pytest.raises(KeyError):
            bank_columns(frame, "vedic_timing")

    def test_label_and_flags_are_not_features(self):
        """Identity and quality columns must never enter a bank."""
        frame, _ = build_banks([_row()], progress_every=0)
        all_features = {c for b in BANKS for c in bank_columns(frame, b)}
        for column in ("person_id", "label", "time_tier", "data_quality"):
            assert column not in all_features


class TestLongitudeEncoding:
    """Longitudes enter as sin/cos so the 0°/360° seam is not a cliff."""

    def test_no_raw_longitude_column_survives(self):
        """A raw-degree column would let a model learn the cusp, not the sky."""
        frame, _ = build_banks([_row()], progress_every=0)
        assert not [c for c in frame.columns if c.endswith("_lon")]

    def test_sin_cos_pair_present_for_every_body(self):
        """Both halves are needed; either alone is ambiguous."""
        frame, _ = build_banks([_row()], progress_every=0)
        sines = {c[:-8] for c in frame.columns if c.endswith("_lon_sin")}
        cosines = {c[:-8] for c in frame.columns if c.endswith("_lon_cos")}
        assert sines and sines == cosines


class TestUndefinedHouses:
    """Polar latitudes must surface as NaN, never a substituted system."""

    def test_polar_chart_yields_nan_angles(self):
        """At 78°N Placidus is undefined — the gap must be visible."""
        frame, _ = build_banks([_row(latitude=78.2, longitude=15.6)], progress_every=0)
        assert math.isnan(frame["w_asc_sin"].iloc[0])
        assert math.isnan(frame["w_Sun_house"].iloc[0])

    def test_temperate_chart_has_real_angles(self):
        """The ordinary case still produces usable values."""
        frame, _ = build_banks([_row()], progress_every=0)
        assert not math.isnan(frame["w_asc_sin"].iloc[0])
        assert 1 <= frame["w_Sun_house"].iloc[0] <= 12


class TestCohortFilter:
    """Flagged rows are excluded explicitly, not by luck."""

    def _frame(self) -> pd.DataFrame:
        return pd.DataFrame({
            "person_id": ["a", "b", "c", "d"],
            "time_tier": ["A", "B", "A", "A"],
            "data_quality": ["ok", "ok", "invalid_date:1888-06-31", "ok"],
            "label": ["scientist"] * 4,
            "cl_birth_year": [1900.0] * 4,
        })

    def test_tier_a_cohort_excludes_rounded_times(self):
        """A rounded time cannot evidence a transit exact for hours."""
        assert set(_cohort(self._frame(), tier="A", min_per_stratum=0)[0]["person_id"]) == {"a", "d"}

    def test_quality_flagged_rows_are_always_excluded(self):
        """A row with an impossible date is out of every cohort."""
        for tier in ("A", "AB"):
            assert "c" not in set(_cohort(self._frame(), tier=tier, min_per_stratum=0)[0]["person_id"])

    def test_ab_cohort_admits_tier_b(self):
        """Relaxing the tier admits rounded times but not flagged ones."""
        assert set(_cohort(self._frame(), tier="AB", min_per_stratum=0)[0]["person_id"]) == {"a", "b", "d"}
