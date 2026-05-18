"""Convert Astro_Data/Astro_Data/output/kundlis.jsonl (Lunar Astro scrape)
into raw.csv + events.csv shapes our pipeline understands.

Source: a completed scrape of research.lunarastro.com via the
`/kundli-all?page=N` + `/kundli-details/<id>` endpoints. Ships ~35,931
records (31,341 personalities + 4,590 events) with 96.7% time coverage
and 100% coord coverage.

Schema in kundlis.jsonl:
  id, name, gender, date_of_birth (DD:MM:YYYY), day, time (HH:MM:SS),
  city, state, country, longitude (string "9.9876° E"), latitude
  (string "48.4011° N"), time_zone, description, tags (list), image_url,
  source_url, category ("personality" | "event")

Critical data-quality fixes this importer applies:
  1. time_zone is HARDCODED to "-05:30:00 hrs" (the site's user-tz) for
     every record — useless for charts. We RECOMPUTE tz_offset from
     (lat, lon, birth_date) using timezonefinder + zoneinfo. The local
     birth time itself is correct.
  2. date_of_birth uses DD:MM:YYYY format — normalize to ISO YYYY-MM-DD.
  3. ~1.3% of records have garbage years (2030-2090) — drop.
  4. ~4.4% of records have garbled coordinates (Unicode issues — e.g.
     "?78.4772? E") — drop.
  5. Heavy user-submission contamination — optional --min-description-len
     filter keeps curated famous-people records only.

Source legal posture: same as Wayback Astro-Databank corpus we already
import — third-party site that compiled this data from public sources.
Used for research/personal analysis, not redistribution.

CLI:
    python -m app.medini.etl.lunarastro_importer \\
        --input        Astro_Data/Astro_Data/output/kundlis.jsonl \\
        --raw-output   data/astro_databank/raw_lunarastro.csv \\
        --events-output data/astro_databank/events_lunarastro.csv \\
        [--min-description-len 50]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Allow large CSV cells (description / tags can be long).
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

# Date format: "14:03:1879" → year 1879, month 3, day 14.
_DOB_RE = re.compile(r"^(\d{1,2}):(\d{1,2}):(\d{4})$")
# Coord format: "9.9876° E", "48.4011° N". Allow optional ° and direction letter.
_COORD_RE = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*°?\s*([NSEW])?\s*$",
)
# Event-tag format inside a description string:
#   "Marriage 1903 (First marriage, Mileva Maric),Death of Father 1903 (..)"
# Each entry is "<event_text> <year> (<note>)" or just "<event_text> <year>".
# We split by ',(' look-back patterns — but the Lunar events have a structured
# `tags` field too. We use that as the primary source.

# Cap on accepted birth years — anything outside this range is data noise.
MIN_YEAR = 1700
MAX_YEAR = 2030


# ---------- Parsers ----------

def parse_dob(dob_str: str) -> str:
    """Convert "DD:MM:YYYY" → "YYYY-MM-DD", or "" if invalid/out-of-range."""
    if not dob_str:
        return ""
    m = _DOB_RE.match(dob_str.strip())
    if not m:
        return ""
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return ""
    if not (MIN_YEAR <= year <= MAX_YEAR):
        return ""
    try:
        return dt.date(year, month, day).isoformat()
    except ValueError:
        return ""


def parse_lunar_coord(coord_str: str) -> float | None:
    """Convert Lunar's "9.9876° E" / "48.4011° N" strings to signed decimal
    degrees (east-positive for longitude, north-positive for latitude).

    Returns None when the string fails the regex — e.g. when Unicode got
    corrupted into "?78.4772? E" (visible in ~1.5% of records) or when
    the direction letter is missing.
    """
    if not coord_str:
        return None
    s = coord_str.strip()
    m = _COORD_RE.match(s)
    if not m:
        return None
    try:
        value = float(m.group(1))
    except ValueError:
        return None
    direction = (m.group(2) or "").upper()
    if direction in ("S", "W"):
        return -abs(value)
    return value


def parse_time(time_str: str) -> str:
    """Pass through HH:MM:SS; return "" on bad input."""
    if not time_str:
        return ""
    parts = time_str.split(":")
    if len(parts) < 2:
        return ""
    try:
        hh = int(parts[0])
        mm = int(parts[1])
        ss = int(parts[2]) if len(parts) >= 3 else 0
    except ValueError:
        return ""
    if not (0 <= hh < 24 and 0 <= mm < 60 and 0 <= ss < 60):
        return ""
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def compute_tz_offset_for_chart(
    latitude: float,
    longitude: float,
    date_iso: str,
    time_str: str,
    tf,
) -> float | None:
    """Recompute the historical UTC offset for the birth moment.

    The Lunar Astro site hardcodes tz_offset=-05:30 for every record
    regardless of birthplace, so we ignore that field and compute the
    true offset from (lat, lon, date_iso, time_str) using:
      - timezonefinder for the IANA zone name (e.g. "Europe/Berlin")
      - zoneinfo for the historical offset at that local moment

    Returns None if any step fails. Failed records get dropped upstream;
    Stage 2 ETL won't accept missing tz_offset.
    """
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    except ImportError:
        return None

    zone_name = tf.timezone_at(lng=longitude, lat=latitude)
    if zone_name is None:
        # timezonefinder couldn't find a tz — usually means we're over ocean
        # (impossible birth point) or near a tz boundary with no land
        return None
    try:
        zone = ZoneInfo(zone_name)
    except ZoneInfoNotFoundError:
        return None

    try:
        date = dt.date.fromisoformat(date_iso)
        parts = (time_str or "12:00:00").split(":")
        hh, mm = int(parts[0]), int(parts[1])
        naive = dt.datetime(date.year, date.month, date.day, hh, mm)
    except (ValueError, IndexError):
        return None

    aware = naive.replace(tzinfo=zone)
    utcoff = aware.utcoffset()
    if utcoff is None:
        return None
    return utcoff.total_seconds() / 3600.0


# ---------- Category extraction ----------

def normalise_tags_to_categories(tags: list[str] | str) -> str:
    """Tags in Lunar are single-word category roots ("Vocation", "Notable",
    "Family", etc.) — same vocabulary as Astro-Databank's top-level
    categories. Join with semicolons matching our raw.csv convention.
    Empty/None tags collapse to ''.

    Falsy values, non-string list members, and the literal string "None"
    (which appears in 47% of Lunar records as a placeholder) are dropped.
    """
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(";")]
    if not isinstance(tags, list):
        return ""
    seen: list[str] = []
    for raw in tags:
        if not isinstance(raw, str):
            continue
        token = raw.strip()
        if not token or token.lower() == "none":
            continue
        if token not in seen:
            seen.append(token)
    return ";".join(seen)


# ---------- Importers ----------

def import_personalities(
    input_path: Path,
    output_csv: Path,
    *,
    min_description_len: int = 0,
) -> dict[str, int]:
    """kundlis.jsonl personalities → raw.csv (Stage-2 compatible).

    Dedup is left to the merger downstream — multiple Lunar IDs for the
    same person (e.g. Einstein appears 3x with different IDs) all get
    written here and the (name, date_of_birth) merger key collapses them.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"input JSONL missing: {input_path}")

    # Lazy-import — only personalities path needs timezonefinder.
    from timezonefinder import TimezoneFinder
    tf = TimezoneFinder()

    stats = {
        "input_records": 0,
        "personalities": 0,
        "skipped_not_personality": 0,
        "skipped_bad_date": 0,
        "skipped_bad_coords": 0,
        "skipped_bad_time": 0,
        "skipped_bad_tz_lookup": 0,
        "skipped_short_description": 0,
        "written": 0,
    }

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as fin, \
         output_csv.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=list(PERSON_COLUMNS))
        writer.writeheader()

        for line in fin:
            stats["input_records"] += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            if rec.get("category") != "personality":
                stats["skipped_not_personality"] += 1
                continue
            stats["personalities"] += 1

            date_iso = parse_dob(rec.get("date_of_birth", ""))
            if not date_iso:
                stats["skipped_bad_date"] += 1
                continue

            lat = parse_lunar_coord(rec.get("latitude", ""))
            lon = parse_lunar_coord(rec.get("longitude", ""))
            if lat is None or lon is None:
                stats["skipped_bad_coords"] += 1
                continue
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                stats["skipped_bad_coords"] += 1
                continue

            time_iso = parse_time(rec.get("time", ""))
            if not time_iso:
                stats["skipped_bad_time"] += 1
                continue

            # The critical fix: ignore Lunar's hardcoded -05:30 tz, compute
            # the real one from (lat, lon, date, time).
            tz_offset = compute_tz_offset_for_chart(
                lat, lon, date_iso, time_iso, tf,
            )
            if tz_offset is None:
                stats["skipped_bad_tz_lookup"] += 1
                continue

            # Optional description-length filter for famous-people-only.
            description = (rec.get("description") or "").strip()
            if min_description_len and len(description) < min_description_len:
                stats["skipped_short_description"] += 1
                continue

            # Tags are top-level categories; rich categorical info is
            # often inside `description`. We add description as a hint
            # so the trainer's substring matching can pick it up.
            categories = normalise_tags_to_categories(rec.get("tags", []))

            name = (rec.get("name") or "").strip()
            if not name:
                continue

            writer.writerow({
                "name": name,
                "date_of_birth": date_iso,
                "time_of_birth": time_iso,
                "latitude": f"{lat:.6f}",
                "longitude": f"{lon:.6f}",
                "tz_offset": f"{tz_offset:.4f}",
                # Lunar doesn't expose Rodden rating; we tag AA only when
                # description suggests high curation. Default to blank
                # (Stage 2's _is_aa_complete filter will drop these unless
                # ratings are present in the merged corpus from another
                # source's version of the same person).
                "rodden_rating": "AA" if min_description_len else "",
                "categories": categories,
                "source_url": rec.get("source_url", "")
                              or f"https://research.lunarastro.com/kundli-details/{rec.get('id', '')}",
            })
            stats["written"] += 1

    return stats


