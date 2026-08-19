"""A2 — learned (non-linear) combine over the engine's own findings (ML_RESEARCH track A).

Hypothesis (ceiling diagnostic + degree engine): the strength ceiling is SYNTHESIS —
`_combine`/`_THRESH` aggregate findings as a blended checklist where Raman applies
gate-like overrides. This module keeps the engine's feature extraction exactly as-is and
replaces only the aggregation with small, interpretable learned models:

  (a) proportional-odds ORDINAL LOGISTIC regression (L2, monotone thresholds), and
  (b) a shallow DECISION TREE (depth <= 3) that can natively express non-linear gates
      ("if 2+ strong malefic testimonies and no exaltation -> cap the grade").

Representation. One vocabulary both corpora sides can produce: each finding becomes a
(delta, frame) token — deltas come from the engine's fixed weight tables, so the vocabulary
is discrete (~30 tokens) — plus the engine's natural aggregates (positive/negative sums per
frame, extremes, counts) and the additive/bhava flag. This sits at exactly the aggregation
altitude: the learned model sees the same weighted testimony `_combine` sees, nothing more.

Protocol (pre-registered in the plan):
  P1 (primary)  LOCO-CV over the 7 held-out chapter corpora in the ENGINE representation
                (train on 6 chapters, test the 7th, rotate) — the same discipline as the
                Phase-2 recalibration, so the number is directly comparable to the live
                engine's 52.8% within-one on the identical rows.
  GATE          The ch. IV anchor (9 rows, typed findings -> same token vocabulary) must
                stay 9/9 within-one under the full-fit model, else the model is REJECTED.
  P2            The NH degree pool (32 rows) scored ONCE by the full-fit model — never in
                any training fold. Comparable to the live engine's 43.8%.
  P3 (context)  Tuned-corpora-only training (Raman's hand-decoded testimony, 112 rows) —
                honest caveat: those findings are what RAMAN cited, not what the engine
                extracts, so a representation shift exists; reported as robustness only.

Measurement only — the engine is NOT modified. If the learned combine decisively beats the
incumbents under P1+GATE, landing it becomes a separate reviewed increment.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.learned_combine
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize

from app.medini.doctrine.validation import recalibrate as RC
from app.medini.doctrine.validation import worked_chart_validate as W
from app.medini.doctrine.validation import fit_weights as F

_N_GRADES = 9
_TOL = 1  # within-one


# ------------------------------------------------------------------ features

def _tokens_from_engine(findings) -> list[tuple[float, str]]:
    return [(round(f.delta, 2), "Navamsa" if f.frame == "Navamsa" else "Rasi")
            for f in findings if f.delta != 0.0]


def _tokens_from_typed(findings) -> list[tuple[float, str]]:
    dg, w, _s, _b = F._unpack([p.default for p in F.PARAMS])
    out = []
    for feat in findings:
        d = round(float(F._token_delta(feat, dg, w)), 2)
        if d != 0.0:
            out.append((d, "Navamsa" if feat.get("frame") == "Navamsa" else "Rasi"))
    return out


def featurize(rows: list[dict], vocab: list[tuple[float, str]] | None = None
              ) -> tuple[np.ndarray, list[tuple[float, str]]]:
    """Rows carry ``tokens`` + ``additive``. Features = token counts over ``vocab`` +
    aggregates (pos/neg sums per frame, extremes, counts, additive flag)."""
    if vocab is None:
        vocab = sorted({t for r in rows for t in r["tokens"]})
    vi = {t: i for i, t in enumerate(vocab)}
    X = np.zeros((len(rows), len(vocab) + 9))
    for i, r in enumerate(rows):
        toks = r["tokens"]
        for t in toks:
            j = vi.get(t)
            if j is not None:
                X[i, j] += 1.0
        deltas = np.array([d for d, _ in toks]) if toks else np.zeros(1)
        rasi = np.array([d for d, fr in toks if fr == "Rasi"]) if toks else np.zeros(0)
        nav = np.array([d for d, fr in toks if fr == "Navamsa"]) if toks else np.zeros(0)
        k = len(vocab)
        X[i, k + 0] = rasi[rasi > 0].sum() if rasi.size else 0.0
        X[i, k + 1] = rasi[rasi < 0].sum() if rasi.size else 0.0
        X[i, k + 2] = nav[nav > 0].sum() if nav.size else 0.0
        X[i, k + 3] = nav[nav < 0].sum() if nav.size else 0.0
        X[i, k + 4] = deltas.max(initial=0.0)
        X[i, k + 5] = deltas.min(initial=0.0)
        X[i, k + 6] = float((deltas < 0).sum())
        X[i, k + 7] = float((deltas > 0).sum())
        X[i, k + 8] = 1.0 if r["additive"] else 0.0
    return X, vocab


FEATURE_TAIL = ["sum_pos_rasi", "sum_neg_rasi", "sum_pos_nav", "sum_neg_nav",
                "max_pos", "min_neg", "n_neg", "n_pos", "is_bhava"]


# ------------------------------------------------------------------ data

def heldout_rows() -> list[dict]:
    """Engine-representation rows from the 7 held-out chapters (one judgment pass via
    recalibrate.build_cache, which caches each scored row's live findings)."""
    rows = []
    for r in RC.build_cache():
        rows.append({"corpus": r["chapter"], "tokens": _tokens_from_engine(r["findings"]),
                     "additive": r["additive"], "y": r["raman"],
                     "_findings": r["findings"]})
    return rows


def nh_rows() -> list[dict]:
    """Engine-representation rows for the NH degree pool (32 rows, degree layer active)."""
    from app.medini.doctrine import raman_chart as rc
    from app.medini.doctrine.domains.house_judgment import (
        _assess_bhava, _assess_karaka, _assess_lord)
    from app.medini.ml.raman_saab.golden_registry import load_registry
    corp = Path(__file__).resolve().parents[4] / "docs/raman_doctrine/validation/corpora"
    patterns = W.load_verdict_map()
    cases = {c.key: c for c in load_registry()}
    rows = []
    for name in ("nh_strength.json", "nh_strength_grow.json"):
        for r in json.loads((corp / name).read_text())["rows"]:
            case = cases.get(r["key"])
            raman = W.map_verdict(r["phrase"], patterns)
            if case is None or not case.positions or raman is None:
                continue
            chart = rc.from_printed_positions(
                case.positions, case.lagna_lon, birth_jd=case.birth_jd,
                retrograde={g: True for g in (case.retro or [])})
            assess = {"bhava": _assess_bhava, "lord": _assess_lord,
                      "karaka": _assess_karaka}[r["factor"]]
            v = assess(chart, int(r["house"]))
            rows.append({"corpus": "nh", "tokens": _tokens_from_engine(v.findings),
                         "additive": r["factor"] == "bhava", "y": W._IDX[raman],
                         "_findings": v.findings})
    return rows


def tuned_rows() -> tuple[list[dict], list[dict]]:
    """(tuned, anchor) rows from the audit corpora (typed findings -> same tokens)."""
    files = sorted(p.name for p in F.CORPORA_DIR.glob("*.json"))
    tuned, anchor = [], []
    for r, y, is_anchor in F.load_rows(files):
        row = {"corpus": "anchor" if is_anchor else "tuned",
               "tokens": _tokens_from_typed(r["findings"]),
               "additive": bool(r["additive"]), "y": y}
        (anchor if is_anchor else tuned).append(row)
    return tuned, anchor


# ------------------------------------------------------------------ models

class OrdinalLogit:
    """Proportional-odds ordinal logistic with L2 and monotone thresholds."""

    def __init__(self, l2: float = 1.0):
        self.l2 = l2
        self.w: np.ndarray | None = None
        self.cuts: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "OrdinalLogit":
        n, d = X.shape
        k = _N_GRADES - 1

        def unpack(v):
            w = v[:d]
            cuts = np.concatenate([[v[d]], v[d] + np.cumsum(np.exp(v[d + 1:]))])
            return w, cuts

        def nll(v):
            w, cuts = unpack(v)
            z = X @ w
            # P(y <= j) = sigmoid(cuts[j] - z)
            cum = 1.0 / (1.0 + np.exp(-(cuts[None, :] - z[:, None])))
            cum = np.concatenate([np.zeros((n, 1)), cum, np.ones((n, 1))], axis=1)
            p = np.clip(cum[np.arange(n), y + 1] - cum[np.arange(n), y], 1e-9, 1.0)
            return -np.log(p).sum() + self.l2 * (w @ w)

        v0 = np.zeros(d + k)
        v0[d] = -2.0
        v0[d + 1:] = np.log(0.6)
        res = minimize(nll, v0, method="L-BFGS-B", options={"maxiter": 500})
        self.w, self.cuts = unpack(res.x)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        z = X @ self.w
        cum = 1.0 / (1.0 + np.exp(-(self.cuts[None, :] - z[:, None])))
        cum = np.concatenate([np.zeros((len(X), 1)), cum, np.ones((len(X), 1))], axis=1)
        return np.argmax(np.diff(cum, axis=1), axis=1)


def _tree(max_depth: int, min_leaf: int):
    from sklearn.tree import DecisionTreeClassifier
    return DecisionTreeClassifier(max_depth=max_depth, min_samples_leaf=min_leaf,
                                  random_state=0)


def _within1(pred: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(np.abs(pred - y) <= _TOL))


# ------------------------------------------------------------------ protocol

def run() -> dict[str, Any]:
    ho = heldout_rows()
    nh = nh_rows()
    tuned, anchor = tuned_rows()
    vocab = sorted({t for r in ho + nh + tuned + anchor for t in r["tokens"]})
    Xh, _ = featurize(ho, vocab)
    yh = np.array([r["y"] for r in ho])
    Xn, _ = featurize(nh, vocab)
    yn = np.array([r["y"] for r in nh])
    Xt, _ = featurize(tuned, vocab)
    yt = np.array([r["y"] for r in tuned])
    Xa, _ = featurize(anchor, vocab)
    ya = np.array([r["y"] for r in anchor])
    chapters = sorted({r["corpus"] for r in ho})

    def loco(model_fn) -> tuple[float, float]:
        """LOCO over held-out chapters; returns (within1, mean_delta) pooled over folds."""
        preds = np.zeros_like(yh)
        for ch in chapters:
            tr = np.array([r["corpus"] != ch for r in ho])
            te = ~tr
            m = model_fn().fit(Xh[tr], yh[tr])
            preds[te] = m.predict(Xh[te])
        return _within1(preds, yh), float(np.mean(preds - yh))

    # Engine incumbent ON THE SAME ROWS (the cache excludes rasi-only rows, so the pooled
    # 52.8%/43.8% headline numbers are not the right baseline here): re-run the live
    # _combine + thresholds over each cached row's findings.
    from app.medini.doctrine.domains import house_judgment as HJ

    def engine_within1(rows) -> float:
        ok = 0
        for r in rows:
            score = HJ._combine(r["_findings"], additive=r["additive"])[0]
            pred = W._IDX[HJ._verdict_label(score)]
            ok += int(abs(pred - r["y"]) <= _TOL)
        return round(100 * ok / len(rows), 1) if rows else 0.0

    out: dict[str, Any] = {"n_heldout": len(ho), "n_nh": len(nh), "n_tuned": len(tuned),
                           "n_anchor": len(anchor), "n_vocab": len(vocab),
                           "engine_incumbent_same_rows": {
                               "heldout_within1_pct": engine_within1(ho),
                               "nh_within1_pct": engine_within1(nh)}}

    # model selection by LOCO (small pinned grid — no peeking beyond held-out folds)
    grid: dict[str, Any] = {}
    for l2 in (0.3, 1.0, 3.0):
        w1, md = loco(lambda l2=l2: OrdinalLogit(l2))
        grid[f"ordinal_l2={l2}"] = {"loco_within1_pct": round(100 * w1, 1),
                                    "loco_mean_delta": round(md, 2)}
    for depth in (2, 3):
        for leaf in (4, 8):
            w1, md = loco(lambda d=depth, m=leaf: _tree(d, m))
            grid[f"tree_d{depth}_l{leaf}"] = {"loco_within1_pct": round(100 * w1, 1),
                                              "loco_mean_delta": round(md, 2)}
    out["loco_grid"] = grid
    best_key = max(grid, key=lambda k: grid[k]["loco_within1_pct"])
    out["best_by_loco"] = {best_key: grid[best_key]}

    def make_best():
        if best_key.startswith("ordinal"):
            return OrdinalLogit(float(best_key.split("=")[1]))
        d = int(best_key.split("_")[1][1:])
        m = int(best_key.split("_")[2][1:])
        return _tree(d, m)

    # full fit on ALL held-out rows -> anchor gate + NH single-shot
    best = make_best().fit(Xh, yh)
    anchor_pred = best.predict(Xa)
    anchor_ok = bool(np.all(np.abs(anchor_pred - ya) <= _TOL))
    out["anchor_gate"] = {"within1_all": anchor_ok,
                          "n_within1": int(np.sum(np.abs(anchor_pred - ya) <= _TOL)),
                          "n": len(ya)}
    nh_pred = best.predict(Xn)
    out["nh_single_shot"] = {"within1_pct": round(100 * _within1(nh_pred, yn), 1),
                             "mean_delta": round(float(np.mean(nh_pred - yn)), 2)}

    # P3 robustness: tuned-only training (representation-shift caveat applies)
    m3 = make_best().fit(Xt, yt)
    p3h = m3.predict(Xh)
    p3n = m3.predict(Xn)
    out["tuned_only_robustness"] = {
        "heldout_within1_pct": round(100 * _within1(p3h, yh), 1),
        "nh_within1_pct": round(100 * _within1(p3n, yn), 1)}

    # interpretability dump for the best tree (if tree won)
    if best_key.startswith("tree"):
        from sklearn.tree import export_text
        names = [f"tok({d:+.2f},{fr[0]})" for d, fr in vocab] + FEATURE_TAIL
        out["tree_rules"] = export_text(best, feature_names=names,
                                        show_weights=False).splitlines()
    return out


def main() -> None:
    print(json.dumps(run(), indent=1))


if __name__ == "__main__":
    main()
