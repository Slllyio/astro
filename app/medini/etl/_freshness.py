"""Shared mtime-based freshness guard for ETL scripts.

Pattern: a CLI ETL script declares its inputs + output. If the output
exists and is newer than every input, the script short-circuits.

Cheaper than content-hashing for files that are append-only or rebuilt
from scratch. Not suitable for inputs that get touched without semantic
change (e.g. ``touch`` for testing) — but no ETL script in this project
does that.

Usage in an ETL ``main()``::

    from app.medini.etl._freshness import skip_if_fresh

    inputs = [data_dir / "dasha_windows.parquet"]
    output = data_dir / "dasha_pd_windows.parquet"
    if skip_if_fresh(output, inputs):
        return 0
    # ... heavy ETL work ...

Pass ``force=True`` (CLI flag ``--force``) to bypass the guard.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


def skip_if_fresh(
    output: Path, inputs: Iterable[Path], *, force: bool = False,
) -> bool:
    """Return True (and log) if ``output`` is up-to-date vs all inputs.

    Returns False if:
      * ``force=True`` is set
      * output file doesn't exist
      * any input file doesn't exist (caller will likely error anyway)
      * any input is newer than the output
    """
    if force:
        return False
    if not output.exists():
        return False
    inputs_list = list(inputs)
    out_mtime = output.stat().st_mtime
    for inp in inputs_list:
        if not inp.exists():
            return False
        if inp.stat().st_mtime > out_mtime:
            logger.info(
                "Input %s newer than output %s — rebuild needed",
                inp.name, output.name,
            )
            return False
    logger.info(
        "Output %s is up-to-date vs %d input(s) — skipping rebuild "
        "(pass --force to override)",
        output.name, len(inputs_list),
    )
    return True
