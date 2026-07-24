"""Stage 1 — apply the pre-registered mapping to the person master -> labels.parquet.

Validation is doctrine-first: every verdict-axis row's signification_key must exist in
`significations_of(house)` (hard-fail on typos); only status=locked rows are scorable;
`exclusive_with` contradictions (a person labeled both childless AND prolific) are quarantined from
BOTH cohorts; the Stage-0 longevity quarantine is applied to the ayurdaya-axis cohorts.

Usage: py -3.12 -m tools.raman_saab.astrobank.build_labels
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

from app.raman_saab.doctrine.significations import significations_of

_MAP = Path(__file__).parent / "mapping" / "category_house_map.csv"
_OUT = Path("data/astro_databank/derived/raman")


def load_mapping() -> list[dict]:
    rows = list(csv.DictReader(_MAP.open(encoding="utf-8")))
    for r in rows:
        if r["status"] != "locked":
            continue
        if r["axis"] == "verdict":
            keys = {s.key for s in significations_of(int(r["house"]))}
            if r["signification_key"] not in keys:
                raise SystemExit(
                    f"mapping {r['map_id']}: signification {r['signification_key']!r} not in "
                    f"H{r['house']} keys {sorted(keys)}")
    return rows


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    mapping = load_mapping()
    locked = [r for r in mapping if r["status"] == "locked"]
    master = pd.read_parquet(_OUT / "person_master.parquet")
    celeb = master[master.population == "celebrity_databank"]
    quarantine = {q["person_id"] for q in
                  json.loads((_OUT / "quarantine.json").read_text(encoding="utf-8"))}

    # token index per person (exact-token, casefolded)
    matches: dict[str, set[str]] = defaultdict(set)   # map_id -> pids
    for r in celeb.itertuples():
        toks = {t.strip().casefold() for t in str(r.categories_raw).split(";")}
        for m in locked:
            if m["pattern"] in toks:
                matches[m["map_id"]].add(r.person_id)

    # exclusive_with contradictions -> drop from BOTH
    dropped: dict[str, int] = defaultdict(int)
    for m in locked:
        excl = [x for x in (m["exclusive_with"] or "").split("|") if x]
        for other in excl:
            both = matches[m["map_id"]] & matches.get(other, set())
            if both:
                matches[m["map_id"]] -= both
                matches[other] -= both
                dropped[f"{m['map_id']}&{other}"] += len(both)

    # Balarishta exclusion (bphs-reviewer REVISE on H8_SHORTLIFE): deaths under 12 are doctrinally
    # outside ayurdaya (HTJAH-II:3916-3923); exclude persons whose own-death age is known < 12.
    ev_path = _OUT / "person_events.parquet"
    balarishta: set[str] = set()
    if ev_path.is_file():
        ev = pd.read_parquet(ev_path)
        birth_year = {r.person_id: int(r.birth_date[:4]) for r in celeb.itertuples()}
        for r in ev.itertuples():
            low = f"{r.event_root} {r.event_subtype}".lower()
            if r.event_root.startswith("Death") and "death of" not in low:
                by = birth_year.get(r.person_id)
                if by and 0 <= r.event_year - by < 12:
                    balarishta.add(r.person_id)

    rows = []
    tier = dict(zip(celeb.person_id, celeb.quality_tier))
    for m in locked:
        pids = matches[m["map_id"]]
        if m["axis"] == "ayurdaya":
            pids = pids - quarantine
            if m["map_id"] == "H8_SHORTLIFE":
                pids = pids - balarishta
        for pid in pids:
            rows.append({"person_id": pid, "map_id": m["map_id"], "house": int(m["house"]),
                         "signification_key": m["signification_key"], "axis": m["axis"],
                         "direction": m["direction"], "strength": m["strength"],
                         "quality_tier": tier.get(pid, "")})
    labels = pd.DataFrame(rows)
    _OUT.mkdir(parents=True, exist_ok=True)
    labels.to_parquet(_OUT / "labels.parquet", engine="pyarrow", compression="zstd", index=False)

    print(f"[labels] locked mappings: {len(locked)}   label rows: {len(labels)}")
    print(f"[labels] contradiction drops: {dict(dropped) or 'none'}")
    print(f"\n{'map_id':18} {'n':>6} {'tierA':>6} {'tierB':>6} {'tierC':>6}")
    for m in locked:
        sub = labels[labels.map_id == m["map_id"]]
        tc = sub.quality_tier.value_counts()
        print(f"{m['map_id']:18} {len(sub):>6} {tc.get('A',0):>6} {tc.get('B',0):>6} {tc.get('C',0):>6}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
