"""Extract dated marriage/divorce EVENTS from VedAstro's Marriage-Divorce dataset.

`vedastro_importer.py` reads the *old* MarriageInfoDataset only for a binary
outcome label (dissolution vs happiness). The newer MIT-licensed dataset
``vedastro-org/15000-Famous-People-Marriage-Divorce-Info`` instead carries the
**dates** of each marriage/divorce (year-precision), per the published schema:
Person Identifier (name + birth year), Marriage Type, Spouse, Marriage/Divorce
dates, Outcome, Data Credibility. Those dates are exactly the dated life events
the timing audit is starved of (the corpus has only 4,590), and the persons join
to the ~15.8k AA-rated birth-time charts from the companion birth dataset.

This module converts that dataset into the project's standard ``events.csv``
(same columns the LunarAstro importer emits) — one row per dated marriage and one
per dated divorce — so `build_event_dasha_join` can attach the active MD/AD and
feed the within-person timing tests.

Because the exact on-disk layout (flat columns vs a JSON ``Info`` blob) and the
precise field names are confirmed only from the dataset's prose description, the
parser is deliberately **schema-tolerant**: it accepts either shape and searches
a list of candidate key names for each field, extracting a 4-digit year from
whatever date representation it finds. When the real CSV is in hand, at most the
candidate-key lists need touching.

CLI::

    python -m app.medini.etl.vedastro_events_importer \\
        --marriages data/vedastro/MarriageDivorceInfo.csv \\
        --output data/vedastro/events.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from app.medini.etl.lunarastro_importer import EVENT_COLUMNS, MAX_YEAR, MIN_YEAR

logger = logging.getLogger(__name__)
csv.field_size_limit(10 ** 7)

# candidate column / JSON keys (matched case-insensitively).
_NAME_KEYS = ("Name", "PersonName", "Person", "Person Identifier",
              "PersonIdentifier", "FullName", "PartitionKey")
_MARRIAGE_DATE_KEYS = ("MarriageDate", "Marriage Date", "Marriage", "Married",
                       "MarriageTime", "DateOfMarriage", "Date of Marriage",
                       "MarriageYear", "Wedding", "date", "Date", "start",
                       "StartTime", "when")
_DIVORCE_DATE_KEYS = ("DivorceDate", "Divorce Date", "Divorce", "Divorced",
                      "DivorceTime", "DateOfDivorce", "DivorceYear", "EndDate",
                      "End Date", "EndTime", "end", "DissolutionDate")
_SPOUSE_KEYS = ("Spouse", "SpouseName", "PartnerName", "Partner", "With")
_TYPE_KEYS = ("MarriageType", "Marriage Type", "Type")
_OUTCOME_KEYS = ("Outcome", "Result", "Status")
_MARRIAGES_LIST_KEYS = ("marriages", "Marriages", "events", "Events")
_INFO_KEYS = ("Info", "info", "Data", "MarriageInfo")

_YEAR_RE = re.compile(r"(?<!\d)(\d{4})(?!\d)")
# trailing " - 1879" / "_1879" / "(1879)" birth-year suffix on a Person Identifier.
_NAME_YEAR_SUFFIX = re.compile(r"[\s\-_(/,]+\(?(1[5-9]\d{2}|20\d{2})\)?\s*$")


def _ci_get(d: dict, keys: Iterable[str]) -> Any:
    """First non-empty value among `keys`, case-insensitive on the dict's keys."""
    lower = {str(k).lower(): v for k, v in d.items()}
    for k in keys:
        v = lower.get(k.lower())
        if v not in (None, "", [], {}):
            return v
    return None


