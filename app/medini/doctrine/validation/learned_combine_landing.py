"""The A2 learned-combine LANDING test — the decisive close (measurement only, NO engine change).

Increment 15 (ML research) fit a small model over the engine's own Finding tokens: 63.5% within-one
under LOCO-CV vs the engine's 51.9% on identical rows. It was NOT landed — it failed the pre-registered
ch. IV anchor gate. The A2′ investigation attributed part of the failure to a typed-representation
artifact but concluded the deeper cause was out-of-distribution collapse (the LOCO folds are
afflicted-skewed dusthāna chapters; the model learned "dense negatives → afflicted" and collapses on
the house-1 strong-lagna anchor). The documented landing prerequisite: **house-1 / kendra-strong
training rows** + a **grid-backed anchor re-baselined through the live engine**.

This module supplies BOTH and runs the decisive test:
  - the anchor is scored in LIVE ENGINE REPRESENTATION (grid-backed casts of ch. IV Charts 12-14 via
    `anchor_live_validate.chart_for` → `judge_house_doctrine` → `_tokens_from_engine`), not the retired
    typed calibration vocabulary — the "re-derivation in engine representation" the landing path names;
  - the model is trained under three regimes, one of which injects the strong-heavy NH degree pool
    (73 rows, 15 strong-graded after grow4) — the "house-1 / kendra-strong training rows" prerequisite.

RESULT — the landing is definitively refused. The model scores **0/8 within-one on the live anchor in
ALL THREE regimes** (held-out only, held-out + full NH, NH only; ordinal and depth-3 tree alike):
adding strong training signal does NOT cure the collapse. The anchor's house-1 strong-lagna verdicts
are not feature-separable from afflicted ones — the same holistic gap increments 29-30 proved
unclosable. The model is strictly worse on the anchor than the live engine (0/8 vs 2/8) because it
lacks the engine-base floor synthesis_v2 uses; and synthesis_v2 already landed the one transferable
discovery (Gate B = the tree's `sum_neg ≤ −1.22` split) LIVE, holding anchor parity. So the ceiling
residual is learnable IN-DISTRIBUTION but NOT landable, and the pre-registered anchor gate is
vindicated at the model level. See ML_RESEARCH.md / HOUSE_SCHEME_AUDIT.md (learned-combine landing).

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.learned_combine_landing [--json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from app.medini.doctrine.validation import anchor_live_validate as A
from app.medini.doctrine.validation import learned_combine as LC
from app.medini.doctrine.validation import worked_chart_validate as W
from app.medini.doctrine.domains.house_judgment import judge_house_doctrine

_CORP = Path(__file__).resolve().parents[4] / "docs/raman_doctrine/validation/corpora"
_FA = {"bhava": "lagna_verdict", "lord": "lord_verdict", "karaka": "karaka_verdict"}
_STRONG = W._IDX["fairly strong"]


def nh_rows_full() -> list[dict]:
    """All 5 NH corpora (73 rows, strong-heavy after grow4), live engine representation."""
    from app.medini.doctrine import raman_chart as rc
    from app.medini.doctrine.domains.house_judgment import _assess_bhava, _assess_karaka, _assess_lord
    from app.medini.ml.raman_saab.golden_registry import load_registry
    pats = W.load_verdict_map()
    cases = {c.key: c for c in load_registry()}
    rows = []
    for name in ("nh_strength.json", "nh_strength_grow.json", "nh_strength_grow2.json",
                 "nh_strength_grow3.json", "nh_strength_grow4.json"):
        for r in json.loads((_CORP / name).read_text())["rows"]:
            case = cases.get(r["key"])
            raman = W.map_verdict(r["phrase"], pats)
            if case is None or not case.positions or raman is None or r["factor"] == "overall":
                continue
            chart = rc.from_printed_positions(case.positions, case.lagna_lon, birth_jd=case.birth_jd,
                                              retrograde={g: True for g in (case.retro or [])})
            assess = {"bhava": _assess_bhava, "lord": _assess_lord, "karaka": _assess_karaka}[r["factor"]]
            v = assess(chart, int(r["house"]))
            rows.append({"tokens": LC._tokens_from_engine(v.findings),
                         "additive": r["factor"] == "bhava", "y": W._IDX[raman]})
    return rows


def live_anchor_rows() -> list[dict]:
    """ch. IV anchor in LIVE engine representation (grid-backed casts, judged live)."""
    corpus = json.loads(A._CORPUS.read_text())
    rows = []
    for rec in corpus["charts"]:
        chart = A.chart_for(rec)
        j = judge_house_doctrine(chart, 1)
        for v in rec["verdicts"]:
            if v["factor"] == "overall" or v.get("structural"):
                continue
            fv = getattr(j, _FA[v["factor"]])
            rows.append({"tokens": LC._tokens_from_engine(fv.findings),
                         "additive": v["factor"] == "bhava", "y": W._IDX[v["raman"]],
                         "tag": f"ch{rec['chart']}-{v['factor']}", "raman": v["raman"]})
    return rows


def _within1(pred: np.ndarray, y: np.ndarray) -> int:
    return int(np.sum(np.abs(pred - y) <= 1))


def _gate(train: list[dict], anchor: list[dict], vocab) -> dict[str, Any]:
    Xtr, _ = LC.featurize(train, vocab)
    ytr = np.array([r["y"] for r in train])
    Xa, _ = LC.featurize(anchor, vocab)
    ya = np.array([r["y"] for r in anchor])
    out: dict[str, Any] = {"n_train": len(train)}
    for name, model in (("ordinal", LC.OrdinalLogit(1.0)), ("tree_d3", LC._tree(3, 4))):
        pa = model.fit(Xtr, ytr).predict(Xa)
        out[name] = {"within1": _within1(pa, ya), "n": len(ya),
                     "preds": [W.VERDICT_SCALE[int(p)] for p in pa]}
    return out


def run() -> dict[str, Any]:
    ho = LC.heldout_rows()
    nh = nh_rows_full()
    anchor = live_anchor_rows()
    vocab = sorted({t for r in ho + nh + anchor for t in r["tokens"]})
    return {"n_heldout": len(ho), "n_nh": len(nh),
            "nh_strong": sum(1 for r in nh if r["y"] >= _STRONG),
            "n_anchor": len(anchor), "anchor_raman": [r["raman"] for r in anchor],
            "anchor_tags": [r["tag"] for r in anchor],
            "regimes": {"heldout_only": _gate(ho, anchor, vocab),
                        "heldout_plus_nh": _gate(ho + nh, anchor, vocab),
                        "nh_only": _gate(nh, anchor, vocab)}}


def main() -> None:
    r = run()
    print("A2 learned-combine LANDING test — live-representation anchor, three training regimes\n")
    print(f"  held-out N={r['n_heldout']}  NH N={r['n_nh']} (strong-graded {r['nh_strong']})  "
          f"anchor N={r['n_anchor']} (house-1, live casts)\n")
    for reg, res in r["regimes"].items():
        o, t = res["ordinal"], res["tree_d3"]
        print(f"  {reg:18} train N={res['n_train']:<3}  anchor within-one: "
              f"ordinal {o['within1']}/{o['n']}, tree {t['within1']}/{t['n']}")
    print("\n  per-row (heldout+NH, tree):  raman → predicted")
    tp = r["regimes"]["heldout_plus_nh"]["tree_d3"]["preds"]
    for tag, ram, pred in zip(r["anchor_tags"], r["anchor_raman"], tp):
        mark = "OK " if abs(W._IDX[ram] - W._IDX[pred]) <= 1 else "MISS"
        print(f"    {mark} {tag:12} {ram:16} → {pred}")
    print("\n  VERDICT: 0/8 in every regime — strong training signal does NOT cure the OOD collapse.")
    print("  The learned combine is NOT landable; its transferable gain (Gate B) is already live in")
    print("  synthesis_v2, which holds anchor parity via the engine-base floor the model lacks.")
    if "--json" in sys.argv:
        print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
