"""Exact TreeSHAP values from XGBoost itself — no `shap` library in the compute path.

Both callers used to build a `shap.TreeExplainer(model)`. That broke outright once xgboost
reached 3.x: shap 0.48 cannot parse the newer tree dump and raises

    ValueError: could not convert string to float: '[5E-1]'

which took down `predictor.predict_for_chart` — a LIVE serving path (`medini_routes.py`
`/medini/predict`) — not merely a test.

XGBoost computes the same TreeSHAP internally, so the dependency was never needed:
``Booster.predict(dmatrix, pred_contribs=True)`` returns per-feature contributions with a
trailing BIAS column, and ``sum(contribs) + bias == margin`` exactly. Using it removes the
version coupling at the root instead of chasing a compatible `shap` release, and drops a heavy
dependency from the serving path. `shap` is still used for PLOTTING in `train_classifier`
(`summary_plot` / `dependence_plot` take plain arrays and never parse the model, so they are
unaffected by the incompatibility).

Usage:
    from app.medini.ml.tree_shap import tree_shap_values
    sv = tree_shap_values(model, X)        # (n_rows, n_features), margin/log-odds space
"""
from __future__ import annotations

from typing import Any

import numpy as np

#: Which class's contributions to return for a multiclass booster. 1 = the positive class,
#: matching the `shap_values[1]` convention both call sites used against the shap library.
_POSITIVE_CLASS = 1


def tree_shap_values(model: Any, X: Any) -> np.ndarray:
    """Per-feature TreeSHAP contributions for `X`, shaped `(n_rows, n_features)`.

    Values are in the model's margin (log-odds) space — the same space
    `shap.TreeExplainer.shap_values` returned for an XGBoost classifier, so downstream
    consumers (`shap_rules.rank_features_by_importance`, the log-odds→probability conversion
    in `extract_rules`) need no change.

    The trailing bias column that `pred_contribs` appends is stripped: it is the model's base
    value, not a feature, and leaving it in would silently misalign every contribution with its
    feature name."""
    import xgboost as xgb

    booster = model.get_booster() if hasattr(model, "get_booster") else model
    # enable_categorical mirrors the trainer (`fit_final_model` sets it) — the feature frame
    # carries pandas Categorical columns, and a DMatrix built without it rejects them.
    contribs = booster.predict(xgb.DMatrix(X, enable_categorical=True), pred_contribs=True)
    contribs = np.asarray(contribs)

    if contribs.ndim == 3:                      # multiclass: (n_rows, n_class, n_features + 1)
        idx = _POSITIVE_CLASS if contribs.shape[1] > _POSITIVE_CLASS else 0
        contribs = contribs[:, idx, :]
    return contribs[:, :-1]                     # drop the bias column
