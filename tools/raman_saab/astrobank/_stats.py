"""Statistical helpers for the astrobank validation (Stage 3/4) — scipy-backed, pre-registered.

AUC here is the probability that a random CASE scores lower/higher (per the pre-registered
direction) than a random CONTRAST member — computed from the Mann-Whitney U. All tests are
one-sided in the registered direction; permutation nulls run within strata.
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def auc_mw(case: np.ndarray, contrast: np.ndarray, direction: str) -> dict:
    """One-sided Mann-Whitney; AUC oriented so >0.5 SUPPORTS the registered direction.

    direction='afflicted': cases expected LOWER (verdict ordinal) than contrast.
    direction='favourable': cases expected HIGHER.
    """
    if len(case) == 0 or len(contrast) == 0:
        return {"auc": float("nan"), "p": float("nan"), "n_case": len(case),
                "n_contrast": len(contrast)}
    alt = "less" if direction == "afflicted" else "greater"
    res = stats.mannwhitneyu(case, contrast, alternative=alt)
    auc = res.statistic / (len(case) * len(contrast))
    if direction == "afflicted":
        auc = 1.0 - auc          # orient: bigger = more support
    return {"auc": float(auc), "p": float(res.pvalue),
            "n_case": int(len(case)), "n_contrast": int(len(contrast))}


def bootstrap_auc_ci(case: np.ndarray, contrast: np.ndarray, direction: str,
                     n_boot: int = 1000, seed: int = 7) -> tuple[float, float, float]:
    """(lo95, hi95, se) of the oriented AUC by case/contrast resampling."""
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(n_boot):
        c = rng.choice(case, size=len(case), replace=True)
        k = rng.choice(contrast, size=len(contrast), replace=True)
        aucs.append(auc_mw(c, k, direction)["auc"])
    arr = np.asarray(aucs)
    return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)), float(arr.std())


def stratified_auc(case_vals: np.ndarray, case_strata: np.ndarray,
                   ctr_vals: np.ndarray, ctr_strata: np.ndarray,
                   direction: str, min_per_side: int = 5) -> dict:
    """Per-stratum oriented AUC combined by inverse-variance (Hanley-McNeil SE); strata with
    fewer than `min_per_side` on either side are pooled out."""
    weights, aucs, used = [], [], 0
    for s in np.unique(np.concatenate([case_strata, ctr_strata])):
        c = case_vals[case_strata == s]
        k = ctr_vals[ctr_strata == s]
        if len(c) < min_per_side or len(k) < min_per_side:
            continue
        a = auc_mw(c, k, direction)["auc"]
        n1, n2 = len(c), len(k)
        q1, q2 = a / (2 - a), 2 * a * a / (1 + a)
        var = (a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n2 - 1) * (q2 - a * a)) / (n1 * n2)
        if var <= 0:
            var = 1e-6
        weights.append(1.0 / var)
        aucs.append(a)
        used += 1
    if not aucs:
        return {"auc_stratified": float("nan"), "strata_used": 0}
    w = np.asarray(weights)
    return {"auc_stratified": float(np.average(aucs, weights=w)), "strata_used": used}


def permutation_p(case_vals: np.ndarray, case_strata: np.ndarray,
                  ctr_vals: np.ndarray, ctr_strata: np.ndarray,
                  direction: str, n_perm: int = 1000, seed: int = 11) -> float:
    """Within-stratum label-shuffle empirical p for the oriented pooled AUC."""
    rng = np.random.default_rng(seed)
    observed = auc_mw(case_vals, ctr_vals, direction)["auc"]
    vals = np.concatenate([case_vals, ctr_vals])
    strata = np.concatenate([case_strata, ctr_strata])
    is_case = np.concatenate([np.ones(len(case_vals), bool), np.zeros(len(ctr_vals), bool)])
    count = 0
    for _ in range(n_perm):
        perm = is_case.copy()
        for s in np.unique(strata):
            idx = np.where(strata == s)[0]
            perm[idx] = rng.permutation(perm[idx])
        a = auc_mw(vals[perm], vals[~perm], direction)["auc"]
        if a >= observed:
            count += 1
    return (count + 1) / (n_perm + 1)


def bh_fdr(pvals: dict[str, float], q: float = 0.10) -> dict[str, bool]:
    """Benjamini-Hochberg: test_id -> passes-FDR flag."""
    items = sorted(((k, p) for k, p in pvals.items() if np.isfinite(p)), key=lambda kv: kv[1])
    m = len(items)
    passed: dict[str, bool] = {k: False for k in pvals}
    threshold_rank = 0
    for i, (_k, p) in enumerate(items, 1):
        if p <= q * i / m:
            threshold_rank = i
    for i, (k, _p) in enumerate(items, 1):
        passed[k] = i <= threshold_rank
    return passed
