"""Stage 10 — the pre-registered confirmatory study + two direct doctrine tests.

Runs EXACTLY what CONFIRMATORY_PREREG.md (committed first) registers:
  1. CONFIRMATORY: suicide -> afflicted H8 death on the HELD-OUT tier-C sample (+ sham companion).
  2. Kuja dosha (Mars in 2/4/7/8/12 from Lagna, HTJAH-II:2579-2632) vs divorce — direct chart test.
  3. Saturn-afflicted Moon vs suicide — direct chart test (+ registered secondaries).

Usage: py -3.12 -m tools.raman_saab.astrobank.confirmatory_study
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from tools.raman_saab.astrobank._stats import auc_mw, bootstrap_auc_ci, bh_fdr
from tools.raman_saab.astrobank._worker import init_worker

_OUT = Path("data/astro_databank/derived/raman")
_KUJA = {2, 4, 7, 8, 12}
_SCORE = {("afflicted", "strong"): 0.0, ("afflicted", "moderate"): 0.17, ("afflicted", "mild"): 0.33,
          ("mixed", "strong"): 1.0, ("mixed", "moderate"): 1.0, ("mixed", "mild"): 1.0,
          ("favourable", "mild"): 1.67, ("favourable", "moderate"): 1.83,
          ("favourable", "strong"): 2.0}


def _features_one(row: dict) -> dict | None:
    """Cast one chart -> the doctrine primitives Studies 2-3 need."""
    try:
        from app.raman_saab.chart.adapter import cast_chart
        from app.raman_saab.chart.model import BirthData
        from app.raman_saab.doctrine import drishti
        pid = row["person_id"]
        y, mo, d = (int(x) for x in row["birth_date"].split("-"))
        t = row["birth_time"]
        ch = cast_chart(BirthData(name=pid, year=y, month=mo, day=d, hour=int(t[:2]),
                                  minute=int(t[3:5]), tz_offset=float(row["tz_offset"]),
                                  latitude=float(row["latitude"]),
                                  longitude=float(row["longitude"])), ayanamsa="raman")
        mars, moon, sun, sat = (ch.planets.get(p) for p in ("Mars", "Moon", "Sun", "Saturn"))
        mars_from_moon = ((mars.sign - moon.sign) % 12) + 1 if mars and moon else None
        return {
            "person_id": pid,
            "kuja_lagna": mars.rasi_house in _KUJA if mars else None,
            "kuja_moon": (mars_from_moon in _KUJA) if mars_from_moon else None,
            "moon_sat_afflicted": bool(moon and sat and (
                sat.rasi_house == moon.rasi_house
                or drishti.aspects_planet("Saturn", "Moon", ch))),
            "moon_mars_afflicted": bool(moon and mars and (
                mars.rasi_house == moon.rasi_house
                or drishti.aspects_planet("Mars", "Moon", ch))),
            "moon_waning": bool(moon and sun and ((moon.lon - sun.lon) % 360.0) >= 180.0),
        }
    except Exception:  # noqa: BLE001
        return None


def _fisher(a_pos: int, a_n: int, b_pos: int, b_n: int) -> dict:
    """One-sided Fisher (greater): is the rate in A higher than in B?"""
    table = [[a_pos, a_n - a_pos], [b_pos, b_n - b_pos]]
    orr, p = stats.fisher_exact(table, alternative="greater")
    # log-OR normal CI (Woolf, 0.5 correction)
    aa, ab, ba, bb = a_pos + .5, a_n - a_pos + .5, b_pos + .5, b_n - b_pos + .5
    se = float(np.sqrt(1/aa + 1/ab + 1/ba + 1/bb))
    lo, hi = np.exp(np.log(aa*bb/(ab*ba)) - 1.96*se), np.exp(np.log(aa*bb/(ab*ba)) + 1.96*se)
    return {"rate_case": a_pos / a_n, "rate_ctrl": b_pos / b_n, "odds_ratio": float(orr),
            "or_ci": [float(lo), float(hi)], "p_one_sided": float(p),
            "n_case": a_n, "n_ctrl": b_n}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    labels = pd.read_parquet(_OUT / "labels.parquet")
    verd = pd.read_parquet(_OUT / "verdicts.parquet")
    master = pd.read_parquet(_OUT / "person_master.parquet").set_index("person_id")
    pop = pd.read_parquet(_OUT / "store_population.parquet")
    by_map = {m: set(g.person_id) for m, g in labels.groupby("map_id")}
    in_store = set(verd.person_id)
    tierC = set(master[master.quality_tier == "C"].index)
    tierAB = set(master[master.quality_tier.isin(["A", "B"])].index)
    results: dict[str, dict] = {}

    # ══ STUDY 1 — CONFIRMATORY (held-out tier C), pure store query ═══════════
    death = verd[(verd.house == 8) & (verd.signification == "death")].set_index("person_id")
    death_score = pd.Series({p: _SCORE.get((r.verdict, r.degree), np.nan)
                             for p, r in death.iterrows()}).dropna()
    cases1 = (by_map["H8_SUICIDE"] & tierC & in_store)
    ctrl1 = ((set(labels.person_id) - by_map["H8_SUICIDE"] - by_map.get("H8_ACCIDENT", set()))
             & tierC & in_store)
    cv = death_score[death_score.index.isin(cases1)].to_numpy()
    kv = death_score[death_score.index.isin(ctrl1)].to_numpy()
    r1 = auc_mw(cv, kv, "afflicted")
    lo, hi, _ = bootstrap_auc_ci(cv, kv, "afflicted")
    results["S1_suicide_confirmatory"] = {**r1, "ci": [lo, hi],
                                          "held_out": True, "prereg_prediction": 0.53}
    print(f"[S1 CONFIRMATORY] held-out tier-C suicide vs controls: "
          f"AUC={r1['auc']:.3f} CI=({lo:.3f},{hi:.3f}) p={r1['p']:.4f} "
          f"n={r1['n_case']}/{r1['n_contrast']}")
    # sham companion: tier-C expatriate on H5 children
    child = verd[(verd.house == 5) & (verd.signification == "children")].set_index("person_id")
    child_score = pd.Series({p: _SCORE.get((r.verdict, r.degree), np.nan)
                             for p, r in child.iterrows()}).dropna()
    expat = {pid for pid in (set(labels.person_id) & tierC & in_store)
             if "lifestyle : home : expatriate" in
             {t.strip().casefold() for t in str(master.categories_raw.get(pid, "")).split(";")}}
    sc = child_score[child_score.index.isin(expat)].to_numpy()
    sk = child_score[child_score.index.isin((set(labels.person_id) & tierC & in_store) - expat)].to_numpy()
    rs = auc_mw(sc, sk, "afflicted")
    slo, shi, _ = bootstrap_auc_ci(sc, sk, "afflicted", n_boot=400)
    results["S1_sham"] = {**rs, "ci": [slo, shi]}
    print(f"[S1 sham] tier-C expatriate->H5: AUC={rs['auc']:.3f} CI=({slo:.3f},{shi:.3f})  "
          f"{'NULL (pipeline valid)' if slo <= 0.5 <= shi else 'SIGNAL - INVESTIGATE'}")

    # ══ chart-feature extraction for Studies 2-3 ═════════════════════════════
    s2_universe = (by_map["H7_DIVORCED"] | by_map["H7_LONGMARRIAGE"]) & tierAB
    ctrl3 = set(pop[pop.is_control].person_id) & tierAB
    s3_universe = (by_map["H8_SUICIDE"] & tierAB) | ctrl3
    need = sorted(s2_universe | s3_universe)
    sel = master.loc[master.index.isin(need)].reset_index()
    rows = sel[["person_id", "birth_date", "birth_time", "tz_offset",
                "latitude", "longitude"]].to_dict("records")
    print(f"[extract] casting {len(rows)} charts for the direct doctrine tests...")
    with mp.Pool(processes=max(1, (mp.cpu_count() or 4) - 2), initializer=init_worker) as pool:
        feats = [f for f in pool.imap_unordered(_features_one, rows, chunksize=200) if f]
    F = pd.DataFrame(feats).set_index("person_id")
    print(f"[extract] features for {len(F)} charts")

    # ══ STUDY 2 — Kuja dosha vs divorce ══════════════════════════════════════
    div = F[F.index.isin(by_map["H7_DIVORCED"])]
    lm = F[F.index.isin(by_map["H7_LONGMARRIAGE"])]
    r2 = _fisher(int(div.kuja_lagna.sum()), len(div), int(lm.kuja_lagna.sum()), len(lm))
    results["S2_kuja_divorce"] = r2
    print(f"[S2 KUJA-DOSHA] divorced dosha-rate={r2['rate_case']:.3f} vs "
          f"long-marriage={r2['rate_ctrl']:.3f}  OR={r2['odds_ratio']:.2f} "
          f"CI=({r2['or_ci'][0]:.2f},{r2['or_ci'][1]:.2f}) p={r2['p_one_sided']:.4f}")
    r2m = _fisher(int(div.kuja_moon.sum()), len(div), int(lm.kuja_moon.sum()), len(lm))
    results["S2_kuja_from_moon_secondary"] = r2m
    print(f"[S2 secondary: from-Moon] OR={r2m['odds_ratio']:.2f} p={r2m['p_one_sided']:.4f}")

    # ══ STUDY 3 — Saturn-afflicted Moon vs suicide ═══════════════════════════
    su = F[F.index.isin(by_map["H8_SUICIDE"])]
    ct = F[F.index.isin(ctrl3)]
    r3 = _fisher(int(su.moon_sat_afflicted.sum()), len(su),
                 int(ct.moon_sat_afflicted.sum()), len(ct))
    results["S3_moon_saturn_suicide"] = r3
    print(f"[S3 MOON-SATURN] suicide afflicted-Moon rate={r3['rate_case']:.3f} vs "
          f"controls={r3['rate_ctrl']:.3f}  OR={r3['odds_ratio']:.2f} "
          f"CI=({r3['or_ci'][0]:.2f},{r3['or_ci'][1]:.2f}) p={r3['p_one_sided']:.4f}")
    dark = _fisher(int((su.moon_sat_afflicted & su.moon_waning).sum()), len(su),
                   int((ct.moon_sat_afflicted & ct.moon_waning).sum()), len(ct))
    results["S3_dark_moon_secondary"] = dark
    mars_c = _fisher(int(su.moon_mars_afflicted.sum()), len(su),
                     int(ct.moon_mars_afflicted.sum()), len(ct))
    results["S3_mars_comparator"] = mars_c
    print(f"[S3 secondary: waning+Saturn] OR={dark['odds_ratio']:.2f} p={dark['p_one_sided']:.4f}"
          f"   [Mars comparator] OR={mars_c['odds_ratio']:.2f} p={mars_c['p_one_sided']:.4f}")

    # family BH across the 3 primaries
    fam = {"S1": results["S1_suicide_confirmatory"]["p"],
           "S2": results["S2_kuja_divorce"]["p_one_sided"],
           "S3": results["S3_moon_saturn_suicide"]["p_one_sided"]}
    passed = bh_fdr(fam, q=0.10)
    for k, v in passed.items():
        results[{"S1": "S1_suicide_confirmatory", "S2": "S2_kuja_divorce",
                 "S3": "S3_moon_saturn_suicide"}[k]]["bh_pass"] = bool(v)
    print(f"\n[family] BH q=0.10 over 3 primaries: "
          + ", ".join(f"{k}={'PASS' if v else 'fail'}" for k, v in passed.items()))
    (_OUT / "confirmatory_results.json").write_text(
        json.dumps(results, indent=2, default=float), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
