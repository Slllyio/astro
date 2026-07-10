"""Fresh, DEGREE-ACCURATE strength held-out from *Notable Horoscopes*.

Every prior strength score is on charts SIGN-reconstructed from Raman's diagrams (degrees are
pada-midpoint approximations). NH prints full degree positions, so its charts reconstruct
exactly via ``raman_chart.from_printed_positions`` -- no vision, no sign back-solve. Each row is
Raman's verbatim, hand-verified "the Nth house/lord is [grade]" verdict (``nh_strength.json``).
The doctrine strength engine was never tuned on NH, so this is a genuinely held-out, and
degree-exact, test -- the strongest strength check the project can build.

Reuses the sign-path scorer's grade lattice + map (`worked_chart_validate`) and the live
`judge_house_doctrine`; only the reconstruction path differs (degrees, not signs).

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.nh_strength_validate
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.medini.doctrine import raman_chart as rc
from app.medini.doctrine.domains.house_judgment import judge_house_doctrine
from app.medini.doctrine.validation import worked_chart_validate as W
from app.medini.ml.raman_saab.golden_registry import load_registry

_ROOT = Path(__file__).resolve().parents[4]
_CORPUS = _ROOT / "docs/raman_doctrine/validation/corpora/nh_strength.json"
_FACTOR_ATTR = {"bhava": "lagna_verdict", "lord": "lord_verdict",
                "karaka": "karaka_verdict", "overall": "conclusion"}


def _chart_for(case) -> "rc.RamanChart":
    """Reconstruct a scoreable chart from a golden case's PRINTED degree positions."""
    retro = {g: True for g in getattr(case, "retro", []) or []}
    return rc.from_printed_positions(case.positions, case.lagna_lon,
                                     birth_jd=case.birth_jd, person_id=case.key, retrograde=retro)


def run(corpus_path: str | Path = _CORPUS) -> dict[str, Any]:
    patterns = W.load_verdict_map()
    rows_spec = json.loads(Path(corpus_path).read_text())["rows"]
    cases = {c.key: c for c in load_registry()}
    idx = W._IDX
    out, exclude = [], []
    for r in rows_spec:
        case = cases.get(r["key"])
        if case is None or not case.positions:
            exclude.append({**r, "why": "no_positions"}); continue
        chart = _chart_for(case)
        raman = W.map_verdict(r["phrase"], patterns)
        if raman is None:
            exclude.append({**r, "why": "unmappable"}); continue
        j = judge_house_doctrine(chart, int(r["house"]))
        eng = getattr(j, _FACTOR_ATTR[r["factor"]]).label
        out.append({"name": r["name"], "house": r["house"], "factor": r["factor"],
                    "raman": raman, "engine": eng, "delta": idx[eng] - idx[raman]})
    n = len(out)
    exact = sum(1 for r in out if r["delta"] == 0)
    within1 = sum(1 for r in out if abs(r["delta"]) <= 1)
    mean = round(sum(r["delta"] for r in out) / n, 2) if n else 0.0
    return {"n": n, "exact": exact, "exact_pct": round(100 * exact / n, 1) if n else 0.0,
            "within1": within1, "within1_pct": round(100 * within1 / n, 1) if n else 0.0,
            "mean_delta": mean, "n_excluded": len(exclude), "excluded": exclude,
            "divergences": [r for r in out if abs(r["delta"]) > 1], "rows": out}


def main() -> None:
    s = run()
    print(f"NH degree-accurate strength held-out (N={s['n']}, {s['n_excluded']} excluded):")
    print(f"  exact       {s['exact']}/{s['n']} ({s['exact_pct']}%)")
    print(f"  within-one  {s['within1']}/{s['n']} ({s['within1_pct']}%)   mean Δ {s['mean_delta']:+.2f}")
    for r in s["divergences"]:
        print(f"    Δ{r['delta']:+d}  {r['name'][:20]:20s} H{r['house']} {r['factor']:6s} "
              f"raman={r['raman']:<12} engine={r['engine']}")


if __name__ == "__main__":
    main()