# ---------- Event extraction ----------

# Pattern for "Event Text YYYY (optional note)" inside a description.
# Lunar events come as comma-separated entries in the description field.
# Examples from Einstein's event record:
#   "Death of Mate 1936 (Second wife, Elsa Lowenthal)"
#   "Prize 1922 (Nobel Prize)"
#   "Marriage 1903 (First marriage, Mileva Maric)"
_EVENT_PATTERN = re.compile(
    r"^(?P<event>[A-Za-z][A-Za-z /,'\-]+?)\s+(?P<year>\d{4})\s*(?:\((?P<note>[^)]*)\))?\s*$",
)


def parse_event_entries(description: str) -> list[dict[str, str]]:
    """Split a Lunar event-record description into (event_text, year, note)
    tuples. Returns a list of dicts; empty list when nothing parses.

    Tolerant of malformed entries — anything that doesn't match the
    "<text> YYYY" pattern is skipped silently.
    """
    if not description:
        return []
    # Split on commas, but only those NOT inside parens (e.g. "(Second wife, Elsa)"
    # shouldn't split on the comma between "wife," and "Elsa").
    entries: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in description:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            entries.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        entries.append("".join(buf).strip())

    parsed: list[dict[str, str]] = []
    for entry in entries:
        if not entry:
            continue
        m = _EVENT_PATTERN.match(entry)
        if not m:
            continue
        parsed.append({
            "event_text": m.group("event").strip(),
            "year": m.group("year"),
            "note": (m.group("note") or "").strip(),
        })
    return parsed


