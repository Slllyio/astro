"""Stage 6 — the CORRECTED questions (pre-registered v3, METHODOLOGY.md).

1. RULE-LEVEL ENRICHMENT: each evaluable engine rule on an outcome-linked signification is tested
   as the conditional claim Raman actually made: P(outcome | rule fires) vs the base rate in the
   labeled universe. (The Stage-3 cohort AUC provably could not see rare-conditional effects, and
   its verdict instrument is near-constant on ordinary charts for children/incarceration/death.)
2. DEATH-WINDOW CONTAINMENT: the doctrinal death-timing instrument — `death_window(chart)`
   (span-anchored maraka bhuktis) — vs the paired per-person null expectation.

Two phases:  --extract  (chart pass: rule fires + death windows -> parquet)   then   --analyze.
Usage:
    py -3.12 -m tools.raman_saab.astrobank.rule_enrichment --extract [--workers N]
    py -3.12 -m tools.raman_saab.astrobank.rule_enrichment --analyze
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from tools.raman_saab.astrobank._worker import init_worker

_OUT = Path("data/astro_databank/derived/raman")
_SIGS = {"children", "incarceration", "marital_happiness", "coverture", "spouse",
         "wealth", "death", "longevity"}

#: outcome -> (case_map, contrast_map|None->control, registered polarity that should enrich it)
OUTCOMES = {
    "childless": ("H5_CHILDLESS", "H5_PROLIFIC", "malefic", "children"),
    "prolific": ("H5_PROLIFIC", "H5_CHILDLESS", "benefic", "children"),
    "prison": ("H12_PRISON", None, "malefic", "incarceration"),
    "divorced": ("H7_DIVORCED", "H7_LONGMARRIAGE", "malefic", "marital_happiness"),
    "long_marriage": ("H7_LONGMARRIAGE", "H7_DIVORCED", "benefic", "marital_happiness"),
    "widowed": ("H7_WIDOWED", None, "malefic", "coverture"),
    "bankrupt": ("H2_BANKRUPT", "H2_WEALTHY", "malefic", "wealth"),
    "wealthy": ("H2_WEALTHY", "H2_BANKRUPT", "benefic", "wealth"),
    "suicide": ("H8_SUICIDE", None, "malefic", "death"),
}


def _rule_index():
    from app.raman_saab.doctrine.rule_sets import ALL_RULES
    return [(r.id, r.signification, r.polarity) for r in ALL_RULES
            if r.kind == "evaluable" and r.condition is not None and r.signification in _SIGS]


def _extract_one(row: dict) -> dict | None:
    try:
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.chart.model import BirthData
        from app.raman_saab.doctrine.conditions import EvalContext
        from app.raman_saab.doctrine.rule_sets import ALL_RULES
        from app.raman_saab.primitives import vimshottari as vim

        pid = row["person_id"]
        y, mo, d = (int(x) for x in row["birth_date"].split("-"))
        t = row["birth_time"]
        chart = cast_chart(BirthData(name=pid, year=y, month=mo, day=d, hour=int(t[:2]),
                                     minute=int(t[3:5]), tz_offset=float(row["tz_offset"]),
                                     latitude=float(row["latitude"]),
                                     longitude=float(row["longitude"])), ayanamsa="raman")
        ctx = EvalContext(chart)
        fires = []
        for r in ALL_RULES:
            if (r.kind == "evaluable" and r.condition is not None and r.signification in _SIGS):
                try:
                    if r.condition.evaluate(ctx):
                        fires.append({"person_id": pid, "rule_id": r.id})
                except Exception:  # noqa: BLE001
                    continue
        dw = [{"person_id": pid, "jd_start": w.start_jd, "jd_end": w.end_jd}
              for w in vim.death_window(chart)]
        return {"fires": fires, "windows": dw}
    except Exception:  # noqa: BLE001
        return None


def extract(workers: int) -> int:
    pop = pd.read_parquet(_OUT / "store_population.parquet")
    master = pd.read_parquet(_OUT / "person_master.parquet").set_index("person_id")
    sel = master.loc[master.index.isin(pop.person_id)].reset_index()
    rows = sel[["person_id", "birth_date", "birth_time", "tz_offset",
                "latitude", "longitude"]].to_dict("records")
    print(f"[extract] {len(rows)} charts, {len(_rule_index())} outcome-linked evaluable rules")
    fires, windows, fails = [], [], 0
    with mp.Pool(processes=workers, initializer=init_worker) as pool:
        for i, res in enumerate(pool.imap_unordered(_extract_one, rows, chunksize=200)):
            if res is None:
                fails += 1
                continue
            fires.extend(res["fires"])
            windows.extend(res["windows"])
            if (i + 1) % 4000 == 0:
                print(f"[extract] {i+1}/{len(rows)}")
    pd.DataFrame(fires).to_parquet(_OUT / "rule_fires.parquet", engine="pyarrow",
                                   compression="zstd", index=False)
    pd.DataFrame(windows).to_parquet(_OUT / "death_windows.parquet", engine="pyarrow",
                                     compression="zstd", index=False)
    print(f"[extract] fires={len(fires)}  death-windows={len(windows)}  failures={fails}")
    return 0


def analyze() -> int:
    from scipy import stats
    from tools.raman_saab.astrobank._stats import bh_fdr

    labels = pd.read_parquet(_OUT / "labels.parquet")
    fires = pd.read_parquet(_OUT / "rule_fires.parquet")
    pop = pd.read_parquet(_OUT / "store_population.parquet")
    master = pd.read_parquet(_OUT / "person_master.parquet").set_index("person_id")
    tier_ok = set(master[master.quality_tier.isin(["A", "B"])].index) & set(pop.person_id)
    by_map = {m: set(g.person_id) & tier_ok for m, g in labels.groupby("map_id")}
    control = set(pop[pop.is_control].person_id) & tier_ok
    fired_by_rule = {r: set(g.person_id) for r, g in fires.groupby("rule_id")}
    rule_meta = {rid: (sig, pol) for rid, sig, pol in _rule_index()}

    rows, pvals = [], {}
    for outcome, (case_map, contrast_map, want_pol, sig) in OUTCOMES.items():
        case = by_map.get(case_map, set())
        universe = case | (by_map.get(contrast_map, set()) if contrast_map else control)
        if len(case) < 20 or len(universe) < 60:
            continue
        base = len(case) / len(universe)
        for rid, (rsig, rpol) in rule_meta.items():
            if rsig != sig or rpol != want_pol:
                continue
            fired = fired_by_rule.get(rid, set()) & universe
            n, k = len(fired), len(fired_by_rule.get(rid, set()) & case)
            if n < 30:
                continue
            enr = (k / n) / base if base else float("nan")
            p = float(stats.binomtest(k, n, base).pvalue)
            key = f"{outcome}:{rid}"
            rows.append({"outcome": outcome, "rule_id": rid, "n_fired": n, "k_case": k,
                         "rate": k / n, "base": base, "enrichment": enr, "p": p})
            pvals[key] = p
    passed = bh_fdr(pvals, q=0.10)
    for r in rows:
        r["bh_pass"] = bool(passed.get(f"{r['outcome']}:{r['rule_id']}"))
    res = pd.DataFrame(rows).sort_values("p")
    res.to_parquet(_OUT / "rule_enrichment.parquet", engine="pyarrow", index=False)

    print(f"[enrichment] {len(res)} rule-outcome tests (n_fired>=30), "
          f"{int(res.bh_pass.sum())} pass BH q=0.10")
    print(res.head(15).to_string(index=False,
          formatters={"rate": "{:.3f}".format, "base": "{:.3f}".format,
                      "enrichment": "{:.2f}".format, "p": "{:.4f}".format}))

    # ── death-window containment (doctrinal instrument) ──────────────────────
    dw = pd.read_parquet(_OUT / "death_windows.parquet")
    ev = pd.read_parquet(_OUT / "person_events.parquet")
    import swisseph as swe
    def _jd(y, m, d): return swe.julday(int(y), max(1, int(m)), max(1, int(d)), 12.0, swe.GREG_CAL)
    YEAR = 365.2425
    deaths = {}
    for r in ev.itertuples():
        low = f"{r.event_root} {r.event_subtype}".lower()
        if r.event_root.startswith("Death") and "death of" not in low and r.person_id in tier_ok:
            deaths.setdefault(r.person_id, _jd(r.event_year, r.event_month, r.event_day))
    win_by = {p: g[["jd_start", "jd_end"]].to_numpy() for p, g in dw.groupby("person_id")}
    obs, exp = [], []
    for pid, djd in deaths.items():
        if pid not in master.index:
            continue
        b = master.loc[pid].birth_date
        bjd = _jd(int(b[:4]), int(b[5:7]), int(b[8:10]))
        lo, hi = bjd + 15 * YEAR, djd
        if hi - lo < 5 * YEAR:
            continue
        wins = win_by.get(pid, np.empty((0, 2)))
        hit = bool(len(wins)) and bool(np.any((wins[:, 0] <= djd) & (djd < wins[:, 1])))
        ov = float(np.clip(np.minimum(wins[:, 1], hi) - np.maximum(wins[:, 0], lo), 0, None).sum()) \
            if len(wins) else 0.0
        obs.append(float(hit))
        exp.append(ov / (hi - lo))
    obs_a, exp_a = np.asarray(obs), np.asarray(exp)
    lift = float(obs_a.mean() - exp_a.mean())
    rng = np.random.default_rng(3)
    boots = [float(np.mean(obs_a[idx]) - np.mean(exp_a[idx]))
             for idx in (rng.integers(0, len(obs_a), len(obs_a)) for _ in range(2000))]
    lo95, hi95 = np.percentile(boots, [2.5, 97.5])
    print(f"\n[death_window] n={len(obs_a)} deaths  observed-in-window={obs_a.mean():.3f}  "
          f"expected(null)={exp_a.mean():.3f}  lift={lift:+.3f}  CI=({lo95:+.3f},{hi95:+.3f})")
    out = {"death_window": {"n": len(obs_a), "observed": float(obs_a.mean()),
                            "expected": float(exp_a.mean()), "lift": lift,
                            "ci": [float(lo95), float(hi95)]},
           "n_rule_tests": int(len(res)), "n_bh_pass": int(res.bh_pass.sum())}
    (_OUT / "enrichment_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (mp.cpu_count() or 4) - 2))
    a = ap.parse_args(argv)
    if a.extract:
        return extract(a.workers)
    if a.analyze:
        return analyze()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
