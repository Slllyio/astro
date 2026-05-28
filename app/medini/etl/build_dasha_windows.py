"""Build the Silver-layer dasha-windows table (Vimshottari MD x AD per person).

For each person with a known birth_jd and moon longitude, enumerate all 81
(Mahadasha, Antardasha) sub-period windows that span the 120-year natal
Vimshottari cycle. Each row represents one MD-AD interval with stable
start_jd / end_jd in Julian Day units.

This module deliberately stops at AD (not PD = Pratyantar) for the Silver
layer. PD is a Gold-layer concern: 729 PDs per person across 43k persons
is ~31M rows of which most will never be queried. PD windows can be
computed on demand in app/medini/etl/build_dasha_tree.py (Phase 5).

Output schema (dasha_windows.parquet):
  window_id      TEXT   -- "{person_id}::MD::{md_lord}::AD::{ad_lord}"  (PK)
  person_id      TEXT   -- FK -> persons.parquet
  md_lord        TEXT   -- one of {Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury}
  ad_lord        TEXT   -- same vocabulary as md_lord
  md_seq         INT    -- 0..8 — position of this MD in the natal cycle
  ad_seq         INT    -- 0..8 — position of this AD within its MD
  start_jd       FLOAT  -- Julian Day of AD start
  end_jd         FLOAT  -- Julian Day of AD end
  duration_days  FLOAT  -- end_jd - start_jd (denormalized for fast queries)

Usage:
    python -m app.medini.etl.build_dasha_windows
    python -m app.medini.etl.build_dasha_windows --limit 1000
"""
from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Final, Any

import pandas as pd

from app.core.ephemeris_engine import DASHA_LORDS, DAYS_PER_VEDIC_YEAR
from app.medini.etl.feature_engineering import compute_full_mahadasha_cycle

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
PERSONS_FILE: Final = "persons.parquet"
CHARTS_FILE: Final = "charts.parquet"
OUTPUT_FILE: Final = "dasha_windows.parquet"

# Canonical Vimshottari lord order (Ketu, Venus, Sun, Moon, Mars, Rahu,
# Jupiter, Saturn, Mercury) with their respective tenures in years. This
# is the SAME constant used by ephemeris_engine, re-exposed here for the
# AD-expansion math.
_LORD_NAMES: Final[tuple[str, ...]] = tuple(name for name, _ in DASHA_LORDS)
_LORD_YEARS: Final[dict[str, int]] = dict(DASHA_LORDS)
_TOTAL_VIMSHOTTARI_YEARS: Final = 120


def _antardashas_in_md(
    md_lord: str, md_start_jd: float, md_duration_years: float,
) -> list[tuple[str, float, float]]:
    """Expand one MD into its 9 ADs.

    The AD sequence starts with the MD lord ITSELF, then proceeds through
    the canonical Vimshottari order. Each AD's length is proportional to
    its lord's Vimshottari tenure scaled by the parent MD's length:

        AD_years = MD_total_years * AD_lord_years / 120

    Returns: list of (ad_lord, ad_start_jd, ad_end_jd) tuples.
    """
    start_idx = _LORD_NAMES.index(md_lord)
    cursor = md_start_jd
    out: list[tuple[str, float, float]] = []
    for offset in range(len(_LORD_NAMES)):
        ad_lord = _LORD_NAMES[(start_idx + offset) % len(_LORD_NAMES)]
        ad_years = md_duration_years * _LORD_YEARS[ad_lord] / _TOTAL_VIMSHOTTARI_YEARS
        ad_end = cursor + ad_years * DAYS_PER_VEDIC_YEAR
        out.append((ad_lord, cursor, ad_end))
        cursor = ad_end
    return out


def _windows_for_person(person_id: str, birth_jd: float, moon_lon: float) -> list[dict[str, Any]]:
    """All 81 (MD, AD) windows for one person."""
    cycle = compute_full_mahadasha_cycle(birth_jd, moon_lon)
    rows: list[dict[str, Any]] = []
    for md_seq, (md_lord, md_start_jd, md_end_jd) in enumerate(cycle):
        md_duration_years = (md_end_jd - md_start_jd) / DAYS_PER_VEDIC_YEAR
        for ad_seq, (ad_lord, ad_start, ad_end) in enumerate(
            _antardashas_in_md(md_lord, md_start_jd, md_duration_years)
        ):
            rows.append({
                "window_id": f"{person_id}::MD::{md_lord}::AD::{ad_lord}::{md_seq}",
                "person_id": person_id,
                "md_lord": md_lord,
                "ad_lord": ad_lord,
                "md_seq": md_seq,
                "ad_seq": ad_seq,
                "start_jd": ad_start,
                "end_jd": ad_end,
                "duration_days": ad_end - ad_start,
            })
    return rows


def _worker(args: tuple[str, float, float]) -> list[dict[str, Any]]:
    """Multiprocessing worker."""
    person_id, birth_jd, moon_lon = args
    try:
        return _windows_for_person(person_id, birth_jd, moon_lon)
    except Exception as exc:  # noqa: BLE001 — sweep + log
        logger.warning("Dasha windows failed for %s: %s", person_id, exc)
        return []


def build_dasha_windows(
    persons: pd.DataFrame, charts: pd.DataFrame, workers: int = 1,
) -> pd.DataFrame:
    """Join persons -> charts to get (birth_jd, moon_lon) then expand to windows."""
    merged = charts[["person_id", "birth_jd_used", "moon_lon"]].copy()
    merged = merged.rename(columns={"birth_jd_used": "birth_jd"})
    inputs = list(zip(
        merged["person_id"].tolist(),
        merged["birth_jd"].tolist(),
        merged["moon_lon"].tolist(),
    ))
    if workers > 1:
        with mp.Pool(workers) as pool:
            chunks = list(pool.imap_unordered(_worker, inputs, chunksize=128))
    else:
        chunks = [_worker(t) for t in inputs]

    flat = [row for chunk in chunks for row in chunk]
    logger.info("Built %d dasha windows for %d persons (avg %d windows/person)",
                len(flat), len(inputs), len(flat) // max(1, len(inputs)))
    return pd.DataFrame(flat)


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    persons = pd.read_parquet(args.data_dir / PERSONS_FILE)
    charts = pd.read_parquet(args.data_dir / CHARTS_FILE)
    if args.limit is not None:
        persons = persons.head(args.limit)
        charts = charts[charts["person_id"].isin(set(persons["person_id"]))]
    logger.info("Loaded %d persons / %d charts", len(persons), len(charts))

    windows = build_dasha_windows(persons, charts, workers=args.workers)
    out_path = args.data_dir / OUTPUT_FILE
    windows.to_parquet(out_path, index=False)
    logger.info("Wrote %d rows to %s", len(windows), out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
