"""Materialize the pre-declared feature banks from an acquired corpus.

Three banks compete in the tournament, plus the chartless twin every one of them
must beat:

* ``chartless``   birth era + geography only. This is the bar, not a control to
  be waved through — lat/lon/date alone reach AUC 0.744 on marriage in prior
  work, so any chart bank's real score is its delta over this.
* ``western``     tropical positions, houses, angles, aspect counts.
* ``raw_astronomy``  the same sky described without astrological interpretation:
  ecliptic latitude, distance, speed. If a chart bank beats this, the *encoding*
  is doing work; if it does not, only the astronomy is.

Longitudes enter as ``sin``/``cos`` pairs rather than raw degrees. A model given
raw degrees sees 359° and 1° as maximally distant when they are 2° apart, which
would let it learn the cusp rather than the sky.

Deliberately excluded: the Vedic-timing bank, which needs dasha windows this
corpus does not carry. Declaring it and shipping it empty would be worse than
saying so.

Usage:
    python -m app.empirical.tournament.build_feature_banks \
        --corpus data/empirical/gauquelin.csv \
        --out data/empirical/feature_banks.parquet
"""

from __future__ import annotations

import argparse
import csv
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable, Sequence

import pandas as pd

from app.empirical.western.aspects import DEFAULT_ORBS, PTOLEMAIC, find_aspects
from app.empirical.western.houses import house_cusps, house_of
from app.empirical.western.tropical import (
    DEFAULT_BODIES,
    Position,
    julian_day_ut,
    tropical_positions,
)

logger = logging.getLogger(__name__)

__all__ = ["BANKS", "ChartRow", "build_banks", "bank_columns"]

#: Which columns belong to which pre-declared bank. Written out alongside the
#: matrix so a scoring run cannot quietly mix banks.
BANKS: Final[tuple[str, ...]] = ("chartless", "western", "raw_astronomy")

_HOUSE_SYSTEM: Final[str] = "placidus"


@dataclass(frozen=True, slots=True)
class ChartRow:
    """One person's inputs, straight from the acquired corpus."""

    person_id: str
    year: int
    month: int
    day: int
    ut_hour: float
    latitude: float
    longitude: float
    label: str
    time_tier: str
    data_quality: str


def _read_corpus(path: str | Path) -> list[ChartRow]:
    rows: list[ChartRow] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                ChartRow(
                    person_id=raw["source_id"],
                    year=int(raw["birth_year"]),
                    month=int(raw["birth_month"]),
                    day=int(raw["birth_day"]),
                    ut_hour=float(raw["birth_ut_hour"]),
                    latitude=float(raw["latitude"]),
                    longitude=float(raw["longitude"]),
                    label=raw["profession"],
                    time_tier=raw["time_tier"],
                    data_quality=raw["data_quality"],
                )
            )
    return rows


_CUMULATIVE_DAYS: Final[tuple[int, ...]] = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def _day_of_year(year: int, month: int, day: int) -> int:
    """Approximate day-of-year, tolerant of the source's impossible dates."""
    if not 1 <= month <= 12:
        return 1
    leap = (year % 4 == 0 and year % 100 != 0) or year % 400 == 0
    return _CUMULATIVE_DAYS[month - 1] + day + (1 if leap and month > 2 else 0)


def _chartless_features(row: ChartRow) -> dict[str, float]:
    """Era + geography. Everything a chart model must beat."""
    # Computed without a strict date type: the corpus legitimately contains
    # rows flagged invalid_date (CURA publishes 1869-02-29 and 1888-06-31), and
    # the builder must produce a row for them so the flag stays visible
    # downstream rather than the record vanishing from the matrix.
    day_of_year = _day_of_year(row.year, row.month, row.day)
    return {
        "cl_birth_year": float(row.year),
        # Full date precision, not just the year. The slow planets (Uranus 84y,
        # Neptune 165y, Pluto 248y) encode the birth epoch to within days, so a
        # chartless twin holding only the integer year leaves sub-year date
        # precision uncontrolled — and any chart bank would then "beat" it merely
        # by knowing the date better. This is the confound Round 11's
        # disambiguation experiment was built to test; the baseline has to carry
        # the date to be a fair bar at all.
        "cl_birth_decimal_year": float(row.year) + day_of_year / 365.25,
        "cl_latitude": row.latitude,
        "cl_longitude": row.longitude,
        # Season enters as sin/cos too: December and January are adjacent.
        "cl_season_sin": math.sin(2 * math.pi * day_of_year / 365.25),
        "cl_season_cos": math.cos(2 * math.pi * day_of_year / 365.25),
    }


