"""Tests for app.medini.ml.shap_rules.

Pure-function tests using synthetic SHAP arrays. No model training, no
parquet IO — these run in ~50ms even on cold CI.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from app.medini.ml.shap_rules import (
    Rule,
    _logit_to_probability_delta,
    extract_rules,
    rank_features_by_importance,
)


# ---------- _logit_to_probability_delta ----------

def test_logit_to_probability_delta_zero_shap_yields_zero_delta() -> None:
    assert _logit_to_probability_delta(0.0, base_rate=0.05) == pytest.approx(0.0, abs=1e-9)


def test_logit_to_probability_delta_positive_shap_increases_probability() -> None:
    delta = _logit_to_probability_delta(1.0, base_rate=0.05)
    assert delta > 0
    assert delta < 1.0  # bounded


def test_logit_to_probability_delta_negative_shap_decreases_probability() -> None:
    delta = _logit_to_probability_delta(-1.0, base_rate=0.5)
    assert delta < 0
    assert delta > -0.5  # can't go below the base rate


def test_logit_to_probability_delta_handles_extreme_base_rates() -> None:
    """At base_rate near 0, even huge SHAP values can't push probability much
    above the base rate. At 0.5, swings are largest."""
    delta_at_low_base = abs(_logit_to_probability_delta(2.0, base_rate=0.001))
    delta_at_mid_base = abs(_logit_to_probability_delta(2.0, base_rate=0.5))
    assert delta_at_mid_base > delta_at_low_base


# ---------- rank_features_by_importance ----------

def test_rank_features_by_importance_orders_by_mean_abs_shap() -> None:
    shap_values = np.array([
        [0.1, 1.5, -0.3],
        [0.2, -1.4, 0.4],
        [-0.1, 1.6, -0.2],
    ])
    feature_names = ["alpha", "beta", "gamma"]
    ranked = rank_features_by_importance(shap_values, feature_names)
    # beta has the largest mean |SHAP|, gamma next, alpha last.
    assert [name for name, _ in ranked] == ["beta", "gamma", "alpha"]
    assert ranked[0][1] == pytest.approx(1.5, abs=1e-9)


def test_rank_features_by_importance_validates_shape() -> None:
    with pytest.raises(ValueError, match="must be 2D"):
        rank_features_by_importance(np.array([0.1, 0.2]), ["a", "b"])
    with pytest.raises(ValueError, match="feature count mismatch"):
        rank_features_by_importance(np.array([[0.1, 0.2]]), ["a", "b", "c"])


# ---------- extract_rules ----------

def _build_synthetic_dataset(
    n_samples: int = 200,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Synthetic feature + SHAP arrays that ENCODE A KNOWN RULE.

    Construction:
      - feature_a: uniform 0..120. SHAP values are +1.0 when feature_a is in
        [60, 90], -1.0 otherwise. This is a clean threshold-shift the
        extractor MUST find at the magnitude filter > 5%.
      - feature_b: uniform 0..1, SHAP values random small noise. Should
        NOT yield any rule (no signal).
      - feature_c: uniform 0..1, SHAP values consistently zero. Should NOT
        yield any rule (zero variance in SHAP).
    """
    rng = np.random.default_rng(seed)
    feature_a = rng.uniform(0, 120, size=n_samples)
    shap_a = np.where((feature_a >= 60) & (feature_a < 90), 1.0, -1.0)

    feature_b = rng.uniform(0, 1, size=n_samples)
    shap_b = rng.normal(0, 0.05, size=n_samples)  # small random noise

    feature_c = rng.uniform(0, 1, size=n_samples)
    shap_c = np.zeros(n_samples)

    feature_matrix = np.column_stack([feature_a, feature_b, feature_c])
    shap_values = np.column_stack([shap_a, shap_b, shap_c])
    feature_names = ["feature_a", "feature_b", "feature_c"]
    return feature_matrix, shap_values, feature_names


def test_extract_rules_finds_known_threshold_rule() -> None:
    """The synthetic dataset has a clean +SHAP zone in [60, 90]; extractor
    must surface a rule covering that range."""
    feature_matrix, shap_values, feature_names = _build_synthetic_dataset()
    rules = extract_rules(
        feature_matrix=feature_matrix,
        shap_values=shap_values,
        feature_names=feature_names,
        base_rate=0.5,           # 50% so probability deltas are large
        top_n_features=3,
        min_rule_impact=0.05,
    )

    feature_a_rules = [r for r in rules if r.feature == "feature_a"]
    assert len(feature_a_rules) >= 1, "extractor missed the planted rule on feature_a"

    # At least one INCREASES rule should overlap [60, 90]
    increases = [r for r in feature_a_rules if r.direction == "INCREASES"]
    assert any(r.range_low <= 60 <= r.range_high or r.range_low <= 90 <= r.range_high
               or (60 <= r.range_low and r.range_high <= 90) for r in increases), (
        f"no INCREASES rule covers [60,90]; got ranges: "
        f"{[(r.range_low, r.range_high) for r in increases]}"
    )


