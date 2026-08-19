"""Pilot A1 — blinded LLM-as-scorer over the held-out strength rows (ML_RESEARCH track A).

Question: does a frontier LLM's *holistic* reading of a chart reproduce Raman's 9-grade
strength verdicts better than the rule engine's ~53%/44% within-one — i.e. is the residual
above the engine's ceiling learnable from structure at all?

Design (pre-registered in the plan; measurement only, no engine change):

- **Rows.** Exactly the rows the validators score: the sign-reconstructed held-out pool
  (`heldout_ch*.json`, N=53) and the degree-accurate NH pool (`nh_strength.json` +
  `nh_strength_grow.json`, N=32). Raman's grade comes from the same pre-registered verdict
  map the validators use; the engine's grade from the live `judge_house_doctrine`.
- **Blinding.** Prompts carry ONLY chart structure (signs, or longitudes for NH rows) and the
  judged factor. No names, no birth lines, no dates, no chart numbers, no book identifiers.
  `audit_prompts` greps every prompt for leak markers and hard-fails on any hit.
- **Contamination probe (perturbed twins).** Both source books are published, so a frontier
  model may have memorized famous charts even blinded. For each row we emit a *twin*: one
  planet moved such that the judged factor's engine-finding multiset (and its label) is
  UNCHANGED — structurally the judged question is identical, but the chart no longer matches
  any published nativity. A structural scorer should grade real and twin alike; a large
  real-minus-twin accuracy gap means memorization, and the pilot reports that verdict.
  (Caveat, stated in the report: finding-multiset equality is sufficiency w.r.t. the
  doctrine's own feature set; a truly holistic judge may legitimately read the moved planet.
  Twins are therefore a conservative memorization detector, not a perfect one.)
- **Grading.** The LLM answers with one label from the same 9-grade scale; deltas use the
  validators' `_IDX` lattice. The LLM side runs as Claude subagents driven from the session
  (auditable JSON in/out under the corpus dir) — this module only builds prompts and scores
  responses, so the run is reproducible without an API key.

CLI:
  PYTHONPATH=. python3 -m app.medini.doctrine.validation.llm_scorer_pilot build <outdir>
  PYTHONPATH=. python3 -m app.medini.doctrine.validation.llm_scorer_pilot score <outdir>
"""
from __future__ import annotations

import glob
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

from app.medini.doctrine import raman_chart as rc
from app.medini.doctrine.domains.house_judgment import judge_house_doctrine
from app.medini.doctrine.validation import reconstruct as R
from app.medini.doctrine.validation import worked_chart_validate as W
from app.medini.ml.raman_saab.golden_registry import load_registry

_ROOT = Path(__file__).resolve().parents[4]
_CORP = _ROOT / "docs/raman_doctrine/validation/corpora"
_FACTOR_ATTR = {"bhava": "lagna_verdict", "lord": "lord_verdict",
                "karaka": "karaka_verdict", "overall": "conclusion"}
_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
_SCALE = ("afflicted", "weak", "moderate", "moderately good", "fairly good",
          "fairly strong", "fairly powerful", "very strong", "very powerful")
_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
# Perturbation candidates: classical non-luminary planets first (their move least disturbs
# frame-level testimony); nodes excluded (the Rahu/Ketu-opposite constraint couples them).
_PERTURB_ORDER = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Sun", "Moon")


def _sig(chart, house: int, factor: str, karaka: str | None = None):
    """The judged factor's engine evidence, as a comparable signature. Uses the numeric
    assessors directly (not the full DSL judgment) — the twin search calls this up to
    ~80x per row, and the assessors are what define the factor's structural findings.
    A named ``karaka`` (multi-karaka 4th-house rows) is assessed as THAT planet, the
    same way ``validate_record`` does. For 'overall' the conclusion blends all three
    factors (0.5 lord + 0.3 lagna + 0.2 karaka, per _build_conclusion)."""
    from app.medini.doctrine.domains.house_judgment import (
        _assess_bhava, _assess_karaka, _assess_lord, _assess_planet, _verdict_label)
    if factor == "overall":
        vs = {"bhava": _assess_bhava(chart, house), "lord": _assess_lord(chart, house),
              "karaka": _assess_karaka(chart, house)}
        parts = [(f, x.text, x.delta, x.frame)
                 for f, v in vs.items() for x in v.findings]
        blend = _verdict_label(round(0.5 * vs["lord"].score + 0.3 * vs["bhava"].score
                                     + 0.2 * vs["karaka"].score, 3))
        return (tuple(sorted(parts)), blend)
    if factor == "karaka" and karaka:
        v = _assess_planet(chart, karaka, "Karaka")
    else:
        assess = {"bhava": _assess_bhava, "lord": _assess_lord,
                  "karaka": _assess_karaka}[factor]
        v = assess(chart, house)
    return (tuple(sorted((x.text, x.delta, x.frame) for x in v.findings)), v.label)


