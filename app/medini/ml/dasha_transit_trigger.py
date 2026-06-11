"""The transit trigger — the untested half of the practitioner's method.

Every practitioner manual says timing = dasha **promise** + transit **trigger**:
the dasha names a multi-year window, and Jupiter/Saturn transits narrow it
(PD 10.12–14 / JP 14.28: marriage when **Jupiter transits a trine to the sign or
navamsa occupied by the 7th lord**; K.N. Rao's modern "double transit": Jupiter
AND Saturn both influencing the relevant house). Findings 8–15c only ever tested
the dasha half. This module tests the transit half — alone and as the joint
dasha+transit confirmation — within-person and exposure-controlled, the same
Poisson–binomial design as `dasha_verse_timing` (each native their own control;
exposure = fraction of in-band person-time the condition holds, so Jupiter's
25%-of-the-zodiac trine coverage is priced in automatically).

Transit machinery: a global 15-day grid of sidereal Jupiter/Saturn signs
(`build_longitudes.longitudes_for`); both planets hold a sign for ≳13 months, so
the grid is effectively exact. "Influence" for the double transit = occupation or
the planet's special whole-sign drishti (Jupiter 5/7/9; Saturn 3/7/10).

Conditions:
  marriage: Jupiter trine natal 7L's rasi (PD 10.14); …or its navamsa (PD 10.14);
            Jupiter trine the 7H sign (popular form); double transit on 7H (Rao);
            Phaladeepika dasha stream alone; **dasha AND Jupiter-trine (the verse-
            faithful joint rule)**; **dasha AND double transit (Rao's joint rule)**.
  career:   Jupiter trine 10H; double transit on 10H; career-significator dasha
            AND double transit (Rao's claim "no major event without it").
  death:    double transit on 8H; Saturn transiting 12/1/2 from natal Moon
            (the classical gochara core behind Sade-sati, PD 26).

Usage::

    python -m app.medini.ml.dasha_transit_trigger --data-dir /tmp/la_run \\
        --out data/ml_runs/lunarastro_dignity
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Callable, Final

import numpy as np
import pandas as pd
from scipy.stats import norm

from app.core.dignity import SIGN_RULERS
from app.medini.etl.build_longitudes import longitudes_for
from app.medini.ml.dasha_classical_dictums import DICTUMS, _significator_set
from app.medini.ml.dasha_event_promise import _sign_in_house
from app.medini.ml.dasha_strength_confirm import _first_events
from app.medini.ml.dasha_verse_timing import DOMAINS

logger = logging.getLogger(__name__)
_GRID_STEP: Final[float] = 15.0          # days; Jupiter ≥390 d/sign, Saturn ≥880
_JUP_DRISHTI: Final[frozenset[int]] = frozenset({1, 5, 7, 9})
_SAT_DRISHTI: Final[frozenset[int]] = frozenset({1, 3, 7, 10})


def trines(sign: int) -> frozenset[int]:
    """Signs 1/5/9 counted from `sign` (inclusive)."""
    return frozenset({((sign - 1) % 12) + 1, ((sign + 3) % 12) + 1, ((sign + 7) % 12) + 1})


def _influences(planet_sign: int, target: int, drishti: frozenset[int]) -> bool:
    pos = ((target - planet_sign) % 12) + 1
    return pos in drishti


class TransitGrid:
    """Sidereal Jupiter/Saturn sign as a step function of JD."""

    def __init__(self, jd_lo: float, jd_hi: float, step: float = _GRID_STEP):
        self.jds = np.arange(jd_lo - step, jd_hi + 2 * step, step)
        jup, sat = [], []
        for jd in self.jds:
            lons = longitudes_for(float(jd))
            jup.append(int(lons["jupiter_lon"] // 30) + 1)
            sat.append(int(lons["saturn_lon"] // 30) + 1)
        self.jup = np.array(jup)
        self.sat = np.array(sat)

    def at(self, jd) -> tuple[np.ndarray, np.ndarray]:
        ix = np.clip(np.searchsorted(self.jds, jd, side="right") - 1, 0, len(self.jds) - 1)
        return self.jup[ix], self.sat[ix]


def _person_targets(crow: pd.Series, d9row: pd.Series | None, domain: str) -> dict:
    asc = int(crow["asc_sign"])
    house = {"marriage": 7, "career": 10, "death": 8}[domain]
    h_sign = _sign_in_house(house, asc)
    lord = SIGN_RULERS[h_sign]
    lord_sign = crow.get(f"{lord.lower()}_sign")
    lord_nav = d9row.get(f"{lord.lower()}_d9_sign") if d9row is not None else None
    sig = _significator_set(crow, d9row, DICTUMS[domain]) if domain in DICTUMS else set()
    return {"house_sign": h_sign, "lord": lord,
            "lord_sign": int(lord_sign) if pd.notna(lord_sign) else None,
            "lord_nav": int(lord_nav) if (lord_nav is not None and pd.notna(lord_nav)) else None,
            "moon_sign": int(crow["moon_sign"]) if pd.notna(crow.get("moon_sign")) else None,
            "sig": sig}


# ── transit predicates over (jup_sign, sat_sign, targets) ───────────────────
def jup_trine_lord_rasi(j, s, t):
    return t["lord_sign"] is not None and j in trines(t["lord_sign"])


def jup_trine_lord_nav(j, s, t):
    return t["lord_nav"] is not None and j in trines(t["lord_nav"])


def jup_trine_house(j, s, t):
    return j in trines(t["house_sign"])


def double_transit_house(j, s, t):
    h = t["house_sign"]
    return (_influences(j, h, _JUP_DRISHTI) and _influences(s, h, _SAT_DRISHTI))


def sat_12_1_2_from_moon(j, s, t):
    m = t["moon_sign"]
    if m is None:
        return False
    return ((s - m) % 12) in (11, 0, 1)          # 12th, 1st, 2nd from Moon


CONDITIONS: Final[dict[str, dict[str, dict]]] = {
    "marriage": {
        "jup_trine_7L_rasi (PD 10.14)": {"transit": jup_trine_lord_rasi},
        "jup_trine_7L_navamsa (PD 10.14)": {"transit": jup_trine_lord_nav},
        "jup_trine_7H (popular)": {"transit": jup_trine_house},
        "double_transit_7H (Rao)": {"transit": double_transit_house},
        "dasha_stream_alone": {"dasha": True},
        "dasha AND jup_trine_7L (verse-faithful joint)": {
            "dasha": True, "transit": lambda j, s, t:
                jup_trine_lord_rasi(j, s, t) or jup_trine_lord_nav(j, s, t)},
        "dasha AND double_transit_7H (Rao joint)": {
            "dasha": True, "transit": double_transit_house},
    },
    "career": {
        "jup_trine_10H": {"transit": jup_trine_house},
        "double_transit_10H (Rao)": {"transit": double_transit_house},
        "dasha AND double_transit_10H (Rao joint)": {
            "dasha": True, "transit": double_transit_house},
    },
    "death": {
        "double_transit_8H (Rao)": {"transit": double_transit_house},
        "saturn_12_1_2_from_Moon (gochara core)": {"transit": sat_12_1_2_from_moon},
    },
}


def within_person_transit(windows, charts, d9, events, grid: TransitGrid,
                          domain: str) -> dict:
    _, (lo, hi) = DOMAINS[domain]
    conds = CONDITIONS[domain]
    cidx = charts.drop_duplicates("person_id").set_index("person_id")
    d9idx = d9.drop_duplicates("person_id").set_index("person_id") if d9 is not None else None
    birth = cidx["birth_jd_used"]
    win_by = {pid: g for pid, g in windows.groupby("person_id")}
    evf = _first_events(events, domain)

    acc = {c: {"H": 0.0, "E": 0.0, "V": 0.0, "n": 0} for c in conds}
    for pid in evf.index:
        if pid not in cidx.index or pid not in win_by or pd.isna(birth.get(pid)):
            continue
        crow = cidx.loc[pid]
        b = float(birth[pid])
        ev_jd = float(evf.loc[pid, "event_jd"])
        band_lo, band_hi = b + lo * 365.25, b + hi * 365.25
        if not (band_lo <= ev_jd <= band_hi):
            continue
        d9row = d9idx.loc[pid] if (d9idx is not None and pid in d9idx.index) else None
        t = _person_targets(crow, d9row, domain)
        # sample grid over the band (≈ duration-weighted exposure).
        pts = np.arange(band_lo, band_hi, _GRID_STEP)
        if len(pts) < 12:
            continue
        jg, sg = grid.at(pts)
        je, se = grid.at(np.array([ev_jd]))
        je, se = int(je[0]), int(se[0])
        # dasha condition: significator runs as MD or AD at t.
        wg = win_by[pid].sort_values("start_jd")
        starts = wg["start_jd"].to_numpy()
        md = wg["md_lord"].astype(str).to_numpy()
        ad = wg["ad_lord"].astype(str).to_numpy()
        wix = np.clip(np.searchsorted(starts, pts, side="right") - 1, 0, len(starts) - 1)
        dasha_flags = np.array([(md[i] in t["sig"]) or (ad[i] in t["sig"]) for i in wix])
        eix = int(np.clip(np.searchsorted(starts, ev_jd, side="right") - 1, 0, len(starts) - 1))
        dasha_ev = (md[eix] in t["sig"]) or (ad[eix] in t["sig"])

        for cname, spec in conds.items():
            tf = spec.get("transit")
            flags = np.ones(len(pts), bool)
            hit = True
            if tf is not None:
                flags &= np.array([tf(int(jg[i]), int(sg[i]), t) for i in range(len(pts))])
                hit = hit and tf(je, se, t)
            if spec.get("dasha"):
                flags &= dasha_flags
                hit = hit and dasha_ev
            expo = float(flags.mean())
            if expo <= 0.0 or expo >= 1.0:
                continue
            a = acc[cname]
            a["H"] += bool(hit)
            a["E"] += expo
            a["V"] += expo * (1 - expo)
            a["n"] += 1

    out = {"domain": domain, "conditions": {}}
    for cname, a in acc.items():
        if a["n"] == 0 or a["V"] <= 0:
            continue
        z = (a["H"] - a["E"]) / np.sqrt(a["V"])
        out["conditions"][cname] = {
            "n": a["n"], "hit_rate": round(a["H"] / a["n"], 4),
            "expected": round(a["E"] / a["n"], 4),
            "lift": round(a["H"] / a["E"], 3) if a["E"] else None,
            "z": round(float(z), 2), "p": round(float(2 * norm.sf(abs(z))), 4)}
    return out


def run(data_dir: Path, out_dir: Path) -> list[dict]:
    events = pd.read_parquet(data_dir / "events_with_dasha.parquet")
    charts = pd.read_parquet(data_dir / "charts.parquet")
    windows = pd.read_parquet(data_dir / "dasha_windows.parquet")
    d9 = pd.read_parquet(data_dir / "charts_d9.parquet") \
        if (data_dir / "charts_d9.parquet").exists() else None

    b = charts["birth_jd_used"].dropna()
    grid = TransitGrid(float(b.min()), float(b.max()) + 105 * 365.25)
    logger.info("transit grid: %d points", len(grid.jds))

    results = []
    for dom in ("marriage", "career", "death"):
        res = within_person_transit(windows, charts, d9, events, grid, dom)
        results.append(res)
        logger.info("%s: %s", dom,
                    {c: (v["lift"], v["p"]) for c, v in res["conditions"].items()})

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "transit_trigger.md").write_text(_report(results), encoding="utf-8")
    (out_dir / "transit_trigger.json").write_text(json.dumps(results, indent=2),
                                                  encoding="utf-8")
    return results


def _report(results: list[dict]) -> str:
    L = ["# The transit trigger — testing the untested half of the method", "",
         "Dasha **promise** was tested in Findings 8–15c; this tests the transit "
         "**trigger** (PD 10.12–14 / JP 14.28 Jupiter-trine rules; Rao's double "
         "transit) and the **joint dasha+transit confirmation** — within-person, "
         "exposure-controlled (each native their own control; a trigger covering "
         "25% of the zodiac is expected to 'hit' 25% of the time by exposure "
         "alone, so lift=1 is chance).", ""]
    for res in results:
        L += [f"## {res['domain']}", "",
              "| condition | n | hit-rate | expected | lift | z | p |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for cname, c in res["conditions"].items():
            star = " ✦" if c["p"] < 0.05 else ""
            L.append(f"| {cname}{star} | {c['n']} | {c['hit_rate']*100:.1f}% | "
                     f"{c['expected']*100:.1f}% | **{c['lift']}** | {c['z']} | {c['p']:.3g} |")
        L.append("")
    L += ["## Reading", "",
          "- `dasha AND …` rows are the practitioner's actual two-stage method: "
          "promise + trigger. If the joint rule lifts where each part alone does "
          "not, the double-confirmation has real synergy; if all sit at 1.0, the "
          "full classical method — both halves — is exposure-level chance.", ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", type=Path, default=Path("/tmp/la_run"))
    ap.add_argument("--out", type=Path, default=Path("data/ml_runs/lunarastro_dignity"))
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")
    res = run(args.data_dir, args.out)
    for r in res:
        print(r["domain"], {c: (v["lift"], v["p"]) for c, v in r["conditions"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
