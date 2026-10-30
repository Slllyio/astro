"""Phase 3Y: Yogini dasha timing through the Phase 3 instrument (docs/validation/PHASE3Y_YOGINI_PREREG.md).

Parashara engine, unchanged. Yogini MDs from `yogini_dasha.timeline` (BPHS-46:199), repeated past the
first 36-year cycle; ADs from `nakshatra_dasha.bhukti_timeline` (BPHS-46:110), birth MD anchored at its
true start as `reading._dashas` does for Vimshottari. Tiers, influence (+ lord-from-Moon), association
and primary marakas are Phase 3's own (`activation_store`). Same risk sets as Phase 3 (seed 20261014):
  P1  Yogini (MD, AD) tier >= 3 for H, day-dated      P2  Yogini MD lord influences H, year-dated
Two effects per primary: E_rs (case - 10 matched controls) and E_wp (case at event - the case's own
lifetime share, ages 15-75). SIGNAL needs both CIs above 0 + Holm. Placebo = nakshatra +1.

Usage:
    py -3.12 -m tools.validation.yogini_timing --derived E:/astro/data/astro_databank/derived --population E:/astro/data/validation/activation_lahiri_AB.parquet --out docs/validation/PHASE3Y_RESULTS.md --sink E:/astro/data/validation/results.jsonl
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from pathlib import Path

import numpy as np
import pandas as pd

from tools.validation import riskset_timing as rt
from tools.validation.activation_store import HOUSES, _init, associated, influence, primary_maraka, tier
from tools.validation.result import Result, emit
from tools.validation.stats import cluster_bootstrap, mde80

PREREG = "PHASE3Y_YOGINI_PREREG@c4c5f710"
LIFE = (15.0, 75.0)
HORIZON = 100.0   # years of Yogini periods generated (events are aged <= 95)


def yogini_ads(chart, nak: int) -> list[tuple[str, str, float, float]]:
    """(MD lord, AD lord, start_age, end_age) from birth to HORIZON; the engine's first cycle, then repeats."""
    from app.parashara.primitives import yogini_dasha as yog
    from app.parashara.primitives.nakshatra_dasha import bhukti_timeline, dasha_timeline
    from app.parashara.reading import _birth_balance
    elapsed = _birth_balance(chart)
    idx = {lord: i for i, (lord, _) in enumerate(yog.CYCLE)}
    first = yog.timeline(nak, elapsed_fraction=elapsed)
    mds = [(p.lord, p.start_year - elapsed * p.years if i == 0 else p.start_year) for i, p in enumerate(first)]
    cursor = first[-1].end_year
    while cursor < HORIZON:
        nxt = dasha_timeline(yog.CYCLE, yog.seed(nak).index)
        mds += [(p.lord, cursor + p.start_year) for p in nxt]
        cursor += nxt[-1].end_year
    out = []
    for lord, start in mds:
        for b in bhukti_timeline(yog.CYCLE, idx[lord], mahadasha_start_year=start):
            if b.end_year > 0 and b.start_year < HORIZON:
                out.append((lord, b.lord, max(0.0, b.start_year), b.end_year))
    return out


def tier_rows(chart, nak: int) -> tuple:
    """Store record (starts, ends, tiers[n, 13] = t1..t12 + t_mk, conj) for one Yogini sequence."""
    from app.parashara.synthesis.chart_facts import planet_signs
    signs = planet_signs(chart)
    inf, mk = {}, {}
    s, e, t, c = [], [], [], []
    for md, ad, a0, a1 in yogini_ads(chart, nak):
        for p in (md, ad):
            if p not in inf:
                inf[p] = [influence(p, h, chart, signs) for h in HOUSES]
                mk[p] = primary_maraka(p, chart, signs)
        assoc = associated(md, ad, signs)
        s.append(a0); e.append(a1)
        t.append([*(tier(inf[md][i], inf[ad][i], assoc) for i in range(12)), tier(mk[md], mk[ad], assoc)])
        c.append(signs.get(md) is not None and signs.get(md) == signs.get(ad))
    return np.array(s), np.array(e), np.array(t, dtype=np.int8), np.array(c)


