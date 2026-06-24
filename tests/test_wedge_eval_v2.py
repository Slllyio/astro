"""Tests for the Phase-3C wedge eval gate logic + dual-schema helpers.

Heavyweight pieces (XGBoost fits, bootstrap loops) are exercised only
through tiny synthetic data; the focus here is on the deterministic
helpers that carry decision-weight: schema resolution, column
filtering, and the gate classifier.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from app.medini.ml import wedge_eval_v2 as wev2


# --------------------------------------------------------------------------- #
# Schema-resolution helpers                                                   #
# --------------------------------------------------------------------------- #

def test_resolve_columns_screening_schema() -> None:
    df = pd.DataFrame({
        "is_event_X": [0, 1],
        "name_norm": ["a", "b"],
    })
    target, group = wev2._resolve_columns(df)
    assert target == "is_event_X"
    assert group == "name_norm"


def test_resolve_columns_event_corpus_schema() -> None:
    df = pd.DataFrame({
        "is_event": [0, 1],
        "name": ["x", "y"],
    })
    target, group = wev2._resolve_columns(df)
    assert target == "is_event"
    assert group == "name"


def test_resolve_columns_prefers_normalised_when_both_present() -> None:
    df = pd.DataFrame({
        "is_event_X": [0, 1],
        "is_event": [0, 1],
        "name_norm": ["a", "b"],
        "name": ["a", "b"],
    })
    target, group = wev2._resolve_columns(df)
    assert target == "is_event_X"
    assert group == "name_norm"


def test_resolve_columns_raises_when_target_missing() -> None:
    df = pd.DataFrame({"name": ["a"]})
    with pytest.raises(KeyError):
        wev2._resolve_columns(df)


def test_resolve_columns_raises_when_group_missing() -> None:
    df = pd.DataFrame({"is_event": [0, 1]})
    with pytest.raises(KeyError):
        wev2._resolve_columns(df)


# --------------------------------------------------------------------------- #
# Yoga column detection                                                       #
# --------------------------------------------------------------------------- #

def test_yoga_columns_in_only_picks_known_slugs() -> None:
    df = pd.DataFrame({
        "vipareeta_harsha_natal_strength": [0.0],
        "vipareeta_harsha_dasha_gated_strength": [0.0],
        "raja_yoga_natal_strength": [0.0],
        "some_other_column": [0.0],
    })
    cols = wev2._yoga_columns_in(df)
    assert "vipareeta_harsha_natal_strength" in cols
    assert "vipareeta_harsha_dasha_gated_strength" in cols
    assert "raja_yoga_natal_strength" in cols
    assert "some_other_column" not in cols


def test_yoga_columns_in_returns_empty_on_baseline() -> None:
    df = pd.DataFrame({"lon_sun": [10.0], "lagna_sign": [1]})
    assert wev2._yoga_columns_in(df) == ()


# --------------------------------------------------------------------------- #
# Coerce features                                                             #
# --------------------------------------------------------------------------- #

def test_coerce_features_drops_non_feature_columns() -> None:
    df = pd.DataFrame({
        "is_event_X": [0, 1],
        "name_norm": ["a", "b"],
        "birth_decade": [1980, 1990],
        "active_md_lord": ["Mercury", "Mars"],
        "lon_sun": [10.0, 20.0],
    })
    coerced = wev2._coerce_features(df)
    assert "is_event_X" not in coerced.columns
    assert "name_norm" not in coerced.columns
    assert "birth_decade" not in coerced.columns
    assert "active_md_lord" not in coerced.columns
    assert "lon_sun" in coerced.columns


def test_coerce_features_casts_objects_to_category() -> None:
    df = pd.DataFrame({
        "is_event_X": [0, 1],
        "name_norm": ["a", "b"],
        "some_categorical": ["yes", "no"],
        "some_numeric": [1.0, 2.0],
    })
    coerced = wev2._coerce_features(df)
    assert isinstance(coerced["some_categorical"].dtype, pd.CategoricalDtype)
    assert pd.api.types.is_numeric_dtype(coerced["some_numeric"])


# --------------------------------------------------------------------------- #
# Gate classifier — synthetic noise + wedge + per-yoga bundles                 #
# --------------------------------------------------------------------------- #

def _make_noise(delta_std: float, delta_mean: float = 0.0) -> dict:
    return {
        "n_seeds": 20, "test_size": 0.20,
        "base_auc_mean": 0.61, "noise_auc_mean": 0.61,
        "delta_mean": delta_mean, "delta_std": delta_std,
        "deltas": [delta_mean] * 20,
    }


def _make_wedge(
    delta_mean: float, sigma_model: float, n_yogas_top50: int,
) -> dict:
    median_rank = {
        slug + "_natal_strength":
            (5 if i < n_yogas_top50 else 200)
        for i, slug in enumerate(wev2._YOGA_SLUGS)
    }
    return {
        "n_seeds": 10, "test_size": 0.20,
        "yoga_columns": list(median_rank),
        "base_auc_mean": 0.61, "wedge_auc_mean": 0.61 + delta_mean,
        "wedge_auc_std": sigma_model,
        "delta_mean": delta_mean, "delta_std": 0.005,
        "deltas": [delta_mean] * 10,
        "mean_gain_per_yoga": {c: 1.0 for c in median_rank},
        "median_rank_per_yoga": median_rank,
    }


def _make_per_yoga(n_passes: int) -> dict:
    out: dict = {}
    for i, slug in enumerate(wev2._YOGA_SLUGS):
        col = slug + "_natal_strength"
        if i < n_passes:
            out[col] = {"marginal_auc": 0.01, "ci_lo": 0.005,
                        "ci_hi": 0.02, "ci_passes": 1}
        else:
            out[col] = {"marginal_auc": 0.001, "ci_lo": -0.01,
                        "ci_hi": 0.01, "ci_passes": 0}
    return out


def test_gate_strong_pass_clears_all_criteria() -> None:
    """Δ_mean ≥ 6σ_noise + lots of per-yoga signal + many top-50."""
    noise = _make_noise(delta_std=0.005)
    wedge = _make_wedge(delta_mean=0.05, sigma_model=0.01, n_yogas_top50=10)
    per_yoga = _make_per_yoga(n_passes=8)

    result = wev2._classify_gate(noise, wedge, per_yoga)
    assert result.criterion_a is True
    assert result.criterion_b is True
    assert result.criterion_c is True
    assert result.overall_pass is True
    assert result.pass_strong is True
    assert result.needs_replication is False


def test_gate_weak_pass_triggers_replication_clause() -> None:
    """Margin between 1.0× and 1.5× — should fire replication."""
    noise = _make_noise(delta_std=0.005)
    # 3σ_noise = 0.015; setting Δ=0.018 → margin 1.2× (in [1.0, 1.5)).
    wedge = _make_wedge(delta_mean=0.018, sigma_model=0.01, n_yogas_top50=6)
    per_yoga = _make_per_yoga(n_passes=0)  # disable per-yoga route

    result = wev2._classify_gate(noise, wedge, per_yoga)
    assert result.criterion_a is True
    assert result.overall_pass is True
    assert result.pass_strong is False
    assert result.needs_replication is True


def test_gate_fails_criterion_a_cumulative_and_per_yoga() -> None:
    """Δ_mean well under 3σ + no per-yoga CI > 0 → criterion A fails."""
    noise = _make_noise(delta_std=0.01)  # 3σ = 0.03
    wedge = _make_wedge(delta_mean=0.005, sigma_model=0.01, n_yogas_top50=6)
    per_yoga = _make_per_yoga(n_passes=0)

    result = wev2._classify_gate(noise, wedge, per_yoga)
    assert result.criterion_a is False
    assert result.overall_pass is False


def test_gate_fails_criterion_b_when_model_unstable() -> None:
    """σ_model > Δ_mean → criterion B fails even if A and C pass."""
    noise = _make_noise(delta_std=0.001)  # cumulative criterion A easily passes
    wedge = _make_wedge(delta_mean=0.02, sigma_model=0.05, n_yogas_top50=10)
    per_yoga = _make_per_yoga(n_passes=8)

    result = wev2._classify_gate(noise, wedge, per_yoga)
    assert result.criterion_a is True
    assert result.criterion_b is False
    assert result.overall_pass is False


def test_gate_fails_criterion_c_when_few_yogas_in_top50() -> None:
    """A and B pass but only 2 yogas in top-50 → criterion C fails."""
    noise = _make_noise(delta_std=0.001)
    wedge = _make_wedge(delta_mean=0.02, sigma_model=0.01, n_yogas_top50=2)
    per_yoga = _make_per_yoga(n_passes=8)

    result = wev2._classify_gate(noise, wedge, per_yoga)
    assert result.criterion_c is False
    assert result.overall_pass is False


def test_gate_per_yoga_route_alone_can_satisfy_criterion_a() -> None:
    """Δ_mean < 3σ but 3+ per-yoga CI > 0 → criterion A passes via per-yoga route."""
    noise = _make_noise(delta_std=0.01)  # 3σ = 0.03
    wedge = _make_wedge(delta_mean=0.01, sigma_model=0.005, n_yogas_top50=8)
    per_yoga = _make_per_yoga(n_passes=4)  # 4 CI passes >= 3

    result = wev2._classify_gate(noise, wedge, per_yoga)
    assert result.criterion_a is True
    # n_yoga_ci_passes / 3 = 4/3 = 1.33 → < 1.5 → needs replication
    assert result.needs_replication is True


# --------------------------------------------------------------------------- #
# Bootstrap CI                                                                 #
# --------------------------------------------------------------------------- #

def test_bootstrap_ci_returns_valid_interval() -> None:
    """Probabilities that clearly outperform baseline → CI should be > 0."""
    rng = np.random.default_rng(0)
    y_true = np.concatenate([np.zeros(50, dtype=int), np.ones(50, dtype=int)])
    # baseline = random (~0.5 AUC); model = perfect discrimination
    proba_base = rng.uniform(0.0, 1.0, size=100)
    proba_model = np.concatenate([np.linspace(0.0, 0.4, 50),
                                  np.linspace(0.6, 1.0, 50)])

    lo, hi = wev2._bootstrap_auc_ci(
        y_true, proba_base, proba_model, n_resamples=200, ci=0.95, rng=rng,
    )
    assert lo > 0.0
    assert hi > lo
    assert hi <= 1.0


def test_bootstrap_ci_returns_zero_interval_when_models_identical() -> None:
    """Two identical predictors → CI lo and hi both ≈ 0."""
    rng = np.random.default_rng(0)
    y_true = np.concatenate([np.zeros(50, dtype=int), np.ones(50, dtype=int)])
    proba = rng.uniform(0.0, 1.0, size=100)

    lo, hi = wev2._bootstrap_auc_ci(
        y_true, proba, proba.copy(), n_resamples=200, ci=0.95, rng=rng,
    )
    assert math.isclose(lo, 0.0, abs_tol=1e-9)
    assert math.isclose(hi, 0.0, abs_tol=1e-9)


# --------------------------------------------------------------------------- #
# Yoga slugs lockstep with ETL                                                #
# --------------------------------------------------------------------------- #

def test_yoga_slugs_match_etl_specs() -> None:
    """If the ETL ships new yoga slugs, the eval must learn them too."""
    from app.medini.etl.add_yoga_features import _YOGA_SPECS
    etl_slugs = tuple(s.slug for s in _YOGA_SPECS)
    assert wev2._YOGA_SLUGS == etl_slugs
