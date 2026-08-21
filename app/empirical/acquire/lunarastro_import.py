"""LunarAstro research-site importer — Phase 1 acquisition, third corpus.

A ~29.5k-row scrape of https://research.lunarastro.com/, supplied directly by
the project owner (not fetched by this module — there is no network path here,
only a local CSV parser). Its value: it is the only corpus in this repo that
carries BOTH a real clock time (Wikidata is tier C, no time at all) AND rich
outcome/vocation category tags per person (Gauquelin has one profession label;
this has up to dozens of category tags spanning vocation, life events, and
notable traits).

**Data-quality defects found by inspection, all flagged rather than silently
dropped or coerced** (the repo's standing rule — see `gauquelin_import.py`):

* **Placeholder identity rows.** 1,771 rows (6.0% of the raw file) carry
  ``date_of_birth == 1970-01-01`` — the Unix epoch, a conventional "no real
  date" default. 59% of those have a single-word name (vs. full names
  elsewhere), and several share that exact date across wildly different
  times/continents under generic first names ("Riko", "Kiyoshi") — the
  signature of placeholder or dummy site-user profiles, not notable people.
  Flagged ``epoch_placeholder``, never dropped: a downstream cohort can
  exclude them, but the shape of the defect stays visible.
* **Implausible/corrupted years.** A handful of rows carry a birth year past
  the plausible ceiling — e.g. "Albert Uderzo" listed as born 2027, when the
  real co-creator of *Asterix* was born 1927 (a 19xx -> 20xx digit-transposition
  pattern, not an unborn person). Flagged ``implausible_year:<year>``.
* **Placeholder clock times.** ``00:00:00``, ``23:59:00`` and ``12:00:00``
  each recur 3-4 orders of magnitude above the ~0.34 expected occurrences for
  a genuinely uniform second-of-day distribution over 29.5k rows — the
  fingerprints of "unknown time" defaults on this class of site. Rows
  carrying one of these are never minute-tiered as real: they are forced to
  time_tier ``C`` (no usable time) regardless of what the minute-frequency
  test alone would say.
* **Name is not an identity key.** Duplicate names include BOTH the same
  chart re-tagged under multiple site categories (safe to merge — 469 cases
  found, identical date/time/lat/lon) AND unrelated people or dummy rows that
  happen to share a name (must NOT merge — 1,044 cases found, conflicting
  data). Identity here is the chart fingerprint (date + time + place) alone,
  exactly the same choice ``gauquelin_import.natural_key`` makes and for the
  same reason.
* **No independent verification column.** ``rodden_rating`` — the standard
  astrological source-reliability scale — is present in the schema but empty
  on every row of this scrape. Time-tier honesty here rests entirely on the
  minute-frequency measurement (:func:`assign_time_tiers`), not on a
  publisher's own rating, and that limitation is real: report it as such.

Usage:
    python -m app.empirical.acquire.lunarastro_import \\
        --raw path/to/raw_lunarastro.csv --out data/empirical/lunarastro.csv
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import logging
from collections import Counter
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

__all__ = [
    "LunarAstroRecord",
    "natural_key",
    "parse_row",
    "assign_time_tiers",
    "import_all",
    "write_csv",
]

#: Clock-time strings that recur far above chance and match this class of
#: site's conventional "unknown time" defaults. Measured, not assumed: see the
#: module docstring for the observed counts.
_PLACEHOLDER_TIMES: Final[frozenset[str]] = frozenset({"00:00:00", "23:59:00", "12:00:00"})

#: The Unix epoch date, used across many systems as a "no real date" default.
_EPOCH_PLACEHOLDER_DATE: Final[str] = "1970-01-01"

#: Static cutoff, not computed at runtime (this module may be re-run years
#: from now against the same raw file; a `datetime.date.today()` ceiling would
#: silently change which historical rows fail this check between runs).
#: Chosen to admit the corpus's genuine range while catching the observed
#: digit-transposition defect (e.g. a real 1927 birth recorded as 2027).
_PLAUSIBLE_YEARS: Final[tuple[int, int]] = (1700, 2026)

#: How many times a minute value's over-representation vs. the uniform 1/60
#: share before it is judged clerical rounding rather than chance. Same
#: threshold and same rationale as `gauquelin_import._ROUNDING_EXCESS`.
_ROUNDING_EXCESS: Final[float] = 3.0


@dataclass(frozen=True)
class LunarAstroRecord:
    """One chart from the LunarAstro scrape.

    Attributes:
      source_id: Deterministic natural key — see :func:`natural_key`. This,
        not ``name``, is the record's identity.
      name: As scraped. Descriptive only — never used for identity or
        deduplication (see the module docstring's name-collision findings).
      birth_year, birth_month, birth_day: Civil date as published.
      birth_hour_local, birth_minute, birth_second: Local clock time as
        published.
      tz_offset: Hours east of UTC, as published (matches the convention used
        throughout ``app/empirical`` — ``ut = local - tz_offset``).
      birth_ut_hour: Decimal UT hour, derived.
      latitude, longitude: Decimal degrees, north/east positive.
      categories: The site's tag set for this person, deduplicated, order
        preserved from first appearance. Outcome/vocation labels for
        downstream feature-bank work — analogous to Gauquelin's profession,
        richer and multi-valued.
      time_is_placeholder: Whether the published clock time is one of
        :data:`_PLACEHOLDER_TIMES`, computed at parse time so
        :func:`assign_time_tiers` never needs to re-parse the string.
      time_tier: ``A`` (minute-precise) | ``B`` (rounded) | ``C`` (no usable
        time — placeholder). Never ``S``: this scrape carries no
        self-reported-vs-registry distinction to draw on.
      data_quality: ``ok``, or a reason the row is suspect. Suspect rows are
        kept — dropping them would hide a source defect — but must be
        excluded from any confirmatory cohort.
      source_url: The scraped page, for traceability.
    """

    source_id: str
    name: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour_local: int
    birth_minute: int
    birth_second: int
    tz_offset: float
    birth_ut_hour: float
    latitude: float
    longitude: float
    categories: tuple[str, ...]
    time_is_placeholder: bool
    time_tier: str
    data_quality: str
    source_url: str


def natural_key(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    latitude: float,
    longitude: float,
) -> str:
    """Deterministic identity for a chart, independent of name.

    Date + clock time + place to 0.01 degrees is the exact tuple a chart is
    cast from — two rows sharing it produce the same chart regardless of what
    name is attached, and this scrape's names are demonstrably unreliable as
    an identity signal (see the module docstring).
    """
    payload = (
        f"{year:04d}-{month:02d}-{day:02d}|{hour:02d}:{minute:02d}:{second:02d}"
        f"|{latitude:.2f}|{longitude:.2f}"
    )
    return "lunar_" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _data_quality(year: int, month: int, day: int, date_str: str) -> str:
    """Flag rows that are internally implausible, without dropping them.

    Order matters: the epoch check must run before the plausible-year check,
    since 1970 is itself inside the plausible range and would otherwise pass
    as merely "ok".
    """
    if date_str == _EPOCH_PLACEHOLDER_DATE:
        return "epoch_placeholder"
    low, high = _PLAUSIBLE_YEARS
    if not low <= year <= high:
        return f"implausible_year:{year}"
    try:
        datetime.date(year, month, day)
    except ValueError:
        return f"invalid_date:{year:04d}-{month:02d}-{day:02d}"
    return "ok"


def _parse_date(raw: str) -> tuple[int, int, int]:
    year_s, month_s, day_s = raw.split("-")
    return int(year_s), int(month_s), int(day_s)


def _parse_time(raw: str) -> tuple[int, int, int]:
    hour_s, minute_s, second_s = raw.split(":")
    return int(hour_s), int(minute_s), int(second_s)


def parse_row(row: dict[str, str]) -> LunarAstroRecord | None:
    """Parse one raw CSV row. Returns ``None`` for a row that cannot be
    parsed at all (missing/malformed field) — logged, not silently counted
    as a valid-but-flagged record; callers report skips separately from
    quality flags because the two mean different things."""
    try:
        raw_date = row["date_of_birth"]
        raw_time = row["time_of_birth"]
        year, month, day = _parse_date(raw_date)
        hour, minute, second = _parse_time(raw_time)
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
        tz_offset = float(row["tz_offset"])
    except (KeyError, ValueError) as exc:
        logger.debug("skipping unparseable row (%s): %r", exc, row)
        return None

    if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
        logger.debug("skipping row with out-of-range coordinates: %r", row)
        return None

    categories: list[str] = []
    for cat in (row.get("categories") or "").split(";"):
        cat = cat.strip()
        if cat and cat not in categories:
            categories.append(cat)

    ut_hour = round((hour + minute / 60.0 + second / 3600.0) - tz_offset, 6)

    return LunarAstroRecord(
        source_id=natural_key(year, month, day, hour, minute, second, latitude, longitude),
        name=(row.get("name") or "").strip(),
        birth_year=year,
        birth_month=month,
        birth_day=day,
        birth_hour_local=hour,
        birth_minute=minute,
        birth_second=second,
        tz_offset=tz_offset,
        birth_ut_hour=ut_hour,
        latitude=round(latitude, 4),
        longitude=round(longitude, 4),
        categories=tuple(categories),
        time_is_placeholder=raw_time in _PLACEHOLDER_TIMES,
        time_tier="A",  # provisional; assign_time_tiers decides
        data_quality=_data_quality(year, month, day, raw_date),
        source_url=(row.get("source_url") or "").strip(),
    )


def _merge_duplicates(records: list[LunarAstroRecord]) -> tuple[list[LunarAstroRecord], int]:
    """Merge rows sharing a chart fingerprint (same natural_key); union their
    categories. Rows with DIFFERENT fingerprints are never merged even if
    they share a name — see the module docstring's name-collision findings.
    """
    by_key: dict[str, LunarAstroRecord] = {}
    merged = 0
    for record in records:
        existing = by_key.get(record.source_id)
        if existing is None:
            by_key[record.source_id] = record
            continue
        merged += 1
        combined = tuple(dict.fromkeys((*existing.categories, *record.categories)))
        by_key[record.source_id] = replace(existing, categories=combined)
    return list(by_key.values()), merged


def assign_time_tiers(
    records: list[LunarAstroRecord],
    *,
    excess: float = _ROUNDING_EXCESS,
) -> tuple[list[LunarAstroRecord], dict[int, int]]:
    """Assign A/B/C by measurement, not by assumption.

    Placeholder-time rows are forced to ``C`` outright — they carry no real
    minute value to measure. The minute-frequency test then runs only over
    the remaining rows, so one popular multi-category-tagged chart cannot
    skew the measured distribution (this is why deduplication must happen
    BEFORE this function runs, not after: :func:`import_all` enforces the
    order).
    """
    real = [r for r in records if not r.time_is_placeholder]
    counts = Counter(r.birth_minute for r in real)
    threshold = excess * len(real) / 60.0 if real else 0.0
    rounded = {minute: n for minute, n in counts.items() if n > threshold}

    out: list[LunarAstroRecord] = []
    for r in records:
        if r.time_is_placeholder:
            tier = "C"
        elif r.birth_minute in rounded or r.data_quality != "ok":
            tier = "B"
        else:
            tier = "A"
        out.append(replace(r, time_tier=tier))
    return out, rounded


def import_all(raw_path: str | Path) -> tuple[list[LunarAstroRecord], dict[str, int]]:
    """Parse, deduplicate (by chart fingerprint), then tier the whole corpus."""
    raw_path = Path(raw_path)
    parsed: list[LunarAstroRecord] = []
    skipped = 0
    with raw_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record = parse_row(row)
            if record is None:
                skipped += 1
                continue
            parsed.append(record)

    deduped, merged = _merge_duplicates(parsed)
    tiered, rounded = assign_time_tiers(deduped)

    stats = {
        "rows_read": len(parsed) + skipped,
        "skipped_unparseable": skipped,
        "duplicates_merged": merged,
        "records": len(tiered),
        "tier_A": sum(1 for r in tiered if r.time_tier == "A"),
        "tier_B": sum(1 for r in tiered if r.time_tier == "B"),
        "tier_C": sum(1 for r in tiered if r.time_tier == "C"),
        "rounded_minutes": len(rounded),
        "flagged_quality": sum(1 for r in tiered if r.data_quality != "ok"),
        "epoch_placeholder": sum(1 for r in tiered if r.data_quality == "epoch_placeholder"),
    }
    return tiered, stats


def write_csv(path: str | Path, records: list[LunarAstroRecord]) -> None:
    """Write records to CSV with a stable column order and JSON-free scalars
    (categories joined with ';', booleans as 'true'/'false' — never a raw
    Python tuple/bool repr, which a naive DictWriter would otherwise emit)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [f.name for f in fields(LunarAstroRecord)]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for record in sorted(records, key=lambda r: (r.birth_year, r.birth_month, r.birth_day, r.source_id)):
            row = asdict(record)
            row["categories"] = ";".join(record.categories)
            row["time_is_placeholder"] = "true" if record.time_is_placeholder else "false"
            writer.writerow(row)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Import a LunarAstro-format research corpus CSV.")
    parser.add_argument("--raw", required=True, help="input raw CSV path")
    parser.add_argument("--out", required=True, help="output canonical CSV path")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    records, stats = import_all(args.raw)
    write_csv(args.out, records)

    logger.info("wrote %s", args.out)
    for key in sorted(stats):
        logger.info("  %-22s %d", key, stats[key])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
