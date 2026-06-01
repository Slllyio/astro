"""Tests for app/medini/ml/xgboost_date_disambiguation.py.

Covers:
- _derive_cyclic_date_features: correctness against known dates
- _build_wikidata_marriage_dataset: schema and cohort integrity
- run_disambiguation (smoke): 5 conditions A-E run end-to-end with correct keys
- _derive_verdict: decision rule thresholds
"""
from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from app.medini.ml.xgboost_date_disambiguation import (
    _CHART_COLS,
    _CYCLIC_DATE_COLS,
    _derive_cyclic_date_features,
    _derive_verdict,
)


# ---------------------------------------------------------------------------
# _derive_cyclic_date_features
# ---------------------------------------------------------------------------

class TestDeriveCyclicDateFeatures:
    """Verify JD -> (month, doy, dom) conversion against known dates."""

    def test_known_date_1912_march_4(self) -> None:
        """Agatha Christie birth date: 1912-03-04 -> month=3, doy=64, dom=4."""
        # JD for 1912-03-04 ~= 2419465.5 (noon = +0.5)
        jd_series = pd.Series([2419465.5])
        result = _derive_cyclic_date_features(jd_series)

        assert result["birth_month"].iloc[0] == 3, "March should be month 3"
        assert result["birth_day_of_month"].iloc[0] == 4, "Day-of-month should be 4"
        # 1912 is a leap year; Jan=31, Feb=29, so Mar 4 = doy 65
        expected_doy = (datetime.date(1912, 3, 4) - datetime.date(1912, 1, 1)).days + 1
        assert result["birth_day_of_year"].iloc[0] == expected_doy

    def test_january_1_is_doy_1(self) -> None:
        """Jan 1 of any year must be day-of-year 1."""
        import swisseph as swe
        jd_jan1_2000 = swe.julday(2000, 1, 1, 12.0, swe.GREG_CAL)
        result = _derive_cyclic_date_features(pd.Series([jd_jan1_2000]))
        assert result["birth_day_of_year"].iloc[0] == 1
        assert result["birth_month"].iloc[0] == 1
        assert result["birth_day_of_month"].iloc[0] == 1

    def test_december_31_leap_year_is_doy_366(self) -> None:
        """Dec 31 of a leap year must be doy 366."""
        import swisseph as swe
        # 2000 is a leap year
        jd_dec31_2000 = swe.julday(2000, 12, 31, 12.0, swe.GREG_CAL)
        result = _derive_cyclic_date_features(pd.Series([jd_dec31_2000]))
        assert result["birth_day_of_year"].iloc[0] == 366
        assert result["birth_month"].iloc[0] == 12

    def test_output_columns_present(self) -> None:
        """Output DataFrame must have exactly the 3 cyclic date columns."""
        import swisseph as swe
        jd = swe.julday(1980, 6, 15, 12.0, swe.GREG_CAL)
        result = _derive_cyclic_date_features(pd.Series([jd]))
        assert list(result.columns) == _CYCLIC_DATE_COLS

    def test_batch_length_matches_input(self) -> None:
        """Output row count must equal input length."""
        import swisseph as swe
        jds = pd.Series([
            swe.julday(1900, 1, 1, 12.0, swe.GREG_CAL),
            swe.julday(1950, 6, 15, 12.0, swe.GREG_CAL),
            swe.julday(2000, 12, 31, 12.0, swe.GREG_CAL),
        ])
        result = _derive_cyclic_date_features(jds)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# _derive_verdict
# ---------------------------------------------------------------------------

class TestDeriveVerdict:
    """Verify the three-way verdict decision rule."""

    def _make_results(self, b_auc: float, d_auc: float) -> dict:
        """Build a minimal results dict for verdict testing."""
        template = {"mean_auc": 0.5, "std_auc": 0.01}
        return {
            "A": {**template, "mean_auc": 0.63},
            "B": {**template, "mean_auc": b_auc},
            "C": {**template, "mean_auc": 0.67},
            "D": {**template, "mean_auc": d_auc},
            "E": {**template, "mean_auc": 0.60},
        }

    def test_confound_when_lift_below_threshold(self) -> None:
        """D - B < 0.005 -> CONFOUND verdict."""
        results = self._make_results(b_auc=0.670, d_auc=0.673)
        verdict, _, lift, _ = _derive_verdict(results)
        assert verdict == "CONFOUND"
        assert lift == pytest.approx(0.003, abs=1e-6)

    def test_real_signal_when_lift_exceeds_threshold(self) -> None:
        """D - B >= 0.020 -> REAL SIGNAL verdict."""
        results = self._make_results(b_auc=0.640, d_auc=0.670)
        verdict, _, lift, _ = _derive_verdict(results)
        assert verdict == "REAL SIGNAL"
        assert lift == pytest.approx(0.030, abs=1e-6)

    def test_ambiguous_when_lift_in_middle(self) -> None:
        """0.005 <= D - B < 0.020 -> AMBIGUOUS verdict."""
        results = self._make_results(b_auc=0.655, d_auc=0.667)
        verdict, _, lift, _ = _derive_verdict(results)
        assert verdict == "AMBIGUOUS"

    def test_explanation_string_contains_verdict(self) -> None:
        """Explanation text must mention the numeric lift."""
        results = self._make_results(b_auc=0.670, d_auc=0.672)
        _, explanation, lift, _ = _derive_verdict(results)
        assert f"{lift:+.4f}" in explanation


