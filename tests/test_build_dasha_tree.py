"""Tests for app/medini/etl/build_dasha_tree.py.

Pins the BPHS Ch.46-47 mutual-relation features against:
- Whole-sign distance is 1-indexed and 1=conjunction, 7=opposition
- Drishti aspect distances respect _DRISHTI_HOUSES per graha
- Dispositor lookup uses the canonical _SIGN_RULERSHIP
- Mutual reception (dispositor_md_is_ad) fires when AD lord rules MD lord's sign
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.etl.build_dasha_tree import build_dasha_tree


@pytest.fixture
def two_window_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    """A minimal dataset: 2 dasha windows, 1 person, 1 chart.

    Person has Moon in Virgo (sign 6, house 10). The two windows test:
      (a) Moon MD x Mercury AD: Mercury is Virgo's lord -> mutual reception
      (b) Moon MD x Jupiter AD: distance Virgo -> Capricorn is 5,
          Jupiter aspects 5/7/9 -> Jupiter aspect to Moon is 9 (back).
    """
    dasha_windows = pd.DataFrame({
        "window_id": ["P:1::A", "P:1::B"],
        "person_id": ["P:1", "P:1"],
        "md_lord": ["Moon", "Moon"],
        "ad_lord": ["Mercury", "Jupiter"],
        "md_seq": [0, 0],
        "ad_seq": [5, 3],
        "start_jd": [0.0, 0.0],
        "end_jd": [1.0, 1.0],
        "duration_days": [1.0, 1.0],
    })

    # One chart row: only the columns build_dasha_tree reads (planet houses + signs).
    charts = pd.DataFrame({
        "person_id": ["P:1"],
        "sun_house": [10], "sun_sign": [6],         # Sun in Virgo
        "moon_house": [10], "moon_sign": [6],       # Moon in Virgo
        "mars_house": [1], "mars_sign": [9],        # Mars in Sagittarius
        "mercury_house": [10], "mercury_sign": [6], # Mercury in Virgo (Moon's dispositor)
        "jupiter_house": [2], "jupiter_sign": [10], # Jupiter in Capricorn
        "venus_house": [11], "venus_sign": [7],
        "saturn_house": [9], "saturn_sign": [5],
        "rahu_house": [6], "rahu_sign": [2],
        "ketu_house": [12], "ketu_sign": [8],
    })
    return dasha_windows, charts


class TestLordPlacementLookup:
    """build_dasha_tree must look up MD/AD lord placements per row."""

    def test_md_lord_house_matches_chart(self, two_window_dataset):
        """Moon-MD row -> md_lord_house == chart.moon_house == 10."""
        dw, c = two_window_dataset
        tree = build_dasha_tree(dw, c)
        assert (tree["md_lord_house"] == 10).all()

    def test_ad_lord_house_differs_per_row(self, two_window_dataset):
        """Mercury AD -> ad_lord_house = 10. Jupiter AD -> ad_lord_house = 2."""
        dw, c = two_window_dataset
        tree = build_dasha_tree(dw, c)
        mercury_row = tree[tree["ad_lord"] == "Mercury"].iloc[0]
        jupiter_row = tree[tree["ad_lord"] == "Jupiter"].iloc[0]
        assert mercury_row["ad_lord_house"] == 10
        assert jupiter_row["ad_lord_house"] == 2


class TestMutualHouseDistance:
    """Whole-sign distance from MD-sign to AD-sign, 1-indexed."""

    def test_same_sign_is_distance_one(self, two_window_dataset):
        """Moon (Virgo=6) -> Mercury (Virgo=6): distance 1 (conjunction)."""
        dw, c = two_window_dataset
        tree = build_dasha_tree(dw, c)
        mercury_row = tree[tree["ad_lord"] == "Mercury"].iloc[0]
        assert mercury_row["mutual_house_distance"] == 1

    def test_virgo_to_capricorn_is_five(self, two_window_dataset):
        """Moon (Virgo=6) -> Jupiter (Capricorn=10): distance = (10-6)%12+1 = 5."""
        dw, c = two_window_dataset
        tree = build_dasha_tree(dw, c)
        jupiter_row = tree[tree["ad_lord"] == "Jupiter"].iloc[0]
        assert jupiter_row["mutual_house_distance"] == 5


class TestMutualAspect:
    """Drishti distances respect _DRISHTI_HOUSES."""

    def test_moon_to_mercury_no_aspect_at_distance_one(self, two_window_dataset):
        """Moon's drishti is {7}; distance=1 isn't in it -> no aspect."""
        dw, c = two_window_dataset
        tree = build_dasha_tree(dw, c)
        mercury_row = tree[tree["ad_lord"] == "Mercury"].iloc[0]
        assert mercury_row["mutual_aspect_md_to_ad"] == 0

    def test_jupiter_aspects_back_to_moon_at_nine(self, two_window_dataset):
        """Jupiter (Capricorn=10) aspects Moon (Virgo=6): distance back = (6-10)%12+1 = 9.

        Jupiter's drishti houses = {5, 7, 9}, so 9 is a hit and the aspect
        distance is 9 (a 9th-aspect).
        """
        dw, c = two_window_dataset
        tree = build_dasha_tree(dw, c)
        jupiter_row = tree[tree["ad_lord"] == "Jupiter"].iloc[0]
        assert jupiter_row["mutual_aspect_ad_to_md"] == 9


class TestDispositorReception:
    """dispositor_md_is_ad detects mutual reception."""

    def test_mercury_disposits_moon_in_virgo(self, two_window_dataset):
        """Moon in Virgo: Virgo's lord is Mercury. So Mercury disposits Moon.
        If AD lord IS Mercury, dispositor_md_is_ad must be True.
        """
        dw, c = two_window_dataset
        tree = build_dasha_tree(dw, c)
        mercury_row = tree[tree["ad_lord"] == "Mercury"].iloc[0]
        assert mercury_row["dispositor_md_is_ad"] is True or mercury_row["dispositor_md_is_ad"] == True

    def test_jupiter_does_not_disposit_moon(self, two_window_dataset):
        """Jupiter doesn't rule Virgo so Jupiter is NOT Moon's dispositor."""
        dw, c = two_window_dataset
        tree = build_dasha_tree(dw, c)
        jupiter_row = tree[tree["ad_lord"] == "Jupiter"].iloc[0]
        assert not jupiter_row["dispositor_md_is_ad"]


class TestSchemaContract:
    """Output schema must include every column downstream R-GCN consumes."""

    def test_required_columns_present(self, two_window_dataset):
        """Every documented column survives the build."""
        dw, c = two_window_dataset
        tree = build_dasha_tree(dw, c)
        required = {
            "window_id", "person_id", "md_lord", "ad_lord", "md_seq", "ad_seq",
            "md_lord_house", "md_lord_sign", "ad_lord_house", "ad_lord_sign",
            "mutual_house_distance",
            "mutual_aspect_md_to_ad", "mutual_aspect_ad_to_md",
            "md_dispositor", "ad_dispositor",
            "dispositor_md_is_ad", "dispositor_ad_is_md",
        }
        assert required.issubset(set(tree.columns))
