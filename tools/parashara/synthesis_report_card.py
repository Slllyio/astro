"""Synthesis report card — the reasoning layer scored against Raman's CONFIRMED published verdicts.

Track 1 of the parashara report card. Runs the full pipeline (`synthesize(read(cast(...)))`) on every
Raman golden that carries full birth data, and compares each house's synthesis verdict with Raman's
own printed conclusion for that house.

READ IT HONESTLY: this is AGREEMENT WITH RAMAN, not "BPHS accuracy". Raman deliberately revised
Parashara, so the ceiling is below 100% by construction — a divergence where the two schools differ
is a doctrinal difference, not necessarily an engine error. Its value is as a FIXED YARDSTICK: run it
before and after a change and the delta says whether the change moved the engine toward or away from
a published authority's conclusions.

Scope: only records with full birth data (synthesize needs a real cast — speeds, Kala, Gulika).
Positions-only records are SKIPPED, never stubbed (no silent approximation).

The 7-verdict synthesis axis is mapped onto Raman's ordinal afflicted < mixed < favourable:
  granted, delayed  -> favourable  (the matter manifests; 'delayed' = manifests late)
  difficult, mixed, ordinary -> mixed (promised-but-obstructed / divided / unremarkable)
  denied            -> afflicted
  indeterminate     -> abstain (scored distance 2, the Raman tool's abstention convention)
The full confusion table (synthesis verdict x gold) is printed alongside, so the mapping can be read
off the data rather than taken on trust.

Usage:
    py -3.12 -m tools.parashara.synthesis_report_card
    py -3.12 -m tools.parashara.synthesis_report_card --limit 10
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from app.parashara.chart.cast import cast as cast_parashara
from app.parashara.reading import read
from app.parashara.synthesis import synthesize
from tools.parashara.cross_engine_agreement import (
    _birth, _confirmed, _dist, _parashara_verdicts, _ratchet_records, load_goldens)

#: synthesis verdict -> Raman's vocabulary (None = abstain).
SYNTH_TO_RAMAN: dict[str, Optional[str]] = {
    "granted": "favourable", "delayed": "favourable",
    "difficult": "mixed", "mixed": "mixed", "ordinary": "mixed",
    "denied": "afflicted",
    "indeterminate": None,
}


def _synthesis_verdicts(rec: dict[str, Any]) -> Optional[dict[int, str]]:
    """{house: synthesis verdict} for a birth-data record, or None if it has no birth data."""
    birth = _birth(rec)
    if birth is None:
        return None
    chart = cast_parashara(year=birth.year, month=birth.month, day=birth.day, hour=birth.hour,
                           minute=birth.minute, tz_offset=birth.tz_offset,
                           latitude=birth.latitude, longitude=birth.longitude)
    report = synthesize(read(chart))
    return {h: j.verdict for h, j in report.houses.items()}


def score(limit: Optional[int] = None) -> dict[str, Any]:
    """Score the synthesis against every CONFIRMED verdict on a birth-data golden."""
    recs = _ratchet_records(load_goldens())
    exact = within1 = inversions = abstained = total = skipped = 0
    # Baselines on the SAME verdicts — the older parashara judges — so deltas are apples to apples.
    base = {k: {"exact": 0, "within1": 0, "inversions": 0} for k in ("ch11", "richer")}
    confusion: Counter[tuple[str, str]] = Counter()
    for rec in recs:
        if limit is not None and total >= limit:
            break
        verdicts = _synthesis_verdicts(rec)
        if verdicts is None:
            skipped += len(_confirmed(rec))
            continue
        older = {"ch11": _parashara_verdicts(rec), "richer": _parashara_verdicts(rec, richer=True)}
        for house, entry in _confirmed(rec):
            gold = entry["verdict"]
            synth = verdicts[house]
            mapped = SYNTH_TO_RAMAN[synth]
            total += 1
            confusion[(synth, gold)] += 1
            d = _dist(mapped, gold)
            exact += d == 0
            within1 += d <= 1
            inversions += mapped is not None and d >= 2
            abstained += mapped is None
            for k, vs in older.items():
                bd = _dist(vs.get(house), gold)
                base[k]["exact"] += bd == 0
                base[k]["within1"] += bd <= 1
                base[k]["inversions"] += bd >= 2
    return {"total": total, "exact": exact, "within1": within1, "inversions": inversions,
            "abstained": abstained, "skipped_positions_only": skipped,
            "confusion": dict(confusion), "baselines": base}


_FIELD_CASE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "field_case_01.json"
_LIFE_SPAN = 80.0   # years over which the timing chance-rate is measured


def score_field_case() -> dict[str, Any]:
    """Track 2 — the one REAL-OUTCOME chart (anonymised, owner-confirmed): its per-signification
    verdicts scored against the synthesis house verdict, and its dated events against the dasha
    windows that target each event's house.

    Event -> house(s) is borrowed from the Raman engine's cited event taxonomy (tooling only; the
    parashara engine itself never imports it). Every timing hit is printed beside its CHANCE RATE —
    the share of life the event's houses are targeted anyway — because window targeting is broad and
    a hit that chance would deliver 90% of the time proves little.
    """
    from app.parashara.synthesis.activation import active_windows
    from app.raman_saab.rectification.events import EVENT_TAXONOMY

    case = json.loads(_FIELD_CASE.read_text(encoding="utf-8"))
    b = case["birth"]
    reading = read(cast_parashara(year=b["year"], month=b["month"], day=b["day"], hour=b["hour"],
                                  minute=b["minute"], tz_offset=b["tz_offset"],
                                  latitude=b["latitude"], longitude=b["longitude"]))
    report = synthesize(reading)

    static_total = static_exact = static_w1 = 0
    static_misses: list[str] = []
    for house_s, sigs in case["confirmed_verdicts"].items():
        synth = report.houses[int(house_s)].verdict
        mapped = SYNTH_TO_RAMAN[synth]
        for sig, truth in sigs.items():
            d = _dist(mapped, truth)
            static_total += 1
            static_exact += d == 0
            static_w1 += d <= 1
            if d >= 2:
                static_misses.append(f"H{house_s}.{sig}: synthesis {synth} vs truth {truth}")

    birth_year = b["year"] + (b["month"] - 1 + b["day"] / 31.0) / 12.0
    events: list[dict[str, Any]] = []
    for e in case["events"]:
        spec = EVENT_TAXONOMY[e["event_type"]]
        houses = (spec.house, *spec.aux_houses)
        age = e["year"] + ((e.get("month") or 6) - 0.5) / 12.0 - birth_year
        windows = active_windows(reading, houses)
        hit = next((w for w in windows if w.start_age <= age < w.end_age), None)
        covered = sum(max(0.0, min(w.end_age, _LIFE_SPAN) - w.start_age)
                      for w in windows if w.start_age < _LIFE_SPAN)
        events.append({"event": e["event_type"], "year": e["year"], "houses": houses,
                       "hit": hit is not None, "quality": hit.quality if hit else None,
                       "chance": min(1.0, covered / _LIFE_SPAN)})
    return {"static_total": static_total, "static_exact": static_exact, "static_within1": static_w1,
            "static_misses": static_misses, "events": events}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, default=None, help="score only the first N verdicts")
    s = score(ap.parse_args().limit)
    n = s["total"]
    print(f"\nSynthesis report card — {n} CONFIRMED Raman verdicts on birth-data charts "
          f"({s['skipped_positions_only']} positions-only verdicts skipped, never stubbed)\n")
    print(f"  exact     = {s['exact']}/{n} = {s['exact'] / n:.3f}")
    print(f"  within-1  = {s['within1']}/{n} = {s['within1'] / n:.3f}")
    print(f"  inversions (favourable<->afflicted) = {s['inversions']}")
    print(f"  abstained (indeterminate)           = {s['abstained']}")
    print("\n  baselines on the same verdicts (older parashara judges):")
    for k, label in (("ch11", "ch.11 bhava judge"), ("richer", "richer bhava judge")):
        b = s["baselines"][k]
        print(f"    {label:20s}: exact={b['exact']}/{n}  within-1={b['within1']}/{n}  "
              f"inversions={b['inversions']}")
    golds = ("favourable", "mixed", "afflicted")
    print("\n  confusion — synthesis verdict (rows) x Raman's verdict (columns):")
    print(f"  {'':14s}" + "".join(f"{g:>12s}" for g in golds))
    for synth in SYNTH_TO_RAMAN:
        row = [s["confusion"].get((synth, g), 0) for g in golds]
        if any(row):
            print(f"  {synth:14s}" + "".join(f"{c:>12d}" for c in row))
    print(f"\n[report-card] synthesis agrees with Raman on {s['exact']}/{n} exact, "
          f"{s['within1']}/{n} within-1, {s['inversions']} inversions")
    print("(agreement with RAMAN, not 'BPHS accuracy' — a fixed yardstick for before/after deltas.)")

    f = score_field_case()
    n2 = f["static_total"]
    print(f"\nTrack 2 — field_case_01 (one real, owner-confirmed chart; Lahiri cast):")
    print(f"  static: exact={f['static_exact']}/{n2}  within-1={f['static_within1']}/{n2}")
    for m in f["static_misses"]:
        print(f"    miss  {m}")
    hits = sum(e["hit"] for e in f["events"])
    mean_chance = sum(e["chance"] for e in f["events"]) / len(f["events"])
    print(f"  timing: {hits}/{len(f['events'])} events fall in a window targeting their house "
          f"(chance would give ~{mean_chance:.0%} — read the hits against that)")
    for e in f["events"]:
        mark = f"HIT ({e['quality']})" if e["hit"] else "miss"
        print(f"    {e['event']:22s} {e['year']}  houses{e['houses']}  {mark:18s} "
              f"chance {e['chance']:.0%}")


if __name__ == "__main__":
    main()
