"""Dasha + double-transit validation on real outcomes (DOUBLE_TRANSIT_PREREG.md).

Double transit (DT) = transiting Jupiter AND Saturn each occupy or fully aspect (BPHS-26: Jupiter
5/7/9, Saturn 3/7/10, both the 7th) the natal house sign OR its lord's natal sign. Primary
instruments: dasha activation (stored AD windows targeting the house, any quality; maraka AD for
death) AND DT. Transit-only variants are reported but are never the headline.

Controls exactly as `timing_tests.py`: within-person control dates (K=min(20, span-1), +/-1yr
blackout), cross-chart same-age control (M=20), person-clustered bootstrap, coverage >= 0.6 withheld.
Day-precision events only (pre-registered).

Usage:
    py -3.12 -m tools.parashara.astrobank.transit_tests --raman-root E:/astro/data/astro_databank/derived/raman --store E:/astro/data/astro_databank/derived/parashara
    # AMENDMENT_1 (pooled A+B = primary store + extension store)
    py -3.12 -m tools.parashara.astrobank.transit_tests --raman-root <raman> --store <parashara> --store <parashara_ext> --population pooled
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

from app.parashara.primitives.graha_drishti import aspects_sign

_YEAR = 365.2425
_M_CROSS = 20
_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL

#: (test_id, event pattern, exclusion, house for DT, dasha leg: 'h7' | 'maraka' | None)
TESTS = [
    ("marriage_H7_DT", r"marriage", r"death of|divorce", 7, "h7"),
    ("divorce_H7_DT", r"divorce", r"death of", 7, "h7"),
    ("death_H8_DT", r"^death", r"death of", 8, "maraka"),
    ("marriage_H7_transit_only", r"marriage", r"death of|divorce", 7, None),
    ("divorce_H7_transit_only", r"divorce", r"death of", 7, None),
    ("death_H8_transit_only", r"^death", r"death of", 8, None),
]


POPULATIONS = ("store", "extension", "pooled")   # tierC withdrawn: AMENDMENT_2


def select_people(population: str, cast: set[str], store_pop: set[str],
                  tier: dict[str, str]) -> set[str]:
    """Who each AMENDMENT_1 analysis reads. Only people with a cast chart are eligible."""
    ab = {p for p in cast if tier.get(p) in ("A", "B")}
    if population == "store":
        return ab & store_pop
    if population == "extension":
        return ab - store_pop
    if population == "pooled":
        return ab
    raise ValueError(population)


def _jd(y: int, m: int, d: int) -> float:
    return swe.julday(int(y), max(1, int(m)), max(1, int(d)), 12.0, swe.GREG_CAL)


@lru_cache(maxsize=None)
def _transit(day: int) -> tuple[int, int]:
    """(Jupiter sign, Saturn sign), Lahiri sidereal, at noon of JD day `day`."""
    jd = day + 0.0
    j = int(swe.calc_ut(jd, swe.JUPITER, _FLAGS)[0][0] % 360.0 // 30) + 1
    s = int(swe.calc_ut(jd, swe.SATURN, _FLAGS)[0][0] % 360.0 // 30) + 1
    return j, s


def _bears(planet: str, psign: int, targets: tuple[int, int]) -> bool:
    return any(psign == t or aspects_sign(planet, psign, t) for t in targets)


def _dt(jd: float, targets: tuple[int, int]) -> bool:
    j, s = _transit(int(round(jd)))
    return _bears("Jupiter", j, targets) and _bears("Saturn", s, targets)


def _in(jd: float, wins: np.ndarray) -> bool:
    return bool(len(wins)) and bool(np.any((wins[:, 0] <= jd) & (jd < wins[:, 1])))


def _cluster_ci(values: np.ndarray, pids: np.ndarray, rng) -> tuple[float, float]:
    uniq = np.unique(pids)
    idx = {p: np.where(pids == p)[0] for p in uniq}
    boots = [float(values[np.concatenate([idx[p] for p in rng.choice(uniq, len(uniq))])].mean())
             for _ in range(2000)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(lo), float(hi)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--raman-root", type=Path, required=True)
    ap.add_argument("--store", type=Path, action="append", required=True,
                    help="Parashara store dir; repeat to pool (e.g. primary + extension)")
    ap.add_argument("--population", choices=POPULATIONS, default="store",
                    help="store = original run (default); extension / pooled = AMENDMENT_1 A+B "
                         "(the tier-C confirmation is withdrawn by AMENDMENT_2)")
    a = ap.parse_args(argv)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    rng = np.random.default_rng(20260724)

    def _cat(name: str) -> pd.DataFrame:
        return pd.concat([pd.read_parquet(st / name) for st in a.store], ignore_index=True)
    natal = _cat("natal.parquet").drop_duplicates("person_id").set_index("person_id")
    sig = _cat("sig_windows.parquet")
    mar = _cat("maraka_windows.parquet")
    h7_wins = {p: g[["jd_start", "jd_end"]].to_numpy()
               for p, g in sig[(sig.house == 7) & (sig.level == "AD")].groupby("person_id")}
    mar_wins = {p: g[["jd_start", "jd_end"]].to_numpy()
                for p, g in mar[mar.level == "AD"].groupby("person_id")}
    master = pd.read_parquet(a.raman_root / "person_master.parquet")[
        ["person_id", "birth_date", "quality_tier"]]
    master["birth_jd"] = [_jd(int(b[:4]), int(b[5:7] or 1), int(b[8:10] or 1))
                          if len(b) >= 10 else np.nan for b in master.birth_date]
    master = master.set_index("person_id")
    ev = pd.read_parquet(a.raman_root / "person_events.parquet")
    pop = set(pd.read_parquet(a.raman_root / "store_population.parquet").person_id)
    ok_people = select_people(a.population, set(natal.index), pop,
                              dict(zip(master.index, master.quality_tier)))
    ev = ev[ev.person_id.isin(ok_people)]
    death_year: dict[str, int] = {}
    for r in ev.itertuples():
        if r.event_root.startswith("Death") and "death of" not in f"{r.event_root} {r.event_subtype}".lower():
            death_year[r.person_id] = min(r.event_year, death_year.get(r.person_id, 9999))
    ev_by_pid = {p: g for p, g in ev.groupby("person_id")}
    everyone = sorted(ok_people)
    results: dict[str, dict] = {}

    for tid, pat, excl, house, leg in TESTS:
        def inst(pid: str, jd: float) -> bool:
            n = natal.loc[pid]
            if not _dt(jd, (int(n[f"h{house}_sign"]), int(n[f"h{house}_lord_sign"]))):
                return False
            if leg == "h7":
                return _in(jd, h7_wins.get(pid, np.empty((0, 2))))
            if leg == "maraka":
                return _in(jd, mar_wins.get(pid, np.empty((0, 2))))
            return True

        lifts, excess, pids, covs = [], [], [], []
        for r in ev.itertuples():
            if r.date_precision != "day":
                continue
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
            real_jd = _jd(r.event_year, r.event_month, r.event_day)
            if not (lo <= real_jd <= hi + _YEAR):
                continue
            real = inst(pid, real_jd)
            same = [_jd(e.event_year, max(1, e.event_month), max(1, e.event_day))
                    for e in ev_by_pid[pid].itertuples()
                    if re.search(pat, f"{e.event_root} {e.event_subtype}".lower())]
            k = int(min(20, max(1, (hi - lo) / _YEAR - 1)))
            ctrl, tries = [], 0
            while len(ctrl) < k and tries < k * 8:
                tries += 1
                cjd = float(rng.uniform(lo, hi))
                if not any(abs(cjd - s) < _YEAR for s in same):
                    ctrl.append(inst(pid, cjd))
            if not ctrl:
                continue
            age_days = real_jd - bjd
            others = [o for o in rng.choice(everyone, size=_M_CROSS + 1, replace=False)
                      if o != pid][:_M_CROSS]
            cross = [inst(o, master.at[o, "birth_jd"] + age_days) for o in others]
            grid = np.linspace(lo, hi, 60)
            covs.append(float(np.mean([inst(pid, g) for g in grid])))
            lifts.append(float(real) - float(np.mean(ctrl)))
            excess.append(float(real) - float(np.mean(cross)))
            pids.append(pid)
        if not lifts:
            results[tid] = {"n_events": 0}
            continue
        la, xa, pa = np.asarray(lifts), np.asarray(excess), np.asarray(pids)
        cov = float(np.mean(covs))
        l_lo, l_hi = _cluster_ci(la, pa, rng)
        x_lo, x_hi = _cluster_ci(xa, pa, rng)
        withheld = cov >= 0.6
        passes = (not withheld) and l_lo > 0 and x_lo > 0     # predicted (positive) direction
        status = "WITHHELD" if withheld else ("PASS" if passes else "null")
        results[tid] = {"n_events": int(len(la)), "n_people": int(len(np.unique(pa))),
                        "coverage": cov, "mean_lift": float(la.mean()), "lift_ci": [l_lo, l_hi],
                        "cross_excess": float(xa.mean()), "excess_ci": [x_lo, x_hi],
                        "status": status, "headline": leg is not None}
        print(f"[{tid}] n={len(la)} people={len(np.unique(pa))} coverage={cov:.2f}  "
              f"lift={la.mean():+.4f} CI=({l_lo:+.4f},{l_hi:+.4f})  "
              f"cross={xa.mean():+.4f} CI=({x_lo:+.4f},{x_hi:+.4f})  -> {status}")
    suffix = "" if a.population == "store" else f"_{a.population}"
    (a.store[0] / f"transit_results{suffix}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
