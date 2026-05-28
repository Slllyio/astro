"""Materialize hot Gold views from the DuckDB catalog as physical parquets.

The Gold views (``v_event_survival``, ``v_event_with_tree``,
``v_chart_with_person``, ``v_persons_canonical``) are recomputed on
every catalog ``SELECT``. For tables joined and queried frequently by
ML experiments, materializing them as physical parquets gives a 10-100x
read-speed improvement at the cost of staleness if upstream Silver
parquets change.

This script materializes the views once and writes them to
``app/medini/data/gold/`` as parquets. The catalog can then expose
either the views (always current) or the materialized parquets (faster
but require rebuild after upstream Silver rebuild).

Output schema:
  app/medini/data/gold/
    v_event_survival.parquet
    v_event_with_tree.parquet
    v_persons_canonical.parquet
    v_chart_with_person.parquet
    v_chart_edge_summary.parquet
    v_natal_md_ads.parquet

Usage:
    python -m app.medini.etl.materialize_gold_views
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import duckdb

from app.medini.etl.build_duckdb_catalog import (
    CATALOG_FILE, DEFAULT_DATA_DIR, initialise_catalog,
)

logger = logging.getLogger(__name__)

# Gold views to materialize. Listed in order of (approximate) compute cost,
# heaviest first — we want the biggest wins materialized.
_GOLD_VIEWS_TO_MATERIALIZE: Final[tuple[str, ...]] = (
    "v_event_with_tree",       # the doctrine-aware survival training matrix
    "v_event_survival",         # the standard survival training matrix
    "v_chart_with_person",      # chart + person metadata
    "v_persons_canonical",      # persons + dedup linkage
    "v_chart_edge_summary",     # per-chart edge counts
    "v_natal_md_ads",           # natal MDs and their ADs
)


def materialize(
    data_dir: Path = DEFAULT_DATA_DIR,
    out_subdir: str = "gold",
) -> None:
    """Materialize each Gold view to its own parquet file under ``data_dir/out_subdir/``.

    The catalog is initialized once at the start. Each view is queried
    in turn and the result is written. Failures on one view do not stop
    the others.
    """
    out_dir = data_dir / out_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    catalog_path = data_dir / CATALOG_FILE
    con = initialise_catalog(data_dir, catalog_path)
    try:
        for view_name in _GOLD_VIEWS_TO_MATERIALIZE:
            try:
                n = con.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
            except Exception as exc:  # noqa: BLE001
                logger.warning("View %s not registered; skipping (%s)", view_name, exc)
                continue
            out_path = out_dir / f"{view_name}.parquet"
            # COPY (SELECT *) TO 'path' (FORMAT 'parquet')
            con.execute(
                f"COPY (SELECT * FROM {view_name}) "
                f"TO '{out_path.as_posix()}' (FORMAT 'parquet')"
            )
            logger.info("Materialized %-25s (%d rows) -> %s",
                        view_name, n, out_path.name)
    finally:
        con.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--out-subdir", type=str, default="gold")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    materialize(data_dir=args.data_dir, out_subdir=args.out_subdir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
