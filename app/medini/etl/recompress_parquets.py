"""One-shot in-place recompression of parquet files from SNAPPY → ZSTD.

Reads each ``.parquet`` under the target directory, re-writes it with
ZSTD compression, reports before/after sizes. Idempotent: parquets
already ZSTD are skipped.

Empirical measurement on this project's data (database-optimizer agent
verdict): ZSTD(level=3) saves ~36% per file with no measurable read-
time penalty under DuckDB/pyarrow parallel decompression.

Usage:
    python -m app.medini.etl.recompress_parquets --dry-run
    python -m app.medini.etl.recompress_parquets --data-dir app/medini/data
    python -m app.medini.etl.recompress_parquets --include 'dasha_*'

The script preserves schema, column ordering, and row ordering — only
the compression codec changes. Safe to re-run.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pyarrow.parquet as pq

from app.medini.etl._parquet_io import write_parquet_zstd

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")


def _current_codec(path: Path) -> str:
    """Read the compression codec from the first column of the first row group."""
    try:
        meta = pq.read_metadata(path)
        if meta.num_row_groups == 0:
            return "EMPTY"
        rg = meta.row_group(0)
        if rg.num_columns == 0:
            return "EMPTY"
        return rg.column(0).compression.upper()
    except Exception as exc:  # noqa: BLE001
        return f"ERROR({exc})"


def recompress_file(path: Path, *, dry_run: bool) -> tuple[int, int]:
    """Recompress one parquet file, returning (before_bytes, after_bytes)."""
    import pandas as pd
    before = path.stat().st_size
    df = pd.read_parquet(path)
    if dry_run:
        # Estimate: write to a temp path, measure, then delete
        tmp = path.with_suffix(".tmp.parquet")
        write_parquet_zstd(df, tmp)
        after = tmp.stat().st_size
        tmp.unlink()
    else:
        write_parquet_zstd(df, path)
        after = path.stat().st_size
    return before, after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument(
        "--include", type=str, default="*.parquet",
        help="Glob pattern within data-dir (default: *.parquet).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report savings without writing anything in place.",
    )
    parser.add_argument(
        "--skip-zstd", action="store_true", default=True,
        help="Skip files already using ZSTD (default behaviour).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    files = sorted(args.data_dir.glob(args.include))
    if not files:
        logger.warning("No files match %s under %s", args.include, args.data_dir)
        return 1

    total_before = 0
    total_after = 0
    skipped_zstd = 0
    skipped_subdir = 0
    converted = 0
    failed: list[str] = []

    for path in files:
        if not path.is_file():
            continue
        # Skip files in subdirectories (e.g. legacy/, knowledge_library/)
        if path.parent != args.data_dir:
            skipped_subdir += 1
            continue
        codec = _current_codec(path)
        if codec == "ZSTD" and args.skip_zstd:
            skipped_zstd += 1
            continue
        if codec.startswith("ERROR"):
            failed.append(f"{path.name}: {codec}")
            continue
        try:
            before, after = recompress_file(path, dry_run=args.dry_run)
            total_before += before
            total_after += after
            converted += 1
            pct = (before - after) / before * 100 if before else 0
            verb = "WOULD save" if args.dry_run else "saved"
            logger.info(
                "%-55s %s %6.1f MB (%s %5.1f%% via %s)",
                path.name,
                f"{before / 1024 / 1024:6.1f} MB ->",
                after / 1024 / 1024, verb, pct, codec,
            )
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{path.name}: {exc}")
            logger.exception("Failed to recompress %s", path.name)

    saved = total_before - total_after
    pct = saved / total_before * 100 if total_before else 0
    verb = "WOULD reclaim" if args.dry_run else "Reclaimed"
    logger.info(
        "Summary: %d converted, %d already-ZSTD skipped, %d subdirs skipped, %d failed",
        converted, skipped_zstd, skipped_subdir, len(failed),
    )
    logger.info(
        "%s %.1f MB (%.1f%%) — %.1f MB before, %.1f MB after",
        verb, saved / 1024 / 1024, pct,
        total_before / 1024 / 1024, total_after / 1024 / 1024,
    )
    if failed:
        logger.warning("Failed files:\n%s", "\n".join(f"  {f}" for f in failed))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
