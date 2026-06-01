"""Tests for app/medini/etl/build_charts_table.py.

Pins the Silver-layer canonical chart against the project's locked
Bangalore baseline (CLAUDE.md): 1990-07-15 12:00 IST at 12.97N 77.59E
produces Virgo Lagna (sign=6, lon~173.99°), Moon at Revati (nakshatra=26).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import swisseph as swe

from app.medini.etl.build_charts_table import (
    GRAHAS,
    _compute_chart,
    _jd_from_birth_date_noon_utc,
    build_charts,
)


# Canonical Bangalore baseline JD = local-noon-IST converted to UTC.
_BANGALORE_JD = swe.julday(1990, 7, 15, 12.0 - 5.5, swe.GREG_CAL)


@pytest.fixture
def persons_df() -> pd.DataFrame:
    """Three rows: ADB w/ time, WD day-precision, ADB w/ missing lat/lon."""
    return pd.DataFrame({
        "person_id": ["ADB:bangalore", "WD:dayonly", "ADB:nogeoloc"],
        "name": ["Bangalore Baseline", "Day Precision", "No Geoloc"],
        "birth_date": ["1990-07-15", "1890-09-15", "1900-01-01"],
        "birth_time": ["12:00:00", None, "00:00:00"],
        "birth_lat": [12.97, 50.468, None],
        "birth_lon": [77.59, -3.532, None],
        "tz_offset": [5.5, None, 0.0],
        "birth_jd": [_BANGALORE_JD, None, None],
        "source": ["astro_databank", "wikidata", "astro_databank"],
    })


class TestBangaloreBaselinePinning:
    """The locked Bangalore baseline must produce Virgo Lagna at lon~173.99°."""

    def test_ascendant_is_virgo(self):
        """Project's locked invariant: 1990-07-15 12:00 IST -> Virgo Lagna."""
        chart = _compute_chart(
            "T", _BANGALORE_JD, "1990-07-15", 12.97, 77.59,
        )
        assert chart["asc_sign"] == 6  # Virgo

    def test_ascendant_longitude_within_one_degree_of_pinned(self):
        """asc_lon should pin at ~173.99° per CLAUDE.md."""
        chart = _compute_chart(
            "T", _BANGALORE_JD, "1990-07-15", 12.97, 77.59,
        )
        assert 173.0 < chart["asc_lon"] < 175.0

    def test_moon_at_revati(self):
        """Project's locked invariant: Moon at Revati (nakshatra index 26)."""
        chart = _compute_chart(
            "T", _BANGALORE_JD, "1990-07-15", 12.97, 77.59,
        )
        assert chart["moon_nakshatra"] == 26


class TestSchemaContract:
    """charts.parquet must always emit the same columns for every chart."""

    def test_every_graha_has_lon_sign_house_nakshatra(self):
        """Each of the 9 grahas gets a 4-tuple of columns."""
        chart = _compute_chart(
            "T", _BANGALORE_JD, "1990-07-15", 12.97, 77.59,
        )
        for g in GRAHAS:
            for suffix in ("lon", "sign", "house", "nakshatra"):
                assert f"{g}_{suffix}" in chart, f"Missing {g}_{suffix}"

    def test_houses_are_in_valid_range(self):
        """Whole-sign house numbers are 1..12 inclusive."""
        chart = _compute_chart(
            "T", _BANGALORE_JD, "1990-07-15", 12.97, 77.59,
        )
        for g in GRAHAS:
            assert 1 <= chart[f"{g}_house"] <= 12, f"{g}_house out of range"

    def test_signs_are_in_valid_range(self):
        """Sign indices are 1..12 inclusive."""
        chart = _compute_chart(
            "T", _BANGALORE_JD, "1990-07-15", 12.97, 77.59,
        )
        for g in GRAHAS:
            assert 1 <= chart[f"{g}_sign"] <= 12, f"{g}_sign out of range"

    def test_nakshatras_are_in_valid_range(self):
        """Nakshatra indices are 0..26 inclusive (matches app/core/nakshatra.py)."""
        chart = _compute_chart(
            "T", _BANGALORE_JD, "1990-07-15", 12.97, 77.59,
        )
        for g in GRAHAS:
            n = chart[f"{g}_nakshatra"]
            assert 0 <= n <= 26, f"{g}_nakshatra={n} out of range"


class TestKetuOppositeToRahu:
    """Ketu must always be exactly 180° from Rahu — a structural invariant."""

    def test_ketu_lon_is_rahu_plus_180_mod_360(self):
        """Ketu is the south lunar node; geometric necessity, not data."""
        chart = _compute_chart(
            "T", _BANGALORE_JD, "1990-07-15", 12.97, 77.59,
        )
        delta = abs((chart["ketu_lon"] - chart["rahu_lon"]) % 360 - 180)
        assert delta < 0.001, f"Ketu off by {delta}° from Rahu opposition"


class TestDayPrecisionFallback:
    """Wikidata-style day-precision births fall back to noon-UTC."""

    def test_day_precision_uses_noon_utc(self):
        """A None birth_jd + valid birth_date -> noon-UTC JD."""
        chart = _compute_chart(
            "T", None, "1890-09-15", 50.468, -3.532,
        )
        assert chart is not None
        assert chart["time_precision"] == "day"
        expected_jd = swe.julday(1890, 9, 15, 12.0, swe.GREG_CAL)
        assert abs(chart["birth_jd_used"] - expected_jd) < 0.001

    def test_jd_from_birth_date_noon_utc(self):
        """Helper round-trips a Gregorian date string to JD at 12 UTC."""
        jd = _jd_from_birth_date_noon_utc("2000-01-01")
        # 2000-01-01 12:00 UTC is the standard J2000 reference - 0.5
        assert jd is not None
        assert abs(jd - 2451545.0) < 0.001

    def test_malformed_birth_date_returns_none(self):
        """Unparseable date string -> None (caller will skip the row)."""
        assert _jd_from_birth_date_noon_utc("not-a-date") is None
        assert _jd_from_birth_date_noon_utc(None) is None


class TestMissingGeolocSkipsRow:
    """Persons without lat/lon cannot have an ascendant -> skipped."""

    def test_missing_lat_returns_none(self):
        """No latitude -> can't compute Lagna -> row is dropped."""
        chart = _compute_chart("T", 2451545.0, "2000-01-01", None, 77.0)
        assert chart is None

    def test_missing_lon_returns_none(self):
        """No longitude -> can't compute Lagna -> row is dropped."""
        chart = _compute_chart("T", 2451545.0, "2000-01-01", 12.0, None)
        assert chart is None


class TestBatchBuild:
    """build_charts handles a mixed-precision dataframe end-to-end."""

    def test_three_persons_one_skipped(self, persons_df: pd.DataFrame):
        """Two rows have geoloc and produce charts; one is skipped."""
        result = build_charts(persons_df, workers=1)
        assert len(result) == 2  # nogeoloc row dropped
        # The Bangalore row should be present.
        bangalore = result[result["person_id"] == "ADB:bangalore"]
        assert len(bangalore) == 1
        assert bangalore.iloc[0]["asc_sign"] == 6

    def test_time_precision_marked_per_corpus(self, persons_df: pd.DataFrame):
        """ADB w/ birth_jd -> 'minute'; WD w/o -> 'day'."""
        result = build_charts(persons_df, workers=1)
        precisions = dict(zip(result["person_id"], result["time_precision"]))
        assert precisions["ADB:bangalore"] == "minute"
        assert precisions["WD:dayonly"] == "day"
