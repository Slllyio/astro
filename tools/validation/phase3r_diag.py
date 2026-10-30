"""Phase 3R diagnostic (EXPLORATORY): is the negative P2 a CHART-level selection effect, not timing?

For the same P2 risk sets, compare each member's LIFETIME MD-activation coverage for the set's houses
(share of ages 15-75 under an activating MD lord), ignoring the event date entirely. If cases'
charts are simply less often activated over their whole lives than the control pool's, the risk-set
E inherits that difference with no timing involved. Then: within-person E (case's exposure at the
event minus the case's own lifetime coverage), which removes the person-level term.

Usage:
    py -3.12 -m tools.validation.phase3r_diag --derived E:/astro/data/astro_databank/derived --store E:/astro/data/validation/raman_activation_raman_AB.parquet
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from tools.validation import riskset_timing as rt
from tools.validation.stats import cluster_bootstrap

GRID = np.linspace(15, 75, 61)


def lifetime_cov(store: rt.Store, pid: str, houses, level: str, variant: str = "real") -> float:
    return float(np.mean([rt.exposed(store.tier(pid, a, houses, variant), level) for a in GRID]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--store", type=Path, required=True)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(rt.SEED)
    ev, master, death_age = rt.load_events(a.derived)
    store = rt.Store(a.store)
    ev = ev[ev.person_id.isin(store.data)]
    sets = rt.build_sets(ev, master, death_age, set(store.data), rng)
    for lvl in ("MD", "AD"):
        ss = [s for s in sets if s["level"] == lvl]
        pids = [s["case"] for s in ss]
        for variant in ("real", "placebo"):
            cc = np.array([lifetime_cov(store, s["case"], s["houses"], lvl, variant) for s in ss])
            ck = np.array([np.mean([lifetime_cov(store, c, s["houses"], lvl, variant) for c in s["controls"]]) for s in ss])
            d = cc - ck
            lo, hi = cluster_bootstrap(d, np.array(pids), rng=np.random.default_rng(1), n_boot=500)
            xc = np.array([rt.exposed(store.tier(s["case"], s["age"], s["houses"], variant), lvl) for s in ss], float)
            w = xc - cc                                   # within-person: event-date exposure vs own lifetime
            wlo, whi = cluster_bootstrap(w, np.array(pids), rng=np.random.default_rng(2), n_boot=500)
            print(f"{lvl} {variant:8s} lifetime coverage case-control {d.mean():+.4f} ({lo:+.4f}..{hi:+.4f})   "
                  f"within-person E {w.mean():+.4f} ({wlo:+.4f}..{whi:+.4f})   n={len(ss)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
