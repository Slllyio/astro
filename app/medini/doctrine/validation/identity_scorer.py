"""Increment 33 — identity-preserving learned scorer (ML_RESEARCH track A3; measurement only).

The root-cause analysis found the ceiling is an AGGREGATION collapse: the additive scalar (and every
gate over it) discards *identity* — which criterion, which placement, which aspect-source nature — and
of 37 verdict-pairs Raman separates by >=2 grades on the SAME additive score, 36 differ in structured
features the engine already computes but throws away. The A2 experiment (`learned_combine`) tried a
learned model but at the "aggregation altitude": it collapsed each finding to a `(delta, frame)` token —
still identity-blind — and, sourcing the anchor from the OLD typed audit corpora, failed the anchor gate.

This module tests the one representation never tried: **identity-preserving features** built from the
same live `Finding` objects for EVERY corpus (held-out, NH, AND the live ch. IV anchor), so the vector is
uniform across all corpora — removing A2's vocabulary mismatch. The vector STRICTLY NESTS A2's aggregates
(sum_pos/neg per frame, extremes, counts, is_bhava), so any LOCO gain over A2 is attributable to identity,
not a different model family.

Protocol (reuses `learned_combine`'s discipline verbatim — same OrdinalLogit / tree / LOCO / within-one):
  P1 (primary)  LOCO-CV over the 7 held-out chapters, identity representation. Comparable to A2 (63.5%)
                and the live engine (58.6% after Gate D).
  GATE          the LIVE ch. IV anchor (8 rows, live findings, SAME featurizer) must stay >= its current
                within-one under the full-fit model, else REJECT (a fair test now — same vocabulary).
  P2            the NH degree pool scored ONCE by the full-fit model, never in any fold.
  DECISIVE      identity model vs A2's (delta,frame) token model ON THE SAME LOCO FOLDS, both featurized
                from the identical rows. If identity does not beat A2, identity does not separate either →
                the ceiling is holistic / data-bound (N~130), the decisive negative that closes the ML lever.

Measurement only — the engine is NOT modified. Landing (if it wins + passes the gate) is a separate
gated increment.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.identity_scorer [--json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from app.medini.doctrine.domains import house_judgment as HJ
from app.medini.doctrine.domains import synthesis_v2 as S2
from app.medini.doctrine.domains.house_judgment import judge_house_doctrine
from app.medini.doctrine.validation import anchor_live_validate as A
from app.medini.doctrine.validation import learned_combine as LC
from app.medini.doctrine.validation import recalibrate as RC
from app.medini.doctrine.validation import worked_chart_validate as W

_CORP = Path(__file__).resolve().parents[4] / "docs/raman_doctrine/validation/corpora"
_NH_ALL = [_CORP / f for f in ("nh_strength.json", "nh_strength_grow.json", "nh_strength_grow2.json",
                               "nh_strength_grow3.json", "nh_strength_grow4.json")]
_FA = {"bhava": "lagna_verdict", "lord": "lord_verdict", "karaka": "karaka_verdict"}
_TOL = 1

# the 10 criteria the assessors emit (house_judgment) — the identity axis the scalar flattens
_CRITERIA = ["dignity", "placement", "lordship", "aspect", "conjunction",
             "kartari", "vargottama", "combustion", "ashtakavarga", "sutra"]
# affliction-bearing criteria whose MULTIPLICITY (neg count) matters beyond the net signed count
_NEG_CRIT = ["aspect", "conjunction", "kartari", "placement"]
_TIER = {"none": 0, "own": 1, "exalted": 2}


# ── identity feature extractor (the only genuinely new piece) ─────────────────────────────────────

def _nature_bucket(text: str) -> str | None:
    """Map an aspect/conjunction finding's source-nature tag to a coarse bucket (closed vocab)."""
    t = text.lower()
    if "yogakaraka" in t:
        return "yoga"
    if "functional malefic" in t or ("malefic" in t and "benefic" not in t):
        return "mal"
    if "functional benefic" in t or "benefic" in t or "(exalted)" in t:
        return "ben"
    return None


