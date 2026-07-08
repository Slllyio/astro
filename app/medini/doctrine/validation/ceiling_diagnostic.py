"""Phase D.0 — the kāraka-ceiling separability diagnostic (measurement only, NO engine change).

Increment 8 ("B") documented an OVER-CREDIT of the lord/kāraka: a kendra placement plus a
strong dignity offsets stacked malefic testimony where Raman grades the planet *afflicted*,
and the over-credit is NOT separable on the engine's sign-only features. Phase D asks whether
the sub-degree resolution we already carry -- ``reconstruct.longitude_for`` parks every planet
at its **pada midpoint**, preserved on ``chart.bundle.chart.planet_lons`` -- could break the
ceiling via a conjunction-orb feature.

But a conjunction-orb only bites on **same-sign conjunctions**; Raman's aspects are whole-sign
rāśi-drishti (degree-free by doctrine), so aspect-based affliction is orb-immune. This script
decides, on the existing held-out data, WHERE the over-credit actually lives:

  for every lord/kāraka row with engine - Raman >= +2, decompose the subject planet's malefic
  testimony (from the LIVE engine's own Findings) into
     * same-sign malefic CONJUNCTIONS  -> compute the pada-orb (min angular gap, and in padas)
     * whole-sign malefic ASPECTS       -> counted, flagged orb-IMMUNE
  and record the POSITIVE offset (placement/dignity/vargottama) propping the planet up.

If the over-credit is concentrated in tight-orb conjunctions -> a conjunction-orb feature can
help (Phase D.1). If it lives in whole-sign aspects / the positive offset (as ch70 hints) ->
pada-orb cannot close it; the honest move is to record the stronger negative result and pivot.

CLI:
  PYTHONPATH=. python3 -m app.medini.doctrine.validation.ceiling_diagnostic          # all held-out corpora
  PYTHONPATH=. python3 -m app.medini.doctrine.validation.ceiling_diagnostic --json   # + machine-readable
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.medini.doctrine.domains.house_judgment import (
    BHAVA_KARAKAS, VERDICT_SCALE, _assess_planet, _lord_of, _verdict_label,
)
from app.medini.doctrine.validation import reconstruct as R
from app.medini.doctrine.validation.worked_chart_validate import (
    _MAP_PATH, load_verdict_map, map_verdict,
)

_IDX = {lab: i for i, lab in enumerate(VERDICT_SCALE)}
_PADA = 30.0 / 9.0                      # 3°20' -- the reconstruction's position granularity
_CORPUS_DIR = (Path(__file__).resolve().parents[4]
               / "docs/raman_doctrine/validation/corpora")
# genuinely held-out houses only (the tuned set 1/2/7/9/11 is excluded by construction)
_HELDOUT_GLOB = "heldout_ch*.json"
_OVERCREDIT = 2                        # engine - Raman >= this  ==>  an "over-credit" row


def _angular_gap(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _companion(label: str) -> str:
    # "conjunct Saturn (malefic)" -> "Saturn"; "aspected by Mars (malefic)" -> "Mars"
    s = label.replace("conjunct ", "").replace("aspected by ", "")
    return s.split(" (", 1)[0].strip()


def _reconstruct(rec: dict):
    """Rebuild the chart exactly as worked_chart_validate does, or None if it can't score
    on the full (rāśi+navāṁśa) axis -- the diagnostic needs real intra-sign longitudes, so
    rāśi-only records (no navāṁśa) are skipped, not faked."""
    if rec.get("axis") == "rasi" or "navamsa" not in rec:
        return None, "rasi_only"
    if R.consistency_errors(rec["rasi"], rec["navamsa"]):
        return None, "inconsistent"
    try:
        return R.chart_from_raman(rec["rasi"], rec["navamsa"],
                                  rec["lagna_rasi"], rec["lagna_navamsa"]), None
    except (ValueError, KeyError) as e:
        return None, f"reconstruct_error: {e}"


def _subject_planet(chart, rec: dict, row: dict) -> str:
    house = int(rec["house_judged"])
    if row["factor"] == "lord":
        return _lord_of(chart, house)
    if row.get("karaka"):
        return row["karaka"]
    return BHAVA_KARAKAS[house][0]


def _decompose(chart, subject: str, verdict) -> dict[str, Any]:
    """Split the subject's malefic testimony into conjunctions (orb-measurable) vs whole-sign
    aspects (orb-immune), and sum the positive offset. Reads the LIVE FactorVerdict.findings so
    the diagnostic sees exactly what the engine scored. Orbs are reckoned in the RĀŚI frame
    (the audit's 'siege rasi') from the preserved pada-midpoint longitudes."""
    lons = chart.bundle.chart.planet_lons
    conj_malefics: list[tuple[str, float]] = []   # (planet, angular gap in the Rasi)
    n_aspect_malefic = 0
    pos_offset = 0.0
    for f in verdict.findings:
        if f.frame == "Navamsa":
            continue                              # ceiling is a Rasi phenomenon; keep it clean
        if f.criterion == "conjunction" and f.delta < 0:
            comp = _companion(f.text)
            gap = _angular_gap(lons[subject], lons[comp]) if comp in lons else float("nan")
            conj_malefics.append((comp, gap))
        elif f.criterion == "aspect" and f.delta < 0:
            n_aspect_malefic += 1
        elif f.delta > 0 and f.criterion in ("placement", "dignity", "vargottama"):
            pos_offset += f.delta
    gaps = [g for _, g in conj_malefics if g == g]  # drop NaN
    min_orb = min(gaps) if gaps else None
    return {
        "n_conj_malefic": len(conj_malefics),
        "conj_malefics": [{"planet": p, "orb_deg": round(g, 2),
                           "orb_padas": round(g / _PADA, 2)}
                          for p, g in conj_malefics if g == g],
        "min_orb_deg": round(min_orb, 2) if min_orb is not None else None,
        "min_orb_padas": round(min_orb / _PADA, 2) if min_orb is not None else None,
        "n_aspect_malefic": n_aspect_malefic,
        "positive_offset": round(pos_offset, 2),
    }


def run(corpus_paths: list[str] | None = None,
        map_path: Path = _MAP_PATH) -> dict[str, Any]:
    patterns = load_verdict_map(map_path)
    paths = (sorted(str(p) for p in _CORPUS_DIR.glob(_HELDOUT_GLOB))
             if corpus_paths is None else corpus_paths)
    rows: list[dict] = []
    skipped: list[dict] = []
    for p in paths:
        corpus = json.loads(Path(p).read_text())
        records = corpus["charts"] if isinstance(corpus, dict) else corpus
        for rec in records:
            chart, why = _reconstruct(rec)
            if chart is None:
                skipped.append({"chart": rec.get("chart_no"), "src": Path(p).name,
                                "why": why})
                continue
            for v in rec.get("verdicts", []):
                if v["factor"] not in ("lord", "karaka"):
                    continue
                raman = map_verdict(v["phrase"], patterns)
                if raman is None:
                    continue
                subject = _subject_planet(chart, rec, v)
                verdict = _assess_planet(chart, subject, v["factor"].capitalize())
                eng = verdict.label
                delta = _IDX[eng] - _IDX[raman]
                if delta < _OVERCREDIT:
                    continue
                rows.append({
                    "chart": rec.get("chart_no"), "src": Path(p).name,
                    "house": int(rec["house_judged"]), "factor": v["factor"],
                    "subject": subject, "raman": raman, "engine": eng, "delta": delta,
                    "phrase": v["phrase"],
                    **_decompose(chart, subject, verdict),
                })
    rows.sort(key=lambda r: (-r["delta"], r["chart"] or 0))
    n = len(rows)
    conj_driven = sum(1 for r in rows if r["n_conj_malefic"] > 0)
    aspect_driven = sum(1 for r in rows if r["n_conj_malefic"] == 0
                        and r["n_aspect_malefic"] > 0)
    offset_only = sum(1 for r in rows if r["n_conj_malefic"] == 0
                      and r["n_aspect_malefic"] == 0)
    tight = [r for r in rows if r["min_orb_padas"] is not None
             and r["min_orb_padas"] <= 1.0]
    return {
        "n_overcredit_rows": n,
        "conj_present": conj_driven,
        "aspect_only": aspect_driven,
        "offset_only": offset_only,
        "conj_present_tight_orb": len(tight),
        "rows": rows,
        "n_skipped": len(skipped),
        "skipped": skipped,
    }


def _print(s: dict) -> None:
    print(f"over-credit rows (lord/kāraka, engine-Raman >= +{_OVERCREDIT}): "
          f"{s['n_overcredit_rows']}")
    print(f"  with >=1 same-sign malefic CONJUNCTION : {s['conj_present']}  "
          f"(of which tight orb <=1 pada: {s['conj_present_tight_orb']})")
    print(f"  aspect-only (no conjunction, orb-IMMUNE): {s['aspect_only']}")
    print(f"  offset-only (no malefic testimony)      : {s['offset_only']}")
    print(f"  skipped (rasi-only / gate / recon)      : {s['n_skipped']}")
    print()
    hdr = (f"{'ch':>4} {'src':<22} {'fac':<6} {'subj':<8} {'raman':<14} "
           f"{'engine':<14} {'Δ':>2} {'#cj':>3} {'orb°':>6} {'orbP':>5} "
           f"{'#asp':>4} {'off':>5}")
    print(hdr)
    print("-" * len(hdr))
    for r in s["rows"]:
        orb = f"{r['min_orb_deg']:.2f}" if r["min_orb_deg"] is not None else "  -  "
        orbp = f"{r['min_orb_padas']:.2f}" if r["min_orb_padas"] is not None else "  -  "
        print(f"{str(r['chart']):>4} {r['src'][:22]:<22} {r['factor']:<6} "
              f"{r['subject']:<8} {r['raman']:<14} {r['engine']:<14} {r['delta']:>+2d} "
              f"{r['n_conj_malefic']:>3} {orb:>6} {orbp:>5} {r['n_aspect_malefic']:>4} "
              f"{r['positive_offset']:>+5.1f}")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    summary = run(args or None)
    _print(summary)
    if "--json" in sys.argv:
        print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
