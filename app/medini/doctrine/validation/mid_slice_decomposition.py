"""Increment 32 diagnostic — decompose the MID-slice misses and test the Gate-B loosening trade
(measurement only, NO engine change).

The mid slice (Raman moderate..fairly-good) is the worst-performing, largest pool (16.7% within-one,
N=42). This decomposes its misses by direction (under- vs over-credit) and, for the under-credit
misses, by why the engine floored them:
  deep-neg           sum_neg ≤ NEG_GATE           — Gate B floored to weak/afflicted (the trade group)
  besieged           papakartari                  — Gate A veto
  shallow-non-besieged  sum_neg > NEG_GATE, not besieged — the residual candidates
It then runs the decisive experiment: does LOOSENING Gate B (raising NEG_GATE / NEG_GATE_DEEP)
recover the deep-neg mid under-credit WITHOUT wrecking the afflicted slice?

MEASURED (held-out + NH-full + anchor, N=140): 42 mid rows, 35 misses (25 under, 10 over). The
under-credit is deep-neg 18 / besieged 1 / shallow-non-besieged 6 — and every shallow candidate has
tier=none with ~zero positive testimony (under-detection, nothing to floor on; disjoint from Gate D).
Loosening Gate B is a PURE TRADE: mid rises 16.7→23.8% but the afflicted slice collapses 82.4→54.4%
and pooled held-out drops 58.6→50.0%. The deep-negative testimony is tag-shared between Raman's
mid-graded and afflicted-graded factors, so no threshold separates them — the same feature-gap
conclusion increment 29 (Gate F) reached, confirmed from the mid slice. Documented NEGATIVE: no gate
over the current vocabulary closes the mid slice. See REPORT_synthesis_v2.md § increment 32.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.mid_slice_decomposition [--json]
"""
from __future__ import annotations

import json
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
MOD, FG = W._IDX["moderate"], W._IDX["fairly good"]

# Gate-B threshold configs for the trade sweep (NEG_GATE, NEG_GATE_DEEP).
_SWEEP = [("DEFAULT -1.22/-2.45", -1.22, -2.45), ("looser -1.6/-2.8", -1.60, -2.80),
          ("looser -2.0/-3.2", -2.00, -3.20), ("looser -2.45/-3.6", -2.45, -3.60),
          ("both off -99/-99", -99.0, -99.0)]


def _rec(pool: str, raman_idx: int, fv) -> dict:
    rasi_f = [f for f in fv.findings if f.frame in ("Rasi", "both")]
    rst = S2._reduce_frame(rasi_f)
    return {"pool": pool, "raman": raman_idx, "fv": fv,
            "sn": round(rst.sum_neg, 3), "besieged": rst.besieged, "tier": rst.tier}


def collect() -> list[dict]:
    pats = W.load_verdict_map()
    rows: list[dict] = []
    corpus = json.loads(A._CORPUS.read_text()); ah = int(corpus["house"])
    for rec in corpus["charts"]:
        chart = A.chart_for(rec); j = judge_house_doctrine(chart, ah)
        for v in rec["verdicts"]:
            if v["factor"] in _FA:
                rows.append(_rec("anchor", W._IDX[v["raman"]], getattr(j, _FA[v["factor"]])))
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
                rows.append(_rec("heldout", W._IDX[raman], fv))
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
            rows.append(_rec("nh", W._IDX[raman], getattr(j, _FA[r["factor"]])))
    return rows


def _within1(pairs: list[tuple[int, int]]) -> tuple[float, int]:
    if not pairs:
        return 0.0, 0
    return 100.0 * sum(1 for ri, e in pairs if abs(ri - e) <= 1) / len(pairs), len(pairs)


def decompose(rows: list[dict]) -> dict[str, Any]:
    """Mid-slice miss decomposition at the DEFAULT thresholds."""
    graded = [(r, S2.grade_factor(r["fv"])[0]) for r in rows]
    mid = [(r, e) for r, e in graded if MOD <= r["raman"] <= FG]
    miss = [(r, e) for r, e in mid if abs(e - r["raman"]) > 1]
    under = [(r, e) for r, e in miss if e < r["raman"] - 1]
    over = [(r, e) for r, e in miss if e > r["raman"] + 1]
    u_deep = [(r, e) for r, e in under if r["sn"] <= S2.NEG_GATE]
    u_bes = [(r, e) for r, e in under if r["besieged"] and r["sn"] > S2.NEG_GATE]
    u_shallow = [(r, e) for r, e in under if r["sn"] > S2.NEG_GATE and not r["besieged"]]
    u_shallow_dignity = [(r, e) for r, e in u_shallow if r["tier"] != "none"]
    return {"n_mid": len(mid), "n_miss": len(miss), "under": len(under), "over": len(over),
            "u_deep": len(u_deep), "u_besieged": len(u_bes), "u_shallow": len(u_shallow),
            "u_shallow_with_dignity": len(u_shallow_dignity)}


def sweep(rows: list[dict]) -> list[dict[str, Any]]:
    """Gate-B loosening trade: mid vs afflicted vs held-out across thresholds."""
    base_ng, base_ngd = S2.NEG_GATE, S2.NEG_GATE_DEEP
    out = []
    try:
        for label, ng, ngd in _SWEEP:
            S2.NEG_GATE, S2.NEG_GATE_DEEP = ng, ngd
            graded = [(r, S2.grade_factor(r["fv"])[0]) for r in rows]
            aff = [(r["raman"], e) for r, e in graded if r["raman"] <= S2.WEAK]
            mid = [(r["raman"], e) for r, e in graded if MOD <= r["raman"] <= FG]
            ho = [(r["raman"], e) for r, e in graded if r["pool"] == "heldout"]
            nh = [(r["raman"], e) for r, e in graded if r["pool"] == "nh"]
            out.append({"config": label, "aff": _within1(aff), "mid": _within1(mid),
                        "heldout": _within1(ho), "nh": _within1(nh)})
    finally:
        S2.NEG_GATE, S2.NEG_GATE_DEEP = base_ng, base_ngd
    return out


def main() -> None:
    rows = collect()
    d = decompose(rows)
    print(f"increment 32 — mid-slice miss decomposition ({len(rows)} rows)\n")
    print(f"  mid rows: {d['n_mid']} | misses {d['n_miss']} (under {d['under']}, over {d['over']})")
    print(f"    under-credit: deep-neg {d['u_deep']} | besieged {d['u_besieged']} | "
          f"shallow-non-besieged {d['u_shallow']} (of which decisive-dignity {d['u_shallow_with_dignity']})")
    print(f"\n  Gate-B loosening trade (mid gain vs afflicted/held-out cost):")
    for s in sweep(rows):
        print(f"    {s['config']:22} | aff {s['aff'][0]:4.1f}% | mid {s['mid'][0]:4.1f}% | "
              f"held-out {s['heldout'][0]:4.1f}% | NH {s['nh'][0]:4.1f}%")
    print("\n  VERDICT: loosening Gate B is a PURE TRADE (mid up, afflicted+held-out down further);")
    print("  the deep-neg mid misses are tag-identical to the afflicted slice → documented NEGATIVE.")
    if "--json" in sys.argv:
        print(json.dumps({"decompose": d, "sweep": sweep(rows)}, indent=1))


if __name__ == "__main__":
    main()
