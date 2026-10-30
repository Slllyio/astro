"""Statistics the validation program needs that `_stats.py` / `controls.py` do not provide.

Every effect here is on a scale where 0 = no effect (AUC - 0.5, log RR, hit-rate difference),
so TOST bounds are symmetric +/- sesoi.

Usage:
    py -3.12 -m tools.validation.stats      # runs the assert self-check
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

Z80 = norm.ppf(0.975) + norm.ppf(0.80)   # 2.8016: two-sided alpha .05, power .80


def mde80(se0: float) -> float:
    """Minimum detectable effect at 80% power from the null SE. Computable from n alone."""
    return float(Z80 * se0)


def tost(effect: float, se: float, sesoi: float) -> float:
    """Two one-sided tests against +/- sesoi. p < .05 <=> the 90% CI lies inside the bounds."""
    p_low = 1.0 - norm.cdf((effect + sesoi) / se)    # H0: effect <= -sesoi
    p_high = norm.cdf((effect - sesoi) / se)         # H0: effect >= +sesoi
    return float(max(p_low, p_high))


def random_effects(effects, ses) -> dict[str, float]:
    """DerSimonian-Laird random-effects pool. tau2 ~ 0 => no family of tests is special.

    Hand-rolled: statsmodels' combine_effects exposes only the HKSJ-style weighted SE, which
    is 0/NaN when studies agree."""
    y, v = np.asarray(effects, float), np.asarray(ses, float) ** 2
    k = len(y)
    w = 1.0 / v
    ybar = (w * y).sum() / w.sum()
    q = float((w * (y - ybar) ** 2).sum())
    c = w.sum() - (w**2).sum() / w.sum()
    tau2 = max(0.0, (q - (k - 1)) / c) if k > 1 else 0.0
    ws = 1.0 / (v + tau2)
    return {"k": k, "effect": float((ws * y).sum() / ws.sum()), "se": float(np.sqrt(1 / ws.sum())),
            "tau2": float(tau2), "q": q, "i2": max(0.0, (q - (k - 1)) / q) if q > 0 else 0.0}


def cluster_bootstrap(values, clusters, *, rng, n_boot: int = 2000) -> tuple[float, float]:
    """95% percentile CI of the mean, resampling whole clusters (people). From transit_tests."""
    values, clusters = np.asarray(values, float), np.asarray(clusters)
    uniq = np.unique(clusters)
    idx = {c: np.where(clusters == c)[0] for c in uniq}
    boots = [values[np.concatenate([idx[c] for c in rng.choice(uniq, len(uniq))])].mean()
             for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(lo), float(hi)


if __name__ == "__main__":
    assert abs(Z80 - 2.8016) < 1e-3
    assert abs(mde80(0.01) - 0.028016) < 1e-5
    # 90% CI (0 +/- 1.645*0.01) is inside +/-0.03 -> equivalent; inside +/-0.01 -> not.
    assert tost(0.0, 0.01, 0.03) < 0.05 and tost(0.0, 0.01, 0.01) > 0.05
    # p_tost at the boundary of the 90% CI is exactly .05
    assert abs(tost(0.0, 0.01, 1.6449 * 0.01) - 0.05) < 1e-3
    # identical studies: no heterogeneity, pooled = common value, se = 1/sqrt(sum w)
    r = random_effects([0.2] * 4, [0.1] * 4)
    assert r["tau2"] == 0 and abs(r["effect"] - 0.2) < 1e-12 and abs(r["se"] - 0.05) < 1e-12
    # spread studies: hand-computed DL tau2 = (Q-(k-1))/C
    y, s = np.array([0.0, 0.5, 1.0]), np.array([0.1, 0.1, 0.1])
    w = 1 / s**2; ybar = (w * y).sum() / w.sum(); q = (w * (y - ybar) ** 2).sum()
    tau2 = (q - 2) / (w.sum() - (w**2).sum() / w.sum())
    assert abs(random_effects(y, s)["tau2"] - tau2) < 1e-9
    # cross-check against statsmodels on the quantities it does get right
    from statsmodels.stats.meta_analysis import combine_effects
    sm = combine_effects(y, s**2, method_re="dl")
    assert abs(sm.tau2 - tau2) < 1e-9 and abs(sm.mean_effect_re - random_effects(y, s)["effect"]) < 1e-9
    lo, hi = cluster_bootstrap([1, 1, 0, 0], ["a", "a", "b", "b"], rng=np.random.default_rng(0))
    assert 0.0 <= lo <= 0.5 <= hi <= 1.0
    print("stats self-check OK")