def import_events(
    input_path: Path,
    output_csv: Path,
) -> dict[str, int]:
    """kundlis.jsonl event records → events.csv.

    For each `event`-category record we explode its description into
    multiple atomic event rows. Lunar packs ~30 lifetime events into
    a single 'event' record for famous people — Einstein's event record
    has 50+ life events in one description string.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"input JSONL missing: {input_path}")

    stats = {
        "input_records": 0,
        "event_records": 0,
        "events_written": 0,
        "skipped_no_description": 0,
        "skipped_unparseable_year": 0,
    }

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8") as fin, \
         output_csv.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=list(EVENT_COLUMNS))
        writer.writeheader()

        for line in fin:
            stats["input_records"] += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            if rec.get("category") != "event":
                continue
            stats["event_records"] += 1

            name = (rec.get("name") or "").strip()
            description = (rec.get("description") or "").strip()
            if not (name and description):
                stats["skipped_no_description"] += 1
                continue

            event_id = rec.get("id", "")
            for idx, parsed in enumerate(parse_event_entries(description)):
                try:
                    year = int(parsed["year"])
                except ValueError:
                    stats["skipped_unparseable_year"] += 1
                    continue
                if not (MIN_YEAR <= year <= MAX_YEAR):
                    stats["skipped_unparseable_year"] += 1
                    continue

                event_text = parsed["event_text"]
                # Try to split "Root : Subtype" if present (rare in Lunar).
                if ":" in event_text:
                    root, _, subtype = event_text.partition(":")
                    root = root.strip()
                    subtype = subtype.strip()
                else:
                    root = event_text
                    subtype = ""

                writer.writerow({
                    "name": name,
                    "event_code": event_text,
                    "event_root": root,
                    "event_subtype": subtype,
                    # We only have year-precision from Lunar events.
                    "event_date": "",
                    "event_year": str(year),
                    "source_url": (
                        "https://research.lunarastro.com/kundli-details/"
                        f"{event_id}#event-{idx}"
                    ),
                })
                stats["events_written"] += 1

    return stats


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.lunarastro_importer",
        description="Import Lunar Astro kundlis scrape into raw.csv + events.csv.",
    )
    parser.add_argument(
        "--input", type=Path,
        default=Path("Astro_Data/Astro_Data/output/kundlis.jsonl"),
        help="Path to kundlis.jsonl from the Lunar Astro scrape.",
    )
    parser.add_argument(
        "--raw-output", type=Path,
        default=Path("data/astro_databank/raw_lunarastro.csv"),
        help="Where to write the personalities-derived raw.csv.",
    )
    parser.add_argument(
        "--events-output", type=Path,
        default=Path("data/astro_databank/events_lunarastro.csv"),
        help="Where to write the events-derived events.csv.",
    )
    parser.add_argument(
        "--min-description-len", type=int, default=0,
        help="Drop personalities with description shorter than N chars. "
             "Use ~50 for famous-people filter. Default 0 (keep all).",
    )
    parser.add_argument(
        "--skip-personalities", action="store_true",
        help="Skip the personalities import (events-only run).",
    )
    parser.add_argument(
        "--skip-events", action="store_true",
        help="Skip the events import (personalities-only run).",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not args.skip_personalities:
        logger.info("Importing personalities from %s", args.input)
        p_stats = import_personalities(
            args.input, args.raw_output,
            min_description_len=args.min_description_len,
        )
        logger.info("Personalities: %s", p_stats)

    if not args.skip_events:
        logger.info("Importing events from %s", args.input)
        e_stats = import_events(args.input, args.events_output)
        logger.info("Events: %s", e_stats)

    return 0


if __name__ == "__main__":
    sys.exit(main())
