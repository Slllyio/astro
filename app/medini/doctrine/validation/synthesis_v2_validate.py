"""Measure the synthesis_v2 gated-override scorer on the same held-out corpora as the live engine.

The live engine is UNTOUCHED: this harness calls `judge_house_doctrine` only as the feature
front-end (to obtain each factor's `FactorVerdict.findings`), then discards its additive `.label`
and re-grades the findings through `synthesis_v2`. It reuses the existing loaders / reconstruction /
pre-registered verdict map verbatim (`worked_chart_validate`, `nh_strength_validate`,
`anchor_live_validate`), so ONLY the synthesis differs.

Three axes, side-by-side with the live engine's pinned numbers:
  - pooled HTJAH held-out (N=53)  — live 54.7% within-one
  - NH degree pool (N=32)         — live 53.1%
  - ch. IV live anchor (N=8)      — live 1/8 (all under-credits)

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.synthesis_v2_validate [--json]
"""
from __future__ import annotations

import dataclasses
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

_ROOT = Path(__file__).resolve().parents[4]
_CORP = _ROOT / "docs/raman_doctrine/validation/corpora"
_HELDOUT = sorted(str(p) for p in _CORP.glob("heldout_ch*.json"))
_NH = [_CORP / "nh_strength.json", _CORP / "nh_strength_grow.json"]
# grow2 (18) + grow3 (11, second-verdict sweep) + grow4 (17, map-v2 recovery of the culled stems)
# extend the degree pool. The increment-26 attribution audit removed 5 bad gold rows from the base
# corpora (default pool N=27); the full pool is N=73. run_nh(_NH_ALL) reports the full pool with its
# own re-measured additive baseline for a fair side-by-side.
_NH_ALL = _NH + [_CORP / "nh_strength_grow2.json", _CORP / "nh_strength_grow3.json",
                 _CORP / "nh_strength_grow4.json"]
_FACTOR_ATTR = W._FACTOR_ATTR if hasattr(W, "_FACTOR_ATTR") else {
    "bhava": "lagna_verdict", "lord": "lord_verdict",
    "karaka": "karaka_verdict", "overall": "conclusion"}

# Pinned live-engine baselines (VALIDATION_SUMMARY.md) — the numbers v2 must beat/hold.
# NH re-pinned at increment 26 (attribution audit; default pool N=27); held-out re-pinned at
# increment 27 (verdict-map v2 grew the HTJAH pool 53 -> 58).
LIVE = {"heldout": (50.0, 22.4, -0.12, 58), "nh": (51.9, 25.9, 0.11, 27), "anchor": (12.5, 1, 8)}


# ── v2 re-graders (the only thing that differs from the live harnesses) ──────────────────────────

def _v2_factor(fv, *, rasi_only: bool = False) -> str:
    if rasi_only:
        # score the Rāśi axis alone (no printed Navāṁśa): zero the Navāṁśa contribution
        fv = dataclasses.replace(fv, navamsa_score=0.0,
                                 findings=tuple(f for f in fv.findings if f.frame in ("Rasi", "both")),
                                 score=fv.rasi_score)
    g, _ = S2.grade_factor(fv)
    return S2.label(g)


def _v2_overall(judgment, house: int) -> str:
    g, _ = S2.synthesize_house(judgment.lagna_verdict, judgment.lord_verdict,
                               judgment.karaka_verdict, house)
    return S2.label(g)


def _score(rows: list[dict]) -> dict[str, Any]:
    n = len(rows)
    exact = sum(1 for r in rows if r["delta"] == 0)
    within1 = sum(1 for r in rows if abs(r["delta"]) <= 1)
    return {"n": n, "exact": exact, "exact_pct": round(100 * exact / n, 1) if n else 0.0,
            "within1": within1, "within1_pct": round(100 * within1 / n, 1) if n else 0.0,
            "mean_delta": round(sum(r["delta"] for r in rows) / n, 3) if n else 0.0,
            "divergences": sorted((r for r in rows if abs(r["delta"]) > 1),
                                  key=lambda x: -abs(x["delta"])), "rows": rows}


# ── axis 1: pooled HTJAH held-out (sign-reconstructed) ───────────────────────────────────────────

def run_heldout(paths: list[str] = _HELDOUT) -> dict[str, Any]:
    patterns = W.load_verdict_map()
    idx = W._IDX
    records: list[dict] = []
    for p in paths:
        corpus = json.loads(Path(p).read_text())
        records += corpus["charts"] if isinstance(corpus, dict) else corpus
    rows, excluded = [], 0
    for rec in records:
        rasi = rec["rasi"]
        rasi_only = rec.get("axis") == "rasi" or "navamsa" not in rec
        try:
            if rasi_only:
                chart = R.chart_from_rasi(rasi, rec["lagna_rasi"])
            else:
                if R.consistency_errors(rasi, rec["navamsa"]):
                    excluded += 1
                    continue
                chart = R.chart_from_raman(rasi, rec["navamsa"], rec["lagna_rasi"],
                                           rec["lagna_navamsa"])
        except (ValueError, KeyError):
            excluded += 1
            continue
        house = int(rec["house_judged"])
        judgment = judge_house_doctrine(chart, house)
        for v in rec.get("verdicts", []):
            factor = v["factor"]
            if factor not in _FACTOR_ATTR:
                continue
            if rasi_only and factor == "overall":
                continue
            raman = W.map_verdict(v["phrase"], patterns)
            if raman is None:
                continue
            if factor == "overall":
                eng = _v2_overall(judgment, house)
            elif factor == "karaka" and v.get("karaka"):
                fv = HJ._assess_planet(chart, v["karaka"], "Karaka")
                eng = _v2_factor(fv, rasi_only=rasi_only)
            else:
                fv = getattr(judgment, _FACTOR_ATTR[factor])
                eng = _v2_factor(fv, rasi_only=rasi_only)
            rows.append({"chart": rec.get("chart_no"), "house": house, "factor": factor,
                         "phrase": v["phrase"], "raman": raman, "engine": eng,
                         "delta": idx[eng] - idx[raman]})
    out = _score(rows)
    out["n_excluded"] = excluded
    return out


