"""Phase 3J-AD: Jaimini chara ANTARDASHA timing (docs/validation/PHASE3J_AD_PREREG.md).

Phase 3J's design, activation rule and death exclusion, one level down: the Parashara engine's
`chara_dasha.antardashas` (BPHS-51 sl.5, sl.7-12). Day-dated events only (an antardasha is ~1/12 of a
1-12-year dasa).
  P_ad   the running antardasha sign IS the event house's sign from the Lagna      (primary)
  S_conv the dasa sign AND the antardasha sign are both that sign                  (secondary)
E_rs + E_wp; SIGNAL needs both CIs above 0; placebo = the sequence seeded at Lagna + 1.

Usage:
    py -3.12 -m tools.validation.jaimini_ad_timing --derived E:/astro/data/astro_databank/derived --population E:/astro/data/validation/activation_lahiri_AB.parquet --out docs/validation/PHASE3J_AD_RESULTS.md --sink E:/astro/data/validation/results.jsonl
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from pathlib import Path

import numpy as np
import pandas as pd

from tools.validation import riskset_timing as rt
from tools.validation.activation_store import _init
from tools.validation.jaimini_timing import HORIZON, death_keys, house_sign
from tools.validation.result import Result, emit
from tools.validation.stats import mde80
from tools.validation.yogini_timing import effects, specificity

PREREG = "PHASE3J_AD_PREREG@27d0516a"


def ad_rows(signs: dict[str, int], seed_asc: int, anchors: tuple[int, ...], converge: bool = False) -> tuple:
    """Store record over antardashas: t[h] = 1 iff the AD sign is the h-th sign from an anchor
    (`converge`: and the dasa sign is too)."""
    from app.parashara.primitives import chara_dasha as cd
    s, e, t = [], [], []
    for md in cd.timeline(seed_asc, signs, horizon=HORIZON):
        for ad in cd.antardashas(md):
            s.append(ad.start_year); e.append(ad.end_year)
            hit = [any(ad.sign == house_sign(a, h) and (not converge or md.sign == ad.sign) for a in anchors)
                   for h in range(1, 13)]
            t.append([int(x) for x in hit] + [0])
    return np.array(s), np.array(e), np.array(t, dtype=np.int8), np.zeros(len(s), bool)


def process(row: dict) -> tuple[str, dict] | None:
    try:
        from app.parashara.chart.cast import cast
        from app.parashara.doctrine.chara_karaka import atmakaraka, karakamsa
        from app.parashara.primitives import chara_dasha as cd
        y, mo, d = (int(x) for x in row["birth_date"].split("-"))
        t = row["birth_time"]
        ch = cast(year=y, month=mo, day=d, hour=int(t[:2]), minute=int(t[3:5]), tz_offset=float(row["tz_offset"]),
                  latitude=float(row["latitude"]), longitude=float(row["longitude"]))
        sg = cd.chart_signs(ch)
        asc = ch.asc_sign
        wide = (asc, sg[atmakaraka(ch.longitudes)], karakamsa(ch.longitudes))
        return row["person_id"], {"real": ad_rows(sg, asc, (asc,)),
                                  "placebo": ad_rows(sg, asc % 12 + 1, (asc,)),
                                  "converge": ad_rows(sg, asc, (asc,), converge=True),
                                  "lagna_ak_karakamsa": ad_rows(sg, asc, wide)}
    except Exception:  # noqa: BLE001 - per-person failure: their sets drop out
        return None


def build_store(rows: list[dict], ayanamsa: str, workers: int) -> rt.Store:
    st = rt.Store.__new__(rt.Store)
    with mp.Pool(workers, initializer=_init, initargs=(ayanamsa,)) as pool:
        st.data = dict(r for r in pool.imap_unordered(process, rows, chunksize=50) if r)
    return st


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--population", type=Path, required=True, help="Phase-3 Lahiri store (person set only)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, default=Path("E:/astro/data/validation/phase3J_AD_results.json"))
    ap.add_argument("--sink", type=Path, default=None)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(rt.SEED)
    ev, master, death_age = rt.load_events(a.derived)
    pop = set(pd.read_parquet(a.population, columns=["person_id"]).person_id.unique())
    ev = ev[ev.person_id.isin(pop)]
    sets_all = rt.build_sets(ev, master, death_age, pop, rng)          # identical to Phase 3 (same draw)
    dk = death_keys(ev)
    sets = [dict(s, level="MD") for s in sets_all if s["level"] == "AD"
            and (s["case"], float(s["event_jd"]), str(s["houses"])) not in dk]
    need = sorted({p for s in sets for p in (s["case"], *s["controls"])})
    m = master.set_index("person_id")
    rows = [dict(m.loc[p, ["birth_date", "birth_time", "tz_offset", "latitude", "longitude"]], person_id=p)
            for p in need]
    store = build_store(rows, "lahiri", a.workers)
    ss = [s for s in sets if all(p in store.data for p in (s["case"], *s["controls"]))]
    pids = [s["case"] for s in ss]
    out: dict = {"n_sets_phase3": len(sets_all), "n_day_dated_nondeath": len(sets), "n_sets_kept": len(ss),
                 "n_people_cast": len(store.data), "n_people_needed": len(need)}

    # ---- 1. gates first (PHASE3_AMENDMENT_1) ----
    xc, xk, _ = rt.score(ss, store)
    for kind in ("sham", "planted"):
        out[f"{kind}_P_ad"] = rt.calibrate(xc, xk, pids, kind, rng)
    out["gates_ok"] = bool(out["sham_P_ad"]["pass"] and out["planted_P_ad"]["pass"])
    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    if not out["gates_ok"]:
        a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        raise SystemExit("[3J-AD] CONTROL GATE FAILED -- real comparison NOT made")

    # ---- 2. placebo, then real; secondaries ----
    out["P_ad_placebo"] = effects(ss, store, "placebo", rng)
    r = effects(ss, store, "real", rng)
    r["clr_or"] = rt.clr_or(xc, xk)
    out["P_ad_real"] = r
    out["S_conv"] = effects(ss, store, "converge", rng)
    out["S2_P_ad"] = specificity(ss, store, rng)
    out["P_ad_lagna_ak_karakamsa"] = effects(ss, store, "lagna_ak_karakamsa", rng)
    fam = {}
    for f in sorted({s["family"] for s in ss}):
        sub = [s for s in ss if s["family"] == f]
        if len(sub) >= 30:
            fam[f] = effects(sub, store, "real", rng)
    out["P_ad_by_family"] = fam
    for rr in ("AA", "A"):
        sub = [s for s in ss if s["rodden"] == rr]
        if len(sub) >= 30:
            out[f"P_ad_rodden_{rr}"] = effects(sub, store, "real", rng)

    # ---- 3. verdict (one primary: Holm over one) ----
    rs, wp = r["rs"], r["wp"]
    result = Result(test_id="phase3j_ad:P_ad", prereg_id=PREREG, engine="parashara", statistic="hit_diff",
                    unit="event", effect=rs["E"], se=rs["se"], se0=rs["se0"], sesoi=rt.SESOI, n_cases=rs["n"],
                    n_clusters=rs["n_people"], sham_ok=True, n_controls=rs["n"] * rt.K_CONTROLS,
                    ci95_override=rs["ci"], planted_recovered=out["planted_P_ad"]["pass"],
                    config={"holm_p": rs["p"], "E_wp": wp["E"], "E_wp_ci": wp["ci"],
                            "coverage": rs["coverage"], "clr_or": r["clr_or"]})
    both_up = rs["ci"][0] > 0 and wp["ci"][0] > 0 and rs["p"] < 0.05
    r["verdict"] = ("SIGNAL" if both_up else "OPPOSITE TO PREDICTION" if rs["ci"][1] < 0
                    else "BOUNDED_NULL" if result.p_tost < 0.05 else "UNDERPOWERED")
    r["holm_p"], r["mde80"], r["p_tost"] = rs["p"], mde80(rs["se0"]), result.p_tost
    if a.sink:
        tmp = a.sink.with_suffix(".tmp")
        rec = emit(result, tmp)
        tmp.unlink()
        rec["verdict"] = r["verdict"]
        with a.sink.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")

    # ---- 4. Raman ayanamsa (descriptive, same sets) ----
    ram = build_store(rows, "raman", a.workers)
    sub = [s for s in ss if all(p in ram.data for p in (s["case"], *s["controls"]))]
    out["P_ad_raman_ayanamsa"] = effects(sub, ram, "real", rng)

    a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    a.out.write_text(markdown(out), encoding="utf-8")
    print(markdown(out).encode("ascii", "replace").decode())
    return 0


def _eff(name: str, r: dict) -> str:
    rs, wp = r["rs"], r["wp"]
    return (f"| {name} | {rs['n']} | {rs['coverage']:.3f} | {rs['E']:+.4f} | {rs['ci'][0]:+.4f}..{rs['ci'][1]:+.4f} "
            f"| {wp['E']:+.4f} | {wp['ci'][0]:+.4f}..{wp['ci'][1]:+.4f} |")


def markdown(o: dict) -> str:
    r = o["P_ad_real"]
    rs, wp = r["rs"], r["wp"]
    L = ["# Phase 3J-AD results: Jaimini chara antardasha timing", "",
         f"Per `docs/validation/PHASE3J_AD_PREREG.md` ({PREREG}). Parashara engine `chara_dasha.antardashas` "
         f"(BPHS-51 sl.7-12), Lahiri. Day-dated non-death Phase 3 sets: {o['n_day_dated_nondeath']}; kept "
         f"{o['n_sets_kept']}; charts cast {o['n_people_cast']}/{o['n_people_needed']}. Gates passed: **{o['gates_ok']}**.", "",
         "Exposure: the running antardasha sign is the event house's sign from the Lagna (CONVENTION, Raman SJ art.159). "
         "SIGNAL needs both E_rs and E_wp CIs above 0. SESOI 0.03.", "",
         "## Primary", "",
         "| test | n | control coverage | E_rs | 95% CI | E_wp | 95% CI | CLR OR | MDE80 | p | p_TOST | verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|",
         f"| P_ad: chara AD sign = house (day-dated) | {rs['n']} | {rs['coverage']:.3f} | {rs['E']:+.4f} "
         f"| {rs['ci'][0]:+.4f}..{rs['ci'][1]:+.4f} | {wp['E']:+.4f} | {wp['ci'][0]:+.4f}..{wp['ci'][1]:+.4f} "
         f"| {(r['clr_or'] or float('nan')):.3f} | {r['mde80']:.3f} | {r['holm_p']:.3f} | {r['p_tost']:.3f} | **{r['verdict']}** |",
         "", "## Control gates (500 draws, before the real comparison)", "",
         "| gate | target | mean E | SD | CI coverage | pass |", "|---|---|---|---|---|---|"]
    for k in ("sham_P_ad", "planted_P_ad"):
        g = o[k]
        L.append(f"| {k} | {g['target']:+.3f} | {g['mean_E']:+.4f} | {g['sd_E']:.4f} | {g['coverage']:.3f} | {g['pass']} |")
    L += ["", "## Placebo, secondary, sensitivity, families (descriptive)", "",
          "| arm | n | coverage | E_rs | 95% CI | E_wp | 95% CI |", "|---|---|---|---|---|---|---|"]
    for k in ("P_ad_placebo", "S_conv", "P_ad_raman_ayanamsa", "P_ad_lagna_ak_karakamsa", "P_ad_rodden_AA", "P_ad_rodden_A"):
        if k in o:
            L.append(_eff(k, o[k]))
    for f, rr in o.get("P_ad_by_family", {}).items():
        L.append(_eff(f"P_ad family: {f}", rr))
    s2 = o["S2_P_ad"]
    L += ["", f"S2 specificity: {s2['E']:+.4f} ({s2['ci'][0]:+.4f}..{s2['ci'][1]:+.4f}), p {s2['p']:.3f}.",
          "Shams check arithmetic only; the placebo (sequence seeded at Lagna + 1) is the informative control.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