def extract_year(value: Any) -> int | None:
    """Pull a plausible 4-digit year (MIN_YEAR..MAX_YEAR) from any date-ish value."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        y = int(value)
        return y if MIN_YEAR <= y <= MAX_YEAR else None
    for m in _YEAR_RE.finditer(str(value)):
        y = int(m.group(1))
        if MIN_YEAR <= y <= MAX_YEAR:
            return y
    return None


def clean_name(value: Any) -> str:
    """Strip a trailing birth-year suffix from a 'name + birth year' identifier."""
    name = str(value or "").strip()
    name = _NAME_YEAR_SUFFIX.sub("", name).strip(" -_/,")
    return name.replace("_", " ").strip()


def _emit(name: str, root: str, year: int, *, spouse: str, mtype: str,
          src: str, idx: int) -> dict[str, str]:
    label = f"{root.capitalize()}"
    if spouse:
        label += f" ({spouse})"
    return {
        "name": name,
        "event_code": root,
        "event_root": root,
        "event_subtype": (mtype or "").strip().lower() if root == "marriage" else "",
        "event_date": "",                       # year precision only
        "event_year": str(year),
        "source_url": f"{src}#{root}-{idx}",
    }


def parse_person_marriages(row: dict, *, src_base: str) -> list[dict[str, str]]:
    """One CSV row → zero or more dated marriage/divorce event dicts.

    Handles two layouts transparently:
      • a JSON `Info` blob holding a `marriages` list of per-marriage objects;
      • a flat row that is itself a single marriage record.
    """
    name = clean_name(_ci_get(row, _NAME_KEYS))
    if not name:
        return []

    # try a JSON Info blob with a marriages list first.
    entries: list[dict] = []
    info = _ci_get(row, _INFO_KEYS)
    if isinstance(info, str) and info.strip():
        try:
            obj = json.loads(info)
            lst = _ci_get(obj, _MARRIAGES_LIST_KEYS) if isinstance(obj, dict) else obj
            if isinstance(lst, list):
                entries = [e for e in lst if isinstance(e, dict)]
            elif isinstance(obj, dict):
                entries = [obj]
        except json.JSONDecodeError:
            entries = []
    if not entries:                              # flat layout: the row is one marriage
        entries = [row]

    out: list[dict[str, str]] = []
    src = f"{src_base}/{name.replace(' ', '_')}"
    for i, e in enumerate(entries):
        spouse = str(_ci_get(e, _SPOUSE_KEYS) or "").strip()
        mtype = str(_ci_get(e, _TYPE_KEYS) or "").strip()
        my = extract_year(_ci_get(e, _MARRIAGE_DATE_KEYS))
        if my is not None:
            out.append(_emit(name, "marriage", my, spouse=spouse, mtype=mtype,
                             src=src, idx=i))
        dy = extract_year(_ci_get(e, _DIVORCE_DATE_KEYS))
        if dy is not None:
            out.append(_emit(name, "divorce", dy, spouse=spouse, mtype="",
                             src=src, idx=i))
    return out


def import_vedastro_events(marriages_csv: Path, output_csv: Path) -> dict[str, int]:
    if not marriages_csv.exists():
        raise FileNotFoundError(f"marriages CSV missing: {marriages_csv}")
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    stats = {"input_rows": 0, "people_with_events": 0,
             "marriages": 0, "divorces": 0, "events_written": 0}
    src_base = "https://huggingface.co/datasets/vedastro-org/15000-Famous-People-Marriage-Divorce-Info"

    with marriages_csv.open("r", encoding="utf-8", newline="") as fin, \
         output_csv.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=list(EVENT_COLUMNS))
        writer.writeheader()
        for row in csv.DictReader(fin):
            stats["input_rows"] += 1
            events = parse_person_marriages(row, src_base=src_base)
            if events:
                stats["people_with_events"] += 1
            for ev in events:
                writer.writerow(ev)
                stats["events_written"] += 1
                stats["marriages" if ev["event_root"] == "marriage" else "divorces"] += 1
    return stats


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m app.medini.etl.vedastro_events_importer",
        description="Extract dated marriage/divorce events from VedAstro's "
                    "Marriage-Divorce dataset into events.csv.")
    p.add_argument("--marriages", type=Path, required=True,
                   help="Path to the Marriage-Divorce dataset CSV.")
    p.add_argument("--output", type=Path, required=True,
                   help="Where to write events.csv (parent dir created).")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    s = import_vedastro_events(args.marriages, args.output)
    logger.info("wrote %d events (%d marriages, %d divorces) from %d rows; "
                "%d people had ≥1 dated event",
                s["events_written"], s["marriages"], s["divorces"],
                s["input_rows"], s["people_with_events"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
