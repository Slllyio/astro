"""SHAP-derived astrological rule extraction.

Takes raw SHAP values + feature values + feature names and emits
human-readable rules in the form:

    "WHEN <feature> IN [<low>, <high>] THEN probability shifts by <delta>"

Method (revised after the Phase 5 round-2 review):
  1. Identify the top-N features by mean |SHAP| magnitude.
  2. For each top feature, fit a shallow `DecisionTreeRegressor(max_depth=2)`
     mapping feature value → SHAP value. The tree's leaf boundaries are
     statistically-robust threshold candidates (vs the previous
     histogram-bucket sign-flip walk, which got trapped in tree-split
     micro-oscillations of the underlying XGBoost model).
  3. For each leaf segment, compute mean SHAP. Convert log-odds to a
     calibrated probability delta — either via the raw sigmoid(base_logit)
     baseline or, when an Isotonic calibrator from the trainer is
     supplied, through the calibrated probability scale (which corrects
     for `scale_pos_weight`-induced output distortion).
  4. Filter: discard rules whose absolute probability delta is below
     the magnitude threshold (default 0.05 = 5%).
  5. Sort by absolute probability impact, descending.

Pure functions except for the optional calibrator argument; no IO; no
direct model dependency. Tests feed synthetic SHAP arrays + optional
calibrators directly without needing a real XGBoost model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

import numpy as np
from sklearn.tree import DecisionTreeRegressor


class ProbabilityCalibrator(Protocol):
    """Duck-typed Isotonic / Platt scaler. Anything with a `.transform([p])
    -> array-like-of-1` works. Matches `sklearn.isotonic.IsotonicRegression`
    and `sklearn.calibration.CalibratedClassifierCV.calibrators_[i]`.
    """

    def transform(self, X) -> np.ndarray: ...


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


def _calibrated_probability_delta(
    shap_value: float,
    base_rate: float,
    calibrator: ProbabilityCalibrator | None = None,
) -> float:
    """Convert a SHAP log-odds value to a probability delta.

    Without calibrator: applies the sigmoid difference between
    (base_logit + shap_value) and base_logit — the original behaviour.

    With calibrator: maps BOTH the raw baseline probability and the
    raw shifted probability through the trainer-fit Isotonic calibrator,
    then returns the delta on the calibrated scale. This corrects for
    the `scale_pos_weight` distortion: XGBoost trained with
    scale_pos_weight=n_neg/n_pos outputs probabilities calibrated to a
    50/50 reference distribution, NOT the real population base rate.
    The raw log-odds → sigmoid mapping therefore overstates probability
    shifts for imbalanced targets (e.g. a SHAP value of +1.0 might
    correspond to a 4% real-world shift even though raw sigmoid says 12%).

    SHAP values for binary classifiers are log-odds contributions.
    base_rate is the marginal positive-class rate (a value in (0, 1)).
    """
    base_rate = max(min(base_rate, 1 - 1e-9), 1e-9)  # clamp away from 0/1
    base_logit = np.log(base_rate / (1.0 - base_rate))
    raw_base_prob = 1.0 / (1.0 + np.exp(-base_logit))
    raw_shifted_prob = 1.0 / (1.0 + np.exp(-(base_logit + shap_value)))
    if calibrator is None:
        return float(raw_shifted_prob - raw_base_prob)
    # calibrator.transform expects 1-D array; returns 1-D array.
    calibrated_base = float(np.asarray(calibrator.transform([raw_base_prob]))[0])
    calibrated_shifted = float(
        np.asarray(calibrator.transform([raw_shifted_prob]))[0]
    )
    return calibrated_shifted - calibrated_base


# Backwards-compatible alias — older callers and tests that don't yet
# supply a calibrator keep working unchanged.
def _logit_to_probability_delta(shap_value: float, base_rate: float) -> float:
    return _calibrated_probability_delta(shap_value, base_rate, calibrator=None)


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
    min_segment_samples: int = 20,
    max_depth: int = 2,
    min_samples_leaf_frac: float = 0.05,
    random_state: int = 42,
) -> list[tuple[float, float, float, int]]:
    """Discover statistically robust rule boundaries via a meta-regression-tree.

    Fits a shallow `DecisionTreeRegressor(max_depth=max_depth)` mapping
    feature_value → shap_value. The tree's split thresholds are the
    macro-level boundaries where SHAP behaviour genuinely changes —
    robust to the micro-oscillations XGBoost SHAP values exhibit at
    individual tree-split boundaries.

    Returns (low, high, mean_shap, sample_count) tuples for each leaf
    segment that contains at least `min_segment_samples` rows.

    With max_depth=2 (the default), this produces at most 3 split
    thresholds → at most 4 segments per feature. min_samples_leaf_frac=0.05
    means no segment captures fewer than 5% of the dataset — guards
    against noise-fitting in sparse regions.

    Returns empty list if input has < 100 non-NaN pairs (insufficient
    data for a meaningful regression tree fit) or has zero feature
    variance (e.g. a constant column slipped through).
    """
    # Drop NaNs in either feature or SHAP — paired masking.
    feature_arr = np.asarray(feature_values, dtype=float)
    shap_arr = np.asarray(shap_for_feature, dtype=float)
    if feature_arr.shape != shap_arr.shape:
        raise ValueError(
            f"shape mismatch: feature {feature_arr.shape} vs shap {shap_arr.shape}"
        )
    mask = ~(np.isnan(feature_arr) | np.isnan(shap_arr))
    X = feature_arr[mask]
    y = shap_arr[mask]
    if len(X) < 100:
        return []
    if float(np.std(X)) < 1e-9:
        return []
    if float(np.std(y)) < 1e-9:
        # SHAP values are flat — the model isn't using this feature.
        # Returning a zero-impact "rule" would be misleading; skip.
        return []

    meta = DecisionTreeRegressor(
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf_frac,
        random_state=random_state,
    )
    meta.fit(X.reshape(-1, 1), y)

    # The tree's `threshold` array has the split value at each internal
    # node; leaf nodes use a sentinel value (-2.0). Collect the real
    # thresholds, sort, and form contiguous segments using the data range.
    raw_thresholds = meta.tree_.threshold
    is_internal = meta.tree_.children_left != -1  # -1 = leaf sentinel
    split_values = sorted(set(
        float(raw_thresholds[i]) for i in range(len(raw_thresholds)) if is_internal[i]
    ))

    boundaries = [float(X.min()), *split_values, float(X.max())]
    ranges: list[tuple[float, float, float, int]] = []
    for i in range(len(boundaries) - 1):
        lo, hi = boundaries[i], boundaries[i + 1]
        # Right-inclusive on the final segment so values exactly at X.max()
        # are captured; otherwise left-inclusive/right-exclusive to avoid
        # double-counting at internal split boundaries.
        if i == len(boundaries) - 2:
            seg_mask = (feature_arr >= lo) & (feature_arr <= hi)
        else:
            seg_mask = (feature_arr >= lo) & (feature_arr < hi)
        # NaN guard — the seg_mask via comparisons already excludes NaNs.
        count = int(seg_mask.sum())
        if count < min_segment_samples:
            continue
        seg_shap = shap_arr[seg_mask]
        if seg_shap.size == 0:
            continue
        ranges.append((
            float(lo),
            float(hi),
            float(np.nanmean(seg_shap)),
            count,
        ))
    return ranges


def extract_rules(
    feature_matrix: np.ndarray,
    shap_values: np.ndarray,
    feature_names: Sequence[str],
    base_rate: float,
    top_n_features: int = 10,
    min_rule_impact: float = 0.05,
    calibrator: ProbabilityCalibrator | None = None,
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
        calibrator:      optional Isotonic / Platt calibrator fit on the
                         trainer's holdout. When supplied, probability
                         deltas are reported on the calibrated scale
                         (corrects for scale_pos_weight distortion).
                         When None, falls back to the original
                         sigmoid-against-base-rate mapping.

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
            feature_values, shap_for_feature,
        ):
            prob_delta = _calibrated_probability_delta(
                mean_shap, base_rate, calibrator=calibrator,
            )

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
