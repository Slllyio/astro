"""LIVE ch. IV anchor validation — the authoritative anchor gate for the engine.

Increment 15b found the live engine had drifted to 2/8 within-one on Raman's own ch. IV
calibration charts while `test_audit_anchor` read 8/8 — because that test runs FROZEN
hand-decoded findings through the old audit harness, not `judge_house_doctrine`. This
validator scores the live engine on the faithfulness-gated anchor corpus
(`htjah_anchor_live.json`, built by `audit/builders/build_anchor_live_corpus.py`) so the
drift can never hide again.

Rows: Raman's graded ch. IV verdicts (house 1: bhava/lord/karaka per chart). The chart-14
bhava row is `structural` (the vargottama-lagna override) and reported separately from the
headline within-one.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.anchor_live_validate
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.medini.doctrine import raman_chart as rc
from app.medini.doctrine.domains.house_judgment import judge_house_doctrine
from app.medini.doctrine.validation import worked_chart_validate as W

_ROOT = Path(__file__).resolve().parents[4]
_CORPUS = _ROOT / "docs/raman_doctrine/audit/corpora/htjah_anchor_live.json"
_FACTOR_ATTR = {"bhava": "lagna_verdict", "lord": "lord_verdict",
                "karaka": "karaka_verdict", "overall": "conclusion"}


def chart_for(rec: dict) -> "rc.RamanChart":
    chart = rc.from_positions(rec["planet_lons"], rec["lagna_lon"],
                              birth_jd=rec["birth_jd"], ayanamsa="raman",
                              degree_resolved=True)
    # Regression tripwire: a future change to varga math or sign assignment that moves
    # any anchor placement must fail loudly here, not shift grades silently.
    for g, want in rec["expected_rasi_signs"].items():
        got = chart.bundle.chart.planet_signs[g]
        if got != want:
            raise AssertionError(f"chart {rec['chart']}: {g} rasi {got} != expected {want}")
    for g, want in rec["expected_navamsa_signs"].items():
        got = chart.varga_signs[g][9]
        if got != want:
            raise AssertionError(f"chart {rec['chart']}: {g} navamsa {got} != expected {want}")
    return chart


def run(corpus_path: str | Path = _CORPUS) -> dict[str, Any]:
    corpus = json.loads(Path(corpus_path).read_text())
    idx = W._IDX
    rows, structural = [], []
    for rec in corpus["charts"]:
        chart = chart_for(rec)
        j = judge_house_doctrine(chart, int(corpus["house"]))
        for v in rec["verdicts"]:
            eng = getattr(j, _FACTOR_ATTR[v["factor"]]).label
            row = {"chart": rec["chart"], "factor": v["factor"],
                   "raman": v["raman"], "engine": eng,
                   "delta": idx[eng] - idx[v["raman"]]}
            (structural if v.get("structural") else rows).append(row)
    n = len(rows)
    within1 = sum(1 for r in rows if abs(r["delta"]) <= 1)
    return {"n": n, "within1": within1,
            "within1_pct": round(100 * within1 / n, 1) if n else 0.0,
            "mean_delta": round(sum(r["delta"] for r in rows) / n, 2) if n else 0.0,
            "rows": rows, "structural": structural}


def main() -> None:
    s = run()
    print(f"LIVE ch. IV anchor: {s['within1']}/{s['n']} within-one "
          f"({s['within1_pct']}%), mean Δ {s['mean_delta']:+.2f}")
    for r in s["rows"]:
        mark = "OK  " if abs(r["delta"]) <= 1 else "MISS"
        print(f"  {mark} chart {r['chart']:>2} {r['factor']:6} "
              f"raman={r['raman']:16} engine={r['engine']:16} Δ{r['delta']:+d}")
    for r in s["structural"]:
        print(f"  [structural] chart {r['chart']} {r['factor']}: "
              f"raman={r['raman']} engine={r['engine']}")


if __name__ == "__main__":
    main()