# ---------------------------------------------------------------- row builders

def build_sign_rows() -> list[dict[str, Any]]:
    patterns = W.load_verdict_map()
    rows: list[dict[str, Any]] = []
    for path in sorted(glob.glob(str(_CORP / "heldout_ch*.json"))):
        corpus = json.loads(Path(path).read_text())
        for rec in corpus["charts"]:
            res = W.validate_record(rec, patterns)
            if res.get("excluded"):
                continue
            for i, row in enumerate(res["rows"]):
                if row.get("excluded"):
                    continue
                rows.append({
                    "id": f"sign:{Path(path).stem}:{rec['chart_no']}:{row['factor']}:{i}",
                    "kind": "sign",
                    "rasi": rec["rasi"], "navamsa": rec.get("navamsa"),
                    "lagna_rasi": rec["lagna_rasi"],
                    "lagna_navamsa": rec.get("lagna_navamsa"),
                    "axis": rec.get("axis") or ("rasi" if "navamsa" not in rec else None),
                    "house": int(rec["house_judged"]), "factor": row["factor"],
                    "karaka": row.get("karaka"),
                    "raman": row["raman"], "engine": row["engine"],
                })
    return rows


def build_nh_rows() -> list[dict[str, Any]]:
    patterns = W.load_verdict_map()
    cases = {c.key: c for c in load_registry()}
    rows: list[dict[str, Any]] = []
    for name in ("nh_strength.json", "nh_strength_grow.json"):
        for i, r in enumerate(json.loads((_CORP / name).read_text())["rows"]):
            case = cases.get(r["key"])
            if case is None or not case.positions:
                continue
            raman = W.map_verdict(r["phrase"], patterns)
            if raman is None:
                continue
            chart = rc.from_printed_positions(
                case.positions, case.lagna_lon, birth_jd=case.birth_jd,
                person_id=r["key"],
                retrograde={g: True for g in (case.retro or [])})
            j = judge_house_doctrine(chart, int(r["house"]))
            eng = getattr(j, _FACTOR_ATTR[r["factor"]]).label
            rows.append({
                "id": f"nh:{name.split('.')[0]}:{r['key']}:{r['factor']}:{i}",
                "kind": "nh",
                "positions": dict(case.positions), "lagna_lon": case.lagna_lon,
                "birth_jd": case.birth_jd, "retro": list(case.retro or []),
                "house": int(r["house"]), "factor": r["factor"], "karaka": None,
                "raman": raman, "engine": eng,
            })
    return rows


# ---------------------------------------------------------------- twins

def _chart_of(row: dict) -> "rc.RamanChart":
    if row["kind"] == "nh":
        return rc.from_printed_positions(
            row["positions"], row["lagna_lon"], birth_jd=row["birth_jd"],
            retrograde={g: True for g in row["retro"]})
    if row["axis"] == "rasi":
        return R.chart_from_rasi(row["rasi"], row["lagna_rasi"])
    return R.chart_from_raman(row["rasi"], row["navamsa"],
                              row["lagna_rasi"], row["lagna_navamsa"])


