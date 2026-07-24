"""Stage 3 — static house-verdict validation against real outcomes (pre-registered protocol).

ORDER OF OPERATIONS (anti-peeking, enforced by the script): the SHAM mapping (expatriate -> H5
children, expected null) is scored FIRST; if the sham shows a "signal" the run stops before any
Tier-1 result is printed (pipeline/confound bug — fix before reading). Then core tests, supporting
tests, the off-target specificity matrix, BH-FDR across the family, and the report.

Metrics per test (see METHODOLOGY.md): oriented AUC (MW-U one-sided in the pre-registered
direction) + bootstrap CI + stratified AUC (decade x latitude band) + within-stratum permutation p.
Primary tier = A+B; sensitivity = A-only, A+B+C.

Usage: py -3.12 -m tools.raman_saab.astrobank.static_tests
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from tools.raman_saab.astrobank import _stats

_OUT = Path("data/astro_databank/derived/raman")

_ORD = {"afflicted": 0.0, "mixed": 1.0, "favourable": 2.0}
#: degree refines the ordinal WITHIN a verdict band (pre-registered mechanical refinement).
_DEG_ADJ = {("afflicted", "strong"): 0.0, ("afflicted", "moderate"): 0.17, ("afflicted", "mild"): 0.33,
            ("mixed", "strong"): 1.0, ("mixed", "moderate"): 1.0, ("mixed", "mild"): 1.0,
            ("favourable", "mild"): 1.67, ("favourable", "moderate"): 1.83,
            ("favourable", "strong"): 2.0}

#: (test_id, case_map, contrast_map|None=corpus control, house, signification, direction, tier)
TESTS = [
    ("H5_children", "H5_CHILDLESS", "H5_PROLIFIC", 5, "children", "afflicted", "core"),
    ("H8_ayurdaya", "H8_SHORTLIFE", "H8_LONGLIFE", None, None, "afflicted", "core"),  # numeric axis
    ("H12_prison", "H12_PRISON", None, 12, "incarceration", "afflicted", "core"),
    ("H7_marriage", "H7_DIVORCED", "H7_LONGMARRIAGE", 7, "marital_happiness", "afflicted", "supporting"),
    ("H7_widowed", "H7_WIDOWED", None, 7, "coverture", "afflicted", "supporting"),
    ("H2_wealth", "H2_BANKRUPT", "H2_WEALTHY", 2, "wealth", "afflicted", "supporting"),
    ("H8_suicide", "H8_SUICIDE", None, 8, "death", "afflicted", "exploratory"),
    ("H8_accident", "H8_ACCIDENT", None, 8, "death", "afflicted", "exploratory"),
]

_PRIMARY_TIERS = ("A", "B")


def _load():
    d = {n: pd.read_parquet(_OUT / f"{n}.parquet")
         for n in ("labels", "verdicts", "ayurdaya", "house_rollups", "store_population")}
    master = pd.read_parquet(_OUT / "person_master.parquet")[
        ["person_id", "birth_date", "latitude", "quality_tier", "categories_raw"]]
    master["decade"] = master.birth_date.str[:3]
    master["latband"] = pd.cut(master.latitude, bins=[-90, 20, 45, 90],
                               labels=["low", "mid", "high"]).astype(str)
    master["stratum"] = master.decade + "|" + master.latband
    return d, master.set_index("person_id")


def _score_frame(verdicts: pd.DataFrame) -> pd.DataFrame:
    v = verdicts.copy()
    v["score"] = [_DEG_ADJ.get((r.verdict, r.degree), _ORD.get(r.verdict, np.nan))
                  for r in v.itertuples()]
    return v


def _vals(pids, scored, house, sig, master, tiers):
    ok = master.loc[master.index.isin(pids) & master.quality_tier.isin(tiers)]
    sub = scored[(scored.house == house) & (scored.signification == sig)
                 & scored.person_id.isin(ok.index)]
    merged = sub.merge(ok[["stratum"]], left_on="person_id", right_index=True)
    merged = merged.dropna(subset=["score"])   # insufficient-evidence verdicts carry no ordinal
    return merged.score.to_numpy(), merged.stratum.to_numpy(), merged.person_id.to_numpy()


def _run_test(case_vals, case_str, ctr_vals, ctr_str, direction) -> dict:
    base = _stats.auc_mw(case_vals, ctr_vals, direction)
    if not np.isfinite(base["auc"]):
        return base
    lo, hi, se = _stats.bootstrap_auc_ci(case_vals, ctr_vals, direction)
    strat = _stats.stratified_auc(case_vals, case_str, ctr_vals, ctr_str, direction)
    perm = _stats.permutation_p(case_vals, case_str, ctr_vals, ctr_str, direction)
    return {**base, "ci_lo": lo, "ci_hi": hi, "se": se, **strat, "perm_p": perm}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    d, master = _load()
    labels, pop = d["labels"], d["store_population"]
    scored = _score_frame(d["verdicts"])
    control_pids = set(pop[pop.is_control].person_id)
    by_map = {m: set(g.person_id) for m, g in labels.groupby("map_id")}
    results: dict[str, dict] = {}

    # ══ 1. SHAM GATE (must run + pass FIRST) ═════════════════════════════════
    expat = {pid for pid in control_pids
             if "lifestyle : home : expatriate" in
             {t.strip().casefold() for t in str(master.categories_raw.get(pid, "")).split(";")}}
    non_expat = control_pids - expat
    cv, cs, _ = _vals(expat, scored, 5, "children", master, _PRIMARY_TIERS)
    kv, ks, _ = _vals(non_expat, scored, 5, "children", master, _PRIMARY_TIERS)
    sham = _run_test(cv, cs, kv, ks, "afflicted")
    results["SHAM_expatriate_H5"] = sham
    sham_null = np.isfinite(sham.get("auc", np.nan)) and sham["ci_lo"] <= 0.5 <= sham["ci_hi"]
    print(f"[sham] expatriate->H5 AUC={sham.get('auc'):.3f} "
          f"CI=({sham.get('ci_lo'):.3f},{sham.get('ci_hi'):.3f}) n={sham.get('n_case')} "
          f"-> {'NULL (gate PASSES)' if sham_null else 'SIGNAL (gate FAILS)'}")
    if not sham_null:
        print("[sham] PIPELINE-VALIDITY GATE FAILED — stopping before Tier-1 is read.")
        (_OUT / "static_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        return 1

    # ══ 2. core + supporting + exploratory tests ═════════════════════════════
    ayur = d["ayurdaya"].set_index("person_id")
    pvals: dict[str, float] = {}
    for tid, case_map, ctr_map, house, sig, direction, strength in TESTS:
        case_pids = by_map.get(case_map, set())
        ctr_pids = by_map.get(ctr_map, set()) if ctr_map else control_pids
        if tid == "H8_ayurdaya":
            def _ay(pids):
                ok = master.loc[master.index.isin(pids) & master.quality_tier.isin(_PRIMARY_TIERS)]
                sub = ayur.loc[ayur.index.isin(ok.index)]
                return sub.total_years.to_numpy(), ok.loc[sub.index].stratum.to_numpy()
            cv, cs = _ay(case_pids)
            kv, ks = _ay(ctr_pids)
        else:
            cv, cs, _ = _vals(case_pids, scored, house, sig, master, _PRIMARY_TIERS)
            kv, ks, _ = _vals(ctr_pids, scored, house, sig, master, _PRIMARY_TIERS)
        r = _run_test(cv, cs, kv, ks, direction)
        r["strength"] = strength
        results[tid] = r
        if strength in ("core", "supporting") and np.isfinite(r.get("perm_p", np.nan)):
            pvals[tid] = r["perm_p"]

    # longevity extras: class match + Spearman vs actual death age
    short_long = by_map["H8_SHORTLIFE"] | by_map["H8_LONGLIFE"]
    ok = master.loc[master.index.isin(short_long) & master.quality_tier.isin(_PRIMARY_TIERS)]
    sub = ayur.loc[ayur.index.isin(ok.index)]
    is_long = sub.index.isin(by_map["H8_LONGLIFE"])
    cls_match = float(np.mean(np.where(is_long, sub.longevity_class == "purna",
                                       sub.longevity_class == "alpa")))
    results["H8_class_match"] = {"rate": cls_match, "n": int(len(sub)),
                                 "note": "purna for long-life / alpa for short-life"}

    # ══ 3. BH-FDR + specificity matrix ═══════════════════════════════════════
    passed = _stats.bh_fdr(pvals, q=0.10)
    for tid, ok_flag in passed.items():
        results[tid]["bh_pass"] = bool(ok_flag)
    rollups = d["house_rollups"].copy()
    rollups["score"] = rollups.rollup.map(_ORD)
    spec: dict[str, dict] = {}
    for tid, case_map, _c, house, _s, direction, strength in TESTS:
        if strength != "core" or house is None:
            continue
        case_pids = by_map[case_map]
        effs = {}
        for h in range(1, 13):
            csub = rollups[(rollups.house == h) & rollups.person_id.isin(case_pids)].score.dropna()
            ksub = rollups[(rollups.house == h) & rollups.person_id.isin(control_pids)].score.dropna()
            a = _stats.auc_mw(csub.to_numpy(), ksub.to_numpy(), direction)["auc"]
            effs[h] = abs(a - 0.5) if np.isfinite(a) else 0.0
        rank = sorted(effs, key=effs.get, reverse=True).index(house) + 1
        spec[tid] = {"mapped_house_rank": rank, "effects": {str(h): round(e, 4) for h, e in effs.items()}}
        results[tid]["specificity_rank"] = rank

    # ══ 4. report ════════════════════════════════════════════════════════════
    lines = ["# Astrobank static validation — results\n"]
    print(f"\n{'test':14} {'str':11} {'AUC':>6} {'CI':>15} {'strat':>6} {'perm_p':>7} {'BH':>3} {'spec':>4} {'n':>5}")
    for tid, r in results.items():
        if "auc" not in r or not np.isfinite(r.get("auc", np.nan)):
            continue
        ci = f"({r.get('ci_lo', 0):.3f},{r.get('ci_hi', 0):.3f})"
        row = (f"{tid:14} {r.get('strength','-'):11} {r['auc']:>6.3f} {ci:>15} "
               f"{r.get('auc_stratified', float('nan')):>6.3f} {r.get('perm_p', float('nan')):>7.4f} "
               f"{'Y' if r.get('bh_pass') else '-':>3} {str(r.get('specificity_rank','-')):>4} "
               f"{r.get('n_case', 0):>5}")
        print(row)
        lines.append(row)
    (_OUT / "static_results.json").write_text(
        json.dumps({"results": results, "specificity": spec}, indent=2, default=float),
        encoding="utf-8")
    (_OUT / "static_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[static] class-match={cls_match:.1%} (n={len(sub)})   wrote static_results.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
