"""Convert VedAstro's HuggingFace datasets into the raw.csv schema our
Stage 2 ETL expects.

VedAstro publishes two MIT-licensed CSVs that fit our pipeline:

  PersonList-15k.csv  - one row per person; ~15,800 AA-rated births.
                        Columns: RowKey, BirthTime (JSON), Gender, Name, Notes
                        (Notes always {'rodden': 'AA'}).
  MarriageInfoDataset.csv - one row per person; same RowKey;
                        Info column is JSON {"marriages": [{outcome, ...}]}.
                        Outcome is "Dissolution" | "Happiness" | other strings.

Joining the two on RowKey gives ~14,300 rows with a clean binary target:
"did this person have at least one marriage end in dissolution?". Base rate
is ~24% — comfortably above the 5-positive minimum the trainer enforces
and not so imbalanced it requires special handling beyond the existing
scale_pos_weight.

This importer reads both CSVs, parses the BirthTime JSON, derives the
marriage_outcome category, and writes a raw.csv that databank_etl.py
consumes verbatim. No scraping, no rate limiting — runs in ~3 seconds.

CLI:
    python -m app.medini.etl.vedastro_importer \\
        --persons data/vedastro/PersonList-15k.csv \\
        --marriages data/vedastro/MarriageInfoDataset.csv \\
        --output data/astro_databank/raw.csv \\
        [--require-marriage-label]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Allow large JSON cells in PersonList/MarriageInfo CSVs.
csv.field_size_limit(10 ** 7)

# StdTime in PersonList-15k uses `HH:MM dd/MM/YYYY ±HH:MM` (no seconds).
_STDTIME_RE = re.compile(
    r"^(?P<hh>\d{1,2}):(?P<mm>\d{2})\s+"
    r"(?P<d>\d{1,2})/(?P<mo>\d{1,2})/(?P<y>\d{4})\s+"
    r"(?P<sign>[+-])(?P<tzh>\d{1,2}):(?P<tzm>\d{2})$"
)


@dataclass(frozen=True)
class Person:
    """Output row, mirroring the columns databank_etl expects."""
    name: str
    date_of_birth: str       # ISO YYYY-MM-DD
    time_of_birth: str       # HH:MM:SS
    latitude: float
    longitude: float
    tz_offset: float         # decimal hours (e.g. 5.5)
    rodden_rating: str       # always "AA" for this dataset
    categories: str          # semicolon-separated; encodes the marriage outcome
    source_url: str


# ---------- BirthTime parsing ----------

def _parse_stdtime(stdtime: str) -> tuple[str, str, float] | None:
    """Decompose `"19:55 26/06/1954 +01:00"` into (ISO date, HH:MM:SS, tz_offset).

    Returns None if the string doesn't conform — the importer skips such
    rows rather than guessing.
    """
    m = _STDTIME_RE.match(stdtime.strip())
    if m is None:
        return None
    try:
        date = dt.date(int(m["y"]), int(m["mo"]), int(m["d"]))
    except ValueError:
        return None
    hh, mm = int(m["hh"]), int(m["mm"])
    if not (0 <= hh < 24 and 0 <= mm < 60):
        return None
    sign = 1 if m["sign"] == "+" else -1
    tz_offset = sign * (int(m["tzh"]) + int(m["tzm"]) / 60.0)
    return date.isoformat(), f"{hh:02d}:{mm:02d}:00", tz_offset


def _parse_birth_json(birth_json: str) -> tuple[str, str, float, float, float] | None:
    """Parse a BirthTime JSON cell into (iso_date, hms, lat, lon, tz_offset).

    None if the JSON is malformed, missing keys, or the StdTime can't be
    decomposed. The outer importer counts these as skipped rows.
    """
    try:
        obj = json.loads(birth_json)
    except json.JSONDecodeError:
        return None
    stdtime = obj.get("StdTime")
    location = obj.get("Location") or {}
    if not isinstance(stdtime, str) or not isinstance(location, dict):
        return None
    parsed = _parse_stdtime(stdtime)
    if parsed is None:
        return None
    date_iso, hms, tz_offset = parsed
    try:
        latitude = float(location.get("Latitude"))
        longitude = float(location.get("Longitude"))
    except (TypeError, ValueError):
        return None
    if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
        return None
    return date_iso, hms, latitude, longitude, tz_offset


# ---------- Marriage outcome derivation ----------

def derive_marriage_category(marriage_info_json: str) -> str | None:
    """Distill the marriages list into one of:
       'marriage : dissolution'     - at least one Dissolution outcome
       'marriage : happiness'       - all known outcomes were Happiness
       None                          - no marriages OR no recognised outcomes

    The substring shape ("marriage : dissolution") is what
    train_classifier.derive_binary_target sees as `categories_lower`, so a
    `--target dissolution` CLI invocation will derive the binary label
    automatically — no trainer changes required.
    """
    try:
        obj = json.loads(marriage_info_json)
    except json.JSONDecodeError:
        return None
    marriages = obj.get("marriages") if isinstance(obj, dict) else None
    if not isinstance(marriages, list) or not marriages:
        return None

    has_dissolution = False
    has_happiness = False
    for m in marriages:
        if not isinstance(m, dict):
            continue
        outcome = (m.get("outcome") or "").strip().lower()
        if "dissolution" in outcome:
            has_dissolution = True
        elif "happiness" in outcome:
            has_happiness = True
    if has_dissolution:
        return "marriage : dissolution"
    if has_happiness:
        return "marriage : happiness"
    return None


# ---------- Main importer ----------

def _load_marriage_categories(path: Path) -> dict[str, str]:
    """RowKey/PartitionKey -> category string. Skip rows whose marriage
    info doesn't yield a known outcome."""
    out: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            # MarriageInfoDataset uses PartitionKey as the join field, but
            # tolerate either name to keep the importer robust to schema drift.
            key = (row.get("PartitionKey") or row.get("RowKey") or "").strip()
            info = row.get("Info") or ""
            if not key or not info.strip():
                continue
            cat = derive_marriage_category(info)
            if cat is not None:
                out[key] = cat
    return out


