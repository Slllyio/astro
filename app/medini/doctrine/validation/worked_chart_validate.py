"""Held-out validation: run the engine on Raman's PRINTED worked charts and compare
its strength verdict to Raman's own, on the 9-grade scale.

Each corpus record (produced by the ``raman-chart-extractor`` subagent) carries Raman's
raw Rāśi + Navāṁśa sign diagrams, the house he judges, and his verbatim verdict
phrase(s) tagged by factor (bhava | lord | karaka | overall) — RAW positions + RAW
verdict, never engine features, so the test stays independent. This harness:

  1. screens the (rāśi, navāṁśa) consistency gate (drops mis-extractions),
  2. reconstructs the chart (``reconstruct.chart_from_raman``),
  3. runs ``judge_house_doctrine`` and reads the bhava/lord/karaka FactorVerdict +
     Conclusion,
  4. maps Raman's phrase to a grade via the PRE-REGISTERED map (unmappable → excluded),
  5. aggregates exact / within-one / per-factor and lists every divergence.

CLI:
  PYTHONPATH=. python3 -m app.medini.doctrine.validation.worked_chart_validate \
      docs/raman_doctrine/validation/corpora/heldout_ch07_4th.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.medini.doctrine.domains.house_judgment import (
    VERDICT_SCALE, judge_house_doctrine,
)
from app.medini.doctrine.validation import reconstruct as R

_IDX = {lab: i for i, lab in enumerate(VERDICT_SCALE)}
_MAP_PATH = (Path(__file__).resolve().parents[4]
             / "docs/raman_doctrine/validation/verdict_grade_map.json")
# record factor -> HouseJudgment attribute holding the FactorVerdict/Conclusion label
_FACTOR_ATTR = {"bhava": "lagna_verdict", "lord": "lord_verdict",
                "karaka": "karaka_verdict", "overall": "conclusion"}


def load_verdict_map(path: Path = _MAP_PATH) -> list[tuple[str, str]]:
    data = json.loads(Path(path).read_text())
    return [(p.lower(), g) for p, g in data["patterns"]]


def map_verdict(phrase: str, patterns: list[tuple[str, str]]) -> str | None:
    """Raman phrase -> 9-grade label (most-specific pattern first), or None if
    unmappable (never guessed)."""
    low = phrase.lower()
    for pat, grade in patterns:
        if pat in low:
            return grade
    return None


def _engine_label(judgment, factor: str) -> str:
    obj = getattr(judgment, _FACTOR_ATTR[factor])
    return obj.label


def validate_record(rec: dict, patterns: list[tuple[str, str]]) -> dict[str, Any]:
    """Validate one worked chart. Returns a result dict with per-verdict deltas, or an
    ``excluded`` reason (bad extraction / unmappable / unjudged)."""
    rasi, nav = rec["rasi"], rec["navamsa"]
    bad = R.consistency_errors(rasi, nav)
    if bad:
        return {"chart": rec.get("chart_no"), "excluded": "inconsistent", "detail": bad}
    try:
        chart = R.chart_from_raman(rasi, nav, rec["lagna_rasi"], rec["lagna_navamsa"])
    except (ValueError, KeyError) as e:
        return {"chart": rec.get("chart_no"), "excluded": "reconstruct_error",
                "detail": str(e)}
    house = int(rec["house_judged"])
    judgment = judge_house_doctrine(chart, house)
    rows = []
    for v in rec.get("verdicts", []):
        factor = v["factor"]
        raman_grade = map_verdict(v["phrase"], patterns)
        if factor not in _FACTOR_ATTR:
            rows.append({"factor": factor, "excluded": "unknown_factor"})
            continue
        if raman_grade is None:
            rows.append({"factor": factor, "phrase": v["phrase"],
                         "excluded": "unmappable_phrase"})
            continue
        eng = _engine_label(judgment, factor)
        d = _IDX[eng] - _IDX[raman_grade]
        rows.append({"factor": factor, "phrase": v["phrase"], "raman": raman_grade,
                     "engine": eng, "delta": d})
    return {"chart": rec.get("chart_no"), "house": house, "rows": rows}


def run(corpus_path: str, map_path: Path = _MAP_PATH) -> dict[str, Any]:
    patterns = load_verdict_map(map_path)
    corpus = json.loads(Path(corpus_path).read_text())
    records = corpus["charts"] if isinstance(corpus, dict) else corpus
    scored, excluded, divergences = [], [], []
    for rec in records:
        res = validate_record(rec, patterns)
        if res.get("excluded"):
            excluded.append(res)
            continue
        for row in res["rows"]:
            if row.get("excluded"):
                excluded.append({"chart": res["chart"], **row})
                continue
            scored.append(row)
            if abs(row["delta"]) > 1:
                divergences.append({"chart": res["chart"], "house": res["house"], **row})
    n = len(scored)
    exact = sum(1 for r in scored if r["delta"] == 0)
    within1 = sum(1 for r in scored if abs(r["delta"]) <= 1)
    by_factor: dict[str, list[int]] = {}
    for r in scored:
        by_factor.setdefault(r["factor"], []).append(r["delta"])
    per_factor = {f: {"n": len(ds),
                      "within1": sum(1 for d in ds if abs(d) <= 1),
                      "exact": sum(1 for d in ds if d == 0),
                      "mean": round(sum(ds) / len(ds), 2)}
                  for f, ds in by_factor.items()}
    return {
        "n_scored": n,
        "exact": exact, "exact_pct": round(100 * exact / n, 1) if n else 0.0,
        "within1": within1, "within1_pct": round(100 * within1 / n, 1) if n else 0.0,
        "mean_delta": round(sum(r["delta"] for r in scored) / n, 3) if n else 0.0,
        "per_factor": per_factor,
        "n_excluded": len(excluded),
        "excluded": excluded,
        "divergences": sorted(divergences, key=lambda x: -abs(x["delta"])),
    }


def _print(summary: dict) -> None:
    print(f"scored={summary['n_scored']}  exact={summary['exact']} "
          f"({summary['exact_pct']}%)  within-one={summary['within1']} "
          f"({summary['within1_pct']}%)  mean={summary['mean_delta']:+}")
    for f, s in summary["per_factor"].items():
        print(f"  {f:<8} n={s['n']:<3} within1={s['within1']:<3} "
              f"exact={s['exact']:<3} mean={s['mean']:+}")
    print(f"excluded={summary['n_excluded']}")
    if summary["divergences"]:
        print("divergences (|d|>1):")
        for d in summary["divergences"]:
            print(f"  ch{d['chart']} {d['factor']:<7} engine={d['engine']:<14} "
                  f"raman={d['raman']:<14} {d['delta']:+d}   \"{d.get('phrase','')[:40]}\"")


def main() -> None:
    paths = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not paths:
        print(__doc__)
        raise SystemExit(2)
    summary = run(paths[0])
    _print(summary)
    if "--json" in sys.argv:
        print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
