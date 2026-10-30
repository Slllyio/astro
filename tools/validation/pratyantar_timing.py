"""Phase 3P: Raman's PRATYANTAR-level timing (docs/validation/PHASE3P_PRATYANTAR_PREREG.md).

Same AD-level (day-dated) risk sets as Phase 3/3R. Raman engine, unchanged:
  P3a  PD lord in timers(H)            (engine rectification Channel A, pratyantar level)
  P3b  MD, AD and PD lords all in timers(H)   (triple convergence)
  timers(H) = timer_set(H) | timer_set(aux)  (as active_houses); death: maraka_set().primary
Two effects per primary: E_rs (case - matched controls) and E_wp (case at event - case's own exact
lifetime time-share, ages 15-75). SIGNAL needs both CIs above 0. Placebo = dasha seeded +1 nakshatra.
No store: each needed person is cast once and only the queries the risk sets need are answered.

Usage:
    py -3.12 -m tools.validation.pratyantar_timing --derived E:/astro/data/astro_databank/derived --population E:/astro/data/validation/raman_activation_raman_AB.parquet --out docs/validation/PHASE3P_RESULTS.md --sink E:/astro/data/validation/results.jsonl
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from pathlib import Path

import numpy as np
import pandas as pd

from tools.validation import riskset_timing as rt
from tools.validation.raman_activation_store import NAK, timeline
from tools.validation.result import Result, emit
from tools.validation.stats import cluster_bootstrap, mde80

PREREG = "PHASE3P_PRATYANTAR_PREREG@06139d16"
_YEAR = 365.2425
LIFE = (15.0, 75.0)


def _key(houses) -> str:
    return houses if isinstance(houses, str) else ",".join(map(str, houses))


def pd_periods(chart, bjd: float, shift: float) -> list[tuple[float, float, str, str, str]]:
    from app.raman_saab.primitives import vimshottari as vd
    out = []
    for md in timeline(chart, shift):
        if md.end_jd <= bjd:
            continue
        for bh in vd.bhuktis(md):
            if bh.end_jd <= bjd:
                continue
            for p in vd.pratyantars(bh):
                if p.end_jd > bjd:
                    out.append(((p.start_jd - bjd) / _YEAR, (p.end_jd - bjd) / _YEAR, p.maha, p.antar, p.pratyantar))
    return out


def worker(task: tuple[dict, list[tuple[float, str]], list[str], str]) -> tuple[str, dict] | None:
    row, queries, life_keys, ayanamsa = task
    try:
        import swisseph as swe
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.chart.model import BirthData
        from app.raman_saab.primitives import vimshottari as vd
        y, mo, d = (int(x) for x in row["birth_date"].split("-"))
        t = row["birth_time"]
        chart = cast_chart(BirthData(name=row["person_id"], year=y, month=mo, day=d, hour=int(t[:2]),
                                     minute=int(t[3:5]), tz_offset=float(row["tz_offset"]),
                                     latitude=float(row["latitude"]), longitude=float(row["longitude"])),
                           ayanamsa=ayanamsa)
        bjd = swe.julday(y, mo, d, 12.0, swe.GREG_CAL)
        mk = vd.maraka_set(chart).primary
        timers: dict[str, set[str]] = {}

        def tset(key: str) -> set[str]:
            if key not in timers:
                if key == rt.MARAKA:
                    timers[key] = set(mk)
                else:
                    s: set[str] = set()
                    for h in map(int, key.split(",")):
                        s |= vd.timer_set(chart, h)
                        for aux in vd._EVENT_AUX_HOUSES.get(h, ()):
                            s |= vd.timer_set(chart, aux)
                    timers[key] = s
            return timers[key]

        res: dict = {}
        for variant, shift in (("real", 0.0), ("placebo", NAK)):
            pds = pd_periods(chart, bjd, shift)
            starts = np.array([p[0] for p in pds])
            q = {}
            for age, key in queries:
                i = int(np.searchsorted(starts, age, side="right")) - 1
                if i < 0 or age >= pds[i][1]:
                    q[(age, key)] = None
                    continue
                _, _, md, ad, pd = pds[i]
                ts = tset(key)
                q[(age, key)] = (pd in ts, md in ts and ad in ts and pd in ts,
                                 int(md in ts) + int(ad in ts) + int(pd in ts))
            life = {}
            for key in life_keys:
                ts = tset(key)
                a = b = 0.0
                for s, e, md, ad, pd in pds:
                    w = max(0.0, min(e, LIFE[1]) - max(s, LIFE[0]))
                    if w > 0:
                        a += w * (pd in ts)
                        b += w * (md in ts and ad in ts and pd in ts)
                life[key] = (a / (LIFE[1] - LIFE[0]), b / (LIFE[1] - LIFE[0]))
            res[variant] = {"q": q, "life": life}
        return row["person_id"], res
    except Exception:  # noqa: BLE001 - per-person failure: their sets drop out
        return None


def run_engine(rows_by_pid, queries, lifes, ayanamsa, workers) -> dict[str, dict]:
    tasks = [(rows_by_pid[p], queries.get(p, []), lifes.get(p, []), ayanamsa) for p in rows_by_pid]
    out = {}
    with mp.Pool(workers) as pool:
        for r in pool.imap_unordered(worker, tasks, chunksize=20):
            if r:
                out[r[0]] = r[1]
    return out


def matrices(sets, data, variant: str, which: int):
    """x_case, x_controls[n,K], life_share_case, levels[n,K+1], kept-set indices."""
    xc, xk, life, lev, keep = [], [], [], [], []
    for i, s in enumerate(sets):
        key = _key(s["houses"])
        mem = [s["case"], *s["controls"]]
        vals = [data.get(p, {}).get(variant, {}).get("q", {}).get((s["age"], key)) for p in mem]
        if any(v is None for v in vals) or s["case"] not in data:
            continue
        xc.append(float(vals[0][which])); xk.append([float(v[which]) for v in vals[1:]])
        life.append(data[s["case"]][variant]["life"][key][which])
        lev.append([v[2] for v in vals]); keep.append(i)
    return np.array(xc), np.array(xk), np.array(life), np.array(lev), keep


def effects(xc, xk, life, pids, rng) -> dict:
    rs = rt.excess(xc, xk, pids, rng)
    w = xc - life
    lo, hi = cluster_bootstrap(w, np.asarray(pids), rng=rng)
    return {"rs": rs, "wp": {"E": float(w.mean()), "ci": (lo, hi), "life_share": float(life.mean())}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--population", type=Path, required=True, help="Phase-3R store (person set only)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, default=Path("E:/astro/data/validation/phase3P_results.json"))
    ap.add_argument("--sink", type=Path, default=None)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(rt.SEED)
    ev, master, death_age = rt.load_events(a.derived)
    pop = set(pd.read_parquet(a.population, columns=["person_id"]).person_id.unique())
    ev = ev[ev.person_id.isin(pop)]
    sets = [s for s in rt.build_sets(ev, master, death_age, pop, rng) if s["level"] == "AD"]
    queries: dict[str, list] = {}
    lifes: dict[str, list] = {}
    for s in sets:
        key = _key(s["houses"])
        for p in (s["case"], *s["controls"]):
            queries.setdefault(p, []).append((s["age"], key))
        lifes.setdefault(s["case"], []).append(key)
    m = pd.read_parquet(a.derived / "raman" / "person_master.parquet").set_index("person_id")
    rows = {p: dict(m.loc[p, ["birth_date", "birth_time", "tz_offset", "latitude", "longitude"]], person_id=p)
            for p in queries}
    data = run_engine(rows, queries, lifes, "raman", a.workers)
    out: dict = {"n_sets": len(sets), "n_people_cast": len(data)}

    # ---- gates first ----
    gates_ok = True
    for tag, which in (("P3a", 0), ("P3b", 1)):
        xc, xk, _, _, keep = matrices(sets, data, "real", which)
        pids = [sets[i]["case"] for i in keep]
        for kind in ("sham", "planted"):
            g = rt.calibrate(xc, xk, pids, kind, rng)
            out[f"{kind}_{tag}"] = g
            gates_ok &= g["pass"]
    out["gates_ok"] = bool(gates_ok)
    if not gates_ok:
        a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        raise SystemExit("[3P] CONTROL GATE FAILED -- real comparison NOT made")

    # ---- placebo, then real ----
    res = {}
    for tag, which in (("P3a", 0), ("P3b", 1)):
        for variant in ("placebo", "real"):
            xc, xk, life, lev, keep = matrices(sets, data, variant, which)
            pids = [sets[i]["case"] for i in keep]
            out[f"{tag}_{variant}"] = effects(xc, xk, life, pids, rng)
            if variant == "real":
                res[tag] = out[f"{tag}_real"]
                out[f"{tag}_real"]["clr_or"] = rt.clr_or(xc, xk)
                if tag == "P3a":
                    out["S1_levels_slope"] = rt.clr_slope(lev)
                    fam = {}
                    for f in sorted({sets[i]["family"] for i in keep}):
                        idx = [j for j, i in enumerate(keep) if sets[i]["family"] == f]
                        if len(idx) >= 30:
                            fam[f] = effects(xc[idx], xk[idx], life[idx], [pids[j] for j in idx], rng)
                    out["P3a_by_family"] = fam
                    for rr in ("AA", "A"):
                        idx = [j for j, i in enumerate(keep) if sets[i]["rodden"] == rr]
                        out[f"P3a_rodden_{rr}"] = effects(xc[idx], xk[idx], life[idx], [pids[j] for j in idx], rng)
    adj = rt.holm({k: v["rs"]["p"] for k, v in res.items()})
    for tag, r in res.items():
        rs, wp = r["rs"], r["wp"]
        result = Result(test_id=f"phase3p:{tag}", prereg_id=PREREG, engine="raman_saab", statistic="hit_diff",
                        unit="event", effect=rs["E"], se=rs["se"], se0=rs["se0"], sesoi=rt.SESOI, n_cases=rs["n"],
                        n_clusters=rs["n_people"], sham_ok=True, ci95_override=rs["ci"],
                        planted_recovered=out[f"planted_{tag}"]["pass"],
                        config={"holm_p": adj[tag], "E_wp": wp["E"], "E_wp_ci": wp["ci"]})
        both_up = rs["ci"][0] > 0 and wp["ci"][0] > 0 and adj[tag] < 0.05
        down = rs["ci"][1] < 0
        r["verdict"] = ("SIGNAL" if both_up else "OPPOSITE TO PREDICTION" if down
                        else "BOUNDED_NULL" if result.p_tost < 0.05 else "UNDERPOWERED")
        r["holm_p"], r["mde80"], r["p_tost"] = adj[tag], mde80(rs["se0"]), result.p_tost
        if a.sink:
            tmp = a.sink.with_suffix(".tmp")
            rec = emit(result, tmp)
            tmp.unlink()
            rec["verdict"] = r["verdict"]
            with a.sink.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, default=str) + "\n")

    # ---- Lahiri frame (descriptive) ----
    lah = run_engine(rows, queries, lifes, "lahiri", a.workers)
    for tag, which in (("P3a", 0), ("P3b", 1)):
        xc, xk, life, _, keep = matrices(sets, lah, "real", which)
        out[f"{tag}_lahiri_frame"] = effects(xc, xk, life, [sets[i]["case"] for i in keep], rng)

    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    a.out.write_text(markdown(out), encoding="utf-8")
    print(markdown(out).encode("ascii", "replace").decode())
    return 0


def _eff(name, r):
    rs, wp = r["rs"], r["wp"]
    return (f"| {name} | {rs['n']} | {rs['coverage']:.2f} | {rs['E']:+.4f} | {rs['ci'][0]:+.4f}..{rs['ci'][1]:+.4f} "
            f"| {wp['E']:+.4f} | {wp['ci'][0]:+.4f}..{wp['ci'][1]:+.4f} |")


def markdown(o: dict) -> str:
    L = ["# Phase 3P results: Raman's pratyantar-level timing", "",
         f"Per `docs/validation/PHASE3P_PRATYANTAR_PREREG.md` ({PREREG}). Raman engine, Raman ayanamsa. "
         f"{o['n_sets']} day-dated risk sets; {o['n_people_cast']} charts cast. Gates passed: **{o['gates_ok']}**.", "",
         "E_rs = case − 10 matched controls; E_wp = case at the event − the case's own lifetime share (ages 15–75). "
         "SIGNAL needs both CIs above 0.", "",
         "## Primaries", "",
         "| test | n | control coverage | E_rs | 95% CI | E_wp | 95% CI | CLR OR | MDE80 | Holm p | p_TOST | verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for tag, lbl in (("P3a", "P3a: pratyantar lord activates"), ("P3b", "P3b: MD+AD+PD all activate")):
        r = o[f"{tag}_real"]
        rs, wp = r["rs"], r["wp"]
        L.append(f"| {lbl} | {rs['n']} | {rs['coverage']:.2f} | {rs['E']:+.4f} | {rs['ci'][0]:+.4f}..{rs['ci'][1]:+.4f} "
                 f"| {wp['E']:+.4f} | {wp['ci'][0]:+.4f}..{wp['ci'][1]:+.4f} | {(r['clr_or'] or float('nan')):.3f} "
                 f"| {r['mde80']:.3f} | {r['holm_p']:.3f} | {r['p_tost']:.3f} | **{r['verdict']}** |")
    L += ["", "## Control gates (500 draws, before the real comparison)", "",
          "| gate | target | mean E | CI coverage | pass |", "|---|---|---|---|---|"]
    for k in ("sham_P3a", "planted_P3a", "sham_P3b", "planted_P3b"):
        g = o[k]
        L.append(f"| {k} | {g['target']:+.3f} | {g['mean_E']:+.4f} | {g['coverage']:.3f} | {g['pass']} |")
    L += ["", "## Placebo, sensitivity, families (descriptive)", "",
          "| arm | n | coverage | E_rs | 95% CI | E_wp | 95% CI |", "|---|---|---|---|---|---|---|"]
    for k in ("P3a_placebo", "P3b_placebo", "P3a_lahiri_frame", "P3b_lahiri_frame", "P3a_rodden_AA", "P3a_rodden_A"):
        L.append(_eff(k, o[k]))
    for f, r in o.get("P3a_by_family", {}).items():
        L.append(_eff(f"P3a family: {f}", r))
    L += ["", f"S1 dose-response over activating levels (0–3: MD, AD, PD), CLR log-odds per level: {o.get('S1_levels_slope')}", ""]
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
