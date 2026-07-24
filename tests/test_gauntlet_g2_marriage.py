"""Tests for the stateless statistics helpers in gauntlet_g2_marriage."""
from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

from app.medini.ml.gauntlet_g2_marriage import _bootstrap_lift, _fast_auc


class TestFastAuc:
    def test_matches_sklearn_on_random_scores(self):
        """Rank-based AUC equals sklearn's roc_auc_score on continuous scores."""
        rng = np.random.default_rng(7)
        y = (rng.random(500) < 0.3).astype(int)
        s = rng.normal(size=500)
        assert _fast_auc(y, s) == pytest.approx(roc_auc_score(y, s), abs=1e-12)

    def test_matches_sklearn_with_heavy_ties(self):
        """Midrank handling reproduces sklearn under massive score ties."""
        rng = np.random.default_rng(11)
        y = (rng.random(800) < 0.4).astype(int)
        s = rng.integers(0, 5, 800).astype(float)  # only 5 distinct scores
        assert _fast_auc(y, s) == pytest.approx(roc_auc_score(y, s), abs=1e-12)

    def test_perfect_separation_is_one(self):
        """Scores that perfectly rank positives above negatives give AUC 1.0."""
        y = np.array([0, 0, 1, 1])
        s = np.array([0.1, 0.2, 0.8, 0.9])
        assert _fast_auc(y, s) == 1.0


class TestBootstrapLift:
    def test_ci_brackets_true_difference(self):
        """Bootstrap CI on AUC(a)-AUC(b) contains the point estimate."""
        rng = np.random.default_rng(3)
        y = (rng.random(600) < 0.3).astype(int)
        s_b = rng.normal(size=600)
        s_a = y * 1.0 + rng.normal(scale=1.0, size=600)  # informative arm
        point = roc_auc_score(y, s_a) - roc_auc_score(y, s_b)
        _, lo, hi = _bootstrap_lift(y, s_a, s_b, n_boot=400, seed=0)
        assert lo < point < hi
        assert lo > 0  # genuinely informative arm must exclude zero here

    def test_null_difference_ci_contains_zero(self):
        """Two equally uninformative arms yield a CI straddling zero."""
        rng = np.random.default_rng(5)
        y = (rng.random(600) < 0.5).astype(int)
        s_a, s_b = rng.normal(size=600), rng.normal(size=600)
        _, lo, hi = _bootstrap_lift(y, s_a, s_b, n_boot=400, seed=1)
        assert lo < 0 < hi