# ── axis 2: NH degree pool ───────────────────────────────────────────────────────────────────────

def run_nh(paths: list[Path] = _NH) -> dict[str, Any]:
    from app.medini.ml.raman_saab.golden_registry import load_registry
    patterns = W.load_verdict_map()
    idx = W._IDX
    cases = {c.key: c for c in load_registry()}
    rows, excluded = [], 0
    live_within1 = live_delta_sum = 0
    for p in paths:
        for r in json.loads(Path(p).read_text())["rows"]:
            case = cases.get(r["key"])
            if case is None or not case.positions:
                excluded += 1
                continue
            raman = W.map_verdict(r["phrase"], patterns)
            if raman is None:
                excluded += 1
                continue
            chart = NH._chart_for(case)
            house = int(r["house"])
            judgment = judge_house_doctrine(chart, house)
            if r["factor"] == "overall":
                eng = _v2_overall(judgment, house)
                live = judgment.conclusion.label
            else:
                fv = getattr(judgment, _FACTOR_ATTR[r["factor"]])
                eng = _v2_factor(fv)
                live = fv.label
            live_d = idx[live] - idx[raman]
            live_within1 += abs(live_d) <= 1
            live_delta_sum += live_d
            rows.append({"name": r["name"], "house": house, "factor": r["factor"],
                         "raman": raman, "engine": eng, "live": live,
                         "delta": idx[eng] - idx[raman], "live_delta": live_d})
    out = _score(rows)
    out["n_excluded"] = excluded
    n = out["n"]
    out["live_within1"] = live_within1
    out["live_within1_pct"] = round(100 * live_within1 / n, 1) if n else 0.0
    out["live_mean_delta"] = round(live_delta_sum / n, 3) if n else 0.0
    return out


# ── axis 3: ch. IV live anchor ───────────────────────────────────────────────────────────────────

def run_anchor(corpus_path: Path = A._CORPUS) -> dict[str, Any]:
    corpus = json.loads(Path(corpus_path).read_text())
    idx = W._IDX
    house = int(corpus["house"])
    rows, structural = [], []
    for rec in corpus["charts"]:
        chart = A.chart_for(rec)
        judgment = judge_house_doctrine(chart, house)
        for v in rec["verdicts"]:
            factor = v["factor"]
            if factor == "overall":
                eng = _v2_overall(judgment, house)
            else:
                fv = getattr(judgment, _FACTOR_ATTR[factor])
                eng = _v2_factor(fv)
            row = {"chart": rec["chart"], "factor": factor, "raman": v["raman"],
                   "engine": eng, "delta": idx[eng] - idx[v["raman"]]}
            (structural if v.get("structural") else rows).append(row)
    out = _score(rows)
    out["structural"] = structural
    return out


def run_all() -> dict[str, Any]:
    return {"heldout": run_heldout(), "nh": run_nh(), "anchor": run_anchor()}


def _line(name: str, s: dict, live: tuple) -> str:
    return (f"  {name:<22} within-one {s['within1']:>3}/{s['n']:<3} ({s['within1_pct']:>5}%)  "
            f"exact {s['exact_pct']:>5}%  Δ {s['mean_delta']:+.2f}"
            f"   [live {live[0]}%]")


def main() -> None:
    res = run_all()
    print("synthesis_v2 (gated overrides) vs live engine — three axes\n")
    print(_line("pooled HTJAH held-out", res["heldout"], LIVE["heldout"]))
    print(_line("NH degree pool", res["nh"], LIVE["nh"]))
    nh50 = run_nh(_NH_ALL)
    print(f"  {'NH enlarged (grow2)':<22} within-one {nh50['within1']:>3}/{nh50['n']:<3} "
          f"({nh50['within1_pct']:>5}%)  Δ {nh50['mean_delta']:+.2f}"
          f"   [live measured {nh50['live_within1_pct']}%]")
    a = res["anchor"]
    print(f"  {'ch. IV live anchor':<22} within-one {a['within1']:>3}/{a['n']:<3} "
          f"({a['within1_pct']:>5}%)  Δ {a['mean_delta']:+.2f}   [live 1/8 = 12.5%]")
    print("\n  anchor rows:")
    for r in a["rows"]:
        mark = "OK  " if abs(r["delta"]) <= 1 else "MISS"
        print(f"    {mark} chart {r['chart']:>2} {r['factor']:6} raman={r['raman']:16} "
              f"v2={r['engine']:16} Δ{r['delta']:+d}")
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
