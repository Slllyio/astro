"""Bulk-materialise astrologer's-lens readings for every dossier person.

Streams from ``person_dossier.parquet`` (Phase R11 Silver layer) through
the Phase 1-9 framework, writing a flat ``readings.parquet`` where each
row carries the **structured** reading output (not prose). Prose is
rendered on-demand from this table via ``app.llm.reading_prose``.

## Output schema (readings.parquet)

Identity (4 cols):
  person_id, corpus, name, asc_sign

Framework summary (8 cols):
  asc_lagna_lord, yogakaraka_planets, badhakesh, strongest_planet,
  weakest_planet, n_active_yogas, n_strong_bhavas, n_afflicted_bhavas

Active yogas list (3 cols):
  active_yoga_names (list[str]), active_yoga_refs (list[str]),
  active_yoga_intensities (list[float])

Per-bhava verdict (12 × 4 = 48 cols):
  b{1..12}_label, b{1..12}_composite, b{1..12}_confirming_yogas,
  b{1..12}_afflicting_yogas

Total ≈ 63 columns.

## Scale

~50 ms per person × 75,149 persons ≈ 62 minutes single-process; with
``--workers 4`` ≈ 16-20 minutes. Output parquet ≈ 25-30 MB.

Usage:
    python -m app.medini.etl.build_person_readings --limit 100
    python -m app.medini.etl.build_person_readings --workers 4
"""
from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
import time
from pathlib import Path
from typing import Any, Final

import pandas as pd

from app.core.chart_model import Chart
from app.core.dkp_modulation import DKPContext
from app.core.reading_composer import compose_reading

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")


def _row_to_reading_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Convert one dossier row to one readings.parquet row.

    Worker function — must be picklable for multiprocessing.
    """
    try:
        chart = Chart.from_dossier_row(row)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Chart build failed for %s: %s", row.get("person_id"), exc)
        return _empty_reading(row)
    try:
        reading = compose_reading(chart, DKPContext())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Compose failed for %s: %s", row.get("person_id"), exc)
        return _empty_reading(row)

    n_strong = sum(1 for c in reading.bhava_claims.values() if c.verdict_label == "strong")
    n_afflicted = sum(1 for c in reading.bhava_claims.values() if c.verdict_label == "afflicted")
    result: dict[str, Any] = {
        "person_id": chart.person_id,
        "corpus": row.get("corpus"),
        "name": row.get("name"),
        "asc_sign": reading.asc_sign,
        "asc_lagna_lord": reading.asc_lagna_lord,
        "yogakaraka_planets": list(reading.yogakarakas),
        "badhakesh": reading.badhakesh,
        "strongest_planet": reading.strongest_planet,
        "weakest_planet": reading.weakest_planet,
        "n_active_yogas": len(reading.active_yogas),
        "n_strong_bhavas": n_strong,
        "n_afflicted_bhavas": n_afflicted,
        "active_yoga_names": [y.name for y in reading.active_yogas],
        "active_yoga_refs": [y.reference for y in reading.active_yogas],
        "active_yoga_intensities": [float(y.intensity) for y in reading.active_yogas],
    }
    for b in range(1, 13):
        claim = reading.bhava_claims[b]
        result[f"b{b}_label"] = claim.verdict_label
        result[f"b{b}_composite"] = round(claim.composite_score, 3)
        result[f"b{b}_confirming_yogas"] = list(claim.confirming_yogas)
        result[f"b{b}_afflicting_yogas"] = list(claim.afflicting_yogas)
    return result


def _empty_reading(row: dict[str, Any]) -> dict[str, Any]:
    """Stub row when chart/composer fails — preserves person_id and corpus."""
    out: dict[str, Any] = {
        "person_id": row.get("person_id"),
        "corpus": row.get("corpus"),
        "name": row.get("name"),
        "asc_sign": pd.NA,
        "asc_lagna_lord": None,
        "yogakaraka_planets": [],
        "badhakesh": None,
        "strongest_planet": None,
        "weakest_planet": None,
        "n_active_yogas": 0,
        "n_strong_bhavas": 0,
        "n_afflicted_bhavas": 0,
        "active_yoga_names": [],
        "active_yoga_refs": [],
        "active_yoga_intensities": [],
    }
    for b in range(1, 13):
        out[f"b{b}_label"] = None
        out[f"b{b}_composite"] = pd.NA
        out[f"b{b}_confirming_yogas"] = []
        out[f"b{b}_afflicting_yogas"] = []
    return out


def build_readings(
    dossier: pd.DataFrame, workers: int = 1,
) -> pd.DataFrame:
    """Materialise readings for every row of ``dossier``."""
    records = dossier.to_dict(orient="records")
    if workers > 1:
        with mp.Pool(workers) as pool:
            results = list(pool.imap_unordered(
                _row_to_reading_dict, records, chunksize=128,
            ))
    else:
        results = [_row_to_reading_dict(r) for r in records]
    logger.info(
        "Built %d readings (%d input rows, %d skipped)",
        sum(1 for r in results if r["asc_sign"] is not pd.NA),
        len(records),
        sum(1 for r in results if r["asc_sign"] is pd.NA),
    )
    return pd.DataFrame(results)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--output", type=str, default="readings.parquet",
        help="Output parquet filename (under data-dir).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    dossier = pd.read_parquet(args.data_dir / "person_dossier.parquet")
    logger.info("Loaded %d dossier rows", len(dossier))
    if args.limit is not None:
        dossier = dossier.head(args.limit)

    start = time.time()
    result = build_readings(dossier, workers=args.workers)
    elapsed = time.time() - start
    rate = len(result) / elapsed if elapsed else 0
    logger.info(
        "Built %d readings in %.1fs (%.1f rows/sec)",
        len(result), elapsed, rate,
    )

    out_path = args.data_dir / args.output
    result.to_parquet(out_path, index=False)
    logger.info(
        "Wrote %d rows x %d cols to %s",
        len(result), len(result.columns), out_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
