"""Phase 4.3: whole-chart blind matching (docs/validation/PHASE4_3_MATCHING_PREREG.md).

True chart vs 4 decoys (same place; regime S: within +/-3 days, regime Y: same year; random clock
time). Profile = verdict-axis outcome labels. Score = sum of +1/-1/0 pole matches; tie-split top-1.
Controls run first: planted recovery (profile drawn from the true chart's own verdicts) and sham
(a 5th same-day decoy posing as the true chart).

Usage:
    py -3.12 -m tools.validation.blind_matching --derived E:/astro/data/astro_databank/derived --out docs/validation/PHASE4_3_RESULTS.md --sink E:/astro/data/validation/results.jsonl
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

from tools.parashara.synthesis_report_card import SYNTH_TO_RAMAN
from tools.validation.result import Result, emit
from tools.validation.stats import mde80

PREREG = "PHASE4_3_MATCHING_PREREG@39dfc2ce"
SEED = 20261014
SESOI = 0.03
N_S, N_Y = 5, 4          # 5 same-day decoys: 4 for the test, the 5th poses as "true" in the sham


def _verdicts(job: tuple[str, int, int, int, int, int, float, float, float]) -> tuple[str, int, dict | None]:
    pid, idx, y, mo, d, minute, tz, lat, lon = job
    try:
        from app.parashara.chart.cast import cast
        from app.parashara.reading import read
        from app.parashara.synthesis import synthesize
        rep = synthesize(read(cast(year=y, month=mo, day=d, hour=minute // 60, minute=minute % 60,
                                   tz_offset=tz, latitude=lat, longitude=lon)))
        return pid, idx, {h: SYNTH_TO_RAMAN.get(j.verdict) for h, j in rep.houses.items()}
    except Exception:  # noqa: BLE001
        return pid, idx, None


def decoy_jobs(row, rng) -> list[tuple]:
    """idx 0 = true chart; 1..5 regime S; 6..9 regime Y."""
    y, mo, d = (int(x) for x in row.birth_date.split("-"))
    t = row.birth_time
    base = (row.person_id, float(row.tz_offset), float(row.latitude), float(row.longitude))
    jobs = [(base[0], 0, y, mo, d, int(t[:2]) * 60 + int(t[3:5]), *base[1:])]
    jd = swe.julday(y, mo, d, 12.0, swe.GREG_CAL)
    for k in range(N_S):
        yy, mm, dd, _ = swe.revjul(jd + int(rng.integers(-3, 4)), swe.GREG_CAL)
        jobs.append((base[0], 1 + k, yy, mm, dd, int(rng.integers(0, 1440)), *base[1:]))
    j0 = swe.julday(y, 1, 1, 12.0, swe.GREG_CAL)
    days = int(swe.julday(y + 1, 1, 1, 12.0, swe.GREG_CAL) - j0)
    for k in range(N_Y):
        yy, mm, dd, _ = swe.revjul(j0 + int(rng.integers(0, days)), swe.GREG_CAL)
        jobs.append((base[0], 1 + N_S + k, yy, mm, dd, int(rng.integers(0, 1440)), *base[1:]))
    return jobs


def score(chart: dict, profile: list[tuple[int, str]]) -> int:
    s = 0
    for h, direction in profile:
        pole = chart.get(h)
        if pole in ("favourable", "afflicted"):
            s += 1 if pole == direction else -1
    return s


def tie_split_hit(true_score: int, decoy_scores: list[int]) -> tuple[float, float]:
    """(hit credit, rank of the true chart with ties averaged)."""
    allsc = [true_score, *decoy_scores]
    top = max(allsc)
    hit = (1.0 / allsc.count(top)) if true_score == top else 0.0
    higher = sum(s > true_score for s in decoy_scores)
    ties = sum(s == true_score for s in decoy_scores)
    return hit, 1 + higher + ties / 2


def evaluate(charts: dict, profiles: dict, true_idx: int, decoy_idx: list[int]) -> tuple[np.ndarray, np.ndarray]:
    hits, ranks = [], []
    for pid, prof in profiles.items():
        c = charts.get(pid, {})
        if true_idx not in c or any(i not in c for i in decoy_idx):
            continue
        h, r = tie_split_hit(score(c[true_idx], prof), [score(c[i], prof) for i in decoy_idx])
        hits.append(h); ranks.append(r)
    return np.array(hits), np.array(ranks)


def summarize(hits: np.ndarray, ranks: np.ndarray, rng) -> dict:
    boots = [hits[rng.integers(0, len(hits), len(hits))].mean() for _ in range(2000)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n": int(len(hits)), "hit_rate": float(hits.mean()), "effect": float(hits.mean() - 0.2),
            "ci": (float(lo - 0.2), float(hi - 0.2)), "se": float((hi - lo) / 3.919928),
            "mean_rank": float(ranks.mean())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, default=Path("E:/astro/data/validation/phase4_3_results.json"))
    ap.add_argument("--sink", type=Path, default=None)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(SEED)
    R = a.derived / "raman"
    lab = pd.read_parquet(R / "labels.parquet")
    lab = lab[(lab.axis == "verdict") & lab.strength.isin(["core", "supporting"]) & lab.quality_tier.isin(["A", "B"])]
    profiles = {p: list(zip(g.house.astype(int), g.direction)) for p, g in lab.groupby("person_id")}
    master = pd.read_parquet(R / "person_master.parquet")
    master = master[master.person_id.isin(profiles) & master.birth_time.str.match(r"^\d\d:\d\d")
                    & master.birth_date.str.match(r"^\d{4}-\d\d-\d\d$")].dropna(
        subset=["tz_offset", "latitude", "longitude"])
    jobs = [j for r in master.itertuples() for j in decoy_jobs(r, rng)]
    charts: dict[str, dict[int, dict]] = {}
    with mp.Pool(a.workers) as pool:
        for pid, idx, v in pool.imap_unordered(_verdicts, jobs, chunksize=50):
            if v is not None:
                charts.setdefault(pid, {})[idx] = v
    profiles = {p: profiles[p] for p in charts}
    S, Y = list(range(1, 5)), list(range(1 + N_S, 1 + N_S + N_Y))
    out: dict = {"n_people": len(profiles), "n_labels": int(sum(len(v) for v in profiles.values()))}

    # ---- controls first ----
    planted = {}
    for pid, prof in profiles.items():
        tc = charts[pid].get(0, {})
        pl = []
        for h, _ in prof:
            pole = tc.get(h)
            if pole not in ("favourable", "afflicted"):
                pole = "favourable" if rng.random() < 0.5 else "afflicted"
            if rng.random() >= 0.75:
                pole = "afflicted" if pole == "favourable" else "favourable"
            pl.append((h, pole))
        planted[pid] = pl
    out["planted"] = summarize(*evaluate(charts, planted, 0, S), rng)
    out["sham"] = summarize(*evaluate(charts, profiles, 5, S), rng)
    planted_ok = out["planted"]["ci"][0] > SESOI
    sham_ok = out["sham"]["ci"][0] <= 0 <= out["sham"]["ci"][1]
    out["controls_ok"] = bool(planted_ok and sham_ok)
    if not out["controls_ok"]:
        a.out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")
        raise SystemExit(f"[4.3] CONTROL FAILED planted_ok={planted_ok} sham_ok={sham_ok}; real profiles NOT scored")

    # ---- real ----
    out["S"] = summarize(*evaluate(charts, profiles, 0, S), rng)
    out["Y"] = summarize(*evaluate(charts, profiles, 0, Y), rng)
    for reg in ("S", "Y"):
        r = out[reg]
        res = Result(test_id=f"phase4_3:{reg}", prereg_id=PREREG, engine="parashara", statistic="hit_rate-0.2",
                     unit="person", effect=r["effect"], se=r["se"], se0=float(np.sqrt(0.16 / r["n"])), sesoi=SESOI,
                     n_cases=r["n"], n_clusters=r["n"], sham_ok=sham_ok, ci95_override=r["ci"],
                     planted_recovered=planted_ok, config={"regime": reg, "mean_rank": r["mean_rank"]})
        r.update(verdict=res.verdict, p_tost=res.p_tost, mde80=mde80(float(np.sqrt(0.16 / r["n"]))))
        if a.sink:
            emit(res, a.sink)
    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    a.out_json.write_text(json.dumps(out, indent=2), encoding="utf-8")
    L = ["# Phase 4.3 results: whole-chart blind matching", "",
         f"Per `docs/validation/PHASE4_3_MATCHING_PREREG.md` ({PREREG}). Parashara engine. "
         f"{out['n_people']} people (A+B), {out['n_labels']} verdict-axis labels. Chance hit rate 0.20, mean rank 3.0.", "",
         "| arm | n | hit rate | effect (−0.20) | 95% CI | mean rank of true chart | MDE80 | p_TOST | verdict |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k, lbl in (("planted", "CONTROL planted (profile drawn from the true chart)"), ("sham", "CONTROL sham (decoy posing as true)"),
                   ("S", "**PRIMARY regime S** (decoys ±3 days)"), ("Y", "secondary regime Y (decoys same year)")):
        r = out[k]
        L.append(f"| {lbl} | {r['n']} | {r['hit_rate']:.4f} | {r['effect']:+.4f} | {r['ci'][0]:+.4f}..{r['ci'][1]:+.4f} "
                 f"| {r['mean_rank']:.3f} | {r.get('mde80', float('nan')):.3f} | {r.get('p_tost', float('nan')):.3f} "
                 f"| {r.get('verdict', 'pass' if k == 'planted' and planted_ok or k == 'sham' and sham_ok else '')} |")
    a.out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
