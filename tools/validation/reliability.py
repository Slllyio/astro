"""Phase 2: how reliable are the engines' own instruments? No outcomes are read; no holdout is spent.

Re-casts a hashed sample of tier-A (Rodden AA) charts with the FROZEN Parashara engine under:
  * birth-time jitter  +/-15, +/-30, +/-60 min  (tz offset shifted: UT = local - tz, so no date rollover)
  * ayanamsa           Lahiri (engine default) vs Raman vs Krishnamurti, by patching
                       `swisseph.set_sid_mode` from tools/; engine code and sha are untouched
and measures agreement + Cohen's kappa against the unperturbed cast for:
  house verdicts (6-category), dasha instruments on a 40-date grid (age 15-75), ayurdaya years.
Kappa is the reliability rho used to disattenuate every later bound (true ~ observed / rho).

Also: Raman-vs-Parashara convergence, kappa per house on the 3-pole scale (Parashara mapped by the
report card's own `SYNTH_TO_RAMAN`), raw on the full store and ayanamsa-matched on the sample.

Usage:
    py -3.12 -m tools.validation.reliability --derived E:/astro/data/astro_databank/derived --n 2000 --out docs/validation/RELIABILITY.md --out-json E:/astro/data/validation/reliability.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import swisseph as swe
from sklearn.metrics import cohen_kappa_score

from tools.parashara.astrobank.build_store import process_person
from tools.parashara.synthesis_report_card import SYNTH_TO_RAMAN

_YEAR = 365.2425
CONDITIONS: dict[str, tuple[int, int]] = {           # label -> (minutes shift, sidereal mode)
    "base": (0, swe.SIDM_LAHIRI),
    "-60m": (-60, swe.SIDM_LAHIRI), "-30m": (-30, swe.SIDM_LAHIRI), "-15m": (-15, swe.SIDM_LAHIRI),
    "+15m": (15, swe.SIDM_LAHIRI), "+30m": (30, swe.SIDM_LAHIRI), "+60m": (60, swe.SIDM_LAHIRI),
    "raman_ayanamsa": (0, swe.SIDM_RAMAN), "kp_ayanamsa": (0, swe.SIDM_KRISHNAMURTI),
}
INSTRUMENTS = {   # name -> (table, filter)
    "h7_AD_any": ("sig_windows", lambda d: d[(d.house == 7) & (d.level == "AD")]),
    "h7_AD_auspicious": ("sig_windows", lambda d: d[(d.house == 7) & (d.level == "AD")
                                                    & (d.quality == "auspicious")]),
    "h7_MD": ("sig_windows", lambda d: d[(d.house == 7) & (d.level == "MD")]),
    "maraka_AD_either": ("maraka_windows", lambda d: d[d.level == "AD"]),
    "maraka_MD": ("maraka_windows", lambda d: d[d.level == "MD"]),
}
_ORIG_SET_SID = swe.set_sid_mode
_TARGET: list[int | None] = [None]


def _patched_set_sid_mode(mode: int, t0: float = 0.0, ayan_t0: float = 0.0) -> None:
    _ORIG_SET_SID(_TARGET[0] if _TARGET[0] is not None else mode, t0, ayan_t0)


def install_ayanamsa_patch() -> None:
    """Route every engine `swe.set_sid_mode(...)` call to the mode in `_TARGET` (None = engine's own)."""
    swe.set_ephe_path(None)
    swe.set_sid_mode = _patched_set_sid_mode


def _cast(task: tuple[dict, str]) -> tuple[str, str, dict | None]:
    row, label = task
    minutes, sidm = CONDITIONS[label]
    _TARGET[0] = None if sidm == swe.SIDM_LAHIRI else sidm
    shifted = dict(row, tz_offset=float(row["tz_offset"]) - minutes / 60.0)
    return row["person_id"], label, process_person(shifted)


def sample_people(master: pd.DataFrame, cast_ok: set[str], n: int, salt: str = "reliability-v1") -> list[str]:
    """Deterministic hashed sample of tier-A people with a castable chart (no RNG to re-roll)."""
    pool = sorted(p for p in master[master.quality_tier == "A"].person_id if p in cast_ok)
    return sorted(pool, key=lambda p: hashlib.sha256(f"{salt}:{p}".encode()).hexdigest())[:n]


def _grid_hits(res: dict, table: str, filt, birth_jd: float) -> np.ndarray:
    df = pd.DataFrame(res[table])
    grid = birth_jd + np.linspace(15, 75, 40) * _YEAR
    if df.empty:
        return np.zeros(len(grid), bool)
    w = filt(df)[["jd_start", "jd_end"]].to_numpy()
    if not len(w):
        return np.zeros(len(grid), bool)
    return ((w[:, 0][None, :] <= grid[:, None]) & (grid[:, None] < w[:, 1][None, :])).any(1)


def _kappa(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    if len(set(a.tolist()) | set(b.tolist())) < 2:
        return 1.0
    return float(cohen_kappa_score(a, b))


def compare(results: dict[str, dict[str, dict]], birth_jd: dict[str, float]) -> dict[str, dict]:
    """Each condition vs base: agreement + kappa per measure. Only people cast in both count."""
    out: dict[str, dict] = {}
    for label in CONDITIONS:
        if label == "base":
            continue
        pids = [p for p in results if results[p].get("base") and results[p].get(label)]
        m: dict[str, Any] = {"n_people": len(pids)}
        a = [v["verdict"] for p in pids for v in sorted(results[p]["base"]["verdicts"], key=lambda x: x["house"])]
        b = [v["verdict"] for p in pids for v in sorted(results[p][label]["verdicts"], key=lambda x: x["house"])]
        m["verdict"] = {"agree": float(np.mean(np.array(a) == np.array(b))), "kappa": _kappa(a, b)}
        for name, (table, filt) in INSTRUMENTS.items():
            x = np.concatenate([_grid_hits(results[p]["base"], table, filt, birth_jd[p]) for p in pids])
            y = np.concatenate([_grid_hits(results[p][label], table, filt, birth_jd[p]) for p in pids])
            m[name] = {"agree": float(np.mean(x == y)), "kappa": _kappa(x, y), "coverage": float(x.mean())}
        ya = np.array([results[p]["base"]["ayurdaya"][0]["total_years"] for p in pids])
        yb = np.array([results[p][label]["ayurdaya"][0]["total_years"] for p in pids])
        m["ayurdaya"] = {"mean_abs_years": float(np.mean(np.abs(ya - yb))),
                         "corr": float(np.corrcoef(ya, yb)[0, 1]) if ya.std() and yb.std() else 1.0}
        out[label] = m
    return out


def convergence(raman_roll: pd.DataFrame, parashara: pd.DataFrame) -> dict[int, dict]:
    """Raman vs Parashara per house on the 3-pole scale (Parashara via SYNTH_TO_RAMAN)."""
    p = parashara.assign(pole=parashara.verdict.map(SYNTH_TO_RAMAN)).dropna(subset=["pole"])
    j = raman_roll.merge(p[["person_id", "house", "pole"]], on=["person_id", "house"])
    j = j[j.rollup.isin(["favourable", "mixed", "afflicted"])]
    return {int(h): {"n": int(len(g)), "agree": float((g.rollup == g.pole).mean()),
                     "kappa": _kappa(g.rollup, g.pole)} for h, g in j.groupby("house")}


def markdown(rel: dict, conv_raw: dict, conv_matched: dict, n: int) -> str:
    L = ["# Instrument reliability (Phase 2)", "",
         f"Frozen Parashara engine, hashed sample of {n} tier-A (Rodden AA) charts. No outcomes read.",
         "Each condition is compared with the unperturbed Lahiri cast. **κ = Cohen's kappa** (chance-corrected); "
         "κ is the reliability ρ: a true effect θ shows up as about ρ·θ.", "",
         "## Birth-time jitter and ayanamsa", ""]
    cols = ["verdict", *INSTRUMENTS]
    L += ["| condition | n | " + " | ".join(f"{c} κ (agree)" for c in cols) + " | ayurdaya Δyrs |",
          "|---|---|" + "---|" * len(cols) + "---|"]
    for label, m in rel.items():
        cells = " | ".join(f"{m[c]['kappa']:.2f} ({m[c]['agree']:.2f})" for c in cols)
        L.append(f"| {label} | {m['n_people']} | {cells} | {m['ayurdaya']['mean_abs_years']:.2f} |")
    base_cov = next(iter(rel.values()))
    L += ["", "Instrument coverage (share of the age-15–75 grid inside a window): "
          + ", ".join(f"{k} {base_cov[k]['coverage']:.2f}" for k in INSTRUMENTS), "",
          "## Raman vs Parashara convergence (κ per house, 3-pole scale)", "",
          "| house | raw: full store (Raman ayanamsa vs Lahiri) n | κ | agree | ayanamsa-matched (sample) n | κ | agree |",
          "|---|---|---|---|---|---|---|"]
    for h in sorted(conv_raw):
        r, s = conv_raw[h], conv_matched.get(h, {"n": 0, "kappa": float("nan"), "agree": float("nan")})
        L.append(f"| {h} | {r['n']} | {r['kappa']:.2f} | {r['agree']:.2f} | {s['n']} | {s['kappa']:.2f} | {s['agree']:.2f} |")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", type=Path, required=True)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=max(1, (mp.cpu_count() or 4) - 2))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    a = ap.parse_args(argv)
    R, P = a.derived / "raman", a.derived / "parashara"
    master = pd.read_parquet(R / "person_master.parquet")
    par_v = pd.read_parquet(P / "verdicts.parquet")
    people = sample_people(master, set(par_v.person_id), a.n)
    rows = master[master.person_id.isin(people)][
        ["person_id", "birth_date", "birth_time", "tz_offset", "latitude", "longitude"]].to_dict("records")
    birth_jd = {r["person_id"]: swe.julday(*(int(x) for x in r["birth_date"].split("-")), 12.0, swe.GREG_CAL)
                for r in rows}
    tasks = [(r, label) for r in rows for label in CONDITIONS]
    results: dict[str, dict[str, dict]] = {}
    with mp.Pool(a.workers, initializer=install_ayanamsa_patch) as pool:
        for pid, label, res in pool.imap_unordered(_cast, tasks, chunksize=20):
            results.setdefault(pid, {})[label] = res
    rel = compare(results, birth_jd)
    conv_raw = convergence(pd.read_parquet(R / "house_rollups.parquet"), par_v)
    matched = pd.DataFrame([dict(v, person_id=p) for p in results if results[p].get("raman_ayanamsa")
                            for v in results[p]["raman_ayanamsa"]["verdicts"]])
    conv_matched = convergence(pd.read_parquet(R / "house_rollups.parquet"), matched)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(markdown(rel, conv_raw, conv_matched, len(people)), encoding="utf-8")
    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    a.out_json.write_text(json.dumps({"n": len(people), "reliability": rel, "convergence_raw": conv_raw,
                                      "convergence_matched": conv_matched}, indent=2), encoding="utf-8")
    print(f"[reliability] {len(people)} people x {len(CONDITIONS)} conditions -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
