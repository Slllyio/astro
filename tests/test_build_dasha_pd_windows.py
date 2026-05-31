"""Tests for app/medini/etl/build_dasha_pd_windows.py.

Pins the Vimshottari PD-within-AD nesting:
- Each AD expands to exactly 9 PDs
- The PD sequence starts with the AD lord, then canonical Vimshottari order
- PD durations sum back to the parent AD duration (no rounding drift)
- 81 ADs × 9 PDs = 729 windows per person
"""
from __future__ import annotations

import math

import pandas as pd
import pytest

from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
from app.medini.etl.build_dasha_pd_windows import (
    _LORD_NAMES,
    _pratyantars_in_ad,
    build_pd_windows,
)


class TestPratyantarExpansion:
    """One AD expands into exactly 9 PDs starting with the AD lord."""

    def test_ad_expands_to_nine_pds(self):
        """Vimshottari rule: every AD has 9 sub-PDs."""
        pds = _pratyantars_in_ad("Saturn", ad_start_jd=0.0, ad_duration_years=1.0)
        assert len(pds) == 9

    def test_first_pd_is_ad_lord_itself(self):
        """PD sequence begins with the parent AD's lord."""
        pds = _pratyantars_in_ad("Jupiter", ad_start_jd=0.0, ad_duration_years=2.0)
        assert pds[0][0] == "Jupiter"

    def test_pd_durations_sum_to_ad_duration(self):
        """No rounding drift: 9 PD lengths must reconstruct the AD length."""
        ad_duration_years = 3.0
        pds = _pratyantars_in_ad("Venus", 0.0, ad_duration_years)
        total_days = pds[-1][2] - pds[0][1]
        expected_days = ad_duration_years * DAYS_PER_VEDIC_YEAR
        assert math.isclose(total_days, expected_days, rel_tol=1e-9)

    def test_consecutive_pds_have_no_gaps(self):
        """Each PD's end_jd must equal the next PD's start_jd exactly."""
        pds = _pratyantars_in_ad("Moon", ad_start_jd=2400000.0,
                                  ad_duration_years=0.83)
        for i in range(len(pds) - 1):
            assert pds[i][2] == pds[i + 1][1]

    def test_pd_lords_cycle_through_canonical_vimshottari_order(self):
        """Starting from AD lord, PDs follow (Ketu, Venus, Sun, ...) wrapping."""
        pds = _pratyantars_in_ad("Sun", 0.0, 0.3)
        lords = [pd[0] for pd in pds]
        # Sun is at index 2 in _LORD_NAMES. PDs should cycle from there.
        expected = [_LORD_NAMES[(2 + i) % 9] for i in range(9)]
        assert lords == expected


class TestBatchBuild:
    """build_pd_windows yields 9 PD rows per AD row."""

    @pytest.fixture
    def two_ad_windows(self) -> pd.DataFrame:
        """Minimal AD-window input — 2 rows for one person."""
        return pd.DataFrame({
            "window_id": ["X::A", "X::B"],
            "person_id": ["X", "X"],
            "md_lord": ["Jupiter", "Jupiter"],
            "ad_lord": ["Jupiter", "Venus"],
            "md_seq": [0, 0],
            "ad_seq": [0, 1],
            "start_jd": [2400000.0, 2400500.0],
            "end_jd": [2400500.0, 2401000.0],
            "duration_days": [500.0, 500.0],
        })

    def test_eighteen_pds_for_two_ads(self, two_ad_windows: pd.DataFrame):
        """2 AD rows × 9 PDs each = 18 rows."""
        result = build_pd_windows(two_ad_windows, workers=1)
        assert len(result) == 18

    def test_first_pd_of_jupiter_ad_is_jupiter(
        self, two_ad_windows: pd.DataFrame,
    ):
        """The first PD of a Jupiter AD is Jupiter PD."""
        result = build_pd_windows(two_ad_windows, workers=1)
        # The row where md_seq=0, ad_seq=0, pd_seq=0 belongs to Jupiter-AD.
        first_pd = result[
            (result["md_seq"] == 0) & (result["ad_seq"] == 0)
            & (result["pd_seq"] == 0)
        ].iloc[0]
        assert first_pd["pd_lord"] == "Jupiter"

    def test_required_columns_present(self, two_ad_windows: pd.DataFrame):
        """Schema contract for downstream PD consumers.

        ``pd_window_id`` was dropped in the 2026-05-31 storage refactor —
        the composite (person_id, md_seq, ad_seq, pd_seq) is the natural
        key and the string concatenation was 562 MB of dead weight in
        the produced parquet.
        """
        result = build_pd_windows(two_ad_windows, workers=1)
        required = {"person_id", "md_lord", "ad_lord",
                    "pd_lord", "md_seq", "ad_seq", "pd_seq",
                    "start_jd", "end_jd", "duration_days"}
        assert required.issubset(set(result.columns))
        assert "pd_window_id" not in result.columns, (
            "pd_window_id is a dropped derivable column; "
            "the natural key is (person_id, md_seq, ad_seq, pd_seq)"
        )

    def test_natural_key_is_unique(self, two_ad_windows: pd.DataFrame):
        """The composite (person_id, md_seq, ad_seq, pd_seq) uniquely identifies a PD window."""
        result = build_pd_windows(two_ad_windows, workers=1)
        natural_key = result[["person_id", "md_seq", "ad_seq", "pd_seq"]]
        assert natural_key.drop_duplicates().shape[0] == len(result), (
            "(person_id, md_seq, ad_seq, pd_seq) is not unique — schema invariant violated"
        )


class TestPDOfPD:
    """Recursive property — the AD-to-PD math is identical structurally
    to MD-to-AD; both follow the same Vimshottari nesting rule."""

    def test_jupiter_pd_in_jupiter_ad_in_jupiter_md_has_first_pd_jupiter(self):
        """If you start with Jupiter MD, Jupiter AD, the first PD is Jupiter."""
        pds = _pratyantars_in_ad("Jupiter", 0.0, ad_duration_years=2.13)
        # Jupiter PD = 2.13 * 16 / 120 ≈ 0.284 years
        assert pds[0][0] == "Jupiter"
        assert math.isclose(
            pds[0][2] - pds[0][1],
            (2.13 * 16 / 120) * DAYS_PER_VEDIC_YEAR,
            rel_tol=1e-9,
        )
