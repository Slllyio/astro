"""Phase 2 — Join events to the dasha window active at event_jd.

This is THE FIX flagged by the multi-agent data-layer audit:

  Stage D's Dynamic-DeepHit was regressing on ``window_duration_days``
  (the length of the dasha window), not on time-to-event from birth.
  A 19-yr Saturn MD with an event on day 5 had duration=6940. A 19-yr
  Saturn MD with NO event also had duration=6940. The temporal model
  had nothing to learn.

This module rebuilds the survival target by:
  1. Parsing each event's ``event_date`` (YYYY-MM-DD) into a Julian Day
     (``event_jd``) at noon-UTC of the event day.
  2. Interval-joining each event to the (MD, AD) dasha window in which
     event_jd falls, via ``dasha_windows.parquet``.
  3. Computing ``age_at_event_years`` and elapsed time within MD / AD.

Output (events_with_dasha.parquet) — one row per event:
  event_id          INT
  person_id         TEXT  -- FK
  event_class       TEXT
  event_date        TEXT  -- preserved as-is
  event_jd          FLOAT -- the temporal target ML needs
  birth_jd          FLOAT -- from charts (used precision JD)
  age_at_event_years FLOAT
  md_lord_at_event  TEXT  -- the active Mahadasha lord at event_jd
  ad_lord_at_event  TEXT  -- the active Antardasha lord at event_jd
  md_seq            INT   -- 0..8 — which MD in the cycle
  ad_seq            INT   -- 0..8 — which AD in the MD
  md_elapsed_years  FLOAT -- time from MD start to event
  ad_elapsed_years  FLOAT -- time from AD start to event
  ad_duration_days  FLOAT -- the AD's full length (for normalization)
  source            TEXT

Events with unparseable or out-of-cycle dates fall through to NaN
columns. Downstream ML can filter on ``md_lord_at_event IS NOT NULL``.

Usage:
    python -m app.medini.etl.build_event_dasha_join
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd
import swisseph as swe

from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
from app.medini.etl.build_duckdb_catalog import initialise_catalog

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
OUTPUT_FILE: Final = "events_with_dasha.parquet"


def event_date_to_jd(event_date: str | None) -> float | None:
    """Convert a YYYY-MM-DD event date to Julian Day at 12:00 UTC.

    Noon-UTC is the standard convention when the time-of-day is unknown
    (which is true for all events in our corpora — only dates are recorded).
    Returns None on parse failure so the caller can null-fill downstream
    columns.
    """
    if event_date is None or pd.isna(event_date):
        return None
    try:
        y, m, d = str(event_date).split("-")
        return swe.julday(int(y), int(m), int(d), 12.0, swe.GREG_CAL)
    except (ValueError, AttributeError):
        return None


def build_event_dasha_join(data_dir: Path) -> pd.DataFrame:
    """Run the interval join via DuckDB and return the result as a DataFrame.

    DuckDB's range join is far more efficient than a pandas
    ``cross_join + filter``; on this corpus (54k events x 3.5M windows)
    the query completes in a few seconds.
    """
    con = initialise_catalog(data_dir, data_dir / "catalog.duckdb")
    try:
        # Materialise event_jd as a temp table so we can join on intervals.
        events = con.execute("""
            SELECT
                event_id, person_id, event_class, event_root, event_subtype,
                event_date, event_label, source
            FROM events
        """).df()

        events["event_jd"] = events["event_date"].map(event_date_to_jd)
        con.register("events_with_jd", events)

        # The interval join. DuckDB picks the optimal IEJoin / range index
        # automatically for predicates of this shape.
        result = con.execute("""
            SELECT
                e.event_id,
                e.person_id,
                e.event_class,
                e.event_date,
                e.event_jd,
                c.birth_jd_used                  AS birth_jd,
                (e.event_jd - c.birth_jd_used) / 365.2425 AS age_at_event_years,
                w.md_lord                        AS md_lord_at_event,
                w.ad_lord                        AS ad_lord_at_event,
                w.md_seq                         AS md_seq,
                w.ad_seq                         AS ad_seq,
                (e.event_jd - md_anchor.start_jd) / 365.2425 AS md_elapsed_years,
                (e.event_jd - w.start_jd) / 365.2425 AS ad_elapsed_years,
                w.duration_days                  AS ad_duration_days,
                e.source                         AS source
            FROM events_with_jd e
            LEFT JOIN dasha_windows w
              ON e.person_id = w.person_id
             AND e.event_jd BETWEEN w.start_jd AND w.end_jd
            LEFT JOIN dasha_windows md_anchor
              ON e.person_id = md_anchor.person_id
             AND md_anchor.md_seq = w.md_seq
             AND md_anchor.ad_seq = 0
            LEFT JOIN charts c
              ON e.person_id = c.person_id
        """).df()
        return result
    finally:
        con.close()


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    result = build_event_dasha_join(args.data_dir)

    n_total = len(result)
    n_matched = result["md_lord_at_event"].notna().sum()
    n_unmatched = n_total - n_matched
    logger.info(
        "Joined %d events: %d matched to a dasha window, %d unmatched "
        "(out-of-cycle dates or unparseable event_date)",
        n_total, n_matched, n_unmatched,
    )

    out_path = args.data_dir / OUTPUT_FILE
    result.to_parquet(out_path, index=False)
    logger.info("Wrote %s", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
