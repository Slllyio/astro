"""Phase 3 deep look: EXPLORATORY variants on the same risk sets (post-hoc; confirmatory result is
PHASE3_RESULTS.md). Any variant that looks positive here is a hypothesis for a new pre-registration
confirmed on holdout C1, never a finding. Holm across the battery.

Variants (AD level, day-dated events, same 2,365 risk sets as P1):
  V_tier4      only Raman's 'par excellence' (both lords influence + associated)
  V_ad_lord    the AD lord influences the house (tiers 2/3/4)
  V_lord       strict lordship: the MD or AD lord IS the lord of the house (death: of the 2nd/7th)
  V_lord_both  both MD and AD lords are among the house's lord + occupants
  V_by_tier    case vs control distribution over tiers 0-4 (descriptive)

Usage:
    py -3.12 -m tools.validation.phase3_deep --derived E:/astro/data/astro_databank/derived --store E:/astro/data/validation/activation_lahiri_AB.parquet --out docs/validation/PHASE3_DEEP.md
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
from pathlib import Path

import numpy as np
import pandas as pd

from tools.validation import riskset_timing as rt


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--store", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(rt.SEED)
    ev, master, death_age = rt.load_events(a.derived)
    store = rt.Store(a.store)
    ev = ev[ev.person_id.isin(store.data)]
    sets = [s for s in rt.build_sets(ev, master, death_age, set(store.data), rng) if s["level"] == "AD"]
    pids = [s["case"] for s in sets]
    members = sorted({p for s in sets for p in (s["case"], *s["controls"])})

    # natal: lagna + planet signs, for the lordship variants
    m = pd.read_parquet(a.derived / "raman" / "person_master.parquet").set_index("person_id")
    rows = [dict(m.loc[p, ["birth_date", "birth_time", "tz_offset", "latitude", "longitude"]], person_id=p)
            for p in members]
    with mp.Pool(12) as pool:
        natal = {r["person_id"]: r for r in pool.map(rt._natal_signs, rows, chunksize=200) if r}
    from app.parashara.primitives.relationships import SIGN_LORDS

    lords = pd.read_parquet(a.store, columns=["person_id", "variant", "md", "ad", "start_age", "end_age"],
                            filters=[("variant", "=", "real")])
    lords = lords[lords.person_id.isin(set(members))].sort_values("start_age")
    per = {p: (g.start_age.to_numpy(), g.end_age.to_numpy(), g.md.to_numpy(), g.ad.to_numpy())
           for p, g in lords.groupby("person_id")}

    def running(p, age):
        s, e, md, ad = per[p]
        i = int(np.searchsorted(s, age, side="right")) - 1
        return (md[i], ad[i]) if 0 <= i and age < e[i] else (None, None)

    def house_set(s):
        return (2, 7) if s["houses"] == rt.MARAKA else s["houses"]

    def lord_of(p, h):
        n = natal[p]
        return SIGN_LORDS[(n["asc"] - 1 + h - 1) % 12 + 1]

    def occupants(p, h):
        n = natal[p]
        hs = (n["asc"] - 1 + h - 1) % 12 + 1
        return {pl for pl, sg in n["signs"].items() if sg == hs}

    def variant(fn):
        xc, xk, keep = [], [], []
        for i, s in enumerate(sets):
            mem = [s["case"], *s["controls"]]
            if not all(p in natal and p in per for p in mem):
                continue
            x = [fn(p, s) for p in mem]
            xc.append(x[0]); xk.append(x[1:]); keep.append(i)
        return np.array(xc, float), np.array(xk, float), [pids[i] for i in keep]

    def v_lord(p, s):
        md, ad = running(p, s["age"])
        L = {lord_of(p, h) for h in house_set(s)}
        return md in L or ad in L

    def v_lord_both(p, s):
        md, ad = running(p, s["age"])
        sig = set().union(*({lord_of(p, h)} | occupants(p, h) for h in house_set(s)))
        return md in sig and ad in sig

    tier = lambda p, s: store.tier(p, s["age"], s["houses"])  # noqa: E731
    variants = {
        "V_tier4": lambda p, s: tier(p, s) == 4,
        "V_ad_lord": lambda p, s: tier(p, s) in (2, 3, 4),
        "V_lord": v_lord,
        "V_lord_both": v_lord_both,
    }
    res = {}
    for name, fn in variants.items():
        xc, xk, pp = variant(fn)
        res[name] = rt.excess(xc, xk, pp, rng)
    adj = rt.holm({k: v["p"] for k, v in res.items()})

    # tier distribution, cases vs controls
    tc, tk = np.zeros(6), np.zeros(6)
    for s in sets:
        mem = [s["case"], *s["controls"]]
        t = [store.tier(p, s["age"], s["houses"]) for p in mem]
        tc[t[0] + 1] += 1
        for x in t[1:]:
            tk[x + 1] += 1
    L = ["# Phase 3 deep look: exploratory variants (post-hoc, NOT confirmatory)", "",
         "Same 2,365 AD-level risk sets as P1. Holm across the battery. A positive variant here would only "
         "be a hypothesis for a new pre-registration confirmed on holdout C1.", "",
         "| variant | E | 95% CI | n | control coverage | p | Holm p |", "|---|---|---|---|---|---|---|"]
    for k, r in res.items():
        L.append(f"| {k} | {r['E']:+.4f} | {r['ci'][0]:+.4f}..{r['ci'][1]:+.4f} | {r['n']} | {r['coverage']:.3f} "
                 f"| {r['p']:.3f} | {adj[k]:.3f} |")
    L += ["", "## Activation tier at the event: cases vs matched controls", "",
          "| tier | meaning | cases | controls |", "|---|---|---|---|"]
    names = ["uncovered", "0 none", "1 feeble (MD only)", "2 limited (AD only)", "3 ordinary", "4 par excellence"]
    for i in range(1, 6):
        L.append(f"| {i-1} | {names[i]} | {tc[i]/tc.sum():.3f} | {tk[i]/tk.sum():.3f} |")
    a.out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
