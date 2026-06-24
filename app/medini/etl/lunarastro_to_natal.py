"""Phase-3C-take-2 ETL step 1: lunarastro CSV → natal-features parquet.

Reads ``kundlis.csv`` from the lunarastro scraper, cleans every row, runs
each through ``compute_chart_features`` in a multiprocessing pool, and
writes a parquet that the downstream screening-cohort builder can
consume.

Key differences from ``databank_etl.py``:

* **Mixed coord formats**: lunarastro mixes ``"9.9876° E"`` (degree
  symbol + cardinal) with bare decimals (``"-118.25"``). The parser
  handles both.

* **Wrong timezone field**: lunarastro's ``time_zone`` column is always
  ``"-05:30:00 hrs"`` (IST) regardless of birth city. We IGNORE that
  field and back-compute the true timezone from
  ``(latitude, longitude, date)`` via ``timezonefinder`` +
  ``zoneinfo``. This adds the historical-DST handling that Einstein in
  Germany needs (CET, not IST).

* **Birth-time confidence score**: 22.7% of rows have ``HH:00:00`` times
  and 2.6% have an explicit "not confirmed" marker in the description.
  We emit ``birth_time_confidence`` in ``[0, 1]`` so the downstream
  cohort builder can filter or weight by confidence.

* **Year filter**: 1700-2030 (drops the malformed ``year 0194 / 7042``
  outliers).

* **Tag passthrough**: free-form ``tags`` + ``category`` + ``description``
  are kept on the row so the cohort builder can map them to event
  classes.

Output schema: one row per lunarastro kundli (after filtering), with
all 535+ chart features plus the cleaned ``name``, ``name_norm``,
``date_of_birth``, ``birth_time``, ``birth_jd``, ``latitude``,
``longitude``, ``tz_offset_used``, ``tz_name_used``,
``birth_time_confidence``, ``category``, ``tags``, ``description``,
``source_url``, ``birth_year``, ``birth_decade``.

Usage:
    python -m app.medini.etl.lunarastro_to_natal \\
        --input  "C:/Users/S.C.C/Downloads/Astro_Data 2/Astro_Data/output/kundlis.csv" \\
        --output app/medini/data/lunarastro_natal.parquet \\
        [--workers N] [--limit N]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import multiprocessing as mp
import re
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import swisseph as swe
from timezonefinder import TimezoneFinder

from app.medini.etl.feature_engineering import compute_chart_features
from app.medini.etl.lahiri_worker import init_worker

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Constants                                                                    #
# --------------------------------------------------------------------------- #

# Year-range filter — drops the 0194 / 7042 typos and obvious data-entry junk.
_MIN_YEAR = 1700
_MAX_YEAR = 2030

# Suspicious times that are almost certainly placeholder rather than real
# birth times. Drops birth-time confidence to ~0.2 when one of these matches.
_SUSPICIOUS_TIMES: frozenset[str] = frozenset({
    "12:00:00", "00:00:00", "06:00:00", "18:00:00", "09:00:00", "15:00:00",
})

# Description text patterns that explicitly say the birth time is unknown
# or unconfirmed. When matched we drop confidence to 0.0.
_TIME_NOT_CONFIRMED_RE = re.compile(
    r"kindly update|not confirm|approximat|tentative|estimated|unknown time",
    re.IGNORECASE,
)

# Coord parsers — the lunarastro corpus mixes "9.9876° E" with bare decimals.
_COORD_CARDINAL_RE = re.compile(
    r"^\s*([+-]?\d+(?:\.\d+)?)\s*[^\d\sEWNSewns]*\s*([EWNSewns])\s*$"
)
_COORD_DECIMAL_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*$")

# Date parser — lunarastro uses "DD:MM:YYYY".
_DATE_RE = re.compile(r"^\s*(\d{1,2})\s*[:/-]\s*(\d{1,2})\s*[:/-]\s*(\d{2,4})\s*$")

# Time parser — lunarastro uses "HH:MM:SS".
_TIME_RE = re.compile(r"^\s*(\d{1,2})\s*:\s*(\d{1,2})\s*:\s*(\d{1,2})\s*$")


# --------------------------------------------------------------------------- #
# Parsers                                                                      #
# --------------------------------------------------------------------------- #

def _parse_coord(value: str, *, axis: str) -> float | None:
    """Parse a lunarastro coord string to signed decimal degrees.

    ``axis`` is 'lat' or 'lon' so the cardinal letter (E/W vs N/S) is
    validated. Returns ``None`` for unparseable / out-of-range values.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    m = _COORD_CARDINAL_RE.match(s)
    if m:
        num = float(m.group(1))
        card = m.group(2).upper()
        if axis == "lat" and card in ("N", "S"):
            sign = 1.0 if card == "N" else -1.0
            result = sign * abs(num)
        elif axis == "lon" and card in ("E", "W"):
            sign = 1.0 if card == "E" else -1.0
            result = sign * abs(num)
        else:
            return None
    else:
        m = _COORD_DECIMAL_RE.match(s)
        if not m:
            return None
        result = float(m.group(1))

    if axis == "lat" and not (-90.0 <= result <= 90.0):
        return None
    if axis == "lon" and not (-180.0 <= result <= 180.0):
        return None
    return result


