"""Equivalence verdicts (addendum 1, item 2) from the stored results and null runs.

For each result: excess = observed Δ − null mean; its 95% interval = bootstrap interval of Δ shifted by
the null mean. BOUNDED_NULL if the whole excess interval lies below the SESOI, UNDERPOWERED if not,
SIGNAL if the pass rule (p < 0.025 and excess >= SESOI) holds.

Usage:
    python -m tools.predictive.verdicts --out /mnt/project-files/astro/predictive
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def verdict(obs: float, ci: list[float], null: list[float], sesoi: float) -> dict:
    nm = float(np.mean(null))
    p = (1 + sum(v >= obs for v in null)) / (1 + len(null))
    lo, hi = ci[0] - nm, ci[1] - nm
    v = "SIGNAL" if (p < 0.025 and obs - nm >= sesoi) else ("BOUNDED_NULL" if hi < sesoi else "UNDERPOWERED")
    return {"observed": obs, "null_mean": nm, "excess": obs - nm, "excess_ci95": [lo, hi], "p": p,
            "mde80": float(2.8 * np.std(null)), "verdict": v}


def _runs(path: Path) -> list[dict]:
    seen = {}
    for x in path.read_text().splitlines():
        if x.strip():
            r = json.loads(x)
            seen.setdefault(r["run"], r)
    return list(seen.values())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    o = a.out
    res = {}
    # Task A (corrected, addendum 3): per target
    A = json.loads((o / "phase2_A_covered_results.json").read_text())["observed"]
    nullA = _runs(o / "phase2_A_covered_N2_runs.jsonl")
    res["A_targets"] = {t: verdict(r["auc_full"] - r["auc_base"], r["ci95_d_full"], [n["targets"][t] for n in nullA], 0.02)
                        for t, r in A["targets"].items()}
    # Task B: pooled, areas, tiers
    B = json.loads((o / "phase2_B_results.json").read_text())
    cis = json.loads((o / "phase2_B_ci_by_area.json").read_text())
    nullB = _runs(o / "phase2_B_N3_runs.jsonl")
    res["B_pooled"] = verdict(B["observed"]["pooled"]["d_full"], B["ci95_d_full"], [n["pooled"]["d_full"] for n in nullB], 0.03)
    for key in ("areas", "tiers"):
        res[f"B_{key}"] = {k: verdict(v["d_full"], v["ci95"], [n[key][k]["d_full"] for n in nullB], 0.03)
                           | {"n_sets": v["n_sets"]} for k, v in cis[key].items()}
    (o / "verdicts.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        items = {"": v} if "verdict" in v else v
        for name, r in items.items():
            print(f"{k:10s} {name:22s} obs {r['observed']:+.4f} null {r['null_mean']:+.4f} excess {r['excess']:+.4f} "
                  f"[{r['excess_ci95'][0]:+.4f},{r['excess_ci95'][1]:+.4f}] p {r['p']:.3f} {r['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
