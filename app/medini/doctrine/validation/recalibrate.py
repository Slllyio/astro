"""Accuracy Phase 2 — global recalibration of the held-out over-scoring bias.

A per-row forensic pass showed the dominant cause of the held-out over-grading is a GLOBAL
threshold miscalibration (`_THRESH` set ~1 grade too low), plus the optimistic planet blend
(`_BLEND_W`). This corrects it with the FEWEST possible global constants -- a threshold
up-shift `b` and the planet blend weight `blend_w` -- fit by LEAVE-ONE-CHAPTER-OUT
cross-validation across the 7 held-out houses, so the number is a calibration generalisation
estimate (two constants over 7 chapters), not per-row memorisation.

Fast: it reconstructs+judges every chart ONCE, caches each scored row's findings, then the
grid search only re-runs the pure-arithmetic `_combine` + threshold compare (no
re-reconstruction). Measurement/search only -- it does NOT mutate the engine; the chosen
(b, blend_w) are applied by editing `house_judgment._THRESH` / `_BLEND_W` in a reviewed step.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.recalibrate [--json]
"""
from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Any

from app.medini.doctrine.domains import house_judgment as HJ
from app.medini.doctrine.domains.house_judgment import (
    _assess_planet, judge_house_doctrine,
)
from app.medini.doctrine.validation import reconstruct as R
from app.medini.doctrine.validation import worked_chart_validate as WCV

_CORPORA = sorted(glob.glob(str(
    Path(__file__).resolve().parents[4]
    / "docs/raman_doctrine/validation/corpora/heldout_ch*.json")))
_B_GRID = [round(x * 0.1, 2) for x in range(0, 15)]        # threshold up-shift 0.0 .. 1.4
_BLEND_GRID = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
_ADDITIVE = {"bhava": True, "lord": False, "karaka": False}
_THRESH0 = HJ._THRESH


def _grade_idx(score: float, b: float) -> int:
    for lo, lab in _THRESH0:
        if score >= lo + b:
            return WCV._IDX[lab]
    return WCV._IDX["afflicted"]


def build_cache() -> list[dict]:
    """One reconstruction+judgment pass; cache each scored row's findings + additive flag +
    Raman grade index + chapter. Mirrors worked_chart_validate.validate_record's row logic."""
    patterns = WCV.load_verdict_map()
    rows: list[dict] = []
    for path in _CORPORA:
        stem = Path(path).stem
        corpus = json.loads(Path(path).read_text())
        for rec in (corpus["charts"] if isinstance(corpus, dict) else corpus):
            if rec.get("axis") == "rasi" or "navamsa" not in rec:
                continue                                   # full-axis rows only (as harness)
            if R.consistency_errors(rec["rasi"], rec["navamsa"]):
                continue
            try:
                chart = R.chart_from_raman(rec["rasi"], rec["navamsa"],
                                           rec["lagna_rasi"], rec["lagna_navamsa"])
            except (ValueError, KeyError):
                continue
            house = int(rec["house_judged"])
            j = judge_house_doctrine(chart, house)
            for v in rec.get("verdicts", []):
                factor = v["factor"]
                if factor not in _ADDITIVE:
                    continue
                raman = WCV.map_verdict(v["phrase"], patterns)
                if raman is None:
                    continue
                if factor == "karaka" and v.get("karaka"):
                    fv = _assess_planet(chart, v["karaka"], "Karaka")
                else:
                    fv = {"bhava": j.lagna_verdict, "lord": j.lord_verdict,
                          "karaka": j.karaka_verdict}[factor]
                rows.append({"chapter": stem, "factor": factor,
                             "additive": _ADDITIVE[factor],
                             "findings": fv.findings, "raman": WCV._IDX[raman]})
    return rows


def _within1(rows: list[dict], b: float, blend_w: float) -> int:
    blend0 = HJ._BLEND_W
    HJ._BLEND_W = blend_w
    try:
        hit = 0
        for r in rows:
            score = HJ._combine(r["findings"], additive=r["additive"])[0]
            if abs(_grade_idx(score, b) - r["raman"]) <= 1:
                hit += 1
        return hit
    finally:
        HJ._BLEND_W = blend0


def _best(rows: list[dict]) -> tuple[float, float]:
    best, key = None, (-1.0, 0.0)
    n = len(rows)
    for b in _B_GRID:
        for bw in _BLEND_GRID:
            pct = _within1(rows, b, bw) / n if n else 0.0
            k = (pct, -(b + (0.3 - bw)))               # prefer the smallest intervention
            if k > key:
                key, best = k, (b, bw)
    return best


def loco_cv(cache: list[dict] | None = None) -> dict[str, Any]:
    rows = cache if cache is not None else build_cache()
    chapters = sorted({r["chapter"] for r in rows})
    cv_hit = cv_n = 0
    folds = []
    for test in chapters:
        train = [r for r in rows if r["chapter"] != test]
        held = [r for r in rows if r["chapter"] == test]
        b, bw = _best(train)
        hit = _within1(held, b, bw)
        cv_hit += hit
        cv_n += len(held)
        folds.append({"chapter": test, "b": b, "blend_w": bw, "within1": hit, "n": len(held)})
    n = len(rows)
    base = _within1(rows, 0.0, HJ._BLEND_W)
    pb, pbw = _best(rows)
    return {
        "baseline": {"within1": base, "n": n, "pct": round(100 * base / n, 1)},
        "loco_cv": {"within1": cv_hit, "n": cv_n, "pct": round(100 * cv_hit / cv_n, 1)},
        "pooled_best": {"b": pb, "blend_w": pbw, "within1": _within1(rows, pb, pbw),
                        "n": n, "pct": round(100 * _within1(rows, pb, pbw) / n, 1)},
        "folds": folds,
    }


def _print(r: dict) -> None:
    print(f"baseline (b=0, blend=0.3): {r['baseline']['within1']}/{r['baseline']['n']} "
          f"({r['baseline']['pct']}%)")
    print(f"LOCO-CV (honest generalisation): {r['loco_cv']['within1']}/{r['loco_cv']['n']} "
          f"({r['loco_cv']['pct']}%)")
    p = r["pooled_best"]
    print(f"pooled-best applied constant: b={p['b']} blend_w={p['blend_w']} -> "
          f"{p['within1']}/{p['n']} ({p['pct']}%)")
    for f in r["folds"]:
        print(f"  {f['chapter']:<24} b={f['b']:<4} blend_w={f['blend_w']:<5} "
              f"-> {f['within1']}/{f['n']}")


def main() -> None:
    import sys
    r = loco_cv()
    _print(r)
    if "--json" in sys.argv:
        print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
