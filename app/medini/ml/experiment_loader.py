"""Phase 3 — Single entry point for ML experiments to materialise their training matrix.

The data-architecture agent's central rule: **no experiment ever writes a
Silver parquet of its own**. All training matrices come from one function
that reads canonical Silver/Gold views via DuckDB. This kills the schema
drift that plagued Round 9 (30+ overlapping parquets with mismatched
``name``/``name_norm``/``Q-number`` join keys).

Usage pattern:

    from app.medini.ml.experiment_loader import build_experiment_matrix

    df = build_experiment_matrix(
        view="v_event_survival",
        label_col="event_class",
        cohort_filter="corpus = 'astro_databank' AND event_class = 'marriage'",
        temporal_cutoff_jd=2440000.0,   # exclude events after this JD
        columns=["time_to_event_days", "md_lord_at_event", "asc_sign"],
    )
    # df is a pandas DataFrame ready for XGBoost / Cox / DeepHit.

Why a whitelist of view names: the cohort_filter is concatenated into
SQL, so injection is a non-trivial concern even on a single-user system.
Whitelisting the view name removes the worst class of injection (CTE
abuse); cohort_filter is restricted to a documented subset.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Final

import duckdb
import pandas as pd

from app.medini.etl.build_duckdb_catalog import (
    CATALOG_FILE, DEFAULT_DATA_DIR, initialise_catalog,
)

logger = logging.getLogger(__name__)

# Whitelist of view names the loader will query. Add new views explicitly
# rather than allowing arbitrary input — protects against SQL injection
# via the view-name parameter and forces experiments to declare a
# canonical feature view in the catalog.
ALLOWED_VIEWS: Final[frozenset[str]] = frozenset({
    # Silver
    "persons", "events", "charts", "dasha_windows",
    "resolved_persons", "events_with_dasha",
    "chart_edges", "static_graph_edges", "dasha_tree",
    # Gold
    "v_persons_canonical", "v_chart_with_person", "v_event_survival",
    "v_chart_edge_summary", "v_natal_md_ads", "v_event_with_tree",
})

# Cohort filter must look like SQL boolean expression over column names,
# string literals, numbers, NULL, AND/OR, parentheses, comparison ops,
# and IN clauses. Rejects keywords that enable injection.
_COHORT_FORBIDDEN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|ATTACH|COPY|PRAGMA|EXPORT|IMPORT)\b",
    re.IGNORECASE,
)


class CohortFilterError(ValueError):
    """Raised when cohort_filter contains a forbidden keyword."""


def _validate_cohort_filter(cohort_filter: str) -> None:
    """Reject filters containing data-mutation keywords."""
    if _COHORT_FORBIDDEN.search(cohort_filter):
        raise CohortFilterError(
            f"cohort_filter contains forbidden keyword: {cohort_filter!r}"
        )


def _ensure_catalog(data_dir: Path) -> Path:
    """Make sure ``data_dir/catalog.duckdb`` exists and is current."""
    catalog_path = data_dir / CATALOG_FILE
    if not catalog_path.exists():
        logger.info("Catalog not found; initialising at %s", catalog_path)
        initialise_catalog(data_dir, catalog_path).close()
    return catalog_path


def build_experiment_matrix(
    view: str,
    label_col: str | None = None,
    columns: list[str] | None = None,
    cohort_filter: str | None = None,
    temporal_cutoff_jd: float | None = None,
    temporal_cutoff_column: str = "event_jd",
    data_dir: Path = DEFAULT_DATA_DIR,
) -> pd.DataFrame:
    """Materialise an experiment training matrix from the catalog.

    Args:
      view: One of ``ALLOWED_VIEWS`` (see module-level constant).
      label_col: Optional — if provided, the column gets renamed to ``label``
        in the result so downstream sklearn-style code can ``df.pop("label")``
        without knowing the feature view's column name.
      columns: Optional explicit column list. If None, returns all columns
        from the view (excluding non-feature metadata when present).
      cohort_filter: SQL WHERE-clause fragment (no leading WHERE) restricted
        to read-only boolean expressions. Forbidden keywords raise
        CohortFilterError.
      temporal_cutoff_jd: If set, exclude rows where
        ``temporal_cutoff_column >= temporal_cutoff_jd``. This is the
        anti-leakage train-cutoff for temporal splits.
      temporal_cutoff_column: Which column is the time axis. Defaults to
        ``event_jd`` for survival views; pass ``start_jd`` for dasha_windows.
      data_dir: Override the data directory (testing).
    """
    if view not in ALLOWED_VIEWS:
        raise ValueError(
            f"view {view!r} not in ALLOWED_VIEWS — register it in "
            f"app/medini/ml/experiment_loader.py:ALLOWED_VIEWS first"
        )

    if cohort_filter is not None:
        _validate_cohort_filter(cohort_filter)

    catalog_path = _ensure_catalog(data_dir)

    select_cols = "*" if columns is None else ", ".join(columns)
    clauses: list[str] = []
    if cohort_filter:
        clauses.append(f"({cohort_filter})")
    if temporal_cutoff_jd is not None:
        clauses.append(f"{temporal_cutoff_column} < {float(temporal_cutoff_jd)}")
    where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""

    query = f"SELECT {select_cols} FROM {view}{where_sql}"
    logger.info("Loading matrix: %s", query)

    con = duckdb.connect(str(catalog_path), read_only=True)
    try:
        df = con.execute(query).df()
    finally:
        con.close()

    if label_col is not None:
        if label_col not in df.columns:
            raise KeyError(f"label_col {label_col!r} not in result columns: {list(df.columns)}")
        df = df.rename(columns={label_col: "label"})

    logger.info("Loaded %d rows x %d cols", len(df), len(df.columns))
    return df


def list_views(data_dir: Path = DEFAULT_DATA_DIR) -> pd.DataFrame:
    """Enumerate registered catalog views + their row counts.

    Quick CLI helper: ``python -m app.medini.ml.experiment_loader``.
    """
    catalog_path = _ensure_catalog(data_dir)
    con = duckdb.connect(str(catalog_path), read_only=True)
    try:
        views = con.execute("""
            SELECT table_name AS view_name
            FROM information_schema.tables
            WHERE table_type IN ('VIEW', 'BASE TABLE')
            ORDER BY view_name
        """).df()
        counts: list[int] = []
        for v in views["view_name"]:
            n = con.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
            counts.append(n)
        views["row_count"] = counts
        views["in_whitelist"] = views["view_name"].isin(ALLOWED_VIEWS)
        return views
    finally:
        con.close()


def main() -> int:
    """CLI: print available views for discovery."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")
    print(list_views().to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
