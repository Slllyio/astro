"""Weighted judge W1 (docs/raman_saab/WEIGHTED_JUDGE_PREREG_2026-10-30.md).

A parallel judge: text-graded rule weights + a five-number ordinal logistic model over the
engine's own fired rules and lord/karaka condition. Never reads hold-outs 4 or 5 unless the
`final` command is given (user's say-so required).

Usage:
    python -m tools.raman_saab.weighted_judge features        # cache features for dev sets
    python -m tools.raman_saab.weighted_judge dev             # fit on pool, report on H1-3
    python -m tools.raman_saab.weighted_judge freeze          # fit on pool+H1-3, write params
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

DIR = Path("docs/raman_saab/weighted_judge")
WEIGHTS = DIR / "rule_weights.json"
FEATURES = DIR / "dev_features.json"
PARAMS = DIR / "w1_frozen.json"
DEV_SETS = {
    "H1": "tests/fixtures/raman_holdout_sealed.jsonl",
    "H2": "tests/fixtures/raman_holdout2_sealed.jsonl",
    "H3": "tests/fixtures/raman_holdout3_sealed.jsonl",
}
FINAL_SETS = {
    "H4": "tests/fixtures/raman_holdout4_sealed.jsonl",
    "H5": "tests/fixtures/raman_holdout5_sealed.jsonl",
}
CLASSES = ("afflicted", "mixed", "favourable")   # ordinal order, low to high
RIDGE = 0.1
SEED = 20261030


def _load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]


def _features(recs, confirmed_only):
    sys.path.insert(0, ".")
    from tests.raman_saab import test_goldens as tg
    import app.raman_saab.judges.house_template as ht
    out = []
    for r in recs:
        ch = tg.build_chart(r)
        pfs = {}
        for h, e in r["expected_verdicts"].items():
            if confirmed_only and not tg._is_confirmed(e):
                continue
            hn = int(h[1:])
            pf = pfs.setdefault(hn, ht.judge_house(ch, hn))
            sv = next((s for s in pf.significations if s.signification == e["signification"]), None)
            led = sv.ledger if sv else None
            out.append({
                "key": f"{r['id']} {h}/{e['signification']}", "chart": r["id"], "gold": e["verdict"],
                "E": sv.verdict if sv else None,
                "ben": [f.rule.id for f in led.fired_benefic] if led else [],
                "mal": [f.rule.id for f in led.fired_malefic] if led else [],
                "lord_strong": led.lord_strong if led else None,
                "karaka_strong": led.karaka_strong if led else None,
                "lord_hard": led.lord_hard_afflicted if led else None,
            })
    return out


def _x(row, w):
    sb = sum(w.get(i, 1.0) for i in row["ben"])
    sm = sum(w.get(i, 1.0) for i in row["mal"])
    lk = (row["lord_strong"] is True) + (row["karaka_strong"] is True) - (row["lord_hard"] is True)
    return sb, sm, float(lk)


def _probs(theta, x):
    b, m, l, c1, d = theta
    c2 = c1 + math.exp(d)                    # c1 < c2 always
    eta = b * x[0] - m * x[1] + l * x[2]
    sig = lambda z: 1.0 / (1.0 + math.exp(-z))
    p_aff = 1.0 - sig(eta - c1)
    p_fav = sig(eta - c2)
    return (p_aff, max(1e-9, 1.0 - p_aff - p_fav), p_fav)


def fit(rows, w):
    X = [_x(r, w) for r in rows]
    y = [CLASSES.index(r["gold"]) for r in rows]

    def nll(t):
        t = list(t)
        t[0], t[1] = abs(t[0]), abs(t[1])     # b, m >= 0
        s = sum(-math.log(max(1e-12, _probs(t, x)[k])) for x, k in zip(X, y))
        return s + RIDGE * (t[0] ** 2 + t[1] ** 2 + t[2] ** 2)

    best = None
    for start in ([0.5, 0.5, 0.3, -0.5, 0.0], [1.0, 1.0, 0.0, 0.0, 0.5], [0.2, 0.8, 0.5, -1.0, -0.5]):
        res = minimize(nll, start, method="Nelder-Mead", options={"maxiter": 20000, "xatol": 1e-6, "fatol": 1e-8})
        if best is None or res.fun < best.fun:
            best = res
    t = list(best.x)
    t[0], t[1] = abs(t[0]), abs(t[1])
    return t


def predict(theta, row, w):
    p = _probs(theta, _x(row, w))
    return CLASSES[int(np.argmax(p))], p


def b3(row):
    nb, nm = len(row["ben"]), len(row["mal"])
    return "favourable" if nb >= nm else "afflicted"


def _dist(a, b):
    o = {"favourable": 0, "mixed": 1, "afflicted": 2}
    if a == b:
        return 0
    return abs(o[a] - o[b]) if a in o and b in o else 2


def score(rows, preds, probs=None, freq=None):
    n = len(rows)
    ex = sum(p == r["gold"] for p, r in zip(preds, rows))
    w1 = sum(_dist(p, r["gold"]) <= 1 for p, r in zip(preds, rows))
    re_ = sum(_dist(p, r["gold"]) >= 2 for p, r in zip(preds, rows))
    rec = []
    for c in CLASSES:
        g = [(p, r) for p, r in zip(preds, rows) if r["gold"] == c]
        if g:
            rec.append(sum(p == c for p, _ in g) / len(g))
    out = {"n": n, "exact": ex, "within1": w1, "real": re_, "macro_recall": round(sum(rec) / len(rec), 3)}
    if probs is not None:
        out["logloss"] = round(sum(-math.log(max(1e-12, p[CLASSES.index(r["gold"])])) for p, r in zip(probs, rows)) / n, 4)
    if freq is not None:
        out["freq_logloss"] = round(sum(-math.log(freq[r["gold"]]) for r in rows) / n, 4)
    return out


def _freq(rows):
    return {c: sum(r["gold"] == c for r in rows) / len(rows) for c in CLASSES}


def _report(name, rows, theta, w, freq):
    pp = [predict(theta, r, w) for r in rows]
    res = {"W1": score(rows, [p for p, _ in pp], [q for _, q in pp], freq),
           "E": score(rows, [r["E"] for r in rows]),
           "B3": score(rows, [b3(r) for r in rows]),
           "W1_says": {c: sum(p == c for p, _ in pp) for c in CLASSES}}
    print(name, json.dumps(res))
    return res


def main(cmd):
    sys.path.insert(0, ".")
    DIR.mkdir(parents=True, exist_ok=True)
    if cmd == "features":
        from tests.raman_saab import test_goldens as tg
        feats = {"pool": _features(tg._TRACK_B_RATCHET, True)}
        for k, p in DEV_SETS.items():
            feats[k] = _features(_load(p), False)
        json.dump(feats, open(FEATURES, "w"), indent=0)
        print({k: len(v) for k, v in feats.items()})
        return
    feats = json.load(open(FEATURES))
    w = json.load(open(WEIGHTS)) if WEIGHTS.exists() else {}
    dev = feats["H1"] + feats["H2"] + feats["H3"]
    if cmd == "dev":
        theta = fit(feats["pool"], w)
        print("theta (fit on pool)", [round(t, 4) for t in theta])
        freq = _freq(feats["pool"])
        _report("pool (in-sample)", feats["pool"], theta, w, freq)
        _report("H1-3 (dev check)", dev, theta, w, freq)
    elif cmd == "freeze":
        allrows = feats["pool"] + dev
        theta = fit(allrows, w)
        verdicts = {r["key"]: predict(theta, r, w)[0] for r in allrows}
        sha = hashlib.sha256(json.dumps(verdicts, sort_keys=True).encode()).hexdigest()
        json.dump({"theta": theta, "freq": _freq(allrows), "sha_dev_verdicts": sha,
                   "weights_sha": hashlib.sha256(WEIGHTS.read_bytes()).hexdigest()},
                  open(PARAMS, "w"), indent=1)
        print("frozen", [round(t, 4) for t in theta], sha)
    elif cmd == "final":
        fz = json.load(open(PARAMS))
        assert fz["weights_sha"] == hashlib.sha256(WEIGHTS.read_bytes()).hexdigest()
        rows = []
        for k, p in FINAL_SETS.items():
            rows += _features(_load(p), False)
        return _report("H4+H5 (final, one time)", rows, fz["theta"], w, fz["freq"])


if __name__ == "__main__":
    main(sys.argv[1])
