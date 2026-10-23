"""Phase 3J: Jaimini chara dasha timing (docs/validation/PHASE3J_JAIMINI_PREREG.md).

Parashara engine `primitives.chara_dasha` (BPHS-46 sl.155-167), mahadasha level only (antardashas are
deferred, rulings Q4). Activation, a CONVENTION (Raman, Studies in Jaimini art.159): the running dasa sign
IS the house's sign counted from the Lagna. Death events are excluded (same article). Same Phase 3 risk
sets (seed 20261014), every set scored at the mahadasha level:
  P_y  year-dated events (mid-year)        P_d  day-dated events (exact date)
E_rs (case - 10 matched controls) and E_wp (case at event - own lifetime share, ages 15-75); SIGNAL needs
both CIs above 0 + Holm over {P_y, P_d}. Placebo = the sequence seeded one sign ahead (Lagna + 1).

Usage:
    py -3.12 -m tools.validation.jaimini_timing --derived E:/astro/data/astro_databank/derived --population E:/astro/data/validation/activation_lahiri_AB.parquet --out docs/validation/PHASE3J_RESULTS.md --sink E:/astro/data/validation/results.jsonl
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import re
from pathlib import Path

import numpy as np
import pandas as pd

from tools.validation import riskset_timing as rt
from tools.validation.activation_store import _init
from tools.validation.result import Result, emit
from tools.validation.stats import mde80
from tools.validation.yogini_timing import effects, specificity

PREREG = "PHASE3J_JAIMINI_PREREG@7d9e4402"
HORIZON = 100.0


def house_sign(anchor: int, house: int) -> int:
    return (anchor - 1 + house - 1) % 12 + 1


def exposure_rows(asc: int, signs: dict[str, int], seed_asc: int, anchors: tuple[int, ...]) -> tuple:
    """Store record for one chara sequence seeded at `seed_asc`: t[h] = 1 iff the dasa sign is the h-th
    sign from any of `anchors` (the real Lagna; + AK sign / Karakamsa in the sensitivity arm)."""
    from app.parashara.primitives import chara_dasha as cd
    s, e, t = [], [], []
    for p in cd.timeline(seed_asc, signs, horizon=HORIZON):
        s.append(p.start_year); e.append(p.end_year)
        t.append([int(any(p.sign == house_sign(a, h) for a in anchors)) for h in range(1, 13)] + [0])
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
        ak_frames = (asc, sg[atmakaraka(ch.longitudes)], karakamsa(ch.longitudes))
        return row["person_id"], {"real": exposure_rows(asc, sg, asc, (asc,)),
                                  "placebo": exposure_rows(asc, sg, asc % 12 + 1, (asc,)),
                                  "lagna_ak_karakamsa": exposure_rows(asc, sg, asc, ak_frames)}
    except Exception:  # noqa: BLE001 - per-person failure: their sets drop out
        return None


def build_store(rows: list[dict], ayanamsa: str, workers: int) -> rt.Store:
    st = rt.Store.__new__(rt.Store)
    with mp.Pool(workers, initializer=_init, initargs=(ayanamsa,)) as pool:
        st.data = dict(r for r in pool.imap_unordered(process, rows, chunksize=50) if r)
    return st


def death_keys(ev: pd.DataFrame) -> set[tuple]:
    """(person, event_jd, houses) of every death event (own or a relative's), excluded per the prereg."""
    is_death = [bool(re.match(r"\s*death", str(r), re.I)) for r in ev.event_root]
    d = ev[is_death]
    return {(p, float(j), str(h)) for p, j, h in zip(d.person_id, d.event_jd, d.houses)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--population", type=Path, required=True, help="Phase-3 Lahiri store (person set only)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, default=Path("E:/astro/data/validation/phase3J_results.json"))
    ap.add_argument("--sink", type=Path, default=None)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(rt.SEED)
    ev, master, death_age = rt.load_events(a.derived)
    pop = set(pd.read_parquet(a.population, columns=["person_id"]).person_id.unique())
    ev = ev[ev.person_id.isin(pop)]
    sets_all = rt.build_sets(ev, master, death_age, pop, rng)          # identical to Phase 3 (same draw)
    dk = death_keys(ev)
    sets = [dict(s, precision=s["level"], level="MD") for s in sets_all
            if (s["case"], float(s["event_jd"]), str(s["houses"])) not in dk]
    need = sorted({p for s in sets for p in (s["case"], *s["controls"])})
    m = master.set_index("person_id")
    rows = [dict(m.loc[p, ["birth_date", "birth_time", "tz_offset", "latitude", "longitude"]], person_id=p)
            for p in need]
    store = build_store(rows, "lahiri", a.workers)
    kept = [s for s in sets if all(p in store.data for p in (s["case"], *s["controls"]))]
    groups = {"P_y": [s for s in kept if s["precision"] == "MD"], "P_d": [s for s in kept if s["precision"] == "AD"]}
    out: dict = {"n_sets_phase3": len(sets_all), "n_death_excluded": len(sets_all) - len(sets),
                 "n_sets_kept": len(kept), "n_people_cast": len(store.data), "n_people_needed": len(need),
                 "n_by_group": {k: len(v) for k, v in groups.items()}}

    # ---- 1. gates first (PHASE3_AMENDMENT_1) ----
    gates_ok = True
    for tag, ss in groups.items():
        xc, xk, _ = rt.score(ss, store)
        for kind in ("sham", "planted"):
            g = rt.calibrate(xc, xk, [s["case"] for s in ss], kind, rng)
            out[f"{kind}_{tag}"] = g
            gates_ok &= g["pass"]
    out["gates_ok"] = bool(gates_ok)
    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    if not gates_ok:
        a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
        raise SystemExit("[3J] CONTROL GATE FAILED -- real comparison NOT made")

    # ---- 2. placebo, then real ----
    res = {}
    for tag, ss in groups.items():
        out[f"{tag}_placebo"] = effects(ss, store, "placebo", rng)
        r = effects(ss, store, "real", rng)
        xc, xk, _ = rt.score(ss, store)
        r["clr_or"] = rt.clr_or(xc, xk)
        res[tag] = out[f"{tag}_real"] = r
        out[f"S2_{tag}"] = specificity(ss, store, rng)
        out[f"{tag}_lagna_ak_karakamsa"] = effects(ss, store, "lagna_ak_karakamsa", rng)
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
        result = Result(test_id=f"phase3j:{tag}", prereg_id=PREREG, engine="parashara", statistic="hit_diff",
                        unit="event", effect=rs["E"], se=rs["se"], se0=rs["se0"], sesoi=rt.SESOI, n_cases=rs["n"],
                        n_clusters=rs["n_people"], sham_ok=True, n_controls=rs["n"] * rt.K_CONTROLS,
                        ci95_override=rs["ci"], planted_recovered=out[f"planted_{tag}"]["pass"],
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
    for tag, ss in groups.items():
        sub = [s for s in ss if all(p in ram.data for p in (s["case"], *s["controls"]))]
        out[f"{tag}_raman_ayanamsa"] = effects(sub, ram, "real", rng)

    a.out_json.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    a.out.write_text(markdown(out), encoding="utf-8")
    print(markdown(out).encode("ascii", "replace").decode())
    return 0


def _eff(name: str, r: dict) -> str:
    rs, wp = r["rs"], r["wp"]
    return (f"| {name} | {rs['n']} | {rs['coverage']:.3f} | {rs['E']:+.4f} | {rs['ci'][0]:+.4f}..{rs['ci'][1]:+.4f} "
            f"| {wp['E']:+.4f} | {wp['ci'][0]:+.4f}..{wp['ci'][1]:+.4f} |")


def markdown(o: dict) -> str:
    L = ["# Phase 3J results: Jaimini chara dasha timing", "",
         f"Per `docs/validation/PHASE3J_JAIMINI_PREREG.md` ({PREREG}). Parashara engine `chara_dasha`, Lahiri, "
         f"mahadasha level. Phase 3 risk sets {o['n_sets_phase3']}; death events excluded {o['n_death_excluded']}; "
         f"kept {o['n_sets_kept']} (year-dated {o['n_by_group']['P_y']}, day-dated {o['n_by_group']['P_d']}); "
         f"charts cast {o['n_people_cast']}/{o['n_people_needed']}. Gates passed: **{o['gates_ok']}**.", "",
         "Exposure: the running chara dasa sign is the event house's sign from the Lagna (CONVENTION, Raman SJ "
         "art.159). E_rs = case − 10 matched controls; E_wp = case at the event − own lifetime share (ages 15–75). "
         "SIGNAL needs both CIs above 0 (Holm over P_y, P_d). SESOI 0.03.", "",
         "## Primaries", "",
         "| test | n | control coverage | E_rs | 95% CI | E_wp | 95% CI | CLR OR | MDE80 | Holm p | p_TOST | verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for tag, lbl in (("P_y", "P_y: chara MD sign = house (year-dated)"), ("P_d", "P_d: chara MD sign = house (day-dated)")):
        r = o[f"{tag}_real"]
        rs, wp = r["rs"], r["wp"]
        L.append(f"| {lbl} | {rs['n']} | {rs['coverage']:.3f} | {rs['E']:+.4f} | {rs['ci'][0]:+.4f}..{rs['ci'][1]:+.4f} "
                 f"| {wp['E']:+.4f} | {wp['ci'][0]:+.4f}..{wp['ci'][1]:+.4f} | {(r['clr_or'] or float('nan')):.3f} "
                 f"| {r['mde80']:.3f} | {r['holm_p']:.3f} | {r['p_tost']:.3f} | **{r['verdict']}** |")
    L += ["", "## Control gates (500 draws, before the real comparison)", "",
          "| gate | target | mean E | SD | CI coverage | pass |", "|---|---|---|---|---|---|"]
    for k in ("sham_P_y", "planted_P_y", "sham_P_d", "planted_P_d"):
        g = o[k]
        L.append(f"| {k} | {g['target']:+.3f} | {g['mean_E']:+.4f} | {g['sd_E']:.4f} | {g['coverage']:.3f} | {g['pass']} |")
    L += ["", "## Placebo, sensitivity, families (descriptive)", "",
          "| arm | n | coverage | E_rs | 95% CI | E_wp | 95% CI |", "|---|---|---|---|---|---|---|"]
    for tag in ("P_y", "P_d"):
        for k in (f"{tag}_placebo", f"{tag}_raman_ayanamsa", f"{tag}_lagna_ak_karakamsa",
                  f"{tag}_rodden_AA", f"{tag}_rodden_A"):
            if k in o:
                L.append(_eff(k, o[k]))
        for f, r in o.get(f"{tag}_by_family", {}).items():
            L.append(_eff(f"{tag} family: {f}", r))
    L += ["", "| secondary | E | 95% CI | p |", "|---|---|---|---|"]
    for k in ("S2_P_y", "S2_P_d"):
        r = o[k]
        L.append(f"| {k} specificity | {r['E']:+.4f} | {r['ci'][0]:+.4f}..{r['ci'][1]:+.4f} | {r['p']:.3f} |")
    L += ["", "Antardashas deferred (rulings Q4), so there is no AD-level test. Death events are excluded (rulings Q5). "
          "Shams check arithmetic only; the placebo (sequence seeded at Lagna + 1) is the informative control.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
