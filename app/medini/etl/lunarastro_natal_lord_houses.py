"""Derive ``natal_lord_houses`` parquet from existing ``lunarastro_natal``.

The Round-9 doctrine scorer expects a row-per-person parquet with columns:
  name_norm, asc_sign, sign_<planet>, occ_<planet>, rules_<planet>,
  aspects_<planet> (for each of Sun..Ketu).

The Astro-Databank pipeline computes these by re-running the ephemeris
from raw birth data (see ``app/medini/etl/build_natal_lord_houses.py``).
For the lunarastro corpus we ALREADY have the ephemeris-derived chart
cached at ``app/medini/data/lunarastro_natal.parquet`` (with lon_<planet>
and lagna_sign), so this script just **derives** sign/rules/aspects/occ
without re-running swisseph. Two orders of magnitude faster than
re-running the full ETL.

Pure derivation — no IO beyond parquet read/write.

Usage:
    python -m app.medini.etl.lunarastro_natal_lord_houses
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from app.medini.etl.build_natal_lord_houses import (
    house_occupied_by,
    houses_aspected_by,
    houses_ruled_by,
)

logger = logging.getLogger(__name__)

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu")


def _sign_from_longitude(lon: float) -> int:
    """Sidereal longitude (0-360) -> 1-indexed sign (1-12). Tolerates NaN."""
    if pd.isna(lon):
        return 0
    return int(lon // 30) + 1


def _row_to_lord_houses(row: pd.Series) -> dict:
    """One lunarastro_natal row -> one natal_lord_houses dict."""
    name = row.get("name_norm")
    asc_sign = row.get("lagna_sign")
    if pd.isna(asc_sign):
        return {"name_norm": name, "asc_sign": None}
    asc_sign = int(asc_sign)
    out = {"name_norm": name, "asc_sign": asc_sign}
    for planet in _PLANETS:
        lon = row.get(f"lon_{planet.lower()}")
        sign = _sign_from_longitude(lon)
        out[f"sign_{planet.lower()}"] = sign
        if sign == 0:
            out[f"occ_{planet.lower()}"] = -1
            out[f"rules_{planet.lower()}"] = []
            out[f"aspects_{planet.lower()}"] = []
            continue
        out[f"occ_{planet.lower()}"] = house_occupied_by(sign, asc_sign)
        out[f"rules_{planet.lower()}"] = houses_ruled_by(planet, asc_sign)
        out[f"aspects_{planet.lower()}"] = houses_aspected_by(planet, sign, asc_sign)
    return out


def derive(natal_path: Path) -> pd.DataFrame:
    """Read lunarastro_natal, derive natal_lord_houses per row."""
    natal_df = pd.read_parquet(natal_path)
    logger.info("loaded lunarastro_natal: rows=%d cols=%d",
                len(natal_df), len(natal_df.columns))
    # De-dup on (name_norm, birth_jd) — the scout report flagged ~3k duplicates.
    # Keep the FIRST occurrence per (name_norm, birth_jd) so each person gets
    # exactly one chart row in the output.
    if "birth_jd" in natal_df.columns:
        before = len(natal_df)
        natal_df = natal_df.drop_duplicates(subset=["name_norm", "birth_jd"])
        logger.info("after dedup on (name_norm, birth_jd): rows=%d (-%d)",
                    len(natal_df), before - len(natal_df))
    out_rows = [_row_to_lord_houses(row) for _, row in natal_df.iterrows()]
    out_df = pd.DataFrame(out_rows)
    # Cast list columns explicitly; pyarrow needs consistent inner types
    for planet in _PLANETS:
        for col in (f"rules_{planet.lower()}", f"aspects_{planet.lower()}"):
            out_df[col] = out_df[col].apply(
                lambda x: list(x) if isinstance(x, (list, tuple)) else []
            )
    return out_df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.lunarastro_natal_lord_houses",
        description="Derive natal_lord_houses from lunarastro_natal (cheap).",
    )
    parser.add_argument(
        "--input", type=Path,
        default=Path("app/medini/data/lunarastro_natal.parquet"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("app/medini/data/lunarastro_natal_lord_houses.parquet"),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    out_df = derive(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(args.output, index=False)
    print(f"wrote {args.output}: rows={len(out_df):,} cols={len(out_df.columns)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
