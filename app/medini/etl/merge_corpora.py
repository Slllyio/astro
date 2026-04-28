"""Merge multiple raw.csv files (VedAstro + Wayback Astro-Databank, or any
future source) into a single deduplicated corpus for Stage 2 ETL.

Why dedup matters: VedAstro derives its 15k records from the same Astro-
Databank wiki the Wayback path scrapes. Roughly 60-70% of the rows
overlap. Without dedup, training rows would weight overlapping people
twice — once with the marriage_outcome label, once with the vocational
labels — biasing the model toward whichever cohort the duplicates favour.

Dedup key: (lowercased name, date_of_birth). A person can only be born
once, so this is a safe natural key. When two sources have the same key,
we pick the row with more complete data:
    1. Both date AND time set
    2. lat/lon set
    3. tz_offset set
    4. Rodden = "AA" (over A/B/C)
    5. More categories listed
    6. As a final tiebreak, the source listed first on the CLI wins.

Categories from both rows are union-merged so the trainer sees ALL labels
the person carries (marriage_outcome from VedAstro AND Vocation:Politics
from Astro-Databank, for example). This gives a single trained model
multiple usable `--target` substrings.

CLI:
    python -m app.medini.etl.merge_corpora \\
        --inputs data/astro_databank/raw.csv data/astro_databank/raw_wayback.csv \\
        --output data/astro_databank/merged.csv
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

# Allow large CSV cells (categories field can be long).
csv.field_size_limit(10 ** 7)

# Required columns for a Stage-2-compatible raw.csv. Anything missing gets
# treated as empty so older corpora with extra columns merge cleanly.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "name", "date_of_birth", "time_of_birth",
    "latitude", "longitude", "tz_offset",
    "rodden_rating", "categories", "source_url",
)


@dataclass(frozen=True)
class CompletenessScore:
    """Bag of booleans + counts that determines which duplicate row wins.

    Ordering: most-significant field first; trainer-relevant signal
    weighted ahead of provenance metadata.
    """
    has_date: bool
    has_time: bool
    has_coords: bool
    has_tz: bool
    is_aa: bool
    category_count: int
    source_priority: int   # lower = preferred (CLI ordering)

    def as_tuple(self) -> tuple:
        """Tuple ordered for `max(...)` to pick the better row."""
        return (
            self.has_date, self.has_time, self.has_coords,
            self.has_tz, self.is_aa, self.category_count,
            -self.source_priority,
        )


def _completeness(row: dict[str, str], source_priority: int) -> CompletenessScore:
    """Score a row for dedup-tiebreak. Higher tuple wins."""
    cats = (row.get("categories") or "").strip()
    cat_count = sum(1 for c in cats.split(";") if c.strip())
    return CompletenessScore(
        has_date=bool((row.get("date_of_birth") or "").strip()),
        has_time=bool((row.get("time_of_birth") or "").strip()),
        has_coords=bool((row.get("latitude") or "").strip()
                        and (row.get("longitude") or "").strip()),
        has_tz=bool((row.get("tz_offset") or "").strip()),
        is_aa=(row.get("rodden_rating") or "").strip().upper() == "AA",
        category_count=cat_count,
        source_priority=source_priority,
    )


def _dedup_key(row: dict[str, str]) -> tuple[str, str] | None:
    """The natural dedup key: (lowercased trimmed name, ISO date_of_birth).

    Returns None if either field is empty — those rows can't be deduped
    safely, so they pass through verbatim.
    """
    name = (row.get("name") or "").strip().lower()
    dob = (row.get("date_of_birth") or "").strip()
    if not name or not dob:
        return None
    return name, dob


def _merge_categories(a: str, b: str) -> str:
    """Union-merge two semicolon-joined category strings, preserving the
    insertion order of the first row's categories then appending unique
    new ones from the second row.
    """
    parts: list[str] = []
    seen: set[str] = set()
    for src in (a or "", b or ""):
        for raw in src.split(";"):
            tok = raw.strip()
            if tok and tok not in seen:
                seen.add(tok)
                parts.append(tok)
    return ";".join(parts)


def _pick_row(
    existing: dict[str, str], new: dict[str, str],
    existing_priority: int, new_priority: int,
) -> dict[str, str]:
    """Choose the better of two duplicate rows; merge categories from both."""
    existing_score = _completeness(existing, existing_priority)
    new_score = _completeness(new, new_priority)
    base = new if new_score.as_tuple() > existing_score.as_tuple() else existing
    # Whichever row we keep, ALWAYS union-merge categories so every label
    # ever seen for this person stays available to the trainer.
    merged = dict(base)
    merged["categories"] = _merge_categories(
        existing.get("categories", ""), new.get("categories", ""),
    )
    return merged


def merge_csvs(
    input_paths: list[Path],
    output_path: Path,
) -> dict[str, int]:
    """Merge `input_paths` into a single deduplicated CSV at `output_path`.

    Returns a stats dict. CLI prints it on completion.
    """
    if not input_paths:
        raise ValueError("at least one input CSV required")

    rows_by_key: dict[tuple[str, str], dict[str, str]] = {}
    untouchable: list[dict[str, str]] = []   # rows we couldn't dedup
    stats = {
        "input_files": len(input_paths),
        "rows_read": 0,
        "rows_written": 0,
        "duplicates_collapsed": 0,
        "rows_unmergeable": 0,
    }
    source_for_key: dict[tuple[str, str], int] = {}

    for priority, path in enumerate(input_paths):
        if not path.exists():
            logger.warning("input %s does not exist; skipping", path)
            continue
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats["rows_read"] += 1
                key = _dedup_key(row)
                if key is None:
                    # Row is missing name or DOB — pass through, don't dedup.
                    untouchable.append(row)
                    stats["rows_unmergeable"] += 1
                    continue
                existing = rows_by_key.get(key)
                if existing is None:
                    rows_by_key[key] = dict(row)
                    source_for_key[key] = priority
                else:
                    rows_by_key[key] = _pick_row(
                        existing, row,
                        source_for_key[key], priority,
                    )
                    # Track the better-priority source so a third dupe is
                    # measured against the same baseline.
                    if priority < source_for_key[key]:
                        source_for_key[key] = priority
                    stats["duplicates_collapsed"] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
        for row in rows_by_key.values():
            writer.writerow({col: row.get(col, "") for col in REQUIRED_COLUMNS})
            stats["rows_written"] += 1
        for row in untouchable:
            writer.writerow({col: row.get(col, "") for col in REQUIRED_COLUMNS})
            stats["rows_written"] += 1

    return stats


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.merge_corpora",
        description="Merge multiple raw.csv files into a deduplicated corpus.",
    )
    parser.add_argument(
        "--inputs", type=Path, nargs="+", required=True,
        help="One or more raw.csv files to merge. Earlier files win ties.",
    )
    parser.add_argument(
        "--output", type=Path, required=True,
        help="Destination merged CSV path.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = merge_csvs(args.inputs, args.output)
    logger.info(
        "merge complete: read=%d written=%d dupes_collapsed=%d unmergeable=%d",
        stats["rows_read"], stats["rows_written"],
        stats["duplicates_collapsed"], stats["rows_unmergeable"],
    )
    print(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