def _frame_block(findings) -> list[float]:
    """Per-frame identity features from a list of Finding objects (already frame-partitioned)."""
    net = {c: 0.0 for c in _CRITERIA}
    negc = {c: 0.0 for c in _NEG_CRIT}
    nat = {"yoga": 0.0, "mal": 0.0, "ben": 0.0}
    for f in findings:
        if f.criterion in net:
            net[f.criterion] += (1.0 if f.delta > 0 else (-1.0 if f.delta < 0 else 0.0))
        if f.criterion in negc and f.delta < 0:
            negc[f.criterion] += 1.0
        if f.criterion in ("aspect", "conjunction"):
            b = _nature_bucket(f.text)
            if b:
                nat[b] += 1.0
    rst = S2._reduce_frame(list(findings))
    block = [net[c] for c in _CRITERIA] + [negc[c] for c in _NEG_CRIT]
    block += [nat["yoga"], nat["mal"], nat["ben"]]
    block += [float(_TIER[rst.tier]), 1.0 if rst.besieged else 0.0, float(rst.fort)]
    return block


def _sav_diff(findings) -> float:
    """SAV bindus minus the neutral average for the bhava (identity the dormant delta=0 hides)."""
    for f in findings:
        if f.criterion == "ashtakavarga" and "ashtakavarga bindus in" in f.text:
            try:
                cnt = float(f.text.split()[0])
                avg = float(f.text.rsplit("avg", 1)[1].strip(" )"))
                return cnt - avg
            except (ValueError, IndexError):
                return 0.0
    return 0.0


def _feature_names() -> list[str]:
    names: list[str] = []
    for fr in ("rasi", "nav"):
        names += [f"{fr}:net:{c}" for c in _CRITERIA]
        names += [f"{fr}:negcnt:{c}" for c in _NEG_CRIT]
        names += [f"{fr}:nat_yoga", f"{fr}:nat_mal", f"{fr}:nat_ben"]
        names += [f"{fr}:tier", f"{fr}:besieged", f"{fr}:fort"]
    names += ["sav_diff"]
    # A2 aggregate tail (strictly nested) — same 9 as learned_combine.FEATURE_TAIL
    names += LC.FEATURE_TAIL
    return names


FEATURE_NAMES = _feature_names()


def identity_features(findings, additive: bool) -> np.ndarray:
    rasi = [f for f in findings if f.frame in ("Rasi", "both")]
    nav = [f for f in findings if f.frame == "Navamsa"]
    vec = _frame_block(rasi) + _frame_block(nav) + [_sav_diff(rasi)]
    # A2 aggregate tail from the same findings (nesting the token model's aggregates)
    deltas = np.array([f.delta for f in findings if f.delta != 0.0]) if findings else np.zeros(1)
    r = np.array([f.delta for f in rasi if f.delta != 0.0], float)
    n = np.array([f.delta for f in nav if f.delta != 0.0], float)
    vec += [r[r > 0].sum() if r.size else 0.0, r[r < 0].sum() if r.size else 0.0,
            n[n > 0].sum() if n.size else 0.0, n[n < 0].sum() if n.size else 0.0,
            float(deltas.max(initial=0.0)), float(deltas.min(initial=0.0)),
            float((deltas < 0).sum()), float((deltas > 0).sum()), 1.0 if additive else 0.0]
    return np.asarray(vec, float)


# ── row collection: every corpus through the live judge path (uniform Finding objects) ─────────────

