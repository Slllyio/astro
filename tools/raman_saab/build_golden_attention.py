"""The second attention benchmark — which house did Raman pronounce on in each worked example?

`tests/fixtures/raman_goldens.jsonl` holds 224 of Raman's own worked examples (HTJAH-I 72,
HTJAH-II 93, Notable Horoscopes 60), each with birth data, his stated Lagna, and the verdicts he
actually pronounced. He pronounces on a **median of one house per example** — so the set of
houses carrying an expected verdict is a sharp record of where he chose to look.

Why a second benchmark rather than growing the first: the Notable Horoscopes benchmark scores
EMPHASIS in free prose ("the most formidable combinations refer to the 10th"), where he ranges
over a whole life. This one scores SELECTION in a targeted illustration ("this chart shows X in
the 7th"). Related questions, not the same question — so they are measured apart and never
pooled.

The practical difference is decisive. The prose benchmark has a trivial baseline of 0.63 p@1 and
31 charts, which resolves nothing smaller than about one chart (~0.071). This one has a trivial
baseline of 0.26 and 190 charts, resolving ~0.005 — the eight signals already declared "no
detectable effect" could not have been seen either way at the old size.

Admission is the same discipline: cast the chart and require the engine's ascendant to match the
Lagna Raman states. On the prose benchmark that check passed 9 of 9.

Usage:
    py -3.12 tools/raman_saab/build_golden_attention.py --out tests/fixtures/golden_attention.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Final, Optional

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData

SOURCE: Final[str] = "tests/fixtures/raman_goldens.jsonl"


def _load(path: Path) -> list[dict]:
    out = []
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith(("//", "#")):
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _houses(rec: dict) -> set[int]:
    ev = rec.get("expected_verdicts") or {}
    return {int(k.lstrip("Hh")) for k in ev if str(k).lstrip("Hh").isdigit()}


def _birth(rec: dict) -> Optional[BirthData]:
    b = rec.get("birth") or {}
    dt, tz, lat, lon = b.get("dt"), b.get("tz"), b.get("lat"), b.get("lon")
    if not dt or lat is None or lon is None:
        return None
    try:
        when = datetime.fromisoformat(str(dt))
    except ValueError:
        return None
    return BirthData(rec.get("name", rec.get("id", "?")), when.year, when.month, when.day,
                     when.hour, when.minute, float(tz if tz is not None else lon / 15.0),
                     float(lat), float(lon))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=SOURCE)
    ap.add_argument("--out", default="tests/fixtures/golden_attention.json")
    args = ap.parse_args()

    records = [r for r in _load(Path(args.source)) if r.get("case_type") == "worked_example"]
    charts, rejected = [], Counter()

    for rec in records:
        truth = _houses(rec)
        birth = _birth(rec)
        if not truth:
            rejected["no pronounced house"] += 1
            continue
        if birth is None:
            rejected["no usable birth data"] += 1
            continue
        try:
            chart = cast_chart(birth)
        except Exception:                                          # noqa: BLE001
            rejected["cast failed"] += 1
            continue

        stated = rec.get("lagna_sign")
        if stated and int(stated) != int(chart.asc_sign):
            rejected["Lagna mismatch"] += 1
            continue

        charts.append({
            "id": rec.get("id"), "book": rec.get("book"), "name": rec.get("name"),
            "birth": rec.get("birth"), "lagna_sign": stated,
            "computed_lagna_sign": int(chart.asc_sign),
            "lagna_confirmed": bool(stated),
            "pronounced_houses": sorted(truth),
            "confidence": rec.get("confidence"),
            "citations": rec.get("citations") or [],
            "review": sorted({(v or {}).get("verdict_review")
                              for v in (rec.get("expected_verdicts") or {}).values()
                              if isinstance(v, dict)} - {None}),
        })

    charts.sort(key=lambda c: str(c["id"]))
    for i, c in enumerate(charts):
        c["split"] = "tune" if i % 2 == 0 else "holdout"

    counter = Counter(h for c in charts for h in c["pronounced_houses"])
    top_house, top_n = counter.most_common(1)[0]
    top3 = [h for h, _ in counter.most_common(3)]

    payload = {
        "_about": ("Which house Raman pronounced on in each of his own worked examples. Target "
                   "is EXPERT ATTENTION, never life outcomes — clear of the astrobank firewall."),
        "_source": args.source,
        "_distinct_from": ("tests/fixtures/notable_attention.json scores EMPHASIS in free prose; "
                           "this scores SELECTION in a targeted illustration. Related questions, "
                           "not the same one. Report them apart; never pool them."),
        "_split": "deterministic: sorted by id, alternating tune/holdout, frozen before scoring",
        "_admission": "cast must reproduce the Lagna Raman states (records without one are kept "
                      "but flagged lagna_confirmed=false)",
        "_trivial_baselines": {
            "always_top_house": {"house": top_house,
                                 "precision_at_1": round(top_n / len(charts), 3)},
            "always_top_3": {"houses": top3,
                             "recall_at_3": round(sum(1 for c in charts
                                                      if set(top3) & set(c["pronounced_houses"]))
                                                  / len(charts), 3)},
        },
        "_counts": {"worked_examples": len(records), "admitted": len(charts),
                    "tune": sum(1 for c in charts if c["split"] == "tune"),
                    "holdout": sum(1 for c in charts if c["split"] == "holdout"),
                    "rejected": dict(rejected)},
        "charts": charts,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"worked examples : {len(records)}")
    print(f"admitted        : {len(charts)}  (tune {payload['_counts']['tune']} / "
          f"holdout {payload['_counts']['holdout']})")
    for reason, n in rejected.most_common():
        print(f"  rejected — {reason}: {n}")
    print(f"\nLagna confirmed : {sum(1 for c in charts if c['lagna_confirmed'])} of {len(charts)}")
    print(f"books           : {dict(Counter(c['book'] for c in charts))}")
    print(f"trivial p@1     : always H{top_house} -> "
          f"{payload['_trivial_baselines']['always_top_house']['precision_at_1']:.3f}")
    print(f"trivial recall@3: always {top3} -> "
          f"{payload['_trivial_baselines']['always_top_3']['recall_at_3']:.3f}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
