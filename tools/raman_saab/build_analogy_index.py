"""Precompute the analogy index — Raman's own worked charts, on the axes he compares them by.

`analogy` answers "this chart resembles Raman's reading of X, in these respects". That needs a
reference set, and the 190 admitted worked examples in `golden_attention.json` are it: real
charts he read and published, each with the house he pronounced on and a citation.

The features are the axes he actually compares charts on, not a generic embedding:

  * the ascendant and its lord's situation — "ascendant lord in situations SIMILAR TO the above
    illustration will confer a weak constitution" (HTJAH-I)
  * which planets bear on the Lagna — "saturnine influences on Lagna"
  * each graha's dignity and house — the vocabulary every one of his comparisons is phrased in

Built with `cast_chart` (~30 ms) rather than a full report (~3 s), so the whole reference set is
seconds rather than ten minutes, and the index is a fixture the runtime just reads.

Usage:
    py -3.12 tools/raman_saab/build_analogy_index.py --out tests/fixtures/analogy_index.json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.dignity import dignity_state
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData

SIGN_LORDS: dict[int, str] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


def chart_features(chart) -> dict:
    """The doctrinal fingerprint of a chart — everything Raman's comparisons are phrased in."""
    asc = int(chart.asc_sign)
    lord = SIGN_LORDS[asc]
    lp = chart.planets.get(lord)
    planets = {}
    for name, p in chart.planets.items():
        sign = getattr(p, "sign", None)
        planets[name] = {
            "house": getattr(p, "rasi_house", None),
            "dignity": dignity_state(name, sign) if sign else None,
            "retrograde": bool(getattr(p, "retrograde", False)),
            "vargottama": bool(getattr(p, "vargottama", False)),
        }
    return {
        "asc_sign": asc,
        "lagna_lord": lord,
        "lagna_lord_house": getattr(lp, "rasi_house", None) if lp else None,
        "lagna_lord_dignity": (dignity_state(lord, getattr(lp, "sign", None))
                               if lp and getattr(lp, "sign", None) else None),
        # "saturnine influences on Lagna" — who actually sits in the rising sign
        "in_lagna": sorted(n for n, v in planets.items() if v["house"] == 1),
        "planets": planets,
    }


def _birth(rec: dict) -> Optional[BirthData]:
    b = rec.get("birth") or {}
    try:
        when = datetime.fromisoformat(str(b.get("dt")))
    except (TypeError, ValueError):
        return None
    if b.get("lat") is None or b.get("lon") is None:
        return None
    tz = b.get("tz")
    return BirthData(rec.get("name") or rec.get("id") or "?", when.year, when.month, when.day,
                     when.hour, when.minute, float(tz if tz is not None else b["lon"] / 15.0),
                     float(b["lat"]), float(b["lon"]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bench", default="tests/fixtures/golden_attention.json")
    ap.add_argument("--out", default="tests/fixtures/analogy_index.json")
    args = ap.parse_args()

    data = json.loads(Path(args.bench).read_text(encoding="utf-8"))
    entries, failed = [], 0
    for rec in data["charts"]:
        birth = _birth(rec)
        if birth is None:
            failed += 1
            continue
        try:
            chart = cast_chart(birth)
        except Exception:                                          # noqa: BLE001
            failed += 1
            continue
        entries.append({
            "id": rec["id"], "book": rec["book"], "name": rec["name"],
            "pronounced_houses": rec["pronounced_houses"],
            "citations": rec.get("citations") or [],
            "features": chart_features(chart),
        })

    payload = {
        "_about": ("Raman's own worked charts, fingerprinted on the axes he compares charts by. "
                   "The reference set for `analogy`."),
        "_source": args.bench,
        "_note": ("Cast with cast_chart (ayanamsa raman, the default) — the same casting that "
                  "reproduced his printed positions to 0.01 degrees and matched his stated "
                  "Lagna 164 times out of 164."),
        "_counts": {"indexed": len(entries), "failed": failed},
        "charts": entries,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    from collections import Counter
    signs = Counter(e["features"]["asc_sign"] for e in entries)
    print(f"indexed {len(entries)} charts ({failed} failed)")
    print(f"ascendant spread: {dict(sorted(signs.items()))}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
