"""Convert lapaasindia/good-time-finder JSON datasets into raw.csv +
events.csv shapes our pipeline understands.

Source: https://github.com/lapaasindia/good-time-finder (public repo, no
LICENSE — same legal posture as ASTROCRM). The repo's data/ directory
ships two files:

  personalities.json   8,722 entries, schema:
                       person_id, name, birth_date (ISO), birth_time
                       (HH:MM), latitude, longitude, timezone (IANA name
                       like 'Europe/London'), rodden_rating

  events.json          12,946 entries, schema:
                       event_id, person_id, event_date (ISO), category
                       (career/marriage/health/etc.), polarity (+1/-1),
                       description

The personalities file is mostly AA/A-rated and gives us 8.7k MORE
records on top of our existing corpus. The events file is uniquely
valuable: each event carries a polarity, which the ASTROCRM events
extractor doesn't. This lets us train models like "good event year"
vs "bad event year" — categorical events with valence.

This importer:
  1. Translates personalities.json → raw.csv (Stage-2 compatible)
  2. Resolves IANA timezone names to numeric offsets at the birth moment
     using zoneinfo (Python stdlib, IANA tzdb).
  3. Translates events.json → events.csv with name backfilled from the
     personalities file (so the events.csv joins to our existing one).

CLI:
    python -m app.medini.etl.lapaas_importer \\
        --personalities data/lapaas/personalities.json \\
        --events        data/lapaas/events.json \\
        --raw-output    data/astro_databank/raw_lapaas.csv \\
        --events-output data/astro_databank/events_lapaas.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import sys
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

csv.field_size_limit(10 ** 7)

PERSON_COLUMNS: tuple[str, ...] = (
    "name", "date_of_birth", "time_of_birth",
    "latitude", "longitude", "tz_offset",
    "rodden_rating", "categories", "source_url",
)

EVENT_COLUMNS: tuple[str, ...] = (
    "name", "event_code", "event_root", "event_subtype",
    "event_date", "event_year", "source_url",
)

# Polarity codes from lapaas → English. Used to disambiguate similar
# categories (e.g. "marriage" with polarity=1 vs "marriage" with polarity=-1).
_POLARITY_LABEL = {1: "Positive", -1: "Negative", 0: "Neutral"}


def resolve_timezone_offset(tz_name: str, date_iso: str, time_str: str) -> float | None:
    """Look up the numeric UTC offset (decimal hours, east-positive) for
    `tz_name` at the local moment `date_iso T time_str`.

    Uses Python's stdlib zoneinfo, which reads the IANA tzdb. Historical
    DST + tz-history rules are honoured (so "Europe/London 1874-11-30"
    correctly returns the LMT offset, not the modern GMT/BST one).

    Returns None if:
      - tz_name isn't a valid IANA zone
      - date or time can't be parsed
      - the timezone is missing from the local IANA data (rare on Windows
        before Python 3.13 — the tzdata package falls back automatically)
    """
    if not tz_name:
        return None
    try:
        zone = ZoneInfo(tz_name.strip())
    except ZoneInfoNotFoundError:
        return None

    # Build a naive datetime in the LOCAL timezone, then ask zoneinfo for
    # its UTC offset.
    try:
        date = dt.date.fromisoformat(date_iso)
        # birth_time is HH:MM (no seconds in lapaas data); fall back to noon
        # if missing so we still get a usable offset (DST distinctions
        # don't matter at noon for the historical rules we care about).
        if time_str and ":" in time_str:
            hh, mm = time_str.split(":")[:2]
            time = dt.time(int(hh), int(mm))
        else:
            time = dt.time(12, 0)
        naive = dt.datetime.combine(date, time)
    except (ValueError, TypeError):
        return None

    aware = naive.replace(tzinfo=zone)
    offset = aware.utcoffset()
    if offset is None:
        return None
    return offset.total_seconds() / 3600.0


def import_personalities(
    personalities_path: Path,
    output_csv: Path,
) -> dict[str, int]:
    """personalities.json → raw.csv (one row per person)."""
    if not personalities_path.exists():
        raise FileNotFoundError(f"personalities missing: {personalities_path}")

    logger.info("loading %s", personalities_path)
    with personalities_path.open("r", encoding="utf-8") as f:
        people = json.load(f)

    stats = {
        "input_rows": len(people),
        "written": 0,
        "skipped_missing_fields": 0,
        "skipped_bad_timezone": 0,
    }

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(PERSON_COLUMNS))
        writer.writeheader()

        for p in people:
            name = (p.get("name") or "").strip()
            date_iso = (p.get("birth_date") or "").strip()
            time_hm = (p.get("birth_time") or "").strip()
            lat = p.get("latitude")
            lon = p.get("longitude")
            if not (name and date_iso and lat is not None and lon is not None):
                stats["skipped_missing_fields"] += 1
                continue

            tz_offset = resolve_timezone_offset(
                p.get("timezone", ""), date_iso, time_hm,
            )
            if tz_offset is None:
                stats["skipped_bad_timezone"] += 1
                continue

            # Pad time_of_birth with seconds so the Stage 2 ETL parser
            # (which expects HH:MM:SS) accepts it verbatim.
            time_full = f"{time_hm}:00" if time_hm and len(time_hm) == 5 else time_hm

            writer.writerow({
                "name": name,
                "date_of_birth": date_iso,
                "time_of_birth": time_full,
                "latitude": f"{float(lat):.6f}",
                "longitude": f"{float(lon):.6f}",
                "tz_offset": f"{tz_offset:.4f}",
                "rodden_rating": str(p.get("rodden_rating", "")).upper().strip(),
                # Categories blank for now — events.csv carries the labels.
                "categories": "",
                "source_url": (
                    "https://github.com/lapaasindia/good-time-finder"
                    f"#person:{p.get('person_id', '')}"
                ),
            })
            stats["written"] += 1

    return stats


def import_events(
    events_path: Path,
    personalities_path: Path,
    output_csv: Path,
) -> dict[str, int]:
    """events.json → events.csv with name backfilled from personalities.json.

    Polarity is incorporated into event_subtype as a suffix so downstream
    target matching can pick "Positive Marriage" vs "Negative Marriage"
    when desired. Original category stays in event_root.
    """
    if not events_path.exists():
        raise FileNotFoundError(f"events missing: {events_path}")
    if not personalities_path.exists():
        raise FileNotFoundError(f"personalities missing: {personalities_path}")

    logger.info("loading %s", events_path)
    with events_path.open("r", encoding="utf-8") as f:
        events = json.load(f)
    with personalities_path.open("r", encoding="utf-8") as f:
        people = json.load(f)
    person_by_id: dict[str, str] = {
        p["person_id"]: (p.get("name") or "").strip() for p in people
    }

    stats = {
        "input_events": len(events),
        "written": 0,
        "skipped_unknown_person": 0,
        "skipped_missing_date": 0,
    }

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(EVENT_COLUMNS))
        writer.writeheader()

        for ev in events:
            pid = (ev.get("person_id") or "").strip()
            name = person_by_id.get(pid, "").strip()
            if not name:
                stats["skipped_unknown_person"] += 1
                continue
            event_date = (ev.get("event_date") or "").strip()
            if not event_date:
                stats["skipped_missing_date"] += 1
                continue
            category = (ev.get("category") or "").strip()
            polarity = ev.get("polarity")
            polarity_label = _POLARITY_LABEL.get(
                int(polarity) if polarity is not None else 0, "Neutral",
            )
            event_year = ""
            try:
                event_year = str(dt.date.fromisoformat(event_date).year)
            except ValueError:
                pass

            writer.writerow({
                "name": name,
                "event_code": f"{category} : {polarity_label}",
                "event_root": category,
                "event_subtype": polarity_label,
                "event_date": event_date,
                "event_year": event_year,
                "source_url": (
                    "https://github.com/lapaasindia/good-time-finder"
                    f"#event:{ev.get('event_id', '')}"
                ),
            })
            stats["written"] += 1

    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.lapaas_importer",
        description="Import lapaasindia/good-time-finder JSON into raw.csv + events.csv.",
    )
    parser.add_argument(
        "--personalities", type=Path, required=True,
        help="Path to personalities.json from lapaasindia/good-time-finder/data.",
    )
    parser.add_argument(
        "--events", type=Path, required=True,
        help="Path to events.json from the same source.",
    )
    parser.add_argument(
        "--raw-output", type=Path, required=True,
        help="Where to write the personalities-derived raw.csv.",
    )
    parser.add_argument(
        "--events-output", type=Path, required=True,
        help="Where to write the events-derived events.csv.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    raw_stats = import_personalities(args.personalities, args.raw_output)
    logger.info(
        "personalities: input=%d written=%d skipped_missing=%d skipped_tz=%d",
        raw_stats["input_rows"], raw_stats["written"],
        raw_stats["skipped_missing_fields"], raw_stats["skipped_bad_timezone"],
    )

    ev_stats = import_events(
        args.events, args.personalities, args.events_output,
    )
    logger.info(
        "events: input=%d written=%d skipped_unknown_person=%d skipped_missing_date=%d",
        ev_stats["input_events"], ev_stats["written"],
        ev_stats["skipped_unknown_person"], ev_stats["skipped_missing_date"],
    )

    print({"personalities": raw_stats, "events": ev_stats})
    return 0


if __name__ == "__main__":
    sys.exit(main())