def import_vedastro(
    persons_csv: Path,
    marriages_csv: Path | None,
    output_csv: Path,
    *,
    require_marriage_label: bool = True,
) -> dict[str, int]:
    """Convert VedAstro CSVs to a raw.csv our Stage 2 ETL can read.

    Returns stats dict: input_persons, with_birthdata, with_marriage_label,
    written. Caller logs them so a CI run prints the funnel.
    """
    if not persons_csv.exists():
        raise FileNotFoundError(f"persons CSV missing: {persons_csv}")

    marriages: dict[str, str] = {}
    if marriages_csv is not None and marriages_csv.exists():
        marriages = _load_marriage_categories(marriages_csv)

    output_csv.parent.mkdir(parents=True, exist_ok=True)

    stats = {
        "input_persons": 0,
        "with_birthdata": 0,
        "with_marriage_label": 0,
        "written": 0,
        "skipped_no_birthdata": 0,
        "skipped_no_label": 0,
    }

    fieldnames = [
        "name", "date_of_birth", "time_of_birth",
        "latitude", "longitude", "tz_offset",
        "rodden_rating", "categories", "source_url",
    ]

    with persons_csv.open("r", encoding="utf-8", newline="") as fin, \
         output_csv.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in csv.DictReader(fin):
            stats["input_persons"] += 1
            name = (row.get("Name") or "").strip()
            row_key = (row.get("RowKey") or "").strip()
            if not name or not row_key:
                continue

            birth = _parse_birth_json(row.get("BirthTime") or "")
            if birth is None:
                stats["skipped_no_birthdata"] += 1
                continue
            stats["with_birthdata"] += 1
            date_iso, hms, lat, lon, tz_offset = birth

            # Rodden — Notes is a Python-repr dict like "{'rodden': 'AA'}"
            # rather than valid JSON, so we string-search instead of parsing.
            notes = (row.get("Notes") or "").lower()
            rodden = "AA" if "'aa'" in notes or '"aa"' in notes else ""

            category = marriages.get(row_key)
            if category is None:
                if require_marriage_label:
                    stats["skipped_no_label"] += 1
                    continue
                category = "marriage : unknown"
            else:
                stats["with_marriage_label"] += 1

            writer.writerow({
                "name": name,
                "date_of_birth": date_iso,
                "time_of_birth": hms,
                "latitude": f"{lat:.6f}",
                "longitude": f"{lon:.6f}",
                "tz_offset": f"{tz_offset:.4f}",
                "rodden_rating": rodden or "AA",
                "categories": category,
                "source_url": f"https://github.com/VedAstro/VedAstro#{row_key}",
            })
            stats["written"] += 1

    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.vedastro_importer",
        description="Convert VedAstro HuggingFace CSVs into raw.csv for Stage 2 ETL.",
    )
    parser.add_argument("--persons", type=Path, required=True,
                        help="Path to PersonList-15k.csv from VedAstro/HuggingFace.")
    parser.add_argument("--marriages", type=Path, default=None,
                        help="Path to MarriageInfoDataset.csv (optional but "
                             "needed for the marriage_dissolution target).")
    parser.add_argument("--output", type=Path, required=True,
                        help="Where to write raw.csv. Parent dir is created.")
    parser.add_argument("--require-marriage-label", action="store_true",
                        default=True,
                        help="Skip rows lacking a known Dissolution/Happiness "
                             "outcome (default ON since downstream trainer needs labels).")
    parser.add_argument("--allow-unlabeled", dest="require_marriage_label",
                        action="store_false",
                        help="Keep rows without marriage labels (categories = "
                             "'marriage : unknown'). Use only for non-target ETL passes.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = import_vedastro(
        persons_csv=args.persons,
        marriages_csv=args.marriages,
        output_csv=args.output,
        require_marriage_label=args.require_marriage_label,
    )
    logger.info(
        "imported %d rows  (input=%d, with_birthdata=%d, with_label=%d, "
        "skipped_no_birthdata=%d, skipped_no_label=%d)",
        stats["written"], stats["input_persons"], stats["with_birthdata"],
        stats["with_marriage_label"], stats["skipped_no_birthdata"],
        stats["skipped_no_label"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
