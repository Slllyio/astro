"""Static house-verdict validation of the Parashara synthesis on real outcomes (PARASHARA_PREREG.md).

A faithful copy of `tools/raman_saab/astrobank/static_tests.py` with only the pre-registered
differences: one verdict per house (no signification), the locked 5-step ordinal, and the
Nisargayu span as the longevity axis. ORDER OF OPERATIONS (anti-peeking, enforced): the SHAM gate
runs first and stops the run before any real result is printed if it shows a signal.

Usage:
    py -3.12 -m tools.parashara.astrobank.static_tests --raman-root E:/astro/data/astro_databank/derived/raman --store E:/astro/data/astro_databank/derived/parashara
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from tools.raman_saab.astrobank import _stats

#: Locked ordinal (PARASHARA_PREREG.md): denied < difficult < mixed = ordinary < delayed < granted.
ORDINAL = {"denied": 0.0, "difficult": 1.0, "mixed": 2.0, "ordinary": 2.0,
           "delayed": 3.0, "granted": 4.0}          # indeterminate -> missing (dropped)

#: (test_id, case_map, contrast_map|None=corpus control, house|None=longevity, strength)
TESTS = [
    ("H5_children", "H5_CHILDLESS", "H5_PROLIFIC", 5, "core"),
    ("H8_longevity", "H8_SHORTLIFE", "H8_LONGLIFE", None, "core"),
    ("H12_prison", "H12_PRISON", None, 12, "core"),
    ("H7_marriage", "H7_DIVORCED", "H7_LONGMARRIAGE", 7, "supporting"),
    ("H7_widowed", "H7_WIDOWED", None, 7, "supporting"),
    ("H2_wealth", "H2_BANKRUPT", "H2_WEALTHY", 2, "supporting"),
    ("H8_suicide", "H8_SUICIDE", None, 8, "exploratory"),
    ("H8_accident", "H8_ACCIDENT", None, 8, "exploratory"),
    ("H9_father", "H9_FATHER_CHILDHOOD", "H9_FATHER_CHILDHOOD_GOOD", 9, "supporting"),
    ("H4_mother", "H4_MOTHER_CHILDHOOD", "H4_MOTHER_CHILDHOOD_GOOD", 4, "supporting"),
]
_TIERS = ("A", "B")          # primary; tier C held out (pre-registered)
_DIRECTION = "afflicted"     # every test: the case cohort scores LOWER


def _load(raman_root: Path, store: Path):
    labels = pd.read_parquet(raman_root / "labels.parquet")
    pop = pd.read_parquet(raman_root / "store_population.parquet")
    verdicts = pd.read_parquet(store / "verdicts.parquet")
    verdicts["score"] = verdicts.verdict.map(ORDINAL)
    ayur = pd.read_parquet(store / "ayurdaya.parquet").set_index("person_id")
    master = pd.read_parquet(raman_root / "person_master.parquet")[
        ["person_id", "birth_date", "latitude", "quality_tier", "categories_raw"]]
    master["stratum"] = (master.birth_date.str[:3] + "|" + pd.cut(
        master.latitude, bins=[-90, 20, 45, 90], labels=["low", "mid", "high"]).astype(str))
    return labels, pop, verdicts, ayur, master.set_index("person_id")


def _vals(pids, verdicts, house, master):
    ok = master.loc[master.index.isin(pids) & master.quality_tier.isin(_TIERS)]
    sub = verdicts[(verdicts.house == house) & verdicts.person_id.isin(ok.index)]
    merged = sub.merge(ok[["stratum"]], left_on="person_id", right_index=True).dropna(
        subset=["score"])
    return merged.score.to_numpy(), merged.stratum.to_numpy()


def _ayur_vals(pids, ayur, master):
    ok = master.loc[master.index.isin(pids) & master.quality_tier.isin(_TIERS)]
    sub = ayur.loc[ayur.index.isin(ok.index)]
    return sub.total_years.to_numpy(), ok.loc[sub.index].stratum.to_numpy()


def _run_test(cv, cs, kv, ks) -> dict:
    base = _stats.auc_mw(cv, kv, _DIRECTION)
    if not np.isfinite(base["auc"]):
        return base
    lo, hi, se = _stats.bootstrap_auc_ci(cv, kv, _DIRECTION)
    strat = _stats.stratified_auc(cv, cs, kv, ks, _DIRECTION)
    perm = _stats.permutation_p(cv, cs, kv, ks, _DIRECTION)
    return {**base, "ci_lo": lo, "ci_hi": hi, "se": se, **strat, "perm_p": perm}


def _status(r: dict) -> str:
    """The pre-registered pass bar."""
    auc = r.get("auc", float("nan"))
    if not np.isfinite(auc):
        return "n/a"
    if auc >= 0.55:
        return "SUPPORTED"
    if auc > 0.50 and r.get("bh_pass"):
        return "weak signal"
    return "null"


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--raman-root", type=Path, required=True)
    ap.add_argument("--store", type=Path, required=True)
    a = ap.parse_args(argv)
    labels, pop, verdicts, ayur, master = _load(a.raman_root, a.store)
    control = set(pop[pop.is_control].person_id)
    by_map = {m: set(g.person_id) for m, g in labels.groupby("map_id")}
    results: dict[str, dict] = {}

    # 1. SHAM GATE — first, hard stop.
    expat = {p for p in control if "lifestyle : home : expatriate" in
             {t.strip().casefold() for t in str(master.categories_raw.get(p, "")).split(";")}}
    cv, cs = _vals(expat, verdicts, 5, master)
    kv, ks = _vals(control - expat, verdicts, 5, master)
    sham = _run_test(cv, cs, kv, ks)
    results["SHAM_expatriate_H5"] = sham
    sham_null = np.isfinite(sham.get("auc", np.nan)) and sham["ci_lo"] <= 0.5 <= sham["ci_hi"]
    print(f"[sham] expatriate->H5 AUC={sham.get('auc'):.3f} CI=({sham.get('ci_lo'):.3f},"
          f"{sham.get('ci_hi'):.3f}) n={sham.get('n_case')} -> "
          f"{'NULL (gate PASSES)' if sham_null else 'SIGNAL (gate FAILS)'}")
    if not sham_null:
        print("[sham] PIPELINE-VALIDITY GATE FAILED — stopping before any real result is read.")
        (a.store / "static_results.json").write_text(json.dumps(results, indent=2, default=float),
                                                     encoding="utf-8")
        return 1

    # 2. the pre-registered tests
    pvals: dict[str, float] = {}
    for tid, case_map, ctr_map, house, strength in TESTS:
        case = by_map.get(case_map, set())
        ctr = by_map.get(ctr_map, set()) if ctr_map else control
        if house is None:
            cv, cs = _ayur_vals(case, ayur, master)
            kv, ks = _ayur_vals(ctr, ayur, master)
        else:
            cv, cs = _vals(case, verdicts, house, master)
            kv, ks = _vals(ctr, verdicts, house, master)
        r = _run_test(cv, cs, kv, ks)
        r["strength"] = strength
        results[tid] = r
        if strength in ("core", "supporting") and np.isfinite(r.get("perm_p", np.nan)):
            pvals[tid] = r["perm_p"]

    # 3. BH-FDR + specificity matrix (core tests vs all 12 house verdicts)
    for tid, ok_flag in _stats.bh_fdr(pvals, q=0.10).items():
        results[tid]["bh_pass"] = bool(ok_flag)
    for tid, case_map, _c, house, strength in TESTS:
        if strength != "core" or house is None:
            continue
        effs = {}
        for h in range(1, 13):
            c = verdicts[(verdicts.house == h) & verdicts.person_id.isin(by_map[case_map])].score.dropna()
            k = verdicts[(verdicts.house == h) & verdicts.person_id.isin(control)].score.dropna()
            auc = _stats.auc_mw(c.to_numpy(), k.to_numpy(), _DIRECTION)["auc"]
            effs[h] = abs(auc - 0.5) if np.isfinite(auc) else 0.0
        results[tid]["specificity_rank"] = sorted(effs, key=effs.get, reverse=True).index(house) + 1

    # 4. report
    print(f"\n{'test':14} {'strength':11} {'AUC':>6} {'CI':>15} {'strat':>6} {'perm_p':>7} "
          f"{'BH':>3} {'spec':>4} {'n':>5}  status")
    lines = ["# Parashara synthesis — static real-outcome validation (pre-registered)\n"]
    for tid, r in results.items():
        if not np.isfinite(r.get("auc", np.nan)):
            continue
        row = (f"{tid:14} {r.get('strength', 'sham'):11} {r['auc']:>6.3f} "
               f"({r.get('ci_lo', 0):.3f},{r.get('ci_hi', 0):.3f}) "
               f"{r.get('auc_stratified', float('nan')):>6.3f} {r.get('perm_p', float('nan')):>7.4f} "
               f"{'Y' if r.get('bh_pass') else '-':>3} {str(r.get('specificity_rank', '-')):>4} "
               f"{r.get('n_case', 0):>5}  {_status(r) if tid != 'SHAM_expatriate_H5' else 'gate'}")
        print(row)
        lines.append(row)
    (a.store / "static_results.json").write_text(json.dumps(results, indent=2, default=float),
                                                 encoding="utf-8")
    (a.store / "static_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
