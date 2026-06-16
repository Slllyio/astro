"""Attach `person_id` to name+birthdate events by matching birth-time charts.

The Wikidata/biography event sources emit `(name_norm, birth_year, event_class,
year)` but no chart — Wikidata rarely records birth *time*. To make those CC0
events usable for the dasha timing tests they must be matched to a birth-*time*
chart (Astro-Databank / VedAstro / LunarAstro) for the same person, which carries
the `person_id` the rest of the pipeline keys on. This is that join — the actual
"event multiplier": every Wikidata event whose person is already charted becomes a
usable dated event.

Match key = normalized name (`resolve_persons_dedup.normalize_name_key`) + birth
year (±`year_tolerance`, default 1, to absorb timezone/date-vs-time edge cases). A
key resolving to **more than one distinct `person_id`** is dropped as ambiguous —
we never guess which homonym an event belongs to. Outputs the matched events with
`person_id` attached, ready for `build_event_dasha_join`.

CLI::

    python -m app.medini.etl.match_events_to_charts \\
        --events app/medini/data/wikidata_dated_events.parquet \\
        --persons app/medini/data/persons.parquet \\
        --output app/medini/data/wikidata_events_matched.parquet
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from app.medini.etl.resolve_persons_dedup import normalize_name_key

logger = logging.getLogger(__name__)


def jd_to_year(jd: float) -> int | None:
    """Gregorian calendar year of a Julian Day (Richards algorithm; exact)."""
    if jd is None or pd.isna(jd):
        return None
    J = int(float(jd) + 0.5)
    f = J + 1401 + (((4 * J + 274277) // 146097) * 3) // 4 - 38
    e = 4 * f + 3
    g = (e % 1461) // 4
    h = 5 * g + 2
    m = (h // 153 + 2) % 12 + 1
    return e // 1461 - 4716 + (12 + 2 - m) // 12


def _ensure_name_norm(df: pd.DataFrame) -> pd.Series:
    if "name_norm" in df.columns:
        return df["name_norm"].fillna("").astype(str)
    if "name" in df.columns:
        return df["name"].map(normalize_name_key)
    raise KeyError("frame needs a 'name_norm' or 'name' column")


def _persons_year(persons: pd.DataFrame) -> pd.Series:
    if "birth_year" in persons.columns:
        return persons["birth_year"].astype("Int64")
    if "birth_jd" in persons.columns:
        return persons["birth_jd"].map(jd_to_year).astype("Int64")
    raise KeyError("persons frame needs 'birth_year' or 'birth_jd'")


def build_index(persons: pd.DataFrame) -> dict[tuple[str, int], set[str]]:
    """(name_norm, birth_year) -> set of person_ids."""
    nn = _ensure_name_norm(persons)
    yr = _persons_year(persons)
    idx: dict[tuple[str, int], set[str]] = {}
    for pid, name, year in zip(persons["person_id"], nn, yr):
        if not name or pd.isna(year):
            continue
        idx.setdefault((name, int(year)), set()).add(str(pid))
    return idx


def attach_person_ids(events: pd.DataFrame, persons: pd.DataFrame, *,
                      year_tolerance: int = 1) -> tuple[pd.DataFrame, dict]:
    """Return (matched events with `person_id`, stats)."""
    idx = build_index(persons)
    ev_name = _ensure_name_norm(events)
    if "birth_year" in events.columns:
        ev_year = events["birth_year"].astype("Int64")
    elif "birth_jd" in events.columns:
        ev_year = events["birth_jd"].map(jd_to_year).astype("Int64")
    else:
        raise KeyError("events frame needs 'birth_year' or 'birth_jd'")

    pids: list[str | None] = []
    stats = {"events": len(events), "matched": 0, "unmatched": 0, "ambiguous": 0}
    for name, year in zip(ev_name, ev_year):
        if not name or pd.isna(year):
            pids.append(None)
            stats["unmatched"] += 1
            continue
        candidates: set[str] = set()
        for dy in range(-year_tolerance, year_tolerance + 1):
            candidates |= idx.get((name, int(year) + dy), set())
        if len(candidates) == 1:
            pids.append(next(iter(candidates)))
            stats["matched"] += 1
        elif len(candidates) == 0:
            pids.append(None)
            stats["unmatched"] += 1
        else:
            pids.append(None)
            stats["ambiguous"] += 1
    out = events.copy()
    out["person_id"] = pids
    matched = out[out["person_id"].notna()].reset_index(drop=True)
    stats["unique_people_matched"] = matched["person_id"].nunique()
    return matched, stats


def build(events_path: Path, persons_path: Path, output: Path, *,
          year_tolerance: int = 1) -> dict:
    events = pd.read_parquet(events_path)
    persons = pd.read_parquet(persons_path)
    matched, stats = attach_person_ids(events, persons, year_tolerance=year_tolerance)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".csv":
        matched.to_csv(output, index=False)
    else:
        matched.to_parquet(output, index=False)
    return stats


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m app.medini.etl.match_events_to_charts",
        description="Attach person_id to name+birthdate events via chart match.")
    p.add_argument("--events", type=Path, required=True)
    p.add_argument("--persons", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--year-tolerance", type=int, default=1)
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    stats = build(args.events, args.persons, args.output,
                  year_tolerance=args.year_tolerance)
    logger.info("matched %d/%d events (%d ambiguous, %d unmatched) → %d people",
                stats["matched"], stats["events"], stats["ambiguous"],
                stats["unmatched"], stats["unique_people_matched"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
