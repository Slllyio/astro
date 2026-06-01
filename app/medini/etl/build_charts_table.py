"""Build the Silver-layer canonical natal-chart table.

For each person in ``app/medini/data/persons.parquet``, compute:
  * Lahiri sidereal positions of all 9 grahas (8 swisseph + Ketu = Rahu+180)
  * Ascendant (Lagna) at the moment-and-place of birth
  * Whole-sign house assignment per planet (1..12, reckoned from Lagna)
  * Nakshatra (1..27) for each planet

Output schema (charts.parquet — Silver-layer canonical chart, FK -> persons):
  person_id          TEXT
  birth_jd_used      FLOAT   -- the Julian Day actually used (noon-UTC fallback)
  time_precision     TEXT    -- "minute" (ADB) | "day" (Wikidata day-precision)
  asc_lon            FLOAT
  asc_sign           INT
  <graha>_lon        FLOAT   -- 9 grahas
  <graha>_sign       INT
  <graha>_house      INT     -- whole-sign from Lagna
  <graha>_nakshatra  INT     -- 0..26 (Ashwini=0, Revati=26 — matches app/core/nakshatra.py)

This module deliberately stores ONLY the canonical chart primitives — no
derived features (no dispositor chains, no aspect orbs, no kinematics).
Those belong in Gold-layer DuckDB views materialised on top of this table.

Day-precision births (Wikidata corpus) fall back to noon-UTC for birth_jd
and consequently the ascendant/house assignments are unreliable for those
persons. Downstream ML should filter on ``time_precision == 'minute'`` if
houses are load-bearing for the experiment.

Usage:
    python -m app.medini.etl.build_charts_table
    python -m app.medini.etl.build_charts_table --limit 100
    python -m app.medini.etl.build_charts_table --workers 8
"""
from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Final, Any

import pandas as pd
import swisseph as swe

from app.core.ephemeris_engine import (
    PLANETS, calculate_ascendant, calculate_d1_position,
    calculate_ketu_d1, whole_sign_house,
)
from app.core.nakshatra import nakshatra_for_longitude

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
PERSONS_FILE: Final = "persons.parquet"
CHARTS_FILE: Final = "charts.parquet"

# Canonical graha order. Matters for column-name stability across reruns.
GRAHAS: Final[tuple[str, ...]] = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
)


def _jd_from_birth_date_noon_utc(birth_date: str) -> float | None:
    """Fallback Julian Day for day-precision births (noon UTC of birth_date).

    Returns None if the date string fails to parse (e.g. pre-Gregorian or
    malformed) — caller skips such rows.
    """
    try:
        y, m, d = birth_date.split("-")
        return swe.julday(int(y), int(m), int(d), 12.0, swe.GREG_CAL)
    except (ValueError, AttributeError):
        return None


def _compute_chart(
    person_id: str,
    birth_jd: float | None,
    birth_date: str | None,
    birth_lat: float | None,
    birth_lon: float | None,
) -> dict[str, Any] | None:
    """Compute the canonical chart for one person.

    Returns None if the row lacks the minimum data needed (no birth_jd or
    no lat/lon). Errors during swisseph calls bubble up to the worker
    wrapper, which logs and returns None.
    """
    if birth_lat is None or birth_lon is None or pd.isna(birth_lat) or pd.isna(birth_lon):
        return None

    if birth_jd is None or pd.isna(birth_jd):
        if birth_date is None or pd.isna(birth_date):
            return None
        jd = _jd_from_birth_date_noon_utc(str(birth_date))
        if jd is None:
            return None
        time_precision = "day"
    else:
        jd = float(birth_jd)
        time_precision = "minute"

    # Ascendant.
    asc = calculate_ascendant(jd, float(birth_lat), float(birth_lon))
    asc_sign = asc["sign"]

    # Planets — Rahu comes from swisseph TRUE_NODE; Ketu derived from Rahu.
    planet_data: dict[str, dict[str, Any]] = {}
    for name, swe_id in PLANETS.items():
        planet_data[name] = calculate_d1_position(jd, swe_id)
    planet_data["Ketu"] = calculate_ketu_d1(planet_data["Rahu"])

    row: dict[str, Any] = {
        "person_id": person_id,
        "birth_jd_used": jd,
        "time_precision": time_precision,
        "asc_lon": asc["longitude"],
        "asc_sign": asc_sign,
        "asc_nakshatra": nakshatra_for_longitude(asc["longitude"])["index"],
    }
    for graha in GRAHAS:
        # Title-case for dict lookup ("Sun"); lowercase for column name ("sun_lon").
        p = planet_data[graha.title()]
        row[f"{graha}_lon"] = p["longitude"]
        row[f"{graha}_sign"] = p["sign"]
        row[f"{graha}_house"] = whole_sign_house(asc_sign, p["sign"])
        row[f"{graha}_nakshatra"] = nakshatra_for_longitude(p["longitude"])["index"]
    return row


def _worker(args: tuple[str, float | None, str | None, float | None, float | None]) -> dict[str, Any] | None:
    """Multiprocessing worker — exceptions return None and log."""
    person_id, birth_jd, birth_date, birth_lat, birth_lon = args
    try:
        return _compute_chart(person_id, birth_jd, birth_date, birth_lat, birth_lon)
    except Exception as exc:  # noqa: BLE001 — sweeping is intentional
        logger.warning("Chart compute failed for %s: %s", person_id, exc)
        return None


def build_charts(
    persons: pd.DataFrame,
    workers: int = 1,
    chunksize: int = 256,
) -> pd.DataFrame:
    """Compute charts for every row of persons, optionally in parallel."""
    inputs = list(zip(
        persons["person_id"].tolist(),
        persons["birth_jd"].tolist(),
        persons["birth_date"].tolist(),
        persons["birth_lat"].tolist(),
        persons["birth_lon"].tolist(),
    ))
    if workers > 1:
        with mp.Pool(workers) as pool:
            results = list(pool.imap_unordered(_worker, inputs, chunksize=chunksize))
    else:
        results = [_worker(t) for t in inputs]

    rows = [r for r in results if r is not None]
    logger.info("Computed %d charts (%d skipped due to missing data)",
                len(rows), len(inputs) - len(rows))
    return pd.DataFrame(rows)


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None,
                        help="Process only the first N persons (smoke test).")
    parser.add_argument("--workers", type=int, default=1,
                        help="Parallel worker processes; 1 = serial.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    persons_path = args.data_dir / PERSONS_FILE
    persons = pd.read_parquet(persons_path)
    if args.limit is not None:
        persons = persons.head(args.limit)
    logger.info("Loaded %d persons from %s", len(persons), persons_path)

    charts = build_charts(persons, workers=args.workers)
    out_path = args.data_dir / CHARTS_FILE
    charts.to_parquet(out_path, index=False)
    logger.info("Wrote %d charts to %s", len(charts), out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
