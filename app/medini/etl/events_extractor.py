"""Extract structured life events from ASTROCRM's astro_people.csv.

Each row's `raw_wikitext` field contains MediaWiki templates of the form:

  {{ASTRODATABANK_evn
  |CodeID=784
  |sevcode=Crime : Assault/ Battery Victimization
  |sevdate=2015/11/13
  |sevdate_dmy=13 November 2015
  ...
  }}

These are biographical events (deaths, marriages, divorces, prizes, new
careers, etc.) with a date AND a category. ASTROCRM's astro_people.csv
embeds them in raw_wikitext but doesn't expose them as a table — this
module pulls them out into a one-row-per-event CSV that can be joined
to the person corpus by name.

Sample distribution from the 6,488-row astro_people.csv:
  3,741 people have at least one event
  9,070 events total
  Top categories:
    Death, Cause unspecified         1,743
    Relationship : Marriage          1,070
    Work : Published/Exhibited        669
    Work : Prize                       598
    Death by Disease                  507
    Relationship : Divorce dates      271
    Work : New Career                 250

Output schema (one row per event):
  name             - the person the event belongs to
  event_code       - full sevcode (e.g. "Relationship : Marriage")
  event_root       - top-level category (e.g. "Relationship", "Work", "Death")
  event_subtype    - leaf category (e.g. "Marriage", "Prize")
  event_date       - ISO YYYY-MM-DD ("" if only year known)
  event_year       - int year, parsed from event_date
  source_url       - traceability ("github.com/.../ASTROCRM#evn:<page_id>:<idx>")

CLI:
    python -m app.medini.etl.events_extractor \\
        --input  data/holos/astro_people.csv \\
        --output data/astro_databank/events.csv \\
        [--filter-event-root Relationship]
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

csv.field_size_limit(10 ** 7)

# Astro-Databank event template name.
_EVENT_BLOCK_RE = re.compile(r"\{\{ASTRODATABANK_evn(.*?)\}\}", re.DOTALL)
_FIELD_RE = re.compile(r"\|(?P<key>[a-zA-Z_]+)\s*=\s*(?P<value>[^|}\n]*)")
# Date formats encountered: "2015/11/13", "1971", "1971/00/00".
_FULL_DATE_RE = re.compile(r"^(?P<y>\d{4})/(?P<m>\d{1,2})/(?P<d>\d{1,2})$")
_YEAR_ONLY_RE = re.compile(r"^(?P<y>\d{4})$")

OUTPUT_COLUMNS: tuple[str, ...] = (
    "name", "event_code", "event_root", "event_subtype",
    "event_date", "event_year", "source_url",
)


def _parse_event_block(block_text: str) -> dict[str, str]:
    """Parse `|key=value|key=value` template fields into a dict."""
    return {m.group("key"): m.group("value").strip() for m in _FIELD_RE.finditer(block_text)}


def _split_event_code(sevcode: str) -> tuple[str, str]:
    """`'Relationship : Marriage'` → (`'Relationship'`, `'Marriage'`).
    `'Death by Disease'` (no colon) → (`'Death by Disease'`, '').
    Astro-Databank uses ' : ' as the hierarchy separator."""
    parts = [p.strip() for p in sevcode.split(":", 1)]
    if len(parts) == 2:
        return parts[0], parts[1]
    return sevcode.strip(), ""


def _normalise_date(sevdate: str) -> tuple[str, int | None]:
    """Convert sevdate (`2015/11/13` or `1971` or `1971/00/00`) to ISO + year.

    Astro-Databank often stores year-only events as `1971/00/00`.
    Returns ('', None) for unparseable input.
    """
    if not sevdate:
        return "", None
    s = sevdate.strip()

    m = _FULL_DATE_RE.match(s)
    if m:
        y = int(m.group("y"))
        mo = int(m.group("m"))
        d = int(m.group("d"))
        if mo == 0 or d == 0:
            return "", y  # year-only fallback
        if not (1 <= mo <= 12 and 1 <= d <= 31):
            return "", y
        return f"{y:04d}-{mo:02d}-{d:02d}", y

    m = _YEAR_ONLY_RE.match(s)
    if m:
        return "", int(m.group("y"))

    return "", None


def extract_events_from_row(
    name: str,
    raw_wikitext: str,
    page_id: str = "",
) -> list[dict[str, str]]:
    """Return one dict per event template found in `raw_wikitext`.

    Empty list if the row has no events. Robust to malformed templates —
    blocks missing sevcode are skipped silently.
    """
    if not raw_wikitext:
        return []

    out: list[dict[str, str]] = []
    for idx, block in enumerate(_EVENT_BLOCK_RE.findall(raw_wikitext)):
        fields = _parse_event_block(block)
        sevcode = fields.get("sevcode", "").strip()
        if not sevcode:
            continue
        root, subtype = _split_event_code(sevcode)
        date_iso, year = _normalise_date(fields.get("sevdate", ""))
        out.append({
            "name": name,
            "event_code": sevcode,
            "event_root": root,
            "event_subtype": subtype,
            "event_date": date_iso,
            "event_year": str(year) if year is not None else "",
            "source_url": (
                f"https://github.com/jfsagro-glitch/ASTROCRM#evn:{page_id}:{idx}"
            ),
        })
    return out


def extract_events(
    input_csv: Path,
    output_csv: Path,
    *,
    filter_event_root: str | None = None,
) -> dict[str, int]:
    """Read astro_people.csv, write events.csv. Returns stats dict."""
    if not input_csv.exists():
        raise FileNotFoundError(f"input CSV missing: {input_csv}")

    logger.info("loading %s", input_csv)
    df = pd.read_csv(input_csv, low_memory=False)

    stats = {
        "input_rows": len(df),
        "people_with_events": 0,
        "events_written": 0,
        "events_filtered_out": 0,
    }

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(OUTPUT_COLUMNS))
        writer.writeheader()

        for _, row in df.iterrows():
            name = (row.get("name") or "").strip()
            if not name:
                continue
            wt = row.get("raw_wikitext") or ""
            page_id = str(row.get("page_id", "") or "").strip()
            events = extract_events_from_row(name, wt, page_id=page_id)
            if not events:
                continue
            stats["people_with_events"] += 1
            for e in events:
                if filter_event_root and e["event_root"].lower() != filter_event_root.lower():
                    stats["events_filtered_out"] += 1
                    continue
                writer.writerow(e)
                stats["events_written"] += 1

    return stats


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.events_extractor",
        description="Extract life events from astro_people.csv raw_wikitext.",
    )
    parser.add_argument(
        "--input", type=Path, required=True,
        help="Path to astro_people.csv (must have raw_wikitext column).",
    )
    parser.add_argument(
        "--output", type=Path, required=True,
        help="Where to write events.csv. Parent dir is created.",
    )
    parser.add_argument(
        "--filter-event-root", type=str, default=None,
        help="Optional: keep only events whose root category matches "
             "(case-insensitive). E.g. 'Relationship', 'Death', 'Work'.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = extract_events(
        input_csv=args.input,
        output_csv=args.output,
        filter_event_root=args.filter_event_root,
    )
    logger.info(
        "extraction complete: people_with_events=%d events_written=%d "
        "events_filtered_out=%d",
        stats["people_with_events"], stats["events_written"],
        stats["events_filtered_out"],
    )
    print(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