def process(row: dict) -> tuple[str, dict] | None:
    try:
        from app.parashara.chart.cast import cast
        y, mo, d = (int(x) for x in row["birth_date"].split("-"))
        t = row["birth_time"]
        chart = cast(year=y, month=mo, day=d, hour=int(t[:2]), minute=int(t[3:5]),
                     tz_offset=float(row["tz_offset"]), latitude=float(row["latitude"]),
                     longitude=float(row["longitude"]))
        nak = chart.janma_nakshatra
        return row["person_id"], {"real": tier_rows(chart, nak), "placebo": tier_rows(chart, nak % 27 + 1)}
    except Exception:  # noqa: BLE001 - per-person failure: their sets drop out
        return None


def build_store(rows: list[dict], ayanamsa: str, workers: int) -> rt.Store:
    st = rt.Store.__new__(rt.Store)
    with mp.Pool(workers, initializer=_init, initargs=(ayanamsa,)) as pool:
        st.data = dict(r for r in pool.imap_unordered(process, rows, chunksize=50) if r)
    return st


def life_share(store: rt.Store, pid: str, houses, level: str, variant: str) -> float:
    """Exact time-share of ages 15-75 in an exposed Yogini period (same exposure rule as the case)."""
    s, e, t, _ = store.data[pid][variant]
    cols = [12] if houses == rt.MARAKA else [h - 1 for h in houses]
    w = np.clip(np.minimum(e, LIFE[1]) - np.maximum(s, LIFE[0]), 0, None)
    x = np.array([rt.exposed(int(v), level) for v in t[:, cols].max(1)])
    return float((w * x).sum() / (LIFE[1] - LIFE[0]))


def effects(ss: list[dict], store: rt.Store, variant: str, rng) -> dict:
    xc, xk, _ = rt.score(ss, store, variant=variant)
    pids = [s["case"] for s in ss]
    life = np.array([life_share(store, s["case"], s["houses"], s["level"], variant) for s in ss])
    w = xc - life
    lo, hi = cluster_bootstrap(w, np.asarray(pids), rng=rng)
    return {"rs": rt.excess(xc, xk, pids, rng),
            "wp": {"E": float(w.mean()), "ci": (lo, hi), "life_share": float(life.mean())}}