def make_twin(row: dict) -> dict | None:
    """Move ONE planet so the judged factor's finding signature is unchanged.
    Returns a twin row (chart fields replaced) or None if no clean perturbation exists."""
    base_sig = _sig(_chart_of(row), row["house"], row["factor"], row.get("karaka"))
    rng = random.Random(row["id"])  # deterministic per row
    for planet in _PERTURB_ORDER:
        if row["factor"] != "bhava" and row.get("karaka") == planet:
            continue
        signs = list(range(1, 13))
        rng.shuffle(signs)
        for new_sign in signs:
            twin = {**row}
            try:
                if row["kind"] == "nh":
                    lons = dict(row["positions"])
                    if planet not in lons:
                        continue
                    old = lons[planet]
                    if int(old // 30) + 1 == new_sign:
                        continue
                    lons[planet] = (new_sign - 1) * 30.0 + (old % 30.0)
                    twin["positions"] = lons
                else:
                    ras = dict(row["rasi"])
                    if planet not in ras:
                        continue
                    if R.sign_num(ras[planet]) == new_sign:
                        continue
                    ras[planet] = _SIGNS[new_sign - 1]
                    twin["rasi"] = ras
                    if row["axis"] != "rasi":
                        # keep a reachable navamsa for the moved planet
                        nav = dict(row["navamsa"])
                        ok = None
                        for nv in range(1, 13):
                            if R.longitude_for(new_sign, nv) is not None:
                                ok = nv
                                break
                        if ok is None:
                            continue
                        nav[planet] = _SIGNS[ok - 1]
                        twin["navamsa"] = nav
                if _sig(_chart_of(twin), row["house"], row["factor"]) == base_sig:
                    twin["id"] = row["id"] + "::twin"
                    twin["twin_of"] = row["id"]
                    twin["perturbed"] = planet
                    return twin
            except (ValueError, KeyError):
                continue
    return None


# ---------------------------------------------------------------- prompts

def _factor_phrase(row: dict) -> str:
    h = row["house"]
    if row["factor"] == "bhava":
        return "the Lagna (the 1st house itself)" if h == 1 else f"the {h}th house (the bhava itself)"
    if row["factor"] == "lord":
        return f"the lord of the {h}th house"
    if row["factor"] == "karaka":
        if row.get("karaka"):
            return f"{row['karaka']} as karaka (significator) of the {h}th house"
        return f"the karaka (significator) of the {h}th house"
    return f"the {h}th house overall (bhava, lord and karaka together)"


def render_prompt(row: dict) -> str:
    lines: list[str] = []
    if row["kind"] == "nh":
        chart = _chart_of(row)
        lag = row["lagna_lon"]
        lines.append("Sidereal chart. Whole-sign houses from the ascendant.")
        lines.append(f"Ascendant: {_SIGNS[int(lag // 30)]} {lag % 30.0:.1f} deg")
        for g in _GRAHAS:
            lon = row["positions"].get(g)
            if lon is None:
                continue
            retro = " (retrograde)" if g in row["retro"] else ""
            nav = _SIGNS[chart.varga_signs[g][9] - 1]
            lines.append(f"{g}: {_SIGNS[int(lon // 30)]} {lon % 30.0:.1f} deg"
                         f" | Navamsa: {nav}{retro}")
    else:
        lines.append("Sidereal chart. Whole-sign houses from the ascendant.")
        lines.append(f"Rasi ascendant: {row['lagna_rasi']}")
        lines.append("Rasi placements: " + "; ".join(
            f"{g} in {row['rasi'][g]}" for g in _GRAHAS if g in row["rasi"]))
        if row["axis"] == "rasi" or not row.get("navamsa"):
            lines.append("Navamsa: not available — judge from the Rasi alone.")
        else:
            lines.append(f"Navamsa ascendant: {row['lagna_navamsa']}")
            lines.append("Navamsa placements: " + "; ".join(
                f"{g} in {row['navamsa'][g]}" for g in _GRAHAS if g in row["navamsa"]))
    lines.append("")
    lines.append(
        f"Question: judged from the ascendant by the classical Vedic (Parashari) "
        f"house-judgment method — weighing sign dignity "
        f"(exaltation/own/friendly/inimical/debilitation), house placement "
        f"(kendra/trikona vs dusthana), lordships, aspects, conjunctions, hemming "
        f"(kartari), vargottama, combustion, and Rasi vs Navamsa testimony — how strong is "
        f"{_factor_phrase(row)}?")
    lines.append("Answer with EXACTLY ONE of these labels (weakest to strongest): "
                 + ", ".join(_SCALE) + ".")
    return "\n".join(lines)


_LEAK = re.compile(r"\b(19|18|17|16|20)\d\d\b|Chart No|Born|Notable Horoscopes"
                   r"|How to Judge|Gandhi|Nehru|Einstein|Lincoln|Buddha|Milton|Raman",
                   re.I)
# honorifics/generic words that occur inside registry names but are ordinary prompt
# vocabulary ("the lord of the 7th") — excluded from the name-leak scan.
_NAME_STOP = {"lord", "king", "queen", "duke", "emperor", "great", "sri", "sir",
              "swami", "the", "example", "for", "von", "chandra"}


def audit_prompts(prompts: dict[str, str], names: list[str]) -> list[str]:
    """Return leak hits (empty = blinding holds). Checks structural markers + every
    registry name against every prompt."""
    hits = []
    name_re = re.compile("|".join(re.escape(n) for n in names), re.I) if names else None
    for pid, text in prompts.items():
        if _LEAK.search(text):
            hits.append(f"{pid}: marker {_LEAK.search(text).group(0)!r}")
        if name_re and name_re.search(text):
            hits.append(f"{pid}: name {name_re.search(text).group(0)!r}")
    return hits


# ---------------------------------------------------------------- build / score

def build(outdir: Path) -> dict[str, Any]:
    rows = build_sign_rows() + build_nh_rows()
    twins = []
    no_twin = []
    for r in rows:
        t = make_twin(r)
        (twins.append(t) if t else no_twin.append(r["id"]))
    prompts = {r["id"]: render_prompt(r) for r in rows + twins}
    names = [c.name for c in load_registry()] + [p for c in load_registry()
                                                 for p in c.name.split()]
    names = [n for n in names if len(n) > 3 and n.lower() not in _NAME_STOP]
    leaks = audit_prompts(prompts, names)
    if leaks:
        raise SystemExit("BLINDING AUDIT FAILED:\n" + "\n".join(leaks))
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "rows.json").write_text(json.dumps(rows + twins, indent=1))
    order = sorted(prompts)          # deterministic, interleaves twins away from sources
    random.Random(20260710).shuffle(order)
    (outdir / "prompts.json").write_text(json.dumps(
        [{"id": pid, "prompt": prompts[pid]} for pid in order], indent=1))
    return {"n_rows": len(rows), "n_twins": len(twins), "no_twin": no_twin,
            "n_prompts": len(prompts), "audit": "clean"}


