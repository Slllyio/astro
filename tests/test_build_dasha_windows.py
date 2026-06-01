"""Tests for app/medini/etl/build_dasha_windows.py.

Pins the Vimshottari MDxAD window expansion against:
- The 81-windows-per-person invariant
- AD-sequence starts with the parent MD lord (canonical Vimshottari rule)
- AD durations sum back to the parent MD duration (no rounding drift)
- The Bangalore baseline person's natal MD lord is Mercury (per CLAUDE.md)
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest
import swisseph as swe

from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
from app.medini.etl.build_dasha_windows import (
    _LORD_NAMES,
    _antardashas_in_md,
    _windows_for_person,
    build_dasha_windows,
)

# Bangalore baseline: 1990-07-15 12:00 IST (06:30 UTC).
# Per CLAUDE.md: Mercury MD running 1978-03-26 -> 1995-03-26 (~17 years).
_BANGALORE_JD = swe.julday(1990, 7, 15, 12.0 - 5.5, swe.GREG_CAL)
_BANGALORE_MOON_LON = 356.32  # Revati nakshatra (index 26) — lord Mercury, per CLAUDE.md


class TestAntardashaExpansion:
    """One MD expands into exactly 9 ADs starting with the MD lord."""

    def test_md_expands_to_nine_ads(self):
        """Vimshottari rule: every MD has 9 sub-periods."""
        ads = _antardashas_in_md("Saturn", md_start_jd=0.0, md_duration_years=19.0)
        assert len(ads) == 9

    def test_first_ad_is_md_lord_itself(self):
        """The AD sequence always begins with the parent MD's lord."""
        ads = _antardashas_in_md("Jupiter", md_start_jd=0.0, md_duration_years=16.0)
        assert ads[0][0] == "Jupiter"

    def test_ad_durations_sum_to_md_duration(self):
        """No rounding drift: 9 AD lengths must reconstruct the parent MD length."""
        md_duration = 20.0  # Venus MD
        ads = _antardashas_in_md("Venus", 0.0, md_duration)
        total_days = ads[-1][2] - ads[0][1]
        expected_days = md_duration * DAYS_PER_VEDIC_YEAR
        assert math.isclose(total_days, expected_days, rel_tol=1e-9)

    def test_consecutive_ads_have_no_gaps(self):
        """Each AD's end_jd must equal the next AD's start_jd exactly."""
        ads = _antardashas_in_md("Moon", md_start_jd=2400000.0, md_duration_years=10.0)
        for i in range(len(ads) - 1):
            assert ads[i][2] == ads[i + 1][1]

    def test_ad_lords_cycle_through_canonical_vimshottari_order(self):
        """Starting from MD lord, ADs follow (Ketu, Venus, Sun, ...) wrapping."""
        ads = _antardashas_in_md("Sun", 0.0, 6.0)
        lords = [ad[0] for ad in ads]
        # Sun is at index 2 in _LORD_NAMES. ADs should cycle from there.
        expected = [_LORD_NAMES[(2 + i) % 9] for i in range(9)]
        assert lords == expected


class TestPerPersonWindows:
    """Each person yields exactly 81 windows spanning the full Vimshottari cycle."""

    def test_eighty_one_windows_per_person(self):
        """9 MDs x 9 ADs = 81 windows, no more, no less."""
        rows = _windows_for_person("T", _BANGALORE_JD, _BANGALORE_MOON_LON)
        assert len(rows) == 81

    def test_full_cycle_spans_one_hundred_twenty_years(self):
        """Total cycle duration should be 120 Vedic years end-to-end."""
        rows = _windows_for_person("T", _BANGALORE_JD, _BANGALORE_MOON_LON)
        total_days = rows[-1]["end_jd"] - rows[0]["start_jd"]
        expected = 120 * DAYS_PER_VEDIC_YEAR
        assert math.isclose(total_days, expected, rel_tol=1e-6)

    def test_window_ids_are_unique(self):
        """The composite (person, MD, AD, md_seq) yields unique window_ids."""
        rows = _windows_for_person("T", _BANGALORE_JD, _BANGALORE_MOON_LON)
        ids = [r["window_id"] for r in rows]
        assert len(set(ids)) == 81

    def test_md_seq_zero_spans_birth(self):
        """Birth must fall within some AD of md_seq=0 (the natal MD).

        The natal MD started ``years_elapsed`` BEFORE birth (compute_full_mahadasha_cycle
        anchors it that way), so md_seq=0's ad_seq=0 is before birth; one of the
        nine ADs of md_seq=0 must contain birth_jd.
        """
        rows = _windows_for_person("T", _BANGALORE_JD, _BANGALORE_MOON_LON)
        natal_mds = [r for r in rows if r["md_seq"] == 0]
        containing = [r for r in natal_mds
                      if r["start_jd"] <= _BANGALORE_JD <= r["end_jd"]]
        assert len(containing) == 1, "birth must fall in exactly one AD of the natal MD"


class TestBangaloreNatalMD:
    """CLAUDE.md pins natal MD as Mercury for 1990-07-15 Bangalore baseline."""

    def test_natal_md_lord_is_mercury(self):
        """The MD active at birth must be Mercury per project conventions."""
        rows = _windows_for_person("T", _BANGALORE_JD, _BANGALORE_MOON_LON)
        md0 = [r for r in rows if r["md_seq"] == 0][0]
        assert md0["md_lord"] == "Mercury"


class TestBatchBuild:
    """End-to-end via persons + charts dataframes."""

    @pytest.fixture
    def small_persons_and_charts(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Two persons, both with valid moon_lon."""
        persons = pd.DataFrame({
            "person_id": ["P:A", "P:B"],
            "birth_jd": [2400000.5, 2410000.5],
        })
        charts = pd.DataFrame({
            "person_id": ["P:A", "P:B"],
            "birth_jd_used": [2400000.5, 2410000.5],
            "moon_lon": [45.0, 200.0],
        })
        return persons, charts

    def test_two_persons_produce_162_rows(
        self, small_persons_and_charts: tuple[pd.DataFrame, pd.DataFrame]
    ):
        """2 persons * 81 windows = 162 rows."""
        persons, charts = small_persons_and_charts
        result = build_dasha_windows(persons, charts, workers=1)
        assert len(result) == 162

    def test_required_columns_present(
        self, small_persons_and_charts: tuple[pd.DataFrame, pd.DataFrame]
    ):
        """Schema contract: every column the Gold layer joins on must exist."""
        persons, charts = small_persons_and_charts
        result = build_dasha_windows(persons, charts, workers=1)
        for col in ("window_id", "person_id", "md_lord", "ad_lord",
                    "md_seq", "ad_seq", "start_jd", "end_jd", "duration_days"):
            assert col in result.columns