def specificity(ss: list[dict], store: rt.Store, rng) -> dict:
    """S2 (Phase 3 definition): E(target) - mean E over the non-target house instruments."""
    from scipy.stats import norm
    xc, xk, _ = rt.score(ss, store)
    alt = []
    for h in range(1, 13):
        idx = [i for i, s in enumerate(ss) if s["houses"] == rt.MARAKA or h not in s["houses"]]
        axc, axk, _ = rt.score([dict(ss[i], houses=(h,)) for i in idx], store)
        d = np.full(len(ss), np.nan)
        d[idx] = axc - axk.mean(1)
        alt.append(d)
    spec = (xc - xk.mean(1)) - np.nanmean(np.vstack(alt), 0)
    lo, hi = cluster_bootstrap(spec, np.asarray([s["case"] for s in ss]), rng=rng)
    se = (hi - lo) / 3.919928
    return {"E": float(spec.mean()), "ci": (lo, hi),
            "p": float(2 * (1 - norm.cdf(abs(spec.mean()) / se))) if se > 0 else 1.0}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--population", type=Path, required=True, help="Phase-3 Lahiri store (person set only)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, default=Path("E:/astro/data/validation/phase3Y_results.json"))
    ap.add_argument("--sink", type=Path, default=None)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(rt.SEED)
    ev, master, death_age = rt.load_events(a.derived)
    pop = set(pd.read_parquet(a.population, columns=["person_id"]).person_id.unique())
    ev = ev[ev.person_id.isin(pop)]
    sets = rt.build_sets(ev, master, death_age, pop, rng)
    need = sorted({p for s in sets for p in (s["case"], *s["controls"])})
    m = master.set_index("person_id")
    rows = [dict(m.loc[p, ["birth_date", "birth_time", "tz_offset", "latitude", "longitude"]], person_id=p)
            for p in need]
    store = build_store(rows, "lahiri", a.workers)
    kept = [s for s in sets if all(p in store.data for p in (s["case"], *s["controls"]))]
    by_level = {lvl: [s for s in kept if s["level"] == lvl] for lvl in ("AD", "MD")}
    out: dict = {"n_sets": len(sets), "n_sets_kept": len(kept), "n_people_cast": len(store.data),
                 "n_people_needed": len(need), "n_by_level": {k: len(v) for k, v in by_level.items()}}

    # ---- 1. gates first (PHASE3_AMENDMENT_1) ----
    gates_ok = True
    for lvl, ss in by_level.items():
        xc, xk, _ = rt.score(ss, store)
        for kind in ("sham", "planted"):
            g = rt.calibrate(xc, xk, [s["case"] for s in ss], kind, rng)
            out[f"{kind}_{lvl}"] = g
            gates_ok &= g["pass"]
    out["gates_ok"] = bool(gates_ok)
    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    if not gates_ok:
        a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        raise SystemExit("[3Y] CONTROL GATE FAILED -- real comparison NOT made")

    # ---- 2. placebo, then real ----
    res = {}
    for lvl, tag in (("AD", "P1"), ("MD", "P2")):
        ss = by_level[lvl]
        out[f"{tag}_placebo"] = effects(ss, store, "placebo", rng)
        r = effects(ss, store, "real", rng)
        xc, xk, tt = rt.score(ss, store)
        r["clr_or"] = rt.clr_or(xc, xk)
        res[tag] = out[f"{tag}_real"] = r
        if lvl == "AD":
            out["S1_slope"] = rt.clr_slope(tt)
        out[f"S2_{tag}"] = specificity(ss, store, rng)
        fam = {}
        for f in sorted({s["family"] for s in ss}):
            sub = [s for s in ss if s["family"] == f]
            if len(sub) >= 30:
                fam[f] = effects(sub, store, "real", rng)
        out[f"{tag}_by_family"] = fam
        for rr in ("AA", "A"):
            sub = [s for s in ss if s["rodden"] == rr]
            if len(sub) >= 30:
                out[f"{tag}_rodden_{rr}"] = effects(sub, store, "real", rng)

    # ---- 3. verdicts + Holm ----
    adj = rt.holm({k: v["rs"]["p"] for k, v in res.items()})
    for tag, r in res.items():
        rs, wp = r["rs"], r["wp"]
        lvl = "AD" if tag == "P1" else "MD"
        result = Result(test_id=f"phase3y:{tag}", prereg_id=PREREG, engine="parashara", statistic="hit_diff",
                        unit="event", effect=rs["E"], se=rs["se"], se0=rs["se0"], sesoi=rt.SESOI, n_cases=rs["n"],
                        n_clusters=rs["n_people"], sham_ok=True, n_controls=rs["n"] * rt.K_CONTROLS,
                        ci95_override=rs["ci"], planted_recovered=out[f"planted_{lvl}"]["pass"],
                        config={"holm_p": adj[tag], "E_wp": wp["E"], "E_wp_ci": wp["ci"],
                                "coverage": rs["coverage"], "clr_or": r["clr_or"]})
        both_up = rs["ci"][0] > 0 and wp["ci"][0] > 0 and adj[tag] < 0.05
        r["verdict"] = ("SIGNAL" if both_up else "OPPOSITE TO PREDICTION" if rs["ci"][1] < 0
                        else "BOUNDED_NULL" if result.p_tost < 0.05 else "UNDERPOWERED")
        r["holm_p"], r["mde80"], r["p_tost"] = adj[tag], mde80(rs["se0"]), result.p_tost
        if a.sink:
            tmp = a.sink.with_suffix(".tmp")
            rec = emit(result, tmp)
            tmp.unlink()
            rec["verdict"] = r["verdict"]
            with a.sink.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, default=str) + "\n")

    # ---- 4. Raman ayanamsa (descriptive, same sets) ----
    ram = build_store(rows, "raman", a.workers)
    for lvl, tag in (("AD", "P1"), ("MD", "P2")):
        ss = [s for s in by_level[lvl] if all(p in ram.data for p in (s["case"], *s["controls"]))]
        out[f"{tag}_raman_ayanamsa"] = effects(ss, ram, "real", rng)

    a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    a.out.write_text(markdown(out), encoding="utf-8")
    print(markdown(out).encode("ascii", "replace").decode())
    return 0


