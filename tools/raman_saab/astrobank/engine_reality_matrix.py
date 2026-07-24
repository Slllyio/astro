"""Stage 7 — the full ENGINE-vs-REALITY matrix (the house-specific paired-column design).

For every kundali in the bank: the engine's reading of each specific house-signification (one
column) beside that person's REALITY for the matched feature (next column) — across the whole
signification surface (H5 is children AND intellect/creativity; H3 courage; H9 father; H12
foreign-residence; ...). Then the correlation is computed feature-by-feature, plus the doctrine's
own specificity claim: the MATCHED signification should track a feature better than unmatched ones
(the diagonal of the cross-matrix should beat the off-diagonal).

Reality features come from categories (vocations, diagnoses, lifestyle) + dated events (early
parental death, legal trouble). Engine scores come from the Stage-2 verdict store (no recasting).
Pre-registered direction per feature (the `direction` column). Outputs:
  engine_reality_matrix.parquet  — the person-level paired matrix (the artifact)
  matrix_sample.csv              — a human-readable slice (200 people)
  matrix_results.json / matrix_report.md — per-feature matched-sig AUC + diagonal test

Usage: py -3.12 -m tools.raman_saab.astrobank.engine_reality_matrix
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from tools.raman_saab.astrobank._stats import auc_mw, bootstrap_auc_ci

_OUT = Path("data/astro_databank/derived/raman")

#: feature_id -> (kind, pattern, house, signification, direction, contrast_feature|None)
#: direction 'afflicted' = feature-positive people should score LOWER on the matched sig;
#: 'favourable' = higher. contrast=None -> everyone-else in the matrix is the contrast.
FEATURES: dict[str, tuple] = {
    "kids_none":        ("cat", r"family : parenting : kids none", 5, "children", "afflicted", "kids_many"),
    "kids_many":        ("cat", r"family : parenting : kids more than 3", 5, "children", "favourable", "kids_none"),
    "creative_vocation": ("cat", r"vocation : (writers|art :|entertain)", 5, "intellect", "favourable", None),
    "science_vocation": ("cat", r"vocation : science", 5, "intellect", "favourable", None),
    "military":         ("cat", r"vocation : military", 3, "courage", "favourable", None),
    "religion_vocation": ("cat", r"vocation : religion|occult fields", 9, "dharma", "favourable", None),
    "expatriate":       ("cat", r"lifestyle : home : expatriate", 12, "foreign_residence", "favourable", None),
    "major_disease":    ("cat", r"diagnoses : major diseases", 6, "disease_chronic", "afflicted", None),
    "divorced":         ("cat", r"family : relationship : number of divorces", 7, "marital_happiness", "afflicted", "long_marriage"),
    "long_marriage":    ("cat", r"family : relationship : marriage more than 15 yrs", 7, "marital_happiness", "favourable", "divorced"),
    "widowed":          ("cat", r"family : relationship : widowed", 7, "coverture", "afflicted", None),
    "wealthy":          ("cat", r"lifestyle : financial : wealthy", 2, "wealth", "favourable", "bankrupt"),
    "bankrupt":         ("cat", r"lifestyle : financial : loss - bankruptcy", 2, "wealth", "afflicted", "wealthy"),
    "prison":           ("cat", r"passions : criminal perpetrator : prison sentence", 12, "incarceration", "afflicted", None),
    "long_life":        ("cat", r"personal : death : long life", 8, "longevity", "favourable", "short_life"),
    "short_life":       ("cat", r"personal : death : short life", 8, "longevity", "afflicted", "long_life"),
    "suicide":          ("cat", r"personal : death : suicide", 8, "death", "afflicted", None),
    "awards_top":       ("cat", r"notable : awards", 10, "status_honour", "favourable", None),
    "eyes_problem":     ("cat", r"body part problems : eyes", 2, "vision", "afflicted", None),
    "inheritance":      ("cat", r"gain - inheritance", 11, "gains", "favourable", None),
    "father_died_early": ("event", "Death of Father", 9, "father", "afflicted", None),
    "mother_died_early": ("event", "Death of Mother", 4, "mother", "afflicted", None),
    "legal_trouble":    ("event", r"legal", 6, "enemies", "afflicted", None),
}

_ORD = {"afflicted": 0.0, "mixed": 1.0, "favourable": 2.0}
_DEG = {("afflicted", "strong"): 0.0, ("afflicted", "moderate"): 0.17, ("afflicted", "mild"): 0.33,
        ("favourable", "mild"): 1.67, ("favourable", "moderate"): 1.83, ("favourable", "strong"): 2.0}


def build_matrix() -> pd.DataFrame:
    master = pd.read_parquet(_OUT / "person_master.parquet").set_index("person_id")
    pop = pd.read_parquet(_OUT / "store_population.parquet")
    verd = pd.read_parquet(_OUT / "verdicts.parquet")
    pids = sorted(set(pop.person_id) & set(master[master.quality_tier.isin(["A", "B"])].index))

    # engine side: one column per (house, signification), continuous score
    verd = verd[verd.person_id.isin(pids)].copy()
    verd["score"] = [_DEG.get((r.verdict, r.degree), _ORD.get(r.verdict, np.nan))
                     for r in verd.itertuples()]
    eng = verd.pivot_table(index="person_id", columns=["house", "signification"],
                           values="score", aggfunc="first")
    eng.columns = [f"eng_H{h}_{s}" for h, s in eng.columns]

    # reality side
    cats = master.loc[eng.index, "categories_raw"].str.lower()
    ev = pd.read_parquet(_OUT / "person_events.parquet")
    by = master.birth_date.str[:4].astype(int)
    real = pd.DataFrame(index=eng.index)
    for fid, (kind, pat, *_rest) in FEATURES.items():
        if kind == "cat":
            real[f"real_{fid}"] = cats.str.contains(pat, regex=True).fillna(False).astype(int)
        else:
            hit = set()
            for r in ev.itertuples():
                if pat == "legal":
                    match = "legal" in r.event_root.lower()
                else:
                    match = r.event_root == pat
                if match and r.person_id in by.index:
                    if pat.startswith("Death of"):
                        if 0 <= r.event_year - by.get(r.person_id, 0) <= 21:
                            hit.add(r.person_id)
                    else:
                        hit.add(r.person_id)
            real[f"real_{fid}"] = real.index.isin(hit).astype(int)

    matrix = pd.concat([eng, real], axis=1)
    matrix.to_parquet(_OUT / "engine_reality_matrix.parquet", engine="pyarrow", compression="zstd")
    # the human-readable paired-column sample the design asks for
    cols = []
    for fid, (_k, _p, h, sig, _d, _c) in FEATURES.items():
        ec = f"eng_H{h}_{sig}"
        if ec in matrix.columns:
            cols += [ec, f"real_{fid}"]
    seen = list(dict.fromkeys(cols))
    sample = matrix[seen].head(200).round(2)
    sample.insert(0, "name", master.loc[sample.index, "name_display"].values)
    sample.to_csv(_OUT / "matrix_sample.csv", encoding="utf-8")
    return matrix


def analyze(matrix: pd.DataFrame) -> None:
    results: dict[str, dict] = {}
    eng_cols = [c for c in matrix.columns if c.startswith("eng_")]
    diag_aucs, offdiag_aucs = [], []
    print(f"{'feature':20} {'matched sig':24} {'n+':>6} {'AUC':>6} {'CI':>16} {'rank':>5}")
    for fid, (_k, _p, h, sig, direction, contrast) in FEATURES.items():
        ec, rc = f"eng_H{h}_{sig}", f"real_{fid}"
        if ec not in matrix.columns:
            continue
        pos = matrix[matrix[rc] == 1]
        neg = matrix[(matrix[f"real_{contrast}"] == 1)] if contrast else matrix[matrix[rc] == 0]
        case = pos[ec].dropna().to_numpy()
        ctr = neg[ec].dropna().to_numpy()
        if len(case) < 25 or len(ctr) < 25:
            continue
        r = auc_mw(case, ctr, direction)
        lo, hi, se = bootstrap_auc_ci(case, ctr, direction, n_boot=400)
        # specificity: this reality feature vs EVERY engine signification
        aucs_all = {}
        for c in eng_cols:
            cv, kv = pos[c].dropna().to_numpy(), neg[c].dropna().to_numpy()
            if len(cv) >= 25 and len(kv) >= 25:
                aucs_all[c] = abs(auc_mw(cv, kv, direction)["auc"] - 0.5)
        rank = (sorted(aucs_all, key=aucs_all.get, reverse=True).index(ec) + 1
                if ec in aucs_all else None)
        diag_aucs.append(abs(r["auc"] - 0.5))
        offdiag_aucs.extend(v for c, v in aucs_all.items() if c != ec)
        results[fid] = {"house": h, "sig": sig, "auc": r["auc"], "ci": [lo, hi],
                        "n_pos": len(case), "n_contrast": len(ctr), "spec_rank": rank,
                        "n_sigs_ranked": len(aucs_all)}
        print(f"{fid:20} H{h}_{sig:22} {len(case):>6} {r['auc']:>6.3f} "
              f"({lo:.3f},{hi:.3f})   {str(rank):>4}/{len(aucs_all)}")

    diag, off = float(np.mean(diag_aucs)), float(np.mean(offdiag_aucs))
    supported = sum(1 for r in results.values() if r["auc"] >= 0.55 and r["ci"][0] > 0.5)
    weak = sum(1 for r in results.values() if 0.5 < r["ci"][0] and r["auc"] < 0.55)
    print(f"\n[matrix] features tested: {len(results)}   supported(AUC>=.55,CI>.5): {supported}   "
          f"weak(CI>.5): {weak}")
    print(f"[matrix] DIAGONAL mean|AUC-.5|={diag:.4f}   OFF-DIAGONAL mean={off:.4f}   "
          f"(doctrine predicts diagonal >> off-diagonal)")
    (_OUT / "matrix_results.json").write_text(
        json.dumps({"features": results, "diagonal_mean_effect": diag,
                    "offdiagonal_mean_effect": off}, indent=2, default=float), encoding="utf-8")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    matrix = build_matrix()
    print(f"[matrix] built: {matrix.shape[0]} persons x {matrix.shape[1]} columns "
          f"({sum(1 for c in matrix.columns if c.startswith('eng_'))} engine sigs, "
          f"{sum(1 for c in matrix.columns if c.startswith('real_'))} reality features)")
    analyze(matrix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
