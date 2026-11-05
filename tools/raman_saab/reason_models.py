"""Reason coding Step 4 (docs/raman_saab/REASON_CODING_PREREG_2026-10-31.md Addendum 1).

Coefficients of Raman's own stated factor types on his verdicts: L2 ordinal logistic and
depth-2 boosted trees with SHAP, both checked by leave-one-chart-out. Descriptive only: the
features come from Raman's text, so this is not a predictive engine.
Usage: python -m tools.raman_saab.reason_models CODED.json KEY.json [--out result.json]
"""
from __future__ import annotations

import json
import random
import sys

import numpy as np

TYPES = ["lord_house", "lord_dignity", "lord_association", "occupants", "house_aspects", "karaka",
         "navamsa", "other_frame", "hemming", "dusthana_lords", "named_yoga", "nodes",
         "strength_number", "dasa_timing", "maraka_longevity", "life_fact", "general_maxim", "other"]
CLS = {"afflicted": 0, "mixed": 1, "favourable": 2}
SEED = 20261031


def features(coded, key):
    X, y, groups, ids = [], [], [], []
    for mid, v in sorted(coded.items()):
        if not v.get("found") or not v.get("factors"):
            continue
        cnt = np.zeros(len(TYPES)); dec = np.zeros(len(TYPES))
        for f in v["factors"]:
            t = f["type"] if f["type"] in TYPES else "other"
            s = 1.0 if f["direction"] == "+" else -1.0
            cnt[TYPES.index(t)] += s
            if f.get("decisive"):
                dec[TYPES.index(t)] += s
        X.append(np.concatenate([cnt, dec])); y.append(CLS[key[mid]["gold"]])
        groups.append(key[mid]["chart"]); ids.append(mid)
    return np.array(X), np.array(y), np.array(groups), ids


def _ordinal_fit(X, y, alpha):
    from scipy.optimize import minimize
    p = X.shape[1]

    def unpack(t):
        return t[:p], t[p], t[p] + np.exp(t[p + 1])

    def nll(t):
        w, c1, c2 = unpack(t)
        eta = X @ w
        s = lambda z: 1 / (1 + np.exp(-z))
        pa = 1 - s(eta - c1); pf = s(eta - c2); pm = np.clip(1 - pa - pf, 1e-9, 1)
        P = np.stack([pa, pm, pf], 1)
        return -np.log(np.clip(P[np.arange(len(y)), y], 1e-12, 1)).sum() + alpha * (w @ w)

    res = minimize(nll, np.zeros(p + 2), method="L-BFGS-B")
    return unpack(res.x)


def _ordinal_predict(model, X):
    w, c1, c2 = model
    eta = X @ w
    s = lambda z: 1 / (1 + np.exp(-z))
    pa = 1 - s(eta - c1); pf = s(eta - c2); pm = np.clip(1 - pa - pf, 1e-9, 1)
    return np.stack([pa, pm, pf], 1)


def loco(X, y, g, fit, pred):
    P = np.zeros((len(y), 3))
    for c in sorted(set(g)):
        te = g == c
        m = fit(X[~te], y[~te])
        P[te] = pred(m, X[te])
    return P


def summary(P, y):
    yhat = P.argmax(1)
    rec = [np.mean(yhat[y == k] == k) for k in range(3) if np.any(y == k)]
    return {"n": int(len(y)), "exact": int((yhat == y).sum()), "real": int((abs(yhat - y) >= 2).sum()),
            "macro_recall": round(float(np.mean(rec)), 3),
            "logloss": round(float(-np.log(np.clip(P[np.arange(len(y)), y], 1e-12, 1)).mean()), 4)}


def main(coded_path, key_path, out):
    coded = json.load(open(coded_path)); key = json.load(open(key_path))
    X, y, g, ids = features(coded, key)
    names = [f"{t}" for t in TYPES] + [f"{t}*decisive" for t in TYPES]
    freq = np.bincount(y, minlength=3) / len(y)
    res = {"n": len(y), "class_freq_logloss": round(float(-np.log(freq[y]).mean()), 4)}
    best = None
    for a in (0.01, 0.1, 0.3, 1.0, 3.0, 10.0):
        P = loco(X, y, g, lambda A, B: _ordinal_fit(A, B, a), _ordinal_predict)
        s = summary(P, y); s["alpha"] = a
        res.setdefault("ordinal_loco_by_alpha", []).append(s)
        if best is None or s["logloss"] < best[1]["logloss"]:
            best = (a, s)
    a = best[0]
    w, c1, c2 = _ordinal_fit(X, y, a)
    rnd = random.Random(SEED); charts = sorted(set(g)); boots = []
    for _ in range(300):
        pick = [rnd.choice(charts) for _ in charts]
        idx = np.concatenate([np.where(g == c)[0] for c in pick])
        boots.append(_ordinal_fit(X[idx], y[idx], a)[0])
    B = np.array(boots)
    res["ordinal"] = {"alpha": a, "loco": best[1], "coefficients": sorted(
        [{"feature": n, "coef": round(float(w[i]), 3), "ci95": [round(float(np.percentile(B[:, i], 2.5)), 3),
          round(float(np.percentile(B[:, i], 97.5)), 3)], "nonzero_rows": int((X[:, i] != 0).sum())}
         for i, n in enumerate(names) if (X[:, i] != 0).any()], key=lambda d: -abs(d["coef"]))}
    from xgboost import XGBClassifier
    gb = lambda A, B: XGBClassifier(max_depth=2, n_estimators=150, learning_rate=0.05, subsample=0.8,
                                    objective="multi:softprob", num_class=3, random_state=SEED,
                                    verbosity=0).fit(A, B)
    gbp = lambda m, A: m.predict_proba(A)
    res["boosted_loco"] = summary(loco(X, y, g, gb, gbp), y)
    import shap
    m = gb(X, y)
    sv = shap.TreeExplainer(m).shap_values(X)
    sv = np.array(sv)
    # mean |SHAP| across classes, per feature
    if sv.ndim == 3 and sv.shape[0] == len(y):
        imp = np.abs(sv).mean(axis=(0, 2))
    else:
        imp = np.abs(sv).mean(axis=(0, 1))
    res["boosted_shap_importance"] = sorted([{"feature": n, "mean_abs_shap": round(float(imp[i]), 4)}
                                             for i, n in enumerate(names) if imp[i] > 0],
                                            key=lambda d: -d["mean_abs_shap"])
    print(json.dumps({k: v for k, v in res.items() if k != "ordinal"}, indent=1)[:3000])
    print("ordinal alpha", a, best[1])
    for c in res["ordinal"]["coefficients"][:20]:
        print("  ", c)
    if out:
        json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], a[a.index("--out") + 1] if "--out" in a else None)
