"""Native TreeSHAP — `app/medini/ml/tree_shap.py`.

Replaces `shap.TreeExplainer`, which raises on xgboost 3.x
(`ValueError: could not convert string to float: '[5E-1]'`) and took down the live
`/medini/predict` path. XGBoost computes the same values internally, so these tests pin the
two properties that make the swap safe: the contributions are EXACT (they reconstruct the
model's margin), and the bias column is stripped so every value still lines up with its
feature name.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xgboost as xgb

from app.medini.ml.tree_shap import tree_shap_values


@pytest.fixture(scope="module")
def fitted():
    rng = np.random.RandomState(0)
    X = pd.DataFrame(rng.rand(80, 4), columns=["a", "b", "c", "d"])
    y = ((X["a"] + X["b"]) > 1.0).astype(int)
    model = xgb.XGBClassifier(n_estimators=10, max_depth=3, enable_categorical=True,
                              tree_method="hist", verbosity=0).fit(X, y)
    return model, X


class TestExactness:
    def test_contributions_plus_bias_reconstruct_the_margin(self, fitted):
        """TreeSHAP's defining property. If this holds the values ARE the SHAP values —
        it is the check that makes dropping the shap library safe rather than approximate."""
        model, X = fitted
        booster = model.get_booster()
        dm = xgb.DMatrix(X, enable_categorical=True)
        raw = np.asarray(booster.predict(dm, pred_contribs=True))
        margin = np.asarray(booster.predict(dm, output_margin=True))
        np.testing.assert_allclose(raw.sum(axis=1), margin, rtol=1e-5, atol=1e-5)

    def test_helper_returns_one_column_per_feature(self, fitted):
        """The bias column must be stripped — leaving it in would shift every contribution
        one place against its feature name, silently mislabelling the whole explanation."""
        model, X = fitted
        sv = tree_shap_values(model, X)
        assert sv.shape == (len(X), X.shape[1])

    def test_helper_matches_the_raw_call_minus_bias(self, fitted):
        model, X = fitted
        raw = np.asarray(model.get_booster().predict(
            xgb.DMatrix(X, enable_categorical=True), pred_contribs=True))
        np.testing.assert_allclose(tree_shap_values(model, X), raw[:, :-1], rtol=1e-6)


class TestContract:
    def test_single_row_works(self, fitted):
        """predict_for_chart always passes exactly one chart."""
        model, X = fitted
        assert tree_shap_values(model, X.iloc[:1]).shape == (1, X.shape[1])

    def test_accepts_categorical_features(self):
        """The trainer sets enable_categorical=True, so the feature frame carries pandas
        Categorical columns; a DMatrix built without that flag rejects them outright."""
        rng = np.random.RandomState(1)
        X = pd.DataFrame({"num": rng.rand(60),
                          "cat": pd.Categorical(rng.choice(list("xyz"), 60))})
        y = (X["num"] > 0.5).astype(int)
        model = xgb.XGBClassifier(n_estimators=8, max_depth=3, enable_categorical=True,
                                  tree_method="hist", verbosity=0).fit(X, y)
        sv = tree_shap_values(model, X)
        assert sv.shape == (60, 2)
        assert np.isfinite(sv).all()

    def test_accepts_a_raw_booster_too(self, fitted):
        """`model` may be an XGBClassifier or an already-unwrapped Booster."""
        model, X = fitted
        np.testing.assert_allclose(tree_shap_values(model.get_booster(), X),
                                   tree_shap_values(model, X), rtol=1e-6)


class TestDownstreamCompatibility:
    def test_output_feeds_rank_features_by_importance_unchanged(self, fitted):
        """shap_rules is pure numpy over a (n, n_features) array and must need no change."""
        from app.medini.ml.shap_rules import rank_features_by_importance

        model, X = fitted
        ranked = rank_features_by_importance(tree_shap_values(model, X), list(X.columns))
        assert len(ranked) == X.shape[1]
        # 'a' and 'b' drive the label; they must outrank the noise features.
        top2 = {name for name, _ in ranked[:2]}
        assert top2 == {"a", "b"}
