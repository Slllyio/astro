"""Tests for the four doctrine-scorer variants used in Round-11.

Covers:
- dasha_doctrine_structural.doctrine_relevance_structural — karaka-stripped scorer
- dasha_doctrine_ad_timing.ad_mutual_score — BPHS Ch.46-47 mutual-relation score
- dasha_doctrine_ad_timing.ad_mutual_score_vec — vectorised counterpart
- dasha_doctrine_personal_disambiguation._shuffle_natal_charts — permutation primitive
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.medini.ml.dasha_doctrine_ad_timing import (
    _DUSTHANA_DISTANCES, _TRIKONA_DISTANCES,
    ad_mutual_score, ad_mutual_score_vec,
)
from app.medini.ml.dasha_doctrine_personal_disambiguation import (
    _shuffle_natal_charts,
)
from app.medini.ml.dasha_doctrine_structural import (
    doctrine_relevance_structural,
)


# --------------------------------------------------------------------------- #
# doctrine_relevance_structural (karaka stripped)                              #
# --------------------------------------------------------------------------- #


class TestStructuralScorer:
    """The karaka-stripped relevance scorer (HR + func_mod only)."""

    @pytest.fixture
    def chart(self) -> dict:
        """Synthetic natal-lord-houses row. Saturn rules dusthana (6, 8) =>
        functional malefic; Jupiter rules trikona (1, 5) => trikona lord."""
        return {
            # Saturn: rules 6 (dusthana), 8 (dusthana); occupies house 8
            "rules_saturn": [6, 8],
            "occ_saturn": 8,
            "aspects_saturn": [],
            "sign_saturn": 8,
            # Jupiter: rules 1 (kendra+trikona), 5 (trikona); occupies house 5
            "rules_jupiter": [1, 5],
            "occ_jupiter": 5,
            "aspects_jupiter": [1, 7],
            "sign_jupiter": 5,
            # Mercury: rules 3 (no special), occupies house 10
            "rules_mercury": [3],
            "occ_mercury": 10,
            "aspects_mercury": [4],
            "sign_mercury": 3,
        }

    def test_karaka_strip_removes_chart_independent_baseline(self, chart):
        """For event_class with karaka=Moon, scoring on Saturn shouldn't
        get the +1.0 karaka boost regardless of chart."""
        # 'personal' has _KARAKA_MAP = {"Moon": 1.0}. A non-Moon lord
        # should get 0 from karaka; the structural variant strips this.
        from app.medini.ml.dasha_doctrine_score import doctrine_relevance
        original_jupiter = doctrine_relevance("Jupiter", "personal", chart)
        structural_jupiter = doctrine_relevance_structural(
            "Jupiter", "personal", chart,
        )
        # Jupiter isn't karaka for personal, so original and structural agree.
        assert original_jupiter == structural_jupiter

    def test_karaka_strip_actually_strips_moon(self, chart):
        """For lord==karaka, structural < original by exactly the karaka weight."""
        # Add Moon to the chart fixture so the function doesn't crash on lookups
        chart["rules_moon"] = [4]
        chart["occ_moon"] = 4
        chart["aspects_moon"] = []
        chart["sign_moon"] = 4
        from app.medini.ml.dasha_doctrine_score import (
            _KARAKA_MAP, doctrine_relevance,
        )
        original_moon = doctrine_relevance("Moon", "personal", chart)
        structural_moon = doctrine_relevance_structural(
            "Moon", "personal", chart,
        )
        kr_weight = _KARAKA_MAP["personal"]["Moon"]
        assert pytest.approx(original_moon - structural_moon, abs=1e-9) == kr_weight

    def test_house_resonance_present_in_structural(self, chart):
        """HR(L, E) is the chart-dependent component; should be nonzero
        when the lord has a non-empty house relation to the event class."""
        # Saturn rules house 8 (career has weight 0 in house 8), but
        # 'death' event class has _HOUSE_MAP[8]=1.0 weight on house 8.
        # So death-relevance for Saturn should be > 0.
        score = doctrine_relevance_structural("Saturn", "death", chart)
        assert score > 0


# --------------------------------------------------------------------------- #
# ad_mutual_score (BPHS Ch.46-47)                                              #
# --------------------------------------------------------------------------- #


class TestAdMutualScore:
    """Per-row mutual-relation score (no chart-structural HR)."""

    def test_no_aspects_no_dispositors_returns_zero(self):
        """All-zero mutual relations => zero score."""
        row = pd.Series({
            "mutual_aspect_md_to_ad": 0,
            "mutual_aspect_ad_to_md": 0,
            "dispositor_md_is_ad": False,
            "dispositor_ad_is_md": False,
            "mutual_house_distance": 4,  # not trikona, not dusthana
        })
        assert ad_mutual_score(row) == 0.0

    def test_mutual_aspect_adds_one_each_direction(self):
        """Each direction of mutual aspect contributes +1.0."""
        row = pd.Series({
            "mutual_aspect_md_to_ad": 7,
            "mutual_aspect_ad_to_md": 5,
            "dispositor_md_is_ad": False,
            "dispositor_ad_is_md": False,
            "mutual_house_distance": 4,
        })
        assert ad_mutual_score(row) == 2.0

    def test_mutual_dispositor_adds_one_each_direction(self):
        """Each direction of dispositor match contributes +1.0."""
        row = pd.Series({
            "mutual_aspect_md_to_ad": 0,
            "mutual_aspect_ad_to_md": 0,
            "dispositor_md_is_ad": True,
            "dispositor_ad_is_md": True,
            "mutual_house_distance": 4,
        })
        assert ad_mutual_score(row) == 2.0

    @pytest.mark.parametrize("dist", sorted(_TRIKONA_DISTANCES))
    def test_trikona_distance_adds_half(self, dist):
        """Trikona distances {1,5,9} contribute +0.5."""
        row = pd.Series({
            "mutual_aspect_md_to_ad": 0,
            "mutual_aspect_ad_to_md": 0,
            "dispositor_md_is_ad": False,
            "dispositor_ad_is_md": False,
            "mutual_house_distance": dist,
        })
        assert ad_mutual_score(row) == 0.5

    @pytest.mark.parametrize("dist", sorted(_DUSTHANA_DISTANCES))
    def test_dusthana_distance_subtracts_half(self, dist):
        """Dusthana distances {6,8,12} contribute -0.5."""
        row = pd.Series({
            "mutual_aspect_md_to_ad": 0,
            "mutual_aspect_ad_to_md": 0,
            "dispositor_md_is_ad": False,
            "dispositor_ad_is_md": False,
            "mutual_house_distance": dist,
        })
        assert ad_mutual_score(row) == -0.5

    def test_max_score_when_all_positive_features_fire(self):
        """Max possible: 1+1+1+1+0.5 = 4.5 (with trikona distance)."""
        row = pd.Series({
            "mutual_aspect_md_to_ad": 7,
            "mutual_aspect_ad_to_md": 5,
            "dispositor_md_is_ad": True,
            "dispositor_ad_is_md": True,
            "mutual_house_distance": 5,  # trikona
        })
        assert ad_mutual_score(row) == 4.5


class TestAdMutualScoreVec:
    """The vectorised version produces row-identical results."""

    def test_vec_matches_per_row(self):
        """Vectorised output must equal the row-by-row output for the same rows."""
        rows_df = pd.DataFrame([
            {"mutual_aspect_md_to_ad": 7, "mutual_aspect_ad_to_md": 0,
             "dispositor_md_is_ad": False, "dispositor_ad_is_md": False,
             "mutual_house_distance": 1},  # trikona, 1 aspect
            {"mutual_aspect_md_to_ad": 0, "mutual_aspect_ad_to_md": 0,
             "dispositor_md_is_ad": True, "dispositor_ad_is_md": False,
             "mutual_house_distance": 8},  # dusthana, 1 dispositor
            {"mutual_aspect_md_to_ad": 5, "mutual_aspect_ad_to_md": 9,
             "dispositor_md_is_ad": True, "dispositor_ad_is_md": True,
             "mutual_house_distance": 5},  # all positive
        ])
        vec = ad_mutual_score_vec(rows_df).tolist()
        per_row = [ad_mutual_score(rows_df.iloc[i]) for i in range(3)]
        assert vec == per_row


# --------------------------------------------------------------------------- #
# Permutation primitive (_shuffle_natal_charts)                                #
# --------------------------------------------------------------------------- #


class TestShuffleNatalCharts:
    """The chart-permutation primitive used by the K=100 falsifier."""

    @pytest.fixture
    def natal(self) -> pd.DataFrame:
        return pd.DataFrame({
            "name_norm": ["a", "b", "c", "d"],
            "sign_sun": [1, 4, 7, 10],
            "sign_moon": [2, 5, 8, 11],
            "rules_sun": [[1], [4], [7], [10]],
        })

    def test_shuffle_preserves_name_norm_order(self, natal):
        """name_norm is the lookup key — must NOT be shuffled."""
        out = _shuffle_natal_charts(natal, seed=42)
        assert out["name_norm"].tolist() == ["a", "b", "c", "d"]

    def test_shuffle_preserves_feature_marginal(self, natal):
        """sum / value-counts of each feature column must be invariant
        under permutation (only assignment to names changes)."""
        out = _shuffle_natal_charts(natal, seed=42)
        for col in ("sign_sun", "sign_moon"):
            assert sorted(out[col].tolist()) == sorted(natal[col].tolist())

    def test_shuffle_deterministic_with_seed(self, natal):
        """Same seed → identical output. Different seed → different output."""
        a = _shuffle_natal_charts(natal, seed=42)
        b = _shuffle_natal_charts(natal, seed=42)
        c = _shuffle_natal_charts(natal, seed=43)
        pd.testing.assert_frame_equal(a, b)
        # c is almost certainly different from a; check at least one column.
        # (For n=4 there's a 1/24 chance of identity per column; vanishingly
        # small that both columns coincide.)
        assert not (a["sign_sun"].equals(c["sign_sun"])
                    and a["sign_moon"].equals(c["sign_moon"]))