def _western_features(
    positions: dict[str, Position],
    jd: float,
    row: ChartRow,
) -> dict[str, float]:
    """Tropical placements, houses, angles, aspect counts."""
    out: dict[str, float] = {}
    for name, pos in positions.items():
        radians = math.radians(pos.longitude)
        out[f"w_{name}_lon_sin"] = math.sin(radians)
        out[f"w_{name}_lon_cos"] = math.cos(radians)
        out[f"w_{name}_retro"] = 1.0 if pos.is_retrograde else 0.0

    cusps = house_cusps(jd, row.latitude, row.longitude, system=_HOUSE_SYSTEM)
    if cusps is None:
        # Undefined at this latitude. NaN, never a substituted value — the
        # tournament must be able to see the gap.
        for name in positions:
            out[f"w_{name}_house"] = float("nan")
        out["w_asc_sin"] = out["w_asc_cos"] = float("nan")
        out["w_mc_sin"] = out["w_mc_cos"] = float("nan")
    else:
        for name, pos in positions.items():
            out[f"w_{name}_house"] = float(house_of(pos.longitude, cusps.cusps))
        out["w_asc_sin"] = math.sin(math.radians(cusps.ascendant))
        out["w_asc_cos"] = math.cos(math.radians(cusps.ascendant))
        out["w_mc_sin"] = math.sin(math.radians(cusps.midheaven))
        out["w_mc_cos"] = math.cos(math.radians(cusps.midheaven))

    hits = find_aspects(positions, orbs=DEFAULT_ORBS, aspects=PTOLEMAIC)
    for adef in PTOLEMAIC:
        out[f"w_n_{adef.name}"] = float(sum(1 for h in hits if h.aspect == adef.name))
    out["w_n_applying"] = float(sum(1 for h in hits if h.applying is True))
    return out


def _raw_astronomy_features(positions: dict[str, Position]) -> dict[str, float]:
    """The same sky, described without astrological interpretation."""
    out: dict[str, float] = {}
    for name, pos in positions.items():
        out[f"r_{name}_ecl_lat"] = pos.latitude
        out[f"r_{name}_distance_au"] = pos.distance_au
        out[f"r_{name}_speed"] = pos.speed_longitude
    return out


def build_banks(
    rows: Sequence[ChartRow],
    *,
    bodies: Iterable[str] = DEFAULT_BODIES,
    progress_every: int = 2000,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Compute every bank for every chart.

    Returns:
      ``(frame, columns_by_bank)``. The frame carries ``person_id``, ``label``,
      ``time_tier`` and ``data_quality`` alongside the features, so cohort
      filtering happens downstream rather than being baked in here.
    """
    bodies = tuple(bodies)
    records: list[dict[str, object]] = []
    undefined_houses = 0

    for i, row in enumerate(rows, 1):
        jd = julian_day_ut(row.year, row.month, row.day, row.ut_hour)
        positions = tropical_positions(jd, bodies)

        features: dict[str, object] = {
            "person_id": row.person_id,
            "label": row.label,
            "time_tier": row.time_tier,
            "data_quality": row.data_quality,
        }
        features.update(_chartless_features(row))
        western = _western_features(positions, jd, row)
        if math.isnan(western.get("w_asc_sin", 0.0)):
            undefined_houses += 1
        features.update(western)
        features.update(_raw_astronomy_features(positions))
        records.append(features)

        if progress_every and i % progress_every == 0:
            logger.info("  %d/%d charts", i, len(rows))

    frame = pd.DataFrame.from_records(records)
    columns_by_bank = {
        "chartless": [c for c in frame.columns if c.startswith("cl_")],
        "western": [c for c in frame.columns if c.startswith("w_")],
        "raw_astronomy": [c for c in frame.columns if c.startswith("r_")],
    }
    if undefined_houses:
        logger.warning(
            "%d charts had no defined %s houses (polar latitude) — features are NaN, not substituted",
            undefined_houses,
            _HOUSE_SYSTEM,
        )
    return frame, columns_by_bank


def bank_columns(frame: pd.DataFrame, bank: str) -> list[str]:
    """Columns belonging to one bank. Guards against silently mixing banks."""
    if bank not in BANKS:
        raise KeyError(f"unknown bank {bank!r}; expected one of {BANKS}")
    prefix = {"chartless": "cl_", "western": "w_", "raw_astronomy": "r_"}[bank]
    return [c for c in frame.columns if c.startswith(prefix)]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Build the tournament feature banks.")
    parser.add_argument("--corpus", required=True, help="acquired corpus CSV")
    parser.add_argument("--out", required=True, help="output parquet path")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    rows = _read_corpus(args.corpus)
    logger.info("read %d charts from %s", len(rows), args.corpus)

    frame, columns = build_banks(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)

    logger.info("wrote %s: %d rows x %d columns", out, len(frame), len(frame.columns))
    for bank, cols in columns.items():
        logger.info("  %-14s %3d features", bank, len(cols))
    logger.info("  labels: %s", dict(frame["label"].value_counts()))
    logger.info("  tier A rows: %d", int((frame["time_tier"] == "A").sum()))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