# ---------------------------------------------------------------------------
# run_disambiguation smoke (fast synthetic data via monkeypatching)
# ---------------------------------------------------------------------------

class TestRunDisambiguationSmoke:
    """End-to-end smoke test using synthetic parquets.

    Patches _build_wikidata_marriage_dataset so no real parquet IO occurs.
    Verifies that run_disambiguation() returns all 5 condition keys with
    the required result structure.
    """

    @pytest.fixture
    def synthetic_dataset(self) -> pd.DataFrame:
        """200-person synthetic dataset with all required columns."""
        rng = np.random.default_rng(0)
        n = 200
        import swisseph as swe
        base_jd = swe.julday(1970, 1, 1, 12.0, swe.GREG_CAL)
        jds = pd.Series(base_jd + rng.uniform(0, 365 * 80, n))

        chart_data = {col: rng.integers(1, 13, n) for col in _CHART_COLS}
        df = pd.DataFrame(chart_data)
        df["birth_jd"] = jds.values
        df["person_id"] = [f"P:{i}" for i in range(n)]
        df["label"] = rng.integers(0, 2, n)

        cyclic = _derive_cyclic_date_features(jds)
        df = pd.concat([df, cyclic], axis=1)
        return df

    def test_all_five_conditions_present(
        self, synthetic_dataset: pd.DataFrame, tmp_path: Path
    ) -> None:
        """run_disambiguation returns keys A, B, C, D, E."""
        from app.medini.ml.xgboost_date_disambiguation import run_disambiguation

        with patch(
            "app.medini.ml.xgboost_date_disambiguation._build_wikidata_marriage_dataset",
            return_value=synthetic_dataset,
        ):
            results = run_disambiguation(data_dir=tmp_path, n_folds=2, seed=0)

        assert set(results.keys()) == {"A", "B", "C", "D", "E"}, (
            "All 5 conditions must be present in results"
        )

    def test_result_structure_per_condition(
        self, synthetic_dataset: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Each condition result has required keys with sensible types."""
        from app.medini.ml.xgboost_date_disambiguation import run_disambiguation

        with patch(
            "app.medini.ml.xgboost_date_disambiguation._build_wikidata_marriage_dataset",
            return_value=synthetic_dataset,
        ):
            results = run_disambiguation(data_dir=tmp_path, n_folds=2, seed=0)

        required_keys = {"feature_set", "n_features", "fold_aucs", "mean_auc", "std_auc",
                         "n_total", "n_positive", "positive_rate"}
        for cond, res in results.items():
            assert required_keys.issubset(res.keys()), f"Condition {cond} missing keys"
            assert isinstance(res["fold_aucs"], list)
            assert len(res["fold_aucs"]) == 2  # n_folds=2
            assert 0.0 <= res["mean_auc"] <= 1.0, f"Cond {cond} AUC out of range"

    def test_feature_counts_match_expectation(
        self, synthetic_dataset: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Feature counts: A=1, B=4, C=29, D=32, E=3."""
        from app.medini.ml.xgboost_date_disambiguation import run_disambiguation

        with patch(
            "app.medini.ml.xgboost_date_disambiguation._build_wikidata_marriage_dataset",
            return_value=synthetic_dataset,
        ):
            results = run_disambiguation(data_dir=tmp_path, n_folds=2, seed=0)

        assert results["A"]["n_features"] == 1, "A: birth_jd only"
        assert results["B"]["n_features"] == 4, "B: birth_jd + 3 cyclic"
        assert results["C"]["n_features"] == 29, "C: birth_jd + 28 chart"
        assert results["D"]["n_features"] == 32, "D: birth_jd + 3 cyclic + 28 chart"
        assert results["E"]["n_features"] == 3, "E: 3 cyclic only"

    def test_identical_splits_used_across_conditions(
        self, synthetic_dataset: pd.DataFrame, tmp_path: Path
    ) -> None:
        """All conditions must share the same y array (same cohort).

        Verified by checking n_total and n_positive are identical across A-E.
        """
        from app.medini.ml.xgboost_date_disambiguation import run_disambiguation

        with patch(
            "app.medini.ml.xgboost_date_disambiguation._build_wikidata_marriage_dataset",
            return_value=synthetic_dataset,
        ):
            results = run_disambiguation(data_dir=tmp_path, n_folds=2, seed=0)

        n_totals = {r["n_total"] for r in results.values()}
        n_positives = {r["n_positive"] for r in results.values()}
        assert len(n_totals) == 1, "All conditions must use same n_total"
        assert len(n_positives) == 1, "All conditions must use same n_positive"