def test_extract_rules_magnitude_filter_drops_noise() -> None:
    """feature_b has only random noise; no rule should pass the 5% filter."""
    feature_matrix, shap_values, feature_names = _build_synthetic_dataset()
    rules = extract_rules(
        feature_matrix=feature_matrix,
        shap_values=shap_values,
        feature_names=feature_names,
        base_rate=0.5,
        top_n_features=3,
        min_rule_impact=0.05,
    )
    # Noise feature should NOT generate any rules above the magnitude floor.
    noise_rules = [r for r in rules if r.feature == "feature_b"]
    assert noise_rules == [], (
        f"magnitude filter failed; noise feature yielded {noise_rules}"
    )


def test_extract_rules_skips_zero_variance_features() -> None:
    """feature_c has zero SHAP variance everywhere; should produce no rules."""
    feature_matrix, shap_values, feature_names = _build_synthetic_dataset()
    rules = extract_rules(
        feature_matrix=feature_matrix,
        shap_values=shap_values,
        feature_names=feature_names,
        base_rate=0.5,
        top_n_features=10,
        min_rule_impact=0.0,   # disable filter to verify the variance-skip works
    )
    feature_c_rules = [r for r in rules if r.feature == "feature_c"]
    # All-zero SHAP → all bucket means = 0 → no signed runs of nonzero sign.
    assert feature_c_rules == []


def test_extract_rules_sorts_by_impact_descending() -> None:
    """Rules must be ordered most-impactful first."""
    feature_matrix, shap_values, feature_names = _build_synthetic_dataset()
    rules = extract_rules(
        feature_matrix=feature_matrix,
        shap_values=shap_values,
        feature_names=feature_names,
        base_rate=0.5,
        top_n_features=3,
        min_rule_impact=0.05,
    )
    if len(rules) >= 2:
        impacts = [abs(r.probability_delta) for r in rules]
        assert impacts == sorted(impacts, reverse=True)


def test_extract_rules_validates_shape_mismatch() -> None:
    feature_matrix = np.zeros((5, 3))
    shap_values = np.zeros((5, 4))  # wrong number of columns
    with pytest.raises(ValueError, match="shape"):
        extract_rules(
            feature_matrix=feature_matrix,
            shap_values=shap_values,
            feature_names=["a", "b", "c", "d"],
            base_rate=0.1,
        )


def test_extract_rules_min_impact_zero_returns_all_signed_ranges() -> None:
    """With min_rule_impact=0 we get every signed run, regardless of magnitude."""
    feature_matrix, shap_values, feature_names = _build_synthetic_dataset()
    rules = extract_rules(
        feature_matrix=feature_matrix,
        shap_values=shap_values,
        feature_names=feature_names,
        base_rate=0.5,
        top_n_features=3,
        min_rule_impact=0.0,
    )
    # At least the planted feature_a rule should appear.
    assert any(r.feature == "feature_a" for r in rules)


def test_rule_as_text_is_human_readable() -> None:
    rule = Rule(
        feature="dist_jupiter_sun",
        range_low=117.3,
        range_high=124.8,
        direction="INCREASES",
        probability_delta=0.12,
        sample_count=487,
        feature_importance=0.45,
    )
    text = rule.as_text()
    assert "dist_jupiter_sun" in text
    assert "117.30" in text
    assert "124.80" in text
    assert "INCREASES" in text
    assert "+12.0%" in text
    assert "n=487" in text


def test_rule_as_text_signs_negative_delta() -> None:
    rule = Rule(
        feature="rx_saturn", range_low=0.5, range_high=1.0,
        direction="DECREASES", probability_delta=-0.08,
        sample_count=120, feature_importance=0.25,
    )
    text = rule.as_text()
    assert "-8.0%" in text
    assert "DECREASES" in text


def test_extract_rules_empty_input_returns_empty_list() -> None:
    rules = extract_rules(
        feature_matrix=np.zeros((0, 2)),
        shap_values=np.zeros((0, 2)),
        feature_names=["a", "b"],
        base_rate=0.1,
    )
    assert rules == []