def _parse_date(value: str) -> dt.date | None:
    """Parse "DD:MM:YYYY" and return a ``date`` in the year window, else None."""
    if not value:
        return None
    m = _DATE_RE.match(str(value))
    if not m:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (_MIN_YEAR <= year <= _MAX_YEAR):
        return None
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def _parse_time(value: str) -> tuple[int, int, int] | None:
    """Parse "HH:MM:SS" into ``(h, m, s)`` ints, else None."""
    if not value:
        return None
    m = _TIME_RE.match(str(value))
    if not m:
        return None
    h, mn, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (0 <= h <= 23 and 0 <= mn <= 59 and 0 <= s <= 59):
        return None
    return h, mn, s


def _birth_time_confidence(time_str: str, description: str) -> float:
    """Confidence in ``[0, 1]`` that the birth time is real.

    * 0.0 — description carries an explicit "not confirmed" marker.
    * 0.2 — time matches a known placeholder like ``12:00:00``.
    * 1.0 — otherwise.
    """
    if description and _TIME_NOT_CONFIRMED_RE.search(description):
        return 0.0
    if time_str in _SUSPICIOUS_TIMES:
        return 0.2
    return 1.0


# --------------------------------------------------------------------------- #
# Timezone backcompute                                                         #
# --------------------------------------------------------------------------- #

# One TimezoneFinder per worker process — created lazily on first call so
# the multiprocessing pickling doesn't transport the bulky index. The fork
# initializer (`init_worker`) sets up swisseph; this lazily sets up the tz.
_TF: TimezoneFinder | None = None


def _tz_finder() -> TimezoneFinder:
    global _TF
    if _TF is None:
        _TF = TimezoneFinder(in_memory=True)
    return _TF


def _true_tz_offset_hours(latitude: float, longitude: float, date: dt.date,
                          time_tuple: tuple[int, int, int]) -> tuple[float, str] | None:
    """Return ``(offset_in_hours, tz_name)`` from coords + naive local datetime.

    ``offset_in_hours`` is the local time's UTC offset on the given date —
    handles DST and historical timezone changes via ``zoneinfo``.

    Returns ``None`` if no timezone can be resolved (coords over open
    ocean, or zoneinfo lookup failure).
    """
    tz_name = _tz_finder().timezone_at(lat=latitude, lng=longitude)
    if not tz_name:
        return None
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        return None
    h, mn, s = time_tuple
    naive = dt.datetime(date.year, date.month, date.day, h, mn, s)
    try:
        offset = naive.replace(tzinfo=tz).utcoffset()
    except Exception:
        return None
    if offset is None:
        return None
    return offset.total_seconds() / 3600.0, tz_name


# --------------------------------------------------------------------------- #
# Row-level worker                                                             #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class _CleanRow:
    """The post-parse row that goes into the chart-features computation."""
    name: str
    date: dt.date
    time_tuple: tuple[int, int, int]
    latitude: float
    longitude: float
    tz_offset_hours: float
    tz_name: str
    birth_time_confidence: float
    # Passthrough metadata for the cohort builder
    raw_id: str
    raw_time_string: str
    category: str
    tags: str
    description: str
    source_url: str
    gender: str


def _clean_row(row: dict[str, str]) -> _CleanRow | None:
    """Apply all parsers + filters. Returns ``None`` if any required field fails."""
    date = _parse_date(row.get("date_of_birth", ""))
    if date is None:
        return None

    raw_time = (row.get("time") or "").strip()
    time_tuple = _parse_time(raw_time)
    if time_tuple is None:
        return None

    latitude = _parse_coord(row.get("latitude", ""), axis="lat")
    longitude = _parse_coord(row.get("longitude", ""), axis="lon")
    if latitude is None or longitude is None:
        return None

    tz_result = _true_tz_offset_hours(latitude, longitude, date, time_tuple)
    if tz_result is None:
        return None
    tz_offset_hours, tz_name = tz_result

    confidence = _birth_time_confidence(raw_time, row.get("description", "") or "")

    return _CleanRow(
        name=(row.get("name") or "").strip(),
        date=date,
        time_tuple=time_tuple,
        latitude=latitude,
        longitude=longitude,
        tz_offset_hours=tz_offset_hours,
        tz_name=tz_name,
        birth_time_confidence=confidence,
        raw_id=str(row.get("id") or ""),
        raw_time_string=raw_time,
        category=(row.get("category") or "").strip(),
        tags=(row.get("tags") or "").strip(),
        description=(row.get("description") or "").strip(),
        source_url=(row.get("source_url") or "").strip(),
        gender=(row.get("gender") or "").strip(),
    )


