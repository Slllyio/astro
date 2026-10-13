"""Dasha-timing validation of the Parashara synthesis on real outcomes (PARASHARA_PREREG.md).

Raman's design (`tools/raman_saab/astrobank/timing_tests.py`), unchanged where it matters: each real
event vs K = min(20, span-1) control dates from the SAME person's eligible span [age 15,
min(death-1yr, 75)], +/-1yr blackout around same-type events, paired lift, person-clustered
bootstrap (2,000). Day-precision events -> AD windows (point-in-interval); year-only -> MD windows
(>=0.5 overlap of the event year); never mixed. Coverage >= 0.6 -> WITHHELD.

NEW, committed: the CROSS-CHART control — the one that exposed Raman's death-window artefact (deaths
hit their own windows 32.3%, but other people's age-aligned windows 32.4%). Each real event is also
tested against the same instrument on M=20 OTHER people's charts at the SAME AGE; chart-specific
excess = own hit - cross-chart mean hit. Pass bar: lift CI AND excess CI both exclude 0.

Usage:
    py -3.12 -m tools.parashara.astrobank.timing_tests --raman-root E:/astro/data/astro_databank/derived/raman --store E:/astro/data/astro_databank/derived/parashara
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

_YEAR = 365.2425
_M_CROSS = 20

#: (test_id, event pattern, exclusion pattern, instrument)
EVENT_TESTS = [
    ("marriage_H7_ausp", r"marriage", r"death of|divorce", "h7_auspicious"),
    ("divorce_H7_adverse", r"divorce", r"death of", "h7_adverse"),
    ("death_maraka_both", r"^death", r"death of", "maraka_both"),
    ("death_maraka_either", r"^death", r"death of", "maraka_either"),
]


def _jd(y: int, m: int, d: int) -> float:
    return swe.julday(int(y), max(1, int(m)), max(1, int(d)), 12.0, swe.GREG_CAL)


def _hit_point(jd: float, wins: np.ndarray) -> bool:
    return bool(len(wins)) and bool(np.any((wins[:, 0] <= jd) & (jd < wins[:, 1])))


def _hit_year(y_start: float, wins: np.ndarray) -> bool:
    if not len(wins):
        return False
    overlap = np.clip(np.minimum(wins[:, 1], y_start + _YEAR) - np.maximum(wins[:, 0], y_start),
                      0, None)
    return float(overlap.sum()) >= 0.5 * _YEAR


def _coverage(wins: np.ndarray, lo: float, hi: float) -> float:
    if not len(wins):
        return 0.0
    overlap = np.clip(np.minimum(wins[:, 1], hi) - np.maximum(wins[:, 0], lo), 0, None)
    return min(1.0, float(overlap.sum()) / max(1.0, hi - lo))


def _instrument_windows(store: Path) -> dict[str, dict[str, dict[str, np.ndarray]]]:
    """instrument -> level ('AD'|'MD') -> person_id -> windows array (in JD, own birth anchor)."""
    sig = pd.read_parquet(store / "sig_windows.parquet")
    mar = pd.read_parquet(store / "maraka_windows.parquet")
    sig7 = sig[sig.house == 7]
    picks = {
        "h7_auspicious": (sig7[(sig7.level == "AD") & (sig7.quality == "auspicious")],
                          sig7[sig7.level == "MD"]),
        "h7_adverse": (sig7[(sig7.level == "AD") & (sig7.quality == "adverse")],
                       sig7[sig7.level == "MD"]),
        "maraka_both": (mar[(mar.level == "AD") & mar.both], mar[mar.level == "MD"]),
        "maraka_either": (mar[mar.level == "AD"], mar[mar.level == "MD"]),
    }
    out: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    for inst, (ad, md) in picks.items():
        out[inst] = {lvl: {pid: g[["jd_start", "jd_end"]].to_numpy()
                           for pid, g in df.groupby("person_id")}
                     for lvl, df in (("AD", ad), ("MD", md))}
    return out


def _cluster_ci(values: np.ndarray, pids: np.ndarray, rng) -> tuple[float, float]:
    uniq = np.unique(pids)
    idx = {p: np.where(pids == p)[0] for p in uniq}
    boots = []
    for _ in range(2000):
        take = rng.choice(uniq, size=len(uniq), replace=True)
        boots.append(float(values[np.concatenate([idx[p] for p in take])].mean()))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(lo), float(hi)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--raman-root", type=Path, required=True)
    ap.add_argument("--store", type=Path, required=True)
    a = ap.parse_args(argv)
    rng = np.random.default_rng(20260724)

    ev = pd.read_parquet(a.raman_root / "person_events.parquet")
    pop = pd.read_parquet(a.raman_root / "store_population.parquet")
    master = pd.read_parquet(a.raman_root / "person_master.parquet")[
        ["person_id", "birth_date", "quality_tier"]]
    master["birth_jd"] = [_jd(int(b[:4]), int(b[5:7] or 1), int(b[8:10] or 1))
                          if len(b) >= 10 else np.nan for b in master.birth_date]
    master = master.set_index("person_id")
    in_store = set(pd.read_parquet(a.store / "verdicts.parquet").person_id) & set(pop.person_id)
    ev = ev[ev.person_id.isin(in_store)
            & ev.person_id.isin(master[master.quality_tier.isin(["A", "B"])].index)]
    windows = _instrument_windows(a.store)

    death_year: dict[str, int] = {}
    for r in ev.itertuples():
        if r.event_root.startswith("Death") and "death of" not in f"{r.event_root} {r.event_subtype}".lower():
            death_year[r.person_id] = min(r.event_year, death_year.get(r.person_id, 9999))
    ev_by_pid = {pid: g for pid, g in ev.groupby("person_id")}
    results: dict[str, dict] = {}

    for tid, pat, excl, inst in EVENT_TESTS:
        pool = {lvl: list(windows[inst][lvl]) for lvl in ("AD", "MD")}
        lifts, excess, pids, covs = [], [], [], []
        for r in ev.itertuples():
            low = f"{r.event_root} {r.event_subtype}".lower()
            if not re.search(pat, low) or re.search(excl, low):
                continue
            pid = r.person_id
            bjd = master.at[pid, "birth_jd"]
            if not np.isfinite(bjd):
                continue
            lo, hi = bjd + 15 * _YEAR, bjd + 75 * _YEAR
            if pid in death_year:
                hi = min(hi, _jd(death_year[pid] - 1, 12, 31))
            if hi - lo < 3 * _YEAR:
                continue
            day = r.date_precision == "day"
            lvl = "AD" if day else "MD"
            wins = windows[inst][lvl].get(pid, np.empty((0, 2)))
            hit = _hit_point if day else _hit_year
            real_jd = _jd(r.event_year, r.event_month, r.event_day) if day else _jd(r.event_year, 1, 1)
            if day and not (lo <= real_jd <= hi + _YEAR):
                continue
            real_hit = hit(real_jd, wins)
            same = [_jd(e.event_year, max(1, e.event_month), max(1, e.event_day))
                    for e in ev_by_pid[pid].itertuples()
                    if re.search(pat, f"{e.event_root} {e.event_subtype}".lower())]
            k = int(min(20, max(1, (hi - lo) / _YEAR - 1)))
            ctrl, tries = [], 0
            while len(ctrl) < k and tries < k * 8:
                tries += 1
                cjd = float(rng.uniform(lo, hi))
                if not any(abs(cjd - s) < _YEAR for s in same):
                    ctrl.append(hit(cjd, wins))
            if not ctrl:
                continue
            # cross-chart control: other people's windows at the SAME AGE as the real event
            age_days = real_jd - bjd
            others = [o for o in rng.choice(pool[lvl], size=min(_M_CROSS + 1, len(pool[lvl])),
                                            replace=False) if o != pid][:_M_CROSS]
            cross = [hit(master.at[o, "birth_jd"] + age_days, windows[inst][lvl][o]) for o in others]
            lifts.append(float(real_hit) - float(np.mean(ctrl)))
            excess.append(float(real_hit) - (float(np.mean(cross)) if cross else 0.0))
            pids.append(pid)
            covs.append(_coverage(wins, lo, hi))
        if not lifts:
            results[tid] = {"n_events": 0}
            continue
        la, xa, pa = np.asarray(lifts), np.asarray(excess), np.asarray(pids)
        cov = float(np.mean(covs))
        l_lo, l_hi = _cluster_ci(la, pa, rng)
        x_lo, x_hi = _cluster_ci(xa, pa, rng)
        withheld = cov >= 0.6
        passes = (not withheld) and (l_lo > 0 or l_hi < 0) and (x_lo > 0 or x_hi < 0)
        results[tid] = {"n_events": int(len(la)), "n_people": int(len(np.unique(pa))),
                        "mean_lift": float(la.mean()), "lift_ci": [l_lo, l_hi],
                        "cross_excess": float(xa.mean()), "excess_ci": [x_lo, x_hi],
                        "coverage": cov, "withheld_saturated": withheld,
                        "status": "WITHHELD" if withheld else ("PASS" if passes else "null")}
        print(f"[{tid}] n={len(la)} people={len(np.unique(pa))} coverage={cov:.2f}  "
              f"lift={la.mean():+.4f} CI=({l_lo:+.4f},{l_hi:+.4f})  "
              f"cross-chart excess={xa.mean():+.4f} CI=({x_lo:+.4f},{x_hi:+.4f})  "
              f"-> {results[tid]['status']}")
    (a.store / "timing_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