def collect_rows() -> tuple[list[dict], list[dict], list[dict]]:
    """(held-out, nh, anchor) rows. Each: {corpus, y, findings, additive}. Held-out is grouped by
    chapter (for LOCO); nh/anchor are single held-out sets."""
    ho = [{"corpus": r["chapter"], "y": r["raman"], "findings": r["findings"],
           "additive": bool(r["additive"])} for r in RC.build_cache()]

    from app.medini.doctrine import raman_chart as rc
    from app.medini.ml.raman_saab.golden_registry import load_registry
    pats = W.load_verdict_map()
    cases = {c.key: c for c in load_registry()}
    nh: list[dict] = []
    seen: set[tuple] = set()
    for p in _NH_ALL:
        for r in json.loads(p.read_text())["rows"]:
            if r["factor"] == "overall":
                continue
            case = cases.get(r["key"]); raman = W.map_verdict(r["phrase"], pats)
            if case is None or not case.positions or raman is None:
                continue
            key = (r["key"], r["house"], r["factor"])
            if key in seen:
                continue
            seen.add(key)
            chart = rc.from_printed_positions(case.positions, case.lagna_lon, birth_jd=case.birth_jd,
                                              retrograde={g: True for g in (case.retro or [])})
            assess = {"bhava": HJ._assess_bhava, "lord": HJ._assess_lord,
                      "karaka": HJ._assess_karaka}[r["factor"]]
            v = assess(chart, int(r["house"]))
            nh.append({"corpus": "nh", "y": W._IDX[raman], "findings": v.findings,
                       "additive": r["factor"] == "bhava"})

    corpus = json.loads(A._CORPUS.read_text()); ah = int(corpus["house"])
    anchor: list[dict] = []
    for rec in corpus["charts"]:
        chart = A.chart_for(rec); j = judge_house_doctrine(chart, ah)
        for v in rec["verdicts"]:
            if v["factor"] in _FA:
                fv = getattr(j, _FA[v["factor"]])
                anchor.append({"corpus": "anchor", "y": W._IDX[v["raman"]], "findings": fv.findings,
                               "additive": v["factor"] == "bhava", "eng": S2.grade_factor(fv)[0]})
    return ho, nh, anchor


def _X(rows: list[dict]) -> np.ndarray:
    return np.vstack([identity_features(r["findings"], r["additive"]) for r in rows])


def _a2_X(rows: list[dict], vocab=None):
    """A2 (delta,frame)-token features from the SAME rows — the same-fold baseline."""
    trows = [{"tokens": LC._tokens_from_engine(r["findings"]), "additive": r["additive"]} for r in rows]
    return LC.featurize(trows, vocab)


# ── protocol ──────────────────────────────────────────────────────────────────────────────────────

def _loco(rows: list[dict], featX, model_fn) -> tuple[float, float]:
    """LOCO over held-out chapters; pooled (within1, train_gap). featX(train_rows)->(vocab or None)."""
    chapters = sorted({r["corpus"] for r in rows})
    preds, ys, train_hits, train_n = [], [], 0, 0
    for ch in chapters:
        tr = [r for r in rows if r["corpus"] != ch]
        te = [r for r in rows if r["corpus"] == ch]
        Xtr, aux = featX(tr, None)
        Xte, _ = featX(te, aux)
        ytr = np.array([r["y"] for r in tr]); yte = np.array([r["y"] for r in te])
        m = model_fn().fit(Xtr, ytr)
        pr = m.predict(Xte)
        preds.append(pr); ys.append(yte)
        tp = m.predict(Xtr)
        train_hits += int(np.sum(np.abs(tp - ytr) <= _TOL)); train_n += len(ytr)
    p = np.concatenate(preds); y = np.concatenate(ys)
    w1 = float(np.mean(np.abs(p - y) <= _TOL))
    train_w1 = train_hits / train_n
    return w1, train_w1 - w1


def _idX(rows, aux):
    return _X(rows), None


