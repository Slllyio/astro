"""Compute per-(person, planet) house relationships from natal charts.

For each person in the dasha corpus, computes:
  - houses_ruled[planet]  — list of 1..12 houses whose sign is owned by `planet`
  - house_occupied[planet] — the house (1..12) the planet sits in
  - houses_aspected[planet] — set of 1..12 houses the planet's drishti reaches

These are then joinable to the dasha corpus per md/ad/pd lord, enabling the
classical "MD lord rules X, occupies Y, aspects Z" reasoning that bare lord
identity cannot capture.

Why a separate ETL: the dasha corpus is huge (6.17M rows at PD granularity),
so we compute natal per person ONCE and join later.

Output schema (one row per person):
  name_norm, asc_sign,
  rules_sun [list[int]], occ_sun [int], aspects_sun [list[int]],
  ... (one triplet per planet)

Usage:
    python -m app.medini.etl.build_natal_lord_houses \\
        --merged data/astro_databank/merged_all.csv \\
        --output app/medini/data/natal_lord_houses.parquet
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import multiprocessing as mp
import sys
import traceback
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.avastha import _DRISHTI_HOUSES
from app.core.dignity import SIGN_RULERS
from app.core.ephemeris_engine import (
    PLANETS, calculate_ascendant, calculate_d1_position, calculate_ketu_d1,
    calculate_jd,
)
from app.medini.etl.lahiri_worker import init_worker

logger = logging.getLogger(__name__)

# Order kept in lockstep with the rest of the project so column names align.
_PLANETS_CANONICAL: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


# --------------------------------------------------------------------------- #
# Pure house-relationship helpers                                              #
# --------------------------------------------------------------------------- #

def houses_ruled_by(planet: str, asc_sign: int) -> list[int]:
    """Return 1-indexed houses whose sign is owned by ``planet`` for this lagna.

    Pure function of (planet, asc_sign). For Mercury/Mars/Venus etc., a planet
    typically rules 2 houses (its 2 sign-domiciles); the Sun/Moon rule 1 each.
    """
    out: list[int] = []
    for h in range(1, 13):
        sign = ((asc_sign - 1 + h - 1) % 12) + 1
        if SIGN_RULERS[sign] == planet:
            out.append(h)
    return out


def house_occupied_by(planet_sign: int, asc_sign: int) -> int:
    """Which 1-indexed house does the planet sit in?  Whole-sign convention."""
    return ((planet_sign - asc_sign) % 12) + 1


def houses_aspected_by(planet: str, planet_sign: int, asc_sign: int) -> list[int]:
    """Houses the planet's drishti reaches (whole-sign aspect convention).

    Excludes co-residency: drishti is glance-aspect, not sitting-in.
    """
    distances = _DRISHTI_HOUSES.get(planet, frozenset())
    occupied = house_occupied_by(planet_sign, asc_sign)
    out: list[int] = []
    for d in distances:
        target_house = ((occupied - 1 + d - 1) % 12) + 1
        out.append(target_house)
    return sorted(out)


# --------------------------------------------------------------------------- #
# Per-person worker                                                            #
# --------------------------------------------------------------------------- #

def _row_to_chart(row: dict[str, str]) -> tuple[int, dict[str, int]] | None:
    """Return (asc_sign, {planet: sign}) for a merged_all row, or None."""
    try:
        date = dt.date.fromisoformat(row["date_of_birth"])
        h, m, s = map(int, row["time_of_birth"].split(":"))
        tz = float(row["tz_offset"])
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
    except (ValueError, AttributeError, KeyError, TypeError):
        return None
    decimal_hour = h + m / 60.0 + s / 3600.0
    jd = calculate_jd(date.year, date.month, date.day, decimal_hour, tz)
    asc = calculate_ascendant(jd, latitude, longitude)
    chart: dict[str, int] = {}
    for name, pid in PLANETS.items():
        pos = calculate_d1_position(jd, pid)
        chart[name] = pos["sign"]
    # Compute Ketu from Rahu
    rahu_pos = calculate_d1_position(jd, PLANETS["Rahu"])
    ketu_d1 = calculate_ketu_d1(rahu_pos)
    chart["Ketu"] = ketu_d1["sign"]
    return asc["sign"], chart


def _process_person(row: dict[str, str]) -> dict[str, Any] | None:
    try:
        parsed = _row_to_chart(row)
        if parsed is None:
            return None
        asc_sign, planet_signs = parsed
        out: dict[str, Any] = {
            "name": row["name"].strip(),
            "name_norm": row["name"].strip().lower(),
            "asc_sign": asc_sign,
        }
        for planet in _PLANETS_CANONICAL:
            psign = planet_signs.get(planet)
            if psign is None:
                continue
            out[f"sign_{planet.lower()}"] = psign
            out[f"rules_{planet.lower()}"] = houses_ruled_by(planet, asc_sign)
            out[f"occ_{planet.lower()}"] = house_occupied_by(psign, asc_sign)
            out[f"aspects_{planet.lower()}"] = houses_aspected_by(planet, psign, asc_sign)
        return out
    except Exception:
        logger.warning(
            "person failed (name=%s): %s",
            row.get("name", "?"), traceback.format_exc(limit=2),
        )
        return None


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run_etl(
    merged_path: Path,
    output_parquet: Path,
    *,
    n_workers: int | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    merged = pd.read_csv(merged_path, low_memory=False)
    merged = merged.dropna(
        subset=["date_of_birth", "time_of_birth", "tz_offset", "latitude",
                "longitude", "name"]
    ).copy()
    merged["name"] = merged["name"].astype(str).str.strip()
    merged = merged.drop_duplicates(subset=["name"], keep="first")
    if limit is not None:
        merged = merged.iloc[:limit]
    rows = merged.to_dict("records")
    logger.info("processing %d people", len(rows))

    n_workers = n_workers or max(1, mp.cpu_count() - 1)
    if n_workers == 1:
        init_worker()
        results = [_process_person(r) for r in rows]
    else:
        with mp.Pool(processes=n_workers, initializer=init_worker) as pool:
            results = pool.map(_process_person, rows)

    succeeded = [r for r in results if r is not None]
    failed = len(results) - len(succeeded)
    logger.info("succeeded=%d failed=%d", len(succeeded), failed)
    if not succeeded:
        raise RuntimeError("no rows succeeded")

    df = pd.DataFrame(succeeded)
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, engine="pyarrow", index=False)
    logger.info("wrote %s rows=%d cols=%d", output_parquet, len(df), df.shape[1])
    return {"input": len(rows), "succeeded": len(succeeded), "failed": failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.build_natal_lord_houses",
        description="Per-person natal lord-house relationships (rule/occupy/aspect).",
    )
    parser.add_argument(
        "--merged", type=Path,
        default=Path("data/astro_databank/merged_all.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("app/medini/data/natal_lord_houses.parquet"),
    )
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = run_etl(
        args.merged, args.output,
        n_workers=args.workers, limit=args.limit,
    )
    print(f"ETL complete: input={stats['input']} succeeded={stats['succeeded']} "
          f"failed={stats['failed']} -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
