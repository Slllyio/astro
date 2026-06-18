"""Compute Ṣaḍbala (six-fold strength) per graha → graha_strength.parquet.

Reuses ``app.core.shadbala.shadbala_total``, fed entirely from charts.parquet
(longitude / sign / house) plus the D9 sign computed via
``app.core.shodashavarga.compute_divisional_longitude``. Strength lets ML *weight*
a placement instead of treating every graha equally, and lets the product show
"strongest/weakest planet" per chart.

Note: charts.parquet carries no retrograde flag, so the Cheṣṭā/Dṛk components
(which need it) use the direct-motion default — consistent with the rest of the
Silver layer. The dominant Sthāna + Dig + Naisargika components are exact.

Output schema (graha_strength.parquet):
  person_id   TEXT  FK -> persons
  graha       TEXT  one of the 7 classical grahas (Rahu/Ketu excluded by tradition)
  shadbala_virupa  FLOAT  total six-fold strength (virupa)
  shadbala_rupa    FLOAT  virupa / 60
  sthana, dig, kala, cheshta, naisargika, drik  FLOAT  component breakdown
  rank        INT   1 = strongest graha in the chart

CLI:
    python -m app.medini.etl.build_graha_strength --workers 4
"""
from __future__ import annotations

import argparse
import logging
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Final

import pandas as pd

from app.core.shadbala import shadbala_total
from app.core.shodashavarga import compute_divisional_longitude

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
# Shadbala is computed for the 7 classical grahas; the nodes are excluded by
# tradition (they have no Sthana/Dig bala in the classical scheme).
_GRAHAS: Final = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_ALL: Final = _GRAHAS + ("Rahu", "Ketu")


def _person_strength_rows(args: tuple) -> list[dict[str, Any]]:
    person_id, row = args
    # Full chart dict (all 9) for drik/paksha context; strength only for the 7.
    chart = {
        g: {
            "longitude": float(row[f"{g.lower()}_lon"]),
            "sign": int(float(row[f"{g.lower()}_lon"]) // 30) + 1,
            "house": int(row[f"{g.lower()}_house"]),
            "is_retrograde": False,
        }
        for g in _ALL
        if not pd.isna(row.get(f"{g.lower()}_lon"))
    }
    out: list[dict[str, Any]] = []
    for g in _GRAHAS:
        if g not in chart:
            continue
        lon = chart[g]["longitude"]
        d1_sign = int(lon // 30) + 1
        d9_lon = compute_divisional_longitude(lon, 9)
        d9_sign = int(d9_lon // 30) + 1
        house = int(row[f"{g.lower()}_house"])
        try:
            b = shadbala_total(g, longitude=lon, d1_sign=d1_sign,
                               d9_sign=d9_sign, house=house, chart=chart)
        except Exception:  # noqa: BLE001 — defensive per-graha skip
            continue
        out.append({
            "person_id": person_id, "graha": g,
            "shadbala_virupa": round(b["total"], 3),
            "shadbala_rupa": round(b["total"] / 60.0, 4),
            "sthana": round(b["sthana"], 3), "dig": round(b["dig"], 3),
            "kala": round(b["kala"], 3), "cheshta": round(b["cheshta"], 3),
            "naisargika": round(b["naisargika"], 3), "drik": round(b["drik"], 3),
        })
    # Rank strongest -> weakest within the chart.
    out.sort(key=lambda r: r["shadbala_virupa"], reverse=True)
    for i, r in enumerate(out, start=1):
        r["rank"] = i
    return out


def build(data_dir: Path = DEFAULT_DATA_DIR, workers: int = 1, limit: int | None = None) -> dict:
    charts = pd.read_parquet(data_dir / "charts.parquet")
    if limit:
        charts = charts.head(limit)
    tasks = [(r["person_id"], r) for _, r in charts.iterrows()]

    rows: list[dict] = []
    if workers > 1:
        with Pool(workers) as pool:
            for chunk in pool.map(_person_strength_rows, tasks, chunksize=256):
                rows.extend(chunk)
    else:
        for t in tasks:
            rows.extend(_person_strength_rows(t))

    cols = ["person_id", "graha", "shadbala_virupa", "shadbala_rupa",
            "sthana", "dig", "kala", "cheshta", "naisargika", "drik", "rank"]
    out = pd.DataFrame(rows, columns=cols)
    out.to_parquet(data_dir / "graha_strength.parquet", index=False)
    logger.info("wrote graha_strength.parquet (%d rows, %d charts)",
                len(out), out["person_id"].nunique() if len(out) else 0)
    return {"charts": len(charts), "rows": len(out)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.medini.etl.build_graha_strength")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    print(build(args.data_dir, args.workers, args.limit))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
