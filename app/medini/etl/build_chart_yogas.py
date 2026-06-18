"""Detect classical yogas per chart → chart_yogas.parquet.

Yogas (planetary combinations) are the heart of BPHS prediction and the crown
jewel for the truth-layer: "does Gajakesari → fame actually hold at population
scale?" becomes a one-line query once yogas are materialized.

Reuses ``app.core.yogas.detect_yogas`` (dict-based, no Chart object needed — it
only reads each graha's `sign` + the ascendant `sign`, both present in
charts.parquet). Covers the five Pañca-Mahāpuruṣa yogas (Ruchaka/Bhadra/Hamsa/
Malavya/Sasa), Gajakesari, and Budha-Āditya.

Output schema (chart_yogas.parquet):
  person_id  TEXT  FK -> persons
  yoga       TEXT  yoga name (e.g. "Gajakesari")
  yoga_type  TEXT  "Pancha Mahapurusha" | "Sambandha" | ...
  planets    TEXT  comma-separated grahas forming it

CLI:
    python -m app.medini.etl.build_chart_yogas
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import pandas as pd

from app.core.yogas import detect_yogas

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
_GRAHAS: Final = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


def _row_yogas(row: pd.Series) -> list[dict]:
    """All yogas for one charts.parquet row."""
    asc_sign = row.get("asc_sign")
    if pd.isna(asc_sign):
        return []
    d1 = {
        g: {"sign": int(row[f"{g.lower()}_sign"])}
        for g in _GRAHAS
        if not pd.isna(row.get(f"{g.lower()}_sign"))
    }
    try:
        yogas = detect_yogas(d1, {"sign": int(asc_sign)})
    except (ValueError, KeyError):
        return []
    return [
        {
            "person_id": row["person_id"],
            "yoga": y["name"],
            "yoga_type": y["type"],
            "planets": ",".join(y["planets_involved"]),
        }
        for y in yogas
    ]


def build_chart_yogas(charts: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, r in charts.iterrows():
        rows.extend(_row_yogas(r))
    return pd.DataFrame(rows, columns=["person_id", "yoga", "yoga_type", "planets"])


def build(data_dir: Path = DEFAULT_DATA_DIR) -> dict:
    charts = pd.read_parquet(data_dir / "charts.parquet")
    out = build_chart_yogas(charts)
    out.to_parquet(data_dir / "chart_yogas.parquet", index=False)
    stats = {
        "charts": len(charts),
        "yoga_rows": len(out),
        "persons_with_yoga": out["person_id"].nunique() if len(out) else 0,
        "by_yoga": out["yoga"].value_counts().to_dict() if len(out) else {},
    }
    logger.info("wrote chart_yogas.parquet (%d yogas across %d persons)",
                len(out), stats["persons_with_yoga"])
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.medini.etl.build_chart_yogas")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    print(build(args.data_dir))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
