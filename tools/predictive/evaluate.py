"""Cross-validated statistics for the learned predictive test (prereg + addendum 1).

Task A: ΔAUC per target = CV AUC(baseline + astro) − CV AUC(baseline); full model and per family.
Task B: ΔC = within-set concordance (full) − concordance (baseline); full model and per family.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, StratifiedKFold

SEED = 20261102
ROUNDS = 300
PARAMS = dict(objective="binary", learning_rate=0.05, num_leaves=8, min_data_in_leaf=50,
              feature_fraction=0.5, bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0,
              seed=SEED, verbose=-1, num_threads=1)


def oof(X: np.ndarray, y: np.ndarray, folds: list[tuple[np.ndarray, np.ndarray]], params=None) -> np.ndarray:
    import lightgbm as lgb
    pr = dict(PARAMS, **(params or {}))
    out = np.zeros(len(y))
    for tr, te in folds:
        m = lgb.train(pr, lgb.Dataset(X[tr], y[tr], free_raw_data=False), num_boost_round=ROUNDS)
        out[te] = m.predict(X[te])
    return out


def folds_A(y: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    return list(StratifiedKFold(5, shuffle=True, random_state=SEED).split(np.zeros(len(y)), y))


def folds_B(groups: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
    return list(GroupKFold(5).split(np.zeros(len(groups)), groups=groups))


def concordance(score: np.ndarray, case: np.ndarray, set_id: np.ndarray) -> np.ndarray:
    """Per-set share of controls the case outranks (ties half). Returns one value per set (sorted ids)."""
    df = pd.DataFrame({"s": score, "c": case, "g": set_id})
    cs = df[df.c == 1].set_index("g").s
    ctl = df[df.c == 0]
    cmp = ctl.s.to_numpy()[:, None]
    case_s = cs.reindex(ctl.g).to_numpy()[:, None]
    val = (case_s > cmp).astype(float) + 0.5 * (case_s == cmp)
    return pd.Series(val.ravel(), index=ctl.g.to_numpy()).groupby(level=0).mean().sort_index().to_numpy()


def boot_ci(per_unit_delta: np.ndarray, units: np.ndarray, rng, reps: int = 1000) -> tuple[float, float]:
    """Person-clustered bootstrap 95% interval of the mean of per-unit values."""
    u, inv = np.unique(units, return_inverse=True)
    sums = np.bincount(inv, weights=per_unit_delta)
    cnts = np.bincount(inv)
    stats = []
    for _ in range(reps):
        k = rng.integers(0, len(u), len(u))
        stats.append(sums[k].sum() / cnts[k].sum())
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def auc_boot_ci(y, p_full, p_base, rng, reps: int = 1000) -> tuple[float, float]:
    n = len(y)
    st = []
    for _ in range(reps):
        k = rng.integers(0, n, n)
        if y[k].min() == y[k].max():
            continue
        st.append(roc_auc_score(y[k], p_full[k]) - roc_auc_score(y[k], p_base[k]))
    return float(np.percentile(st, 2.5)), float(np.percentile(st, 97.5))
