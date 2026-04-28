"""Stage 2 ETL: raw Astro-Databank CSV -> ML-ready parquet.

Reads the CSV produced by `app.medini.etl.scraper`, filters strictly to
AA-rated rows with complete birth data, runs each row through
`compute_chart_features` in a multiprocessing.Pool (per-worker pyswisseph
state via `lahiri_worker.init_worker`), and writes the result as parquet.

CLI:
    python -m app.medini.etl.databank_etl \\
        --input data/astro_databank/raw.csv \\
        --output app/medini/data/ml_astro_features.parquet \\
        [--workers N] [--limit N]

Robust to per-row failures: a single row's pyswisseph exception (e.g.,
extreme historical date outside ephemeris range) is caught, logged, and
skipped. The dataset finishes; the row count differs from the input by
the failure count, which is reported.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import multiprocessing as mp
import sys
import traceback
from pathlib import Path
from typing import Any

import pandas as pd
import swisseph as swe

from app.medini.etl.feature_engineering import (
    compute_chart_features,
    expected_feature_columns,
)
from app.medini.etl.lahiri_worker import init_worker

logger = logging.getLogger(__name__)

# Columns the trainer wants alongside the 193 features for traceability +
# label derivation. NOT in expected_feature_columns() because they're not
# fed to the ML model directly.
LABEL_COLUMNS: tuple[str, ...] = (
    "name", "rodden_rating", "categories_raw", "categories_lower",
    "categories_tokens", "source_url",
)


# ---------- Per-row computation (called by Pool workers) ----------

def _row_to_jd(row: dict[str, str]) -> float | None:
    """Convert (date, time, tz_offset) into a Julian Day in UT.

    Returns None if any field missing or unparseable. Stage 2 filters such
    rows out before reaching this function, but the defensive return
    keeps the worker safe if upstream filtering ever drifts.
    """
    date_str = row.get("date_of_birth", "")
    time_str = row.get("time_of_birth", "")
    tz_str = row.get("tz_offset", "")
    if not (date_str and time_str and tz_str):
        return None

    try:
        date = dt.date.fromisoformat(date_str)
        h, m, s = map(int, time_str.split(":"))
        tz_offset = float(tz_str)
    except (ValueError, AttributeError):
        return None

    # Local time → UT decimal hour
    decimal_hour_local = h + m / 60.0 + s / 3600.0
    decimal_hour_ut = decimal_hour_local - tz_offset

    return swe.julday(date.year, date.month, date.day, decimal_hour_ut, swe.GREG_CAL)


def _normalize_categories(raw: str) -> dict[str, Any]:
    """Stage 2 category-flattening (locked decision in plan)."""
    parts = [c.strip() for c in (raw or "").split(";") if c.strip()]
    lower_join = " | ".join(c.lower() for c in parts)
    tokens: list[str] = []
    for part in parts:
        for tok in part.lower().replace(":", " ").split():
            if tok and tok not in tokens:
                tokens.append(tok)
    return {
        "categories_raw": raw or "",
        "categories_lower": lower_join,
        "categories_tokens": tokens,
    }


def _process_row(row: dict[str, str]) -> dict[str, Any] | None:
    """Worker function: one CSV row in, one feature dict out (or None on
    failure). Runs in a subprocess; pyswisseph state was set by init_worker.
    """
    try:
        jd = _row_to_jd(row)
        if jd is None:
            return None
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])

        features = compute_chart_features(jd, latitude, longitude)

        cats = _normalize_categories(row.get("categories", ""))
        features.update(cats)
        features["name"] = row.get("name", "")
        features["rodden_rating"] = row.get("rodden_rating", "")
        features["source_url"] = row.get("source_url", "")
        return features
    except Exception:
        # Log the traceback to stderr so the parent process can collect it
        # via the pool's standard logging without crashing the entire run.
        logger.warning(
            "row failed (name=%s url=%s): %s",
            row.get("name", "?"),
            row.get("source_url", "?"),
            traceback.format_exc(limit=2),
        )
        return None


# ---------- Filtering ----------

def _is_aa_complete(row: dict[str, str]) -> bool:
    """True if the row passes Stage 2's strict AA-only + complete-data filter.

    Per the plan: drop anything not Rodden AA, drop missing date/time/lat/lon
    (silent corruption sources), drop missing tz_offset (LMT and other
    unparseable timezones produce empty strings — see scraper.parse_tz_offset).
    """
    if row.get("rodden_rating", "").strip().upper() != "AA":
        return False
    for field in ("date_of_birth", "time_of_birth", "latitude", "longitude", "tz_offset"):
        if not row.get(field, "").strip():
            return False
    return True


# ---------- Main ETL pipeline ----------

def run_etl(
    input_csv: Path,
    output_parquet: Path,
    n_workers: int | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    """Execute the Stage 2 pipeline.

    Returns a stats dict: {input_count, after_filter, succeeded, failed}.
    """
    if not input_csv.exists():
        raise FileNotFoundError(f"input CSV not found: {input_csv}")

    output_parquet.parent.mkdir(parents=True, exist_ok=True)

    # Read + filter
    with input_csv.open("r", encoding="utf-8", newline="") as f:
        all_rows = list(csv.DictReader(f))
    input_count = len(all_rows)

    filtered = [r for r in all_rows if _is_aa_complete(r)]
    if limit is not None:
        filtered = filtered[:limit]
    after_filter = len(filtered)
    logger.info(
        "input=%d, after AA+complete filter=%d, dropped=%d",
        input_count, after_filter, input_count - after_filter,
    )

    if not filtered:
        raise RuntimeError(
            "no rows survived filtering (need rodden_rating=AA + non-empty "
            "date/time/lat/lon/tz). Check the scraper output."
        )

    # Multiprocessing pool with the critical Lahiri initializer
    n_workers = n_workers or mp.cpu_count()
    logger.info("computing features across %d worker process(es)...", n_workers)

    with mp.Pool(processes=n_workers, initializer=init_worker) as pool:
        results = pool.map(_process_row, filtered)

    succeeded = [r for r in results if r is not None]
    failed = len(results) - len(succeeded)
    logger.info("succeeded=%d, failed=%d", len(succeeded), failed)

    if not succeeded:
        raise RuntimeError("all rows failed feature extraction")

    # Write parquet. Pandas + pyarrow handles the categorical columns
    # transparently; tokenized lists remain Python lists in the parquet
    # (pyarrow's list type), readable by the Stage 3 trainer.
    df = pd.DataFrame(succeeded)
    df.to_parquet(output_parquet, engine="pyarrow", index=False)
    logger.info("wrote %s (%d rows, %d columns)", output_parquet, len(df), len(df.columns))

    return {
        "input_count": input_count,
        "after_filter": after_filter,
        "succeeded": len(succeeded),
        "failed": failed,
    }


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.databank_etl",
        description="Compute the Vedic Tensor for every AA-rated row in a "
                    "scraper CSV and emit a parquet for Stage 3 ML training.",
    )
    parser.add_argument("--input", type=Path,
                        default=Path("data/astro_databank/raw.csv"),
                        help="Scraper output CSV.")
    parser.add_argument("--output", type=Path,
                        default=Path("app/medini/data/ml_astro_features.parquet"),
                        help="Parquet destination.")
    parser.add_argument("--workers", type=int, default=None,
                        help="Worker process count (defaults to CPU count).")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only the first N filtered rows (for smoke tests).")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = run_etl(args.input, args.output, n_workers=args.workers, limit=args.limit)
    print(
        f"ETL complete: input={stats['input_count']}, after_filter={stats['after_filter']}, "
        f"succeeded={stats['succeeded']}, failed={stats['failed']}, output={args.output}"
    )
    return 0 if stats["succeeded"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
