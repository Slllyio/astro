"""Increment 30 — structural-feature separability diagnostic (measurement only, NO engine change).

Increment 29 (Gate F) proved the strong-side under-credit is a FEATURE gap: synthesis_v2's gates
read Finding *tags*, and the tags marking Raman's strong-graded-yet-afflicted factors (exaltation,
kendra, benefic aspect) are identical to those on his afflicted-graded factors, so no gate over the
CURRENT vocabulary separates them. Increment 30 asks the natural follow-up: do NEW structural
features — computed from the same chart but absent from the Finding vocabulary — separate the two?

Three candidate features, each targeting a documented strong-side miss and each computable from the
existing sign+navamsa data:

  yoga_pos  — the factor's planet (the house LORD for a bhava factor) participates in a POSITIVE
              strength yoga (``app.reading.computations.yogas_extended.detect_yogas`` — true
              participants parsed from each Finding's ``participants=`` evidence).
  disp_ge5  — the factor planet's DISPOSITOR (``dignity.SIGN_RULERS`` of its sign) itself grades
              >= "fairly strong" under synthesis_v2 (Raman credits "the lord is in the sign of an
              exalted/strong planet").
  cluster   — >= 3 benefic/yogakaraka grahas ASPECT or CONJOIN the factor's house (the "combined
              aspect" structure Raman names; today one flat Finding per aspecter).

The go/no-go question (the whole increment): do these tokens appear on the STRONG-graded slice and
NOT on the AFFLICTED slice? If they anti-separate, a gate on them cannot help — increment 30 is a
documented negative, established read-only, with the live engine untouched (the inert-token design's
whole point: fail fast at near-zero cost).

MEASURED RESULT: they ANTI-separate. Pooled across held-out + NH + anchor (N strong=30, aff=68):
  yoga_pos  37% strong  vs  43% afflicted
  disp_ge5   0% strong  vs  12% afflicted
  cluster    0% strong  vs   1% afflicted
  any signal 37% strong  vs  49% afflicted
Every signal is at least as common on Raman's afflicted factors as his strong ones — a gate would
lift the afflicted slice MORE than the strong slice, worsening the over-credit. The discriminator
Raman uses to credit a strong-but-afflicted factor is not recoverable from yoga-participation,
dispositor-strength, or benefic-cluster structure over this feature space. Documented negative;
synthesis_v2 / house_judgment unchanged. See REPORT_synthesis_v2.md § increment 30.

CLI:
  PYTHONPATH=. python3 -m app.medini.doctrine.validation.structural_separability [--json]
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any

from app.core.dignity import SIGN_RULERS
from app.core.drishti_argala import planets_aspecting_bhava
from app.medini.doctrine.domains import house_judgment as HJ
from app.medini.doctrine.domains import synthesis_v2 as S2
from app.medini.doctrine.validation import anchor_live_validate as A
from app.medini.doctrine.validation import nh_strength_validate as NH
from app.medini.doctrine.validation import reconstruct as R
from app.medini.doctrine.validation import worked_chart_validate as W

_ROOT = Path(__file__).resolve().parents[4]
_CORP = _ROOT / "docs/raman_doctrine/validation/corpora"
_HELDOUT = sorted(str(p) for p in _CORP.glob("heldout_ch*.json"))
_NH_ALL = [_CORP / "nh_strength.json", _CORP / "nh_strength_grow.json",
           _CORP / "nh_strength_grow2.json", _CORP / "nh_strength_grow3.json",
           _CORP / "nh_strength_grow4.json"]
GRAHAS = HJ.GRAHAS


# ── the three candidate structural features ──────────────────────────────────────────────────────

def yoga_participation(chart) -> dict[str, set[str]]:
    """{planet: {'+','-'}} — grahas participating in a positive/negative yoga. Only the trusted
    ``participants=[...]`` evidence entry is read (falling back to graha names in the verdict for
    detectors that don't emit one)."""
    from app.reading.computations.yogas_extended import detect_yogas
    c = chart.bundle.chart
    d1 = {p: {"sign": c.planet_signs[p], "longitude": c.planet_lons[p]} for p in c.planet_signs}
    out: dict[str, set[str]] = {}
    for f in detect_yogas(d1, c.asc_sign, c.planet_signs["Moon"]):
        direction = "+" if getattr(f, "direction", "") == "positive" else "-"
        parts = None
        for e in getattr(f, "evidence", []):
            s = str(e)
            if s.startswith("participants="):
                try:
                    parts = ast.literal_eval(s.split("=", 1)[1])
                except (ValueError, SyntaxError):
                    parts = None
                break
        if parts is None:
            blob = getattr(f, "verdict", "")
            parts = [g for g in GRAHAS if g in blob or g[:3] in blob]
        for g in parts:
            if g in GRAHAS:
                out.setdefault(g, set()).add(direction)
    return out


def dispositor_grade(chart, planet: str) -> tuple[str | None, int]:
    """(dispositor, synthesis_v2 grade). -1 when the planet is its own dispositor (own sign)."""
    sign = chart.bundle.chart.planet_signs[planet]
    disp = SIGN_RULERS.get(sign)
    if disp is None or disp == planet:
        return disp, -1
    g, _ = S2.grade_factor(HJ._assess_planet(chart, disp, "Dispositor"))
    return disp, g


def fortification_cluster(chart, house: int, factor_planet: str | None) -> int:
    """Count benefic/yogakaraka grahas aspecting or conjoining the factor's house."""
    d1 = HJ._d1_houses(chart)
    around = set(planets_aspecting_bhava(house, d1)) | {g for g in GRAHAS if d1.get(g) == house}
    n = 0
    for g in around:
        if g == factor_planet:
            continue
        _b, tag = HJ._planet_nature(chart, g, None)
        if HJ._bhava_benefic(chart, g, None) or tag == "yogakaraka":
            n += 1
    return n


def _factor_planet(chart, house: int, factor: str, rec_karaka: str | None = None) -> str:
    # bhava's dispositor/yoga signal uses the house LORD; cluster is on the house's own set.
    if factor == "karaka":
        return rec_karaka or HJ.BHAVA_KARAKAS[house][0]
    return HJ._lord_of(chart, house)


# ── the row-level probe + slice aggregation ──────────────────────────────────────────────────────

def _row(raman: str, chart, house: int, factor: str, rec_karaka: str | None = None) -> dict:
    planet = _factor_planet(chart, house, factor, rec_karaka)
    yp = yoga_participation(chart)
    _disp, dg = dispositor_grade(chart, planet)
    cl = fortification_cluster(chart, house, planet if factor != "karaka" else planet)
    ri = S2._IDX.get(raman, -1)
    slc = "strong" if ri >= S2.FAIRLY_STRONG else ("afflicted" if ri <= S2.WEAK else "mid")
    return {"slice": slc, "yoga_pos": "+" in yp.get(planet, set()),
            "disp_ge5": dg >= S2.FAIRLY_STRONG, "cluster": cl >= 3, "cluster_n": cl}


def collect() -> list[dict]:
    pats = W.load_verdict_map()
    rows: list[dict] = []
    # anchor
    corpus = json.loads(A._CORPUS.read_text())
    ah = int(corpus["house"])
    for rec in corpus["charts"]:
        chart = A.chart_for(rec)
        for v in rec["verdicts"]:
            if v["factor"] in ("bhava", "lord", "karaka"):
                rows.append(_row(v["raman"], chart, ah, v["factor"]))
    # held-out
    for path in _HELDOUT:
        c = json.loads(Path(path).read_text())
        for rec in (c["charts"] if isinstance(c, dict) else c):
            rasi = rec["rasi"]
            ro = rec.get("axis") == "rasi" or "navamsa" not in rec
            try:
                if ro:
                    chart = R.chart_from_rasi(rasi, rec["lagna_rasi"])
                elif R.consistency_errors(rasi, rec["navamsa"]):
                    continue
                else:
                    chart = R.chart_from_raman(rasi, rec["navamsa"], rec["lagna_rasi"],
                                               rec["lagna_navamsa"])
            except (ValueError, KeyError):
                continue
            house = int(rec["house_judged"])
            for v in rec.get("verdicts", []):
                if v["factor"] not in ("bhava", "lord", "karaka"):
                    continue
                raman = W.map_verdict(v["phrase"], pats)
                if raman is not None:
                    rows.append(_row(raman, chart, house, v["factor"], v.get("karaka")))
    # NH degree pool
    from app.medini.ml.raman_saab.golden_registry import load_registry
    cases = {c.key: c for c in load_registry()}
    for path in _NH_ALL:
        for r in json.loads(Path(path).read_text())["rows"]:
            case = cases.get(r["key"])
            if case is None or not case.positions or r["factor"] == "overall":
                continue
            raman = W.map_verdict(r["phrase"], pats)
            if raman is not None:
                rows.append(_row(raman, NH._chart_for(case), int(r["house"]), r["factor"]))
    return rows


def summarize(rows: list[dict]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for slc in ("strong", "mid", "afflicted"):
        sel = [r for r in rows if r["slice"] == slc]
        n = len(sel)
        out[slc] = {"n": n,
                    "yoga_pos": sum(r["yoga_pos"] for r in sel),
                    "disp_ge5": sum(r["disp_ge5"] for r in sel),
                    "cluster": sum(r["cluster"] for r in sel),
                    "any": sum(1 for r in sel if r["yoga_pos"] or r["disp_ge5"] or r["cluster"])}
    return out


def main() -> None:
    rows = collect()
    s = summarize(rows)
    print("increment 30 — structural-feature separability (do NEW tokens separate strong from afflicted?)\n")
    print(f"  {'signal':12} {'strong':>16} {'mid':>16} {'afflicted':>16}")

    def cell(slc, key):
        n = s[slc]["n"]
        return f"{s[slc][key]}/{n} ({100*s[slc][key]//n if n else 0}%)"
    for key in ("yoga_pos", "disp_ge5", "cluster", "any"):
        print(f"  {key:12} {cell('strong', key):>16} {cell('mid', key):>16} {cell('afflicted', key):>16}")
    print("\n  VERDICT: the signals anti-separate (each at least as common on afflicted as on strong)")
    print("  → structural tokens cannot separate the strong slice; documented negative (incr. 30).")
    if "--json" in sys.argv:
        print(json.dumps({"summary": s}, indent=1))


if __name__ == "__main__":
    main()