def run() -> dict[str, Any]:
    ho, nh, anchor = collect_rows()
    yh = np.array([r["y"] for r in ho]); yn = np.array([r["y"] for r in nh])
    ya = np.array([r["y"] for r in anchor])
    out: dict[str, Any] = {"n": {"heldout": len(ho), "nh": len(nh), "anchor": len(anchor)}}

    # Held-out / NH live baselines are the drift-guard-pinned pool numbers (build_cache rows carry
    # findings but not the FactorVerdict scores grade_factor needs). The ANCHOR baseline IS recomputed
    # on the identical rows (anchor fvs are available) — the fair gate reference.
    eng_anchor = int(np.sum(np.abs(np.array([r["eng"] for r in anchor]) - ya) <= _TOL))
    out["engine_live"] = {"heldout_pinned": 58.6, "nh_pinned": 47.9,
                          "anchor_within1": eng_anchor, "anchor_n": len(anchor)}

    # model grid, LOCO on held-out — identity vs A2, SAME folds
    grid: dict[str, dict] = {}
    for rep, featX in (("identity", _idX), ("a2_token", _a2_X)):
        for l2 in (0.5, 1.0, 2.0, 4.0):
            w1, gap = _loco(ho, featX, lambda l2=l2: LC.OrdinalLogit(l2=l2))
            grid[f"{rep}:ordinal_l2={l2}"] = {"loco": round(100 * w1, 1), "gap": round(100 * gap, 1)}
        for depth in (2, 3):
            w1, gap = _loco(ho, featX, lambda d=depth: LC._tree(d, 8))
            grid[f"{rep}:tree_d{depth}"] = {"loco": round(100 * w1, 1), "gap": round(100 * gap, 1)}
    out["loco_grid"] = grid
    best_id = max((k for k in grid if k.startswith("identity")), key=lambda k: grid[k]["loco"])
    best_a2 = max((k for k in grid if k.startswith("a2_token")), key=lambda k: grid[k]["loco"])
    out["best"] = {"identity": {best_id: grid[best_id]}, "a2_token": {best_a2: grid[best_a2]}}

    # full-fit identity model → anchor GATE + NH single-shot
    Xh = _X(ho)
    if best_id.split(":")[1].startswith("ordinal"):
        l2 = float(best_id.split("l2=")[1]); model = LC.OrdinalLogit(l2=l2).fit(Xh, yh)
    else:
        d = int(best_id.split("tree_d")[1]); model = LC._tree(d, 8).fit(Xh, yh)
    Xa = _X(anchor); ap = model.predict(Xa)
    out["anchor_gate"] = {"n_within1": int(np.sum(np.abs(ap - ya) <= _TOL)), "n": len(anchor),
                          "engine_within1": out["engine_live"]["anchor_within1"],
                          "pass": int(np.sum(np.abs(ap - ya) <= _TOL)) >= out["engine_live"]["anchor_within1"]}
    Xn = _X(nh); npd = model.predict(Xn)
    out["nh_single_shot"] = round(100 * float(np.mean(np.abs(npd - yn) <= _TOL)), 1)
    return out


def main() -> None:
    o = run()
    print(f"increment 33 — identity-preserving learned scorer  (N held-out {o['n']['heldout']}, "
          f"NH {o['n']['nh']}, anchor {o['n']['anchor']})\n")
    el = o["engine_live"]
    print(f"  live engine (synthesis_v2): held-out {el['heldout_pinned']}% (pinned) | "
          f"NH {el['nh_pinned']}% (pinned) | anchor {el['anchor_within1']}/{el['anchor_n']} (on these rows)\n")
    print("  LOCO-CV within-one (identity vs A2 token, same folds; gap = train−test overfit):")
    for k in sorted(o["loco_grid"], key=lambda k: (k.split(":")[0], -o["loco_grid"][k]["loco"])):
        g = o["loco_grid"][k]
        print(f"    {k:26} loco {g['loco']:4.1f}%  (gap {g['gap']:+.1f})")
    bi = list(o["best"]["identity"]); ba = list(o["best"]["a2_token"])
    print(f"\n  BEST identity {bi[0]} = {o['best']['identity'][bi[0]]['loco']}%  vs  "
          f"BEST A2 {ba[0]} = {o['best']['a2_token'][ba[0]]['loco']}%")
    ag = o["anchor_gate"]
    print(f"  anchor GATE: identity {ag['n_within1']}/{ag['n']} within-one "
          f"(engine {ag['engine_within1']}/{ag['n']}) | NH single-shot {o['nh_single_shot']}%")
    if "--json" in sys.argv:
        print("\n" + json.dumps(o, indent=1))


if __name__ == "__main__":
    main()