def _process_row(row: dict[str, str]) -> dict[str, Any] | None:
    """Worker entrypoint: raw csv dict in, feature dict out (or None)."""
    try:
        clean = _clean_row(row)
        if clean is None:
            return None

        h, mn, s = clean.time_tuple
        decimal_hour_local = h + mn / 60.0 + s / 3600.0
        decimal_hour_ut = decimal_hour_local - clean.tz_offset_hours
        jd = swe.julday(clean.date.year, clean.date.month, clean.date.day,
                        decimal_hour_ut, swe.GREG_CAL)

        features = compute_chart_features(jd, clean.latitude, clean.longitude)

        # Attach passthrough metadata so the cohort builder can derive
        # event labels + birth-decade stratification.
        features["lunarastro_id"] = clean.raw_id
        features["name"] = clean.name
        features["name_norm"] = clean.name.lower()
        features["date_of_birth"] = clean.date.isoformat()
        features["birth_time"] = clean.raw_time_string
        features["birth_jd"] = jd
        features["birth_year"] = clean.date.year
        features["birth_decade"] = (clean.date.year // 10) * 10
        features["latitude"] = clean.latitude
        features["longitude"] = clean.longitude
        features["tz_offset_used"] = clean.tz_offset_hours
        features["tz_name_used"] = clean.tz_name
        features["birth_time_confidence"] = clean.birth_time_confidence
        features["category"] = clean.category
        features["tags"] = clean.tags
        features["description"] = clean.description
        features["source_url"] = clean.source_url
        features["gender"] = clean.gender
        return features
    except Exception:
        logger.warning(
            "row failed (id=%s name=%s): %s",
            row.get("id", "?"), row.get("name", "?"),
            traceback.format_exc(limit=2),
        )
        return None


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run_etl(
    input_csv: Path,
    output_parquet: Path,
    *,
    n_workers: int | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    """Top-level entrypoint. Loads, cleans, computes, writes."""
    with input_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    input_count = len(rows)
    if limit is not None:
        rows = rows[:limit]
    logger.info("loaded %d rows from %s (limit=%s)", len(rows), input_csv, limit)

    n_workers = n_workers or max(1, mp.cpu_count() - 1)
    logger.info("computing features across %d worker process(es)...", n_workers)

    # The lahiri init_worker sets up swisseph state per-worker. We do tz
    # finder + zoneinfo lazily in each worker; no extra init needed.
    if n_workers == 1:
        # Inline path makes debugging easier (no pickling).
        init_worker()
        results = [_process_row(r) for r in rows]
    else:
        with mp.Pool(processes=n_workers, initializer=init_worker) as pool:
            results = pool.map(_process_row, rows)

    succeeded = [r for r in results if r is not None]
    failed = len(results) - len(succeeded)
    logger.info("succeeded=%d, failed=%d", len(succeeded), failed)

    if not succeeded:
        raise RuntimeError("all rows failed feature extraction")

    df = pd.DataFrame(succeeded)
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_parquet, engine="pyarrow", index=False)
    logger.info("wrote %s (%d rows, %d columns)", output_parquet, len(df), len(df.columns))

    return {
        "input_count": input_count,
        "processed": len(rows),
        "succeeded": len(succeeded),
        "failed": failed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.lunarastro_to_natal",
        description="Compute natal features for every lunarastro kundli row.",
    )
    parser.add_argument(
        "--input", type=Path,
        default=Path(
            r"C:/Users/S.C.C/Downloads/Astro_Data 2/Astro_Data/output/kundlis.csv"
        ),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("app/medini/data/lunarastro_natal.parquet"),
    )
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not args.input.exists():
        print(f"ERROR input not found: {args.input}", file=sys.stderr)
        return 2

    stats = run_etl(
        args.input, args.output,
        n_workers=args.workers, limit=args.limit,
    )
    print(
        f"ETL complete: input={stats['input_count']}, processed={stats['processed']}, "
        f"succeeded={stats['succeeded']}, failed={stats['failed']}, "
        f"output={args.output}"
    )
    return 0 if stats["succeeded"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