def score(outdir: Path) -> dict[str, Any]:
    rows = {r["id"]: r for r in json.loads((outdir / "rows.json").read_text())}
    responses: dict[str, str] = {}
    for f in sorted(outdir.glob("responses*.json")):
        for item in json.loads(f.read_text()):
            responses[item["id"]] = item["grade"].strip().lower()
    idx = W._IDX

    def bucket(pred: str | None, raman: str) -> int | None:
        if pred not in idx:
            return None
        return idx[pred] - idx[raman]

    out: dict[str, Any] = {}
    for label, pick in (("real", lambda r: "twin_of" not in r),
                        ("twin", lambda r: "twin_of" in r)):
        sub = [r for r in rows.values() if pick(r) and r["id"] in responses]
        deltas = []
        bad = 0
        for r in sub:
            d = bucket(responses[r["id"]], r["raman"])
            if d is None:
                bad += 1
                continue
            deltas.append((r, d))
        n = len(deltas)
        out[label] = {
            "n": n, "invalid_label": bad,
            "exact": sum(1 for _, d in deltas if d == 0),
            "within1": sum(1 for _, d in deltas if abs(d) <= 1),
            "within1_pct": round(100 * sum(1 for _, d in deltas if abs(d) <= 1) / n, 1) if n else 0.0,
            "mean_delta": round(sum(d for _, d in deltas) / n, 2) if n else 0.0,
        }
        for kind in ("sign", "nh"):
            ds = [d for r, d in deltas if r["kind"] == kind]
            if ds:
                out[label][kind] = {
                    "n": len(ds),
                    "within1_pct": round(100 * sum(1 for d in ds if abs(d) <= 1) / len(ds), 1),
                    "mean_delta": round(sum(ds) / len(ds), 2)}
    # engine side-by-side on the same real rows the LLM answered
    real = [r for r in rows.values() if "twin_of" not in r and r["id"] in responses]
    n = len(real)
    if n:
        eng = [idx[r["engine"]] - idx[r["raman"]] for r in real]
        out["engine_on_same_rows"] = {
            "n": n, "within1_pct": round(100 * sum(1 for d in eng if abs(d) <= 1) / n, 1),
            "mean_delta": round(sum(eng) / n, 2)}
    if out.get("real", {}).get("n") and out.get("twin", {}).get("n"):
        out["contamination_gap_pp"] = round(
            out["real"]["within1_pct"] - out["twin"]["within1_pct"], 1)
    return out


def main() -> None:
    cmd, outdir = sys.argv[1], Path(sys.argv[2])
    if cmd == "build":
        print(json.dumps(build(outdir), indent=1))
    elif cmd == "score":
        print(json.dumps(score(outdir), indent=1))
    else:
        raise SystemExit(f"unknown command {cmd!r}")


if __name__ == "__main__":
    main()
