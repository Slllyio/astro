"""Stage 4 — dasha-timing validation with a within-chart control-date null (saturation-escaping).

`active_houses` is NOT used (proven saturated). Instruments come from the Stage-2 store:
  * significator windows (MD level = MD lord in timer_set; AD level = BOTH lords — par excellence)
  * maraka windows (AD periods whose antar lord is a maraka, with weights)

Design (pre-registered, METHODOLOGY.md): each real event is compared against K=min(20, span-1)
control dates drawn uniformly from the person's eligible span [age 15, min(death-1yr, age 75)],
with a +/-1yr blackout around same-root real events. Paired lift = hit(real) - mean(hit(controls));
aggregated with a person-clustered bootstrap (2,000 resamples). Precision rule: full-date events ->
AD-level point-in-interval; year-only -> MD-level >=0.5-overlap of the event year; never mixed.
Coverage (fraction of span inside instrument windows) is the saturation alarm: a test with
coverage >= 0.6 is WITHHELD (redesign, don't report).

Usage: py -3.12 -m tools.raman_saab.astrobank.timing_tests
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import swisseph as swe

_OUT = Path("data/astro_databank/derived/raman")
_YEAR = 365.2425

#: (test_id, event pattern on root+subtype, exclusion pattern, house|'maraka', family)
EVENT_TESTS = [
    ("marriage_H7", r"marriage", r"death of|divorce", 7, "timing"),
    ("divorce_H7", r"divorce", r"death of", 7, "timing"),
    ("death_maraka", r"^death", r"death of", "maraka", "timing"),
]


def _jd(y: int, m: int, d: int) -> float:
    return swe.julday(int(y), max(1, int(m)), max(1, int(d)), 12.0, swe.GREG_CAL)


def _load():
    ev = pd.read_parquet(_OUT / "person_events.parquet")
    sig = pd.read_parquet(_OUT / "significator_windows.parquet")
    mar = pd.read_parquet(_OUT / "maraka_windows.parquet")
    pop = pd.read_parquet(_OUT / "store_population.parquet")
    master = pd.read_parquet(_OUT / "person_master.parquet")[
        ["person_id", "birth_date", "quality_tier"]]
    master["birth_jd"] = [
        _jd(int(b[:4]), int(b[5:7] or 1), int(b[8:10] or 1)) if len(b) >= 10 else np.nan
        for b in master.birth_date]
    return ev, sig, mar, pop, master.set_index("person_id")


def _windows_for(person_windows: pd.DataFrame, level: str) -> np.ndarray:
    w = person_windows[person_windows.level == level] if "level" in person_windows else person_windows
    return w[["jd_start", "jd_end"]].to_numpy()


def _hit_point(jd: float, wins: np.ndarray) -> bool:
    return bool(len(wins)) and bool(np.any((wins[:, 0] <= jd) & (jd < wins[:, 1])))


def _hit_year(y_start: float, wins: np.ndarray) -> bool:
    """>=0.5-overlap of the event year with the union of windows."""
    if not len(wins):
        return False
    y_end = y_start + _YEAR
    overlap = np.clip(np.minimum(wins[:, 1], y_end) - np.maximum(wins[:, 0], y_start), 0, None)
    return float(overlap.sum()) >= 0.5 * _YEAR   # windows are disjoint per level

def _coverage(wins: np.ndarray, span: tuple[float, float]) -> float:
    if not len(wins):
        return 0.0
    lo, hi = span
    overlap = np.clip(np.minimum(wins[:, 1], hi) - np.maximum(wins[:, 0], lo), 0, None)
    return float(overlap.sum()) / max(1.0, hi - lo)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ev, sig, mar, pop, master = _load()
    rng = np.random.default_rng(20260724)
    in_store = set(pop.person_id)
    tiers_ok = master[master.quality_tier.isin(["A", "B"])].index
    ev = ev[ev.person_id.isin(in_store) & ev.person_id.isin(tiers_ok)]

    # own-death year per person (caps the control span)
    death_year: dict[str, int] = {}
    for r in ev.itertuples():
        low = f"{r.event_root} {r.event_subtype}".lower()
        if r.event_root.startswith("Death") and "death of" not in low:
            death_year[r.person_id] = min(r.event_year, death_year.get(r.person_id, 9999))

    sig_by_pid = {pid: g for pid, g in sig.groupby("person_id")}
    mar_by_pid = {pid: g for pid, g in mar.groupby("person_id")}
    results: dict[str, dict] = {}

    for tid, pat, expat, instrument, _fam in EVENT_TESTS:
        lifts, coverages = [], []          # per-event paired lift, person keyed for clustering
        lift_pids = []
        for r in ev.itertuples():
            low = f"{r.event_root} {r.event_subtype}".lower()
            if not re.search(pat, low) or re.search(expat, low):
                continue
            pid = r.person_id
            m = master.loc[pid]
            if not np.isfinite(m.birth_jd):
                continue
            birth_jd = float(m.birth_jd)
            dy = death_year.get(pid)
            span_lo = birth_jd + 15 * _YEAR
            span_hi = birth_jd + 75 * _YEAR
            if dy:
                span_hi = min(span_hi, _jd(dy - 1, 12, 31))
            if span_hi - span_lo < 3 * _YEAR:
                continue                    # graceful drop (pre-registered)
            # instrument windows
            if instrument == "maraka":
                g = mar_by_pid.get(pid)
                wins = g[["jd_start", "jd_end"]].to_numpy() if g is not None else np.empty((0, 2))
            else:
                g = sig_by_pid.get(pid)
                if g is None:
                    continue
                g = g[g.house == instrument]
                level = "AD" if r.date_precision == "day" else "MD"
                wins = _windows_for(g, level)
            # real-event hit
            if r.date_precision == "day":
                real_jd = _jd(r.event_year, r.event_month, r.event_day)
                if not (span_lo <= real_jd <= span_hi + _YEAR):
                    continue
                real_hit = _hit_point(real_jd, wins)
            else:
                real_jd = _jd(r.event_year, 1, 1)
                real_hit = _hit_year(real_jd, wins)
            # blackout: +/-1yr around same-root events of this person
            same = [_jd(e.event_year, max(1, e.event_month), max(1, e.event_day))
                    for e in ev[ev.person_id == pid].itertuples()
                    if re.search(pat, f"{e.event_root} {e.event_subtype}".lower())]
            span_years = (span_hi - span_lo) / _YEAR
            k = int(min(20, max(1, span_years - 1)))
            ctrl_hits = []
            tries = 0
            while len(ctrl_hits) < k and tries < k * 8:
                tries += 1
                cjd = float(rng.uniform(span_lo, span_hi))
                if any(abs(cjd - s) < _YEAR for s in same):
                    continue
                ctrl_hits.append(_hit_point(cjd, wins) if r.date_precision == "day"
                                 else _hit_year(cjd, wins))
            if not ctrl_hits:
                continue
            lifts.append(float(real_hit) - float(np.mean(ctrl_hits)))
            lift_pids.append(pid)
            coverages.append(_coverage(wins, (span_lo, span_hi)))

        if not lifts:
            results[tid] = {"n": 0}
            continue
        lifts_a = np.asarray(lifts)
        pids_a = np.asarray(lift_pids)
        cov = float(np.mean(coverages))
        # person-clustered bootstrap of the mean lift
        uniq = np.unique(pids_a)
        boots = []
        for _ in range(2000):
            take = rng.choice(uniq, size=len(uniq), replace=True)
            mask_idx = np.concatenate([np.where(pids_a == p)[0] for p in take])
            boots.append(float(lifts_a[mask_idx].mean()))
        lo95, hi95 = np.percentile(boots, [2.5, 97.5])
        results[tid] = {
            "n_events": int(len(lifts_a)), "n_people": int(len(uniq)),
            "mean_lift": float(lifts_a.mean()), "ci_lo": float(lo95), "ci_hi": float(hi95),
            "hit_rate_real": float(np.mean(lifts_a > -1)),  # informational
            "coverage": cov, "withheld_saturated": bool(cov >= 0.6),
        }
        flag = "WITHHELD (coverage>=0.6)" if cov >= 0.6 else ""
        print(f"[{tid}] n={len(lifts_a)} people={len(uniq)}  lift={lifts_a.mean():+.4f} "
              f"CI=({lo95:+.4f},{hi95:+.4f})  coverage={cov:.2f} {flag}")

    (_OUT / "timing_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[timing] wrote timing_results.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
