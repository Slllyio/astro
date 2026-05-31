"""Shared parquet write helper — locks all new writes to ZSTD compression.

The default pandas/pyarrow codec is SNAPPY; empirical measurement on
this project's data shows ZSTD(3) saves ~36% per file with no measurable
read-time penalty (DuckDB and pyarrow both decompress ZSTD in parallel).

Pattern in ETL scripts::

    from app.medini.etl._parquet_io import write_parquet_zstd

    write_parquet_zstd(df, out_path)        # replaces df.to_parquet(out_path, index=False)

For one-off in-place recompression of existing snappy files, use the
``recompress_parquets`` CLI::

    python -m app.medini.etl.recompress_parquets --data-dir app/medini/data
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# ZSTD level 3 — empirically the sweet spot on this project's data:
# ~36% smaller than SNAPPY, same decompression wall-clock under
# DuckDB's parallel reader. Level 9 gives ~3% more compression for
# 6× slower writes; not worth it for ETL outputs.
DEFAULT_ZSTD_LEVEL = 3


def write_parquet_zstd(
    df: pd.DataFrame, path: Path, *, level: int = DEFAULT_ZSTD_LEVEL,
    index: bool = False,
) -> None:
    """Write a DataFrame to parquet with ZSTD compression.

    Mirrors ``df.to_parquet(path, index=False)`` semantics but pins the
    codec. PyArrow is the only engine that supports passing per-codec
    levels; we always use it (the project ships pyarrow as a hard dep).
    """
    df.to_parquet(
        path, index=index, engine="pyarrow",
        compression="zstd", compression_level=level,
    )
    logger.debug(
        "Wrote %d rows × %d cols to %s (ZSTD level %d)",
        len(df), len(df.columns), path, level,
    )
