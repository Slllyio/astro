"""Tests for the Certified Cohort matched-pair engine's stateless logic."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tools.raman_saab.astrobank.certified_matched_pairs import (
    _SCORE,
    _match_pairs,
    _paired_stats,
    _score_frame,
)


class TestScoreFrame:
    def test_maps_verdicts_to_ordinal_and_drops_other_houses(self):
        """Only the requested (house, signification) rows are scored, via _SCORE."""
        v = pd.DataFrame([
            {"person_id": "a", "house": 7, "signification": "marital_happiness",
             "verdict": "afflicted", "degree": "strong"},
            {"person_id": "b", "house": 7, "signification": "marital_happiness",
             "verdict": "favourable", "degree": "strong"},
            {"person_id": "c", "house": 8, "signification": "death",
             "verdict": "afflicted", "degree": "strong"},
        ])
        s = _score_frame(v, 7, "marital_happiness")
        assert set(s.index) == {"a", "b"}          # house-8 row excluded
        assert s["a"] == _SCORE[("afflicted", "strong")] == 0.0
        assert s["b"] == _SCORE[("favourable", "strong")] == 2.0


class TestPairedStats:
    def _pairs(self, case_scores, control_scores):
        return pd.DataFrame({
            "case_score": case_scores, "control_score": control_scores,
            "case_id": range(len(case_scores)), "control_id": range(len(case_scores)),
        })

    def test_afflicted_direction_detects_more_afflicted_cases(self):
        """When cases are always more afflicted (lower score), paired AUC -> 1.0."""
        pairs = self._pairs([0.0] * 40, [2.0] * 40)   # case afflicted, control favourable
        out = _paired_stats(pairs, "afflicted", n_boot=200)
        assert out["paired_auc"] == 1.0
        assert out["signed_rank_p"] < 0.05
        assert out["ci95"][0] > 0.5

    def test_no_difference_is_null_half(self):
        """Identical within-pair scores give paired AUC 0.5 (all ties)."""
        pairs = self._pairs([1.0] * 30, [1.0] * 30)
        out = _paired_stats(pairs, "afflicted", n_boot=200)
        assert out["paired_auc"] == 0.5
        assert out["signed_rank_p"] is None       # <10 nonzero deltas -> undefined

    def test_direction_flip_inverts_concordance(self):
        """Reversing the pre-registered direction flips concordance about 0.5."""
        pairs = self._pairs([0.0] * 40, [2.0] * 40)
        aff = _paired_stats(pairs, "afflicted", n_boot=100)["paired_auc"]
        fav = _paired_stats(pairs, "favourable", n_boot=100)["paired_auc"]
        assert aff == pytest.approx(1.0)
        assert fav == pytest.approx(0.0)


class TestMatchPairs:
    def test_pairs_only_within_shared_strata(self):
        """A case matches only a control sharing (decade, lat_band, lon_band)."""
        cohort = pd.DataFrame([
            {"person_id": "case1", "is_case": True, "score": 0.0,
             "decade": 1950, "lat_band": 3, "lon_band": 2},
            {"person_id": "ctrlA", "is_case": False, "score": 2.0,
             "decade": 1950, "lat_band": 3, "lon_band": 2},   # same stratum -> matchable
            {"person_id": "ctrlB", "is_case": False, "score": 2.0,
             "decade": 1980, "lat_band": 1, "lon_band": 4},   # different stratum
        ])
        pairs = _match_pairs(cohort, seed=1)
        assert len(pairs) == 1
        assert pairs.iloc[0]["control_id"] == "ctrlA"

    def test_case_without_stratum_match_is_dropped(self):
        """A case with no same-stratum control produces no pair (reported as attrition)."""
        cohort = pd.DataFrame([
            {"person_id": "case1", "is_case": True, "score": 0.0,
             "decade": 1950, "lat_band": 3, "lon_band": 2},
            {"person_id": "ctrlB", "is_case": False, "score": 2.0,
             "decade": 1980, "lat_band": 1, "lon_band": 4},
        ])
        assert len(_match_pairs(cohort, seed=1)) == 0