def _eff(name: str, r: dict) -> str:
    rs, wp = r["rs"], r["wp"]
    return (f"| {name} | {rs['n']} | {rs['coverage']:.2f} | {rs['E']:+.4f} | {rs['ci'][0]:+.4f}..{rs['ci'][1]:+.4f} "
            f"| {wp['E']:+.4f} | {wp['ci'][0]:+.4f}..{wp['ci'][1]:+.4f} |")


def markdown(o: dict) -> str:
    L = ["# Phase 3Y results: Yogini dasha timing", "",
         f"Per `docs/validation/PHASE3Y_YOGINI_PREREG.md` ({PREREG}). Parashara engine, Lahiri, Phase 3 instrument "
         f"with Yogini lords. Risk sets {o['n_sets']} (kept {o['n_sets_kept']}: AD {o['n_by_level']['AD']}, "
         f"MD {o['n_by_level']['MD']}); charts cast {o['n_people_cast']}/{o['n_people_needed']}. "
         f"Gates passed: **{o['gates_ok']}**.", "",
         "E_rs = case − 10 matched controls; E_wp = case at the event − the case's own lifetime share (ages 15–75). "
         "SIGNAL needs both CIs above 0 (Holm over P1, P2). SESOI 0.03.", "",
         "## Primaries", "",
         "| test | n | control coverage | E_rs | 95% CI | E_wp | 95% CI | CLR OR | MDE80 | Holm p | p_TOST | verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for tag, lbl in (("P1", "P1: Yogini AD tier ≥ 3 (day-dated)"), ("P2", "P2: Yogini MD lord activates (year-dated)")):
        r = o[f"{tag}_real"]
        rs, wp = r["rs"], r["wp"]
        L.append(f"| {lbl} | {rs['n']} | {rs['coverage']:.2f} | {rs['E']:+.4f} | {rs['ci'][0]:+.4f}..{rs['ci'][1]:+.4f} "
                 f"| {wp['E']:+.4f} | {wp['ci'][0]:+.4f}..{wp['ci'][1]:+.4f} | {(r['clr_or'] or float('nan')):.3f} "
                 f"| {r['mde80']:.3f} | {r['holm_p']:.3f} | {r['p_tost']:.3f} | **{r['verdict']}** |")
    L += ["", "## Control gates (500 draws, before the real comparison)", "",
          "| gate | target | mean E | SD | CI coverage | pass |", "|---|---|---|---|---|---|"]
    for k in ("sham_AD", "planted_AD", "sham_MD", "planted_MD"):
        g = o[k]
        L.append(f"| {k} | {g['target']:+.3f} | {g['mean_E']:+.4f} | {g['sd_E']:.4f} | {g['coverage']:.3f} | {g['pass']} |")
    L += ["", "## Placebo, sensitivity, families (descriptive)", "",
          "| arm | n | coverage | E_rs | 95% CI | E_wp | 95% CI |", "|---|---|---|---|---|---|---|"]
    for tag in ("P1", "P2"):
        for k in (f"{tag}_placebo", f"{tag}_raman_ayanamsa", f"{tag}_rodden_AA", f"{tag}_rodden_A"):
            if k in o:
                L.append(_eff(k, o[k]))
        for f, r in o.get(f"{tag}_by_family", {}).items():
            L.append(_eff(f"{tag} family: {f}", r))
    L += ["", "| secondary | E | 95% CI | p |", "|---|---|---|---|"]
    for k in ("S2_P1", "S2_P2"):
        r = o[k]
        L.append(f"| {k} specificity | {r['E']:+.4f} | {r['ci'][0]:+.4f}..{r['ci'][1]:+.4f} | {r['p']:.3f} |")
    L += ["", f"S1 dose-response (CLR log-odds per Yogini tier 0–4, P1 sets): {o.get('S1_slope')}",
          "S3 (double transit) not run, per the prereg. Shams check arithmetic only; the placebo Yogini is the "
          "informative control.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
