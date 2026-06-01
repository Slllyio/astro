"""Build the divisional-charts table (Shodashavarga: D1 + 14 sub-vargas).

For every person with a chart, compute the per-varga per-planet placement
(sign, degree, house from varga Lagna, houses ruled in that varga).

## Output schema (divisional_charts.parquet)

  person_id       TEXT  (FK → persons)
  varga           TEXT  "D1_Rashi" | "D2_Hora" | ... | "D60_Shastiamsa"
  graha           TEXT  Sun..Ketu OR "Lagna" (the varga's own ascendant)
  longitude       FLOAT divisional sidereal longitude
  sign            INT   1..12
  degree_in_sign  FLOAT 0..30
  house           INT   1..12 from the varga's own Lagna
  houses_ruled    TEXT  comma-separated houses this planet rules in this varga
                        (empty for Rahu/Ketu/Lagna)
  is_retrograde   BOOL  (only meaningful for the 7 visible planets in D1)

## Scale

75,149 persons × 15 vargas × (9 planets + 1 Lagna) ≈ 11.3M rows.
Compressed parquet ≈ 100-150 MB.

Usage:
    python -m app.medini.etl.build_divisional_charts
    python -m app.medini.etl.build_divisional_charts --workers 6
"""
from __future__ import annotations

import argparse
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Final, Any

import pandas as pd

from app.core.shodashavarga import (
    SHODASHAVARGA_DIVISORS, SHODASHAVARGA_NAMES,
    compute_divisional_charts, compute_divisional_longitude,
)
from app.medini.ml.person_profile import (
    _GRAHAS, _SIGN_RULERS, _houses_ruled_by_planet,
)

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")


def _chart_row_to_d1_dict(row: pd.Series) -> dict:
    """Convert a charts.parquet row into the dict shape compute_divisional_charts expects."""
    return {
        graha: {
            "longitude": float(row[f"{graha.lower()}_lon"]),
            "is_retrograde": False,  # charts.parquet doesn't carry this; default False
        }
        for graha in _GRAHAS
    }


def _person_divisional_rows(args: tuple) -> list[dict[str, Any]]:
    """Compute one person's divisional-chart rows (D1 + 14 sub-vargas)."""
    person_id, asc_lon, d1_chart = args
    out: list[dict[str, Any]] = []

    # D1 (natal Rashi) — Lagna at asc_lon.
    d1_lagna_sign = int(asc_lon // 30) + 1
    out.append({
        "person_id": person_id,
        "varga": "D1_Rashi",
        "graha": "Lagna",
        "longitude": asc_lon,
        "sign": d1_lagna_sign,
        "degree_in_sign": asc_lon - (d1_lagna_sign - 1) * 30.0,
        "house": 1,
        "houses_ruled": "",
        "is_retrograde": False,
    })
    for graha in _GRAHAS:
        p = d1_chart[graha]
        sign = int(p["longitude"] // 30) + 1
        deg = p["longitude"] - (sign - 1) * 30.0
        house = ((sign - d1_lagna_sign) % 12) + 1
        houses = _houses_ruled_by_planet(graha, d1_lagna_sign)
        out.append({
            "person_id": person_id,
            "varga": "D1_Rashi",
            "graha": graha,
            "longitude": p["longitude"],
            "sign": sign,
            "degree_in_sign": deg,
            "house": house,
            "houses_ruled": ",".join(str(h) for h in houses),
            "is_retrograde": bool(p.get("is_retrograde", False)),
        })

    # All other vargas via compute_divisional_charts.
    all_v = compute_divisional_charts(d1_chart)
    for divisor in SHODASHAVARGA_DIVISORS:
        varga_name = SHODASHAVARGA_NAMES[divisor]
        # Varga Lagna.
        v_asc_lon = compute_divisional_longitude(asc_lon, divisor) % 360.0
        v_lagna_sign = int(v_asc_lon // 30) + 1
        out.append({
            "person_id": person_id,
            "varga": varga_name,
            "graha": "Lagna",
            "longitude": v_asc_lon,
            "sign": v_lagna_sign,
            "degree_in_sign": v_asc_lon - (v_lagna_sign - 1) * 30.0,
            "house": 1,
            "houses_ruled": "",
            "is_retrograde": False,
        })
        for graha in _GRAHAS:
            p = all_v[varga_name][graha]
            sign = p["sign"]
            deg = p["degree_in_sign"]
            house = ((sign - v_lagna_sign) % 12) + 1
            houses = _houses_ruled_by_planet(graha, v_lagna_sign)
            out.append({
                "person_id": person_id,
                "varga": varga_name,
                "graha": graha,
                "longitude": p["longitude"],
                "sign": sign,
                "degree_in_sign": deg,
                "house": house,
                "houses_ruled": ",".join(str(h) for h in houses),
                "is_retrograde": bool(p.get("is_retrograde", False)),
            })
    return out


def _worker(args: tuple) -> list[dict[str, Any]]:
    try:
        return _person_divisional_rows(args)
    except Exception as exc:  # noqa: BLE001
        person_id = args[0]
        logger.warning("Varga compute failed for %s: %s", person_id, exc)
        return []


def build_divisional_charts(
    charts: pd.DataFrame, workers: int = 1,
) -> pd.DataFrame:
    """Compute divisional charts for every row of charts.parquet."""
    inputs: list[tuple] = []
    for _, row in charts.iterrows():
        d1_chart = _chart_row_to_d1_dict(row)
        inputs.append((row["person_id"], float(row["asc_lon"]), d1_chart))

    if workers > 1:
        with mp.Pool(workers) as pool:
            chunks = list(pool.imap_unordered(_worker, inputs, chunksize=64))
    else:
        chunks = [_worker(t) for t in inputs]

    flat = [r for chunk in chunks for r in chunk]
    logger.info("Built %d divisional rows for %d persons (~%d rows/person)",
                len(flat), len(charts), len(flat) // max(1, len(charts)))
    return pd.DataFrame(flat)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    charts = pd.read_parquet(args.data_dir / "charts.parquet")
    if args.limit is not None:
        charts = charts.head(args.limit)
    logger.info("Loaded %d charts", len(charts))

    result = build_divisional_charts(charts, workers=args.workers)
    out_path = args.data_dir / "divisional_charts.parquet"
    result.to_parquet(out_path, index=False)
    logger.info("Wrote %d rows to %s", len(result), out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
