"""Increment 31 diagnostic — decompose the strong-side misses by which lever fixes each, and test
the from-the-Moon separation (measurement only, NO engine change).

The root-cause analysis found the ceiling is an aggregation collapse. This decomposes the strong-graded
factors the engine floors (Raman ≥ fairly strong, engine ≤ raman−2) into three groups:
  deep-afflicted   sum_neg ≤ NEG_GATE            — the fortified-but-afflicted residual (Gate F/tokens failed)
  under-detection  shallow neg, ~no positive testimony — Raman graded on evidence absent from the chart
  dignity-crushed  shallow neg, decisive dignity, strong positives — `_cap_positive` floored it → Gate D
Only the last group is tractable; it became Gate D (increment 31). It also tests the from-the-Moon
lever the analysis proposed: does the factor's grade FROM THE MOON separate strong from afflicted?

MEASURED (held-out + NH + anchor): of 24 strong-floored misses — 15 deep-afflicted, 6 under-detection,
3 dignity-crushed; from-the-Moon does NOT separate (1/24 strong-floored are strong from the Moon, below
the afflicted slice's ~5%). So Gate D targets the 3; range-decompression-only and from-the-Moon are
refuted. See REPORT_synthesis_v2.md § increment 31.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.strong_side_decomposition [--json]
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any

from app.medini.doctrine.domains import house_judgment as HJ
from app.medini.doctrine.domains import synthesis_v2 as S2
from app.medini.doctrine.domains.house_judgment import judge_house_doctrine
from app.medini.doctrine.validation import anchor_live_validate as A
from app.medini.doctrine.validation import nh_strength_validate as NH
from app.medini.doctrine.validation import reconstruct as R
from app.medini.doctrine.validation import worked_chart_validate as W

_CORP = Path(__file__).resolve().parents[4] / "docs/raman_doctrine/validation/corpora"
_HELDOUT = sorted(str(p) for p in _CORP.glob("heldout_ch*.json"))
_NH_ALL = [_CORP / f for f in ("nh_strength.json", "nh_strength_grow.json", "nh_strength_grow2.json",
                               "nh_strength_grow3.json", "nh_strength_grow4.json")]
_FA = {"bhava": "lagna_verdict", "lord": "lord_verdict", "karaka": "karaka_verdict"}


def _from_moon(chart, house, factor, rec_karaka=None) -> int:
    moon_sign = chart.bundle.chart.planet_signs["Moon"]
    mh = HJ._moon_houses(chart)
    if factor == "bhava":
        fv = HJ._assess_bhava_reference(chart, house, mh, moon_sign, "Chandra Lagna", exclude="Moon")
    else:
        planet = rec_karaka or (HJ._lord_of(chart, house) if factor == "lord"
                                else HJ.BHAVA_KARAKAS[house][0])
        fv = HJ._assess_planet(chart, planet, "from Moon", ref_sign=moon_sign, houses=mh)
    return S2.grade_factor(fv)[0]


def _row(raman: str, chart, house: int, factor: str, fv, rec_karaka=None) -> dict:
    rasi_f = [f for f in fv.findings if f.frame in ("Rasi", "both")]
    sum_neg = round(sum(f.delta for f in rasi_f if f.delta < 0), 3)
    sum_pos = round(sum(f.delta for f in rasi_f if f.delta > 0), 3)
    lagna = S2.grade_factor(fv)[0]
    ri = W._IDX[raman]
    slc = "strong" if ri >= S2.FAIRLY_STRONG else ("afflicted" if ri <= S2.WEAK else "mid")
    return {"slice": slc, "raman": ri, "lagna": lagna, "moon": _from_moon(chart, house, factor, rec_karaka),
            "sum_neg": sum_neg, "sum_pos": sum_pos, "tier": S2._reduce_frame(rasi_f).tier}


def collect() -> list[dict]:
    pats = W.load_verdict_map()
    rows: list[dict] = []
    corpus = json.loads(A._CORPUS.read_text()); ah = int(corpus["house"])
    for rec in corpus["charts"]:
        chart = A.chart_for(rec); j = judge_house_doctrine(chart, ah)
        for v in rec["verdicts"]:
            if v["factor"] in _FA:
                rows.append(_row(v["raman"], chart, ah, v["factor"], getattr(j, _FA[v["factor"]])))
    for p in _HELDOUT:
        c = json.loads(Path(p).read_text())
        for rec in (c["charts"] if isinstance(c, dict) else c):
            rasi = rec["rasi"]; ro = rec.get("axis") == "rasi" or "navamsa" not in rec
            try:
                chart = (R.chart_from_rasi(rasi, rec["lagna_rasi"]) if ro else
                         (None if R.consistency_errors(rasi, rec["navamsa"]) else
                          R.chart_from_raman(rasi, rec["navamsa"], rec["lagna_rasi"], rec["lagna_navamsa"])))
            except (ValueError, KeyError):
                chart = None
            if chart is None:
                continue
            house = int(rec["house_judged"]); j = judge_house_doctrine(chart, house)
            for v in rec.get("verdicts", []):
                if v["factor"] not in _FA:
                    continue
                raman = W.map_verdict(v["phrase"], pats)
                if raman is None:
                    continue
                fv = (HJ._assess_planet(chart, v["karaka"], "Karaka") if v["factor"] == "karaka"
                      and v.get("karaka") else getattr(j, _FA[v["factor"]]))
                rows.append(_row(raman, chart, house, v["factor"], fv, v.get("karaka")))
    from app.medini.ml.raman_saab.golden_registry import load_registry
    cases = {c.key: c for c in load_registry()}
    for p in _NH_ALL:
        for r in json.loads(Path(p).read_text())["rows"]:
            case = cases.get(r["key"])
            if case is None or not case.positions or r["factor"] == "overall":
                continue
            raman = W.map_verdict(r["phrase"], pats)
            if raman is None:
                continue
            chart = NH._chart_for(case); house = int(r["house"]); j = judge_house_doctrine(chart, house)
            rows.append(_row(raman, chart, house, r["factor"], getattr(j, _FA[r["factor"]])))
    return rows


def summarize(rows: list[dict]) -> dict[str, Any]:
    strong = [r for r in rows if r["slice"] == "strong"]
    miss = [r for r in strong if r["lagna"] - r["raman"] <= -2]
    deep = [r for r in miss if r["sum_neg"] <= S2.NEG_GATE]
    dignity = [r for r in miss if r["sum_neg"] > S2.NEG_GATE and r["tier"] != "none"
               and r["sum_pos"] >= S2.DECOMP_POS_LO]
    under = [r for r in miss if r not in deep and r not in dignity]
    aff = [r for r in rows if r["slice"] == "afflicted"]
    return {"n_strong": len(strong), "n_miss": len(miss), "deep": len(deep),
            "under_detection": len(under), "dignity_crushed": len(dignity),
            "moon_hi_strong_miss": sum(1 for r in miss if r["moon"] >= S2.FAIRLY_STRONG),
            "moon_hi_afflicted": sum(1 for r in aff if r["moon"] >= S2.FAIRLY_STRONG), "n_aff": len(aff)}


def main() -> None:
    s = summarize(collect())
    print("increment 31 — strong-side miss decomposition\n")
    print(f"  strong-graded rows floored (Δ≤−2): {s['n_miss']} of {s['n_strong']}")
    print(f"    deep-afflicted (residual)        : {s['deep']}")
    print(f"    under-detection (residual)       : {s['under_detection']}")
    print(f"    dignity-crushed (→ Gate D)       : {s['dignity_crushed']}")
    print(f"\n  from-the-Moon lever (refuted): strong-floored strong-from-Moon "
          f"{s['moon_hi_strong_miss']}/{s['n_miss']}  vs  afflicted {s['moon_hi_afflicted']}/{s['n_aff']}")
    if "--json" in sys.argv:
        print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
