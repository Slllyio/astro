"""SHAP-derived astrological rule extraction.

Takes raw SHAP values + feature values + feature names and emits
human-readable rules in the form:

    "WHEN <feature> IN [<low>, <high>] THEN probability shifts by <delta>"

Method (per the locked plan):
  1. Identify the top-N features by mean |SHAP| magnitude.
  2. For each top feature, scan its (value, shap_value) pairs to find
     contiguous ranges where the SHAP contribution is consistently
     positive or consistently negative.
  3. Compute the *mean SHAP shift* in each such range. Convert SHAP
     log-odds to a probability delta via the sigmoid difference at
     the base rate.
  4. Filter: discard rules whose absolute probability delta is below
     the magnitude threshold (default 0.05 = 5%).
  5. Sort by absolute probability impact, descending.

Pure functions; no IO; no model dependency. Tests feed synthetic SHAP
arrays directly without needing a real XGBoost model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class Rule:
    """One human-readable astrological rule discovered by SHAP analysis."""
    feature: str                # e.g. "dist_jupiter_sun"
    range_low: float            # lower bound of the value range
    range_high: float           # upper bound (inclusive)
    direction: str              # "INCREASES" or "DECREASES"
    probability_delta: float    # +/- probability shift (e.g. +0.12 = +12%)
    sample_count: int           # how many training rows fall in this range
    feature_importance: float   # mean |SHAP| for this feature (rank signal)

    def as_text(self) -> str:
        """Human-readable rule in the canonical format."""
        sign = "+" if self.probability_delta >= 0 else ""
        pct = self.probability_delta * 100.0
        return (
            f"WHEN {self.feature} IN [{self.range_low:.2f}, {self.range_high:.2f}] "
            f"THEN probability {self.direction} by {sign}{pct:.1f}% "
            f"(n={self.sample_count})"
        )


def _logit_to_probability_delta(shap_value: float, base_rate: float) -> float:
    """Convert a SHAP log-odds value to a probability delta at a base rate.

    SHAP values for binary classifiers are log-odds contributions. To turn
    one into a "% change in predicted probability," apply the sigmoid
    difference between (base_logit + shap_value) and base_logit.

    base_rate is the marginal positive-class rate (a value in (0, 1));
    base_logit = log(p / (1 - p)).
    """
    base_rate = max(min(base_rate, 1 - 1e-9), 1e-9)  # clamp away from 0/1
    base_logit = np.log(base_rate / (1.0 - base_rate))
    new_logit = base_logit + shap_value
    new_prob = 1.0 / (1.0 + np.exp(-new_logit))
    return float(new_prob - base_rate)


def rank_features_by_importance(
    shap_values: np.ndarray,
    feature_names: Sequence[str],
) -> list[tuple[str, float]]:
    """Sort features by mean |SHAP| descending. Returns (feature, importance)."""
    if shap_values.ndim != 2:
        raise ValueError(f"shap_values must be 2D, got shape {shap_values.shape}")
    if shap_values.shape[1] != len(feature_names):
        raise ValueError(
            f"feature count mismatch: shap_values has {shap_values.shape[1]} "
            f"columns, feature_names has {len(feature_names)}"
        )
    importances = np.abs(shap_values).mean(axis=0)
    indexed = list(zip(feature_names, importances.tolist(), strict=True))
    return sorted(indexed, key=lambda x: x[1], reverse=True)


def _find_signed_ranges(
    feature_values: np.ndarray,
    shap_for_feature: np.ndarray,
    n_bins: int = 10,
) -> list[tuple[float, float, float, int]]:
    """Bucket feature values, compute mean SHAP per bucket, and yield contiguous
    same-sign ranges as (low, high, mean_shap, sample_count) tuples.

    Pre-bucketing prevents per-row noise from creating spurious tiny rules
    while still revealing the threshold structure SHAP dependence plots show.
    """
    if len(feature_values) == 0:
        return []

    # Edges include both extremes; np.histogram_bin_edges returns n_bins+1 edges
    bin_edges = np.histogram_bin_edges(feature_values, bins=n_bins)
    bucket_indices = np.clip(
        np.digitize(feature_values, bin_edges) - 1,
        0,
        n_bins - 1,
    )

    ranges: list[tuple[float, float, float, int]] = []
    current_sign: int = 0
    current_lo_idx: int = 0
    current_shap_sum = 0.0
    current_count = 0

    for i in range(n_bins):
        mask = bucket_indices == i
        n = int(mask.sum())
        if n == 0:
            # Empty bucket; close any open run and reset
            if current_count > 0:
                lo = float(bin_edges[current_lo_idx])
                hi = float(bin_edges[i])
                mean_shap = current_shap_sum / current_count
                ranges.append((lo, hi, mean_shap, current_count))
            current_sign = 0
            current_count = 0
            current_shap_sum = 0.0
            continue

        bucket_mean = float(shap_for_feature[mask].mean())
        sign = 1 if bucket_mean > 0 else (-1 if bucket_mean < 0 else 0)

        if sign == 0:
            # Bucket has no signal (mean SHAP exactly 0). Close any open
            # run and skip — emitting a zero-impact "rule" is meaningless.
            if current_sign != 0 and current_count > 0:
                lo = float(bin_edges[current_lo_idx])
                hi = float(bin_edges[i])
                mean_shap = current_shap_sum / current_count
                ranges.append((lo, hi, mean_shap, current_count))
            current_sign = 0
            current_count = 0
            current_shap_sum = 0.0
            continue

        if current_sign == 0:
            current_sign = sign
            current_lo_idx = i
            current_shap_sum = bucket_mean * n
            current_count = n
        elif sign == current_sign:
            current_shap_sum += bucket_mean * n
            current_count += n
        else:
            # Sign flip: emit current range, start new one
            lo = float(bin_edges[current_lo_idx])
            hi = float(bin_edges[i])
            mean_shap = current_shap_sum / current_count
            ranges.append((lo, hi, mean_shap, current_count))
            current_sign = sign
            current_lo_idx = i
            current_shap_sum = bucket_mean * n
            current_count = n

    # Close final run
    if current_count > 0:
        lo = float(bin_edges[current_lo_idx])
        hi = float(bin_edges[-1])
        mean_shap = current_shap_sum / current_count
        ranges.append((lo, hi, mean_shap, current_count))

    return ranges


def extract_rules(
    feature_matrix: np.ndarray,
    shap_values: np.ndarray,
    feature_names: Sequence[str],
    base_rate: float,
    top_n_features: int = 10,
    min_rule_impact: float = 0.05,
    n_bins: int = 10,
) -> list[Rule]:
    """Discover astrological rules from a trained model's SHAP outputs.

    Args:
        feature_matrix:  (n_samples, n_features) numeric feature values
                         from the test/full set.
        shap_values:     (n_samples, n_features) per-sample SHAP contributions
                         from `shap.TreeExplainer.shap_values(X)`.
        feature_names:   ordered list of column names (must match shap shape).
        base_rate:       overall positive-class rate in the training set
                         (e.g., 0.05 for "5% of charts are politicians").
        top_n_features:  scan only the top-N features by |SHAP| importance.
        min_rule_impact: minimum |probability_delta| required to emit a rule.
                         Default 0.05 = 5% probability shift. Lower = noisier.
        n_bins:          per-feature bucket count for range detection.

    Returns:
        List of Rule objects, sorted by |probability_delta| descending. Empty
        list if no rule passes the magnitude filter (all signal too weak).
    """
    if feature_matrix.shape != shap_values.shape:
        raise ValueError(
            f"feature_matrix shape {feature_matrix.shape} != "
            f"shap_values shape {shap_values.shape}"
        )

    # Empty input: nothing to rank or extract; short-circuit to avoid
    # numpy "Mean of empty slice" runtime warnings inside .mean()/.std()
    if feature_matrix.shape[0] == 0:
        return []

    ranked = rank_features_by_importance(shap_values, feature_names)
    top_features = ranked[:top_n_features]

    rules: list[Rule] = []
    for feature_name, importance in top_features:
        col_idx = list(feature_names).index(feature_name)
        feature_values = feature_matrix[:, col_idx]
        shap_for_feature = shap_values[:, col_idx]

        # Skip features with no variance (e.g., always-zero columns)
        if float(np.std(feature_values)) < 1e-9:
            continue

        for lo, hi, mean_shap, count in _find_signed_ranges(
            feature_values, shap_for_feature, n_bins=n_bins,
        ):
            prob_delta = _logit_to_probability_delta(mean_shap, base_rate)

            if abs(prob_delta) < min_rule_impact:
                continue

            rules.append(Rule(
                feature=feature_name,
                range_low=lo,
                range_high=hi,
                direction="INCREASES" if prob_delta > 0 else "DECREASES",
                probability_delta=prob_delta,
                sample_count=count,
                feature_importance=float(importance),
            ))

    rules.sort(key=lambda r: abs(r.probability_delta), reverse=True)
    return rules
