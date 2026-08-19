"""Track 2 — `synthesize_house` (the overall house-conclusion fusion) consistency diagnostic.

synthesize_house (`synthesis_v2.py`) fuses the bhava/lord/karaka factor grades into a house
conclusion and its label is promoted LIVE (increment 28), yet it is validated against ≈0 gold:
Raman's OVERALL house verdicts are narrative ("the house is good", "occupied by exalted Jupiter")
or soft, and the pre-registered 9-grade map (correctly) won't grade them. This module records that
low-yield finding reproducibly, then measures the fusion the only honest way the data allows —
against the CENTRAL TENDENCY of Raman's own three factor verdicts (his crisp, mappable
bhava/lord/karaka phrases), which DO exist.

Two measurements, on the held-out charts that carry >= 2 mappable factor verdicts:
  (a) end-to-end  — synthesize_house(ENGINE factor verdicts) vs the central tendency of Raman's
                    mapped factor grades: "does the engine's overall verdict match the gist of what
                    Raman said about the parts?" (conflates factor error + fusion error).
  (b) fusion-logic — the SAME fusion formula applied to RAMAN's factor grades vs their own central
                    tendency: "is the class-weight + lead-veto fusion itself sensible (near central
                    tendency)?" (isolates the fusion logic from the engine's factor accuracy).

YIELD (read-only, over 168 held-out charts): overall "the Nth house is X" clauses from
worked_analyses.jsonl map to a 9-grade verdict in only 3 cases; Chandra-Lagna clauses in 1. So the
components stay reading-side-by-design; this consistency check is the honest substitute.

CLI:  PYTHONPATH=. python3 -m app.medini.doctrine.validation.overall_consistency [--json]
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
from app.medini.doctrine.validation import reconstruct as R
from app.medini.doctrine.validation import worked_chart_validate as W

_ROOT = Path(__file__).resolve().parents[4]
_CORP = _ROOT / "docs/raman_doctrine/validation/corpora"
_HELDOUT = sorted(str(p) for p in _CORP.glob("heldout_ch*.json"))
_FA = {"bhava": "lagna_verdict", "lord": "lord_verdict", "karaka": "karaka_verdict"}


def _fuse_raw(g_b: int, g_l: int, g_k: int, house: int) -> int:
    """The synthesize_house fusion (class-weighted mean + lead-veto), applied to RAW factor grades —
    a faithful mirror of `synthesis_v2.synthesize_house`'s arithmetic (lines ~288-295)."""
    cls = S2._HOUSE_CLASS[house]
    w_l, w_b, w_k = S2._WEIGHTS[cls]
    grade = round(w_l * g_l + w_b * g_b + w_k * g_k)
    lead = {"lord_led": g_l, "occupancy_led": g_b, "karaka_intrinsic": g_l}[cls]
    if lead <= S2.WEAK:
        grade = min(grade, S2.MODERATE)
    return max(0, min(8, grade))


def _central(grades: list[int]) -> int:
    """Central tendency of Raman's mapped factor grades — the derived overall target (median; mean
    as tiebreak is unnecessary for the within-one comparison)."""
    return int(round(statistics.median(grades)))


def run() -> dict[str, Any]:
    pats = W.load_verdict_map()
    idx = W._IDX
    rows: list[dict] = []
    for path in _HELDOUT:
        c = json.loads(Path(path).read_text())
        for rec in (c["charts"] if isinstance(c, dict) else c):
            rasi = rec["rasi"]
            ro = rec.get("axis") == "rasi" or "navamsa" not in rec
            if ro:
                continue  # overall fusion needs the Navāṁśa axis
            try:
                if R.consistency_errors(rasi, rec["navamsa"]):
                    continue
                chart = R.chart_from_raman(rasi, rec["navamsa"], rec["lagna_rasi"],
                                           rec["lagna_navamsa"])
            except (ValueError, KeyError):
                continue
            house = int(rec["house_judged"])
            raman_g: dict[str, int] = {}
            for v in rec.get("verdicts", []):
                if v["factor"] in _FA:
                    g = W.map_verdict(v["phrase"], pats)
                    if g is not None:
                        raman_g[v["factor"]] = idx[g]
            if len(raman_g) < 2:
                continue
            j = judge_house_doctrine(chart, house)
            g_b, _ = S2.grade_factor(j.lagna_verdict)
            g_l, _ = S2.grade_factor(j.lord_verdict)
            g_k, _ = S2.grade_factor(j.karaka_verdict)
            eng_overall, _ = S2.synthesize_house(j.lagna_verdict, j.lord_verdict,
                                                 j.karaka_verdict, house)
            central = _central(list(raman_g.values()))
            # fusion-logic: feed RAMAN's grades through the fusion (missing factor → its central)
            rb = raman_g.get("bhava", central)
            rl = raman_g.get("lord", central)
            rk = raman_g.get("karaka", central)
            fusion_only = _fuse_raw(rb, rl, rk, house)
            rows.append({"chart": rec.get("chart_no"), "house": house,
                         "n_factors": len(raman_g), "raman_central": central,
                         "eng_overall": eng_overall, "fusion_only": fusion_only,
                         "additive": idx[HJ._verdict_label(j.conclusion.score)],
                         "d_end2end": eng_overall - central,
                         "d_fusion": fusion_only - central})
    return {"rows": rows}


def _slice(rows: list[dict], min_factors: int, key: str) -> dict[str, Any]:
    sel = [r for r in rows if r["n_factors"] >= min_factors]
    n = len(sel)
    w1 = sum(1 for r in sel if abs(r[key]) <= 1)
    md = round(sum(r[key] for r in sel) / n, 3) if n else 0.0
    return {"n": n, "within1": w1, "within1_pct": round(100 * w1 / n, 1) if n else 0.0,
            "mean_delta": md}


def main() -> None:
    res = run()
    rows = res["rows"]
    print("Track 2 — synthesize_house consistency vs the central tendency of Raman's factor verdicts\n")
    print("  YIELD (why this is the honest substitute): Raman's OVERALL house verdicts map to a")
    print("  9-grade in 3/168 charts, Chandra-Lagna in 1/67 — narrative prose, unmeasurable directly.\n")
    for mf, lab in [(3, "all-3-factor charts"), (2, ">=2-factor charts")]:
        e = _slice(rows, mf, "d_end2end")
        f = _slice(rows, mf, "d_fusion")
        print(f"  {lab} (N={e['n']}):")
        print(f"    end-to-end  synthesize_house(engine) vs Raman-central   "
              f"within-one {e['within1']}/{e['n']} ({e['within1_pct']}%)  Δ{e['mean_delta']:+.2f}")
        print(f"    fusion-only fuse(Raman grades)       vs Raman-central   "
              f"within-one {f['within1']}/{f['n']} ({f['within1_pct']}%)  Δ{f['mean_delta']:+.2f}")
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
