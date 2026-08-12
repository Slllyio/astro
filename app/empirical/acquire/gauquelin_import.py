"""Gauquelin / CURA archive importer — Phase 1 acquisition.

The Gauquelin series A ("professional notabilities") is the single best public
source of *registry-timed* births: Michel and Françoise Gauquelin collected birth
times from civil birth records across France, Italy, Belgium, the Netherlands and
Germany from 1949 onward, and CURA publishes the six volumes as plain tabular
data. Six volumes, ~15-20k persons, each with a profession label.

Why it matters here: birth-time quality is the binding constraint on every
transit-level test. Self-reported and rounded times cannot evidence a transit
that is exact for hours. This corpus is the tier-A backbone.

**Honest time tiers.** Registry sourcing does not make every time exact. Where a
clerk wrote "born at 6 o'clock", the record carries MN=0 with no more precision
than the hour. :func:`assign_time_tiers` measures that directly — it compares the
observed frequency of each minute value against the uniform 1/60 expectation and
downgrades the over-represented values to tier B rather than assuming the whole
corpus is tier A. On volume A1 this is not a hypothetical: the post-1940 records
are visibly dominated by MN=0.

**Provenance, not just data.** Every row keeps its source URL, volume, and the
publisher's own record number, so any downstream claim can be traced back.

Sources are fetched once and cached under ``data/empirical/raw/gauquelin/``;
re-runs read the cache and do not touch the network.

Usage:
    python -m app.empirical.acquire.gauquelin_import --out data/empirical/gauquelin.csv
    python -m app.empirical.acquire.gauquelin_import --out data/empirical/gauquelin.csv --volume A1
    python -m app.empirical.acquire.gauquelin_import --out data/empirical/gauquelin.csv --refresh
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import re
import time
import urllib.request
from collections import Counter
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Final, Iterable, Sequence

logger = logging.getLogger(__name__)

__all__ = [
    "VOLUMES",
    "GauquelinRecord",
    "parse_latitude",
    "parse_longitude",
    "parse_volume",
    "assign_time_tiers",
    "natural_key",
    "fetch_volume",
    "import_all",
]

_BASE_URL: Final[str] = "http://cura.free.fr/gauq/"
_ENCODING: Final[str] = "latin-1"
_CACHE_DIR: Final[Path] = Path("data/empirical/raw/gauquelin")

#: Volume id -> (CURA file stem, human description). The ``y`` suffix is CURA's
#: "Chronological Order (Complete Data)" edition — the only one carrying the full
#: time and place columns. The B/D/E series are gated behind a request process and
#: are deliberately not scraped.
VOLUMES: Final[dict[str, tuple[str, str]]] = {
    "A1": ("902gdA1y", "sports champions"),
    "A2": ("902gdA2y", "scientists and physicians"),
    "A3": ("902gdA3y", "military men"),
    "A4": ("902gdA4y", "painters and musicians"),
    "A5": ("902gdA5y", "actors and politicians"),
    "A6": ("902gdA6y", "writers and journalists"),
}

#: CURA's single-letter profession codes, per the volume legends.
PROFESSION_CODES: Final[dict[str, str]] = {
    "C": "sport_champion",
    "S": "scientist",
    "M": "military_or_musician",  # ambiguous in CURA: M is military in A3, musician in A4
    "P": "painter",
    "A": "actor",
    "PT": "politician",
    "W": "writer",
    "J": "journalist",
    "X": "executive",
}

#: Country letter -> ISO-ish code.
COUNTRIES: Final[dict[str, str]] = {
    "F": "FR", "I": "IT", "G": "DE", "B": "BE", "N": "NL", "S": "CH",
}

# "48N 0" / "50N30" / "43S 7"
_LAT_RE: Final[re.Pattern[str]] = re.compile(r"^\s*(\d+)\s*([NS])\s*(\d+)\s*$")
# "4W 6" / "13E 0" / "10E45"
_LON_RE: Final[re.Pattern[str]] = re.compile(r"^\s*(\d+)\s*([EW])\s*(\d+)\s*$")

#: The Gauquelin series-A collections cover births from the early 1800s to the
#: mid 1900s. Anything outside this window is a source typo, not a discovery —
#: A5 record 401 is published as born in 1600, which for an actor collected from
#: 20th-century civil registries is impossible (almost certainly 1900).
_PLAUSIBLE_YEARS: Final[tuple[int, int]] = (1700, 1975)

#: A minute value is called "rounded" when it occurs at least this many times
#: more often than the uniform 1/60 expectation. 3x is deliberately conservative:
#: it catches the 0/30 clerical spikes without demoting ordinary variation.
_ROUNDING_EXCESS: Final[float] = 3.0


@dataclass(frozen=True, slots=True)
class GauquelinRecord:
    """One person from the Gauquelin archive.

    Attributes:
      source_id: Deterministic natural key — see :func:`natural_key`.
      volume: Which CURA volume (A1..A6).
      cura_number: The publisher's own record number, for traceability.
      profession: Decoded profession label.
      country: CURA's ``COU`` column. This tracks the *collection group*
        (broadly nationality), not necessarily the country of birth — A5 record
        725 is coded ``F`` with The Hague's coordinates. The latitude/longitude
        are the authoritative birth place; treat this field as a grouping label.
      birth_year, birth_month, birth_day: Civil date of birth.
      birth_hour_local, birth_minute, birth_second: Local standard time as published.
      tz_offset: CURA's zone column; ``ut = local + tz_offset``.
      birth_jd_ut_hour: Decimal UT hour, derived.
      latitude, longitude: Decimal degrees, north/east positive.
      place_code, city: Birth place as published.
      time_tier: ``A`` (minute-precise) or ``B`` (rounded — see
        :func:`assign_time_tiers`). Never ``S``: nothing here is self-reported.
      data_quality: ``ok``, or a reason the row is suspect. Suspect rows are
        kept (dropping them would hide a source defect) but must be excluded
        from confirmatory cohorts.
      source_url: Exact page the row came from.
    """

    source_id: str
    volume: str
    cura_number: str
    profession: str
    country: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour_local: int
    birth_minute: int
    birth_second: int
    tz_offset: int
    birth_ut_hour: float
    latitude: float
    longitude: float
    place_code: str
    city: str
    time_tier: str
    data_quality: str
    source_url: str


def parse_latitude(raw: str) -> float:
    """``"48N 0"`` -> ``48.0``; ``"50N30"`` -> ``50.5``. South is negative."""
    match = _LAT_RE.match(raw)
    if not match:
        raise ValueError(f"unparseable latitude {raw!r}")
    degrees, hemisphere, minutes = int(match[1]), match[2], int(match[3])
    value = degrees + minutes / 60.0
    return -value if hemisphere == "S" else value


def parse_longitude(raw: str) -> float:
    """``"4W 6"`` -> ``-4.1``; ``"13E 0"`` -> ``13.0``. West is negative."""
    match = _LON_RE.match(raw)
    if not match:
        raise ValueError(f"unparseable longitude {raw!r}")
    degrees, hemisphere, minutes = int(match[1]), match[2], int(match[3])
    value = degrees + minutes / 60.0
    return -value if hemisphere == "W" else value


def natural_key(
    country: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    latitude: float,
    longitude: float,
) -> str:
    """Deterministic identity for a record, independent of name.

    CURA's complete-data tables publish no names for most rows, so a
    ``sha1(name|date)`` key is not available here. Date + clock time + place to
    0.01° is a *stronger* discriminator than a name anyway — it is exactly the
    tuple a chart is cast from, and two people sharing it would produce the same
    chart regardless of what they were called.

    Deliberately NOT fuzzy: the 774-collision name trap in the existing master is
    the reason nothing here auto-merges on a name.
    """
    payload = f"{country}|{year:04d}-{month:02d}-{day:02d}|{hour:02d}:{minute:02d}|{latitude:.2f}|{longitude:.2f}"
    return "gauq_" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _data_quality(year: int, profession: str) -> str:
    """Flag rows that are internally implausible, without dropping them.

    Silently discarding a bad row hides a defect in the source; silently keeping
    it lets the defect into a cohort. Flagging does neither.
    """
    low, high = _PLAUSIBLE_YEARS
    if not low <= year <= high:
        return f"implausible_year:{year}"
    if profession.startswith("unknown_"):
        return profession
    return "ok"


def _profession_for(code: str, volume: str) -> str:
    """Decode a profession code, disambiguating CURA's reused ``M``."""
    code = code.strip().upper()
    if code == "M":
        return "military" if volume == "A3" else "musician"
    return PROFESSION_CODES.get(code, f"unknown_{code.lower()}")


def fetch_volume(volume: str, *, refresh: bool = False, cache_dir: Path = _CACHE_DIR) -> str:
    """Return one volume's raw HTML, fetching once and caching to disk.

    Re-runs read the cache. The polite delay applies only to real fetches.
    """
    if volume not in VOLUMES:
        raise KeyError(f"unknown volume {volume!r}; expected one of {sorted(VOLUMES)}")
    stem, _desc = VOLUMES[volume]
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / f"{stem}.html"

    if cached.is_file() and not refresh:
        logger.info("%s: reading cache %s", volume, cached)
        return cached.read_text(encoding=_ENCODING)

    url = f"{_BASE_URL}{stem}.html"
    logger.info("%s: fetching %s", volume, url)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "astro-empirical/1.0 (research corpus build; contact via repo)"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed host
        payload = response.read()
    text = payload.decode(_ENCODING, errors="replace")
    cached.write_text(text, encoding=_ENCODING)
    time.sleep(1.0)  # be a good guest on a volunteer-run archive
    return text


def parse_volume(html: str, volume: str) -> list[GauquelinRecord]:
    """Parse one volume's complete-data table into records.

    Only the first ``<pre>`` block is the complete table; the later blocks are
    partial name indexes covering a small minority of rows and are ignored.
    Rows that fail to parse are logged and skipped rather than silently dropped.

    Time tiers are NOT assigned here — that needs the whole volume, so callers
    pass the result through :func:`assign_time_tiers`.
    """
    blocks = re.findall(r"<pre>(.*?)</pre>", html, re.S | re.I)
    if not blocks:
        raise ValueError(f"{volume}: no <pre> data block found")
    stem, _ = VOLUMES[volume]
    source_url = f"{_BASE_URL}{stem}.html"

    records: list[GauquelinRecord] = []
    skipped = 0
    for line in blocks[0].splitlines():
        if not line.strip() or line.lstrip().startswith("YEA"):
            continue
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) < 14:
            skipped += 1
            continue
        try:
            (year, month, day, pro, num, cou, hour, minute,
             second, tz, lat_raw, lon_raw, code, city) = parts[:14]
            latitude = parse_latitude(lat_raw)
            longitude = parse_longitude(lon_raw)
            year_i, month_i, day_i = int(year), int(month), int(day)
            hour_i, minute_i, second_i = int(hour), int(minute), int(second)
            tz_i = int(tz)
        except (ValueError, IndexError) as exc:
            logger.debug("%s: skipping unparseable row (%s): %s", volume, exc, line[:80])
            skipped += 1
            continue

        # CURA publishes local standard time plus the zone column such that
        # ut = local + tz (tz is 0 for GMT, -1 for CET).
        ut_hour = hour_i + minute_i / 60.0 + second_i / 3600.0 + tz_i

        profession = _profession_for(pro, volume)
        records.append(
            GauquelinRecord(
                source_id=natural_key(cou, year_i, month_i, day_i, hour_i, minute_i, latitude, longitude),
                volume=volume,
                cura_number=num,
                profession=profession,
                country=COUNTRIES.get(cou.strip().upper(), cou.strip().upper()),
                birth_year=year_i,
                birth_month=month_i,
                birth_day=day_i,
                birth_hour_local=hour_i,
                birth_minute=minute_i,
                birth_second=second_i,
                tz_offset=tz_i,
                birth_ut_hour=round(ut_hour, 6),
                latitude=round(latitude, 4),
                longitude=round(longitude, 4),
                place_code=code,
                city=city,
                time_tier="A",  # provisional; assign_time_tiers decides
                data_quality=_data_quality(year_i, profession),
                source_url=source_url,
            )
        )
    if skipped:
        logger.info("%s: %d rows parsed, %d skipped", volume, len(records), skipped)
    return records


def assign_time_tiers(
    records: Sequence[GauquelinRecord],
    *,
    excess: float = _ROUNDING_EXCESS,
) -> tuple[list[GauquelinRecord], dict[int, int]]:
    """Downgrade clerically-rounded times from tier A to tier B.

    Measures rather than assumes. If birth minutes were recorded faithfully they
    would be roughly uniform over 0-59, so any minute value occurring more than
    ``excess`` times its 1/60 share is a clerical artefact — the clerk wrote "6
    o'clock", not 06:00:00. Those records keep their data but lose their tier-A
    claim, which excludes them from transit-level tests where an hour of slop is
    fatal.

    Returns:
      ``(records_with_tiers, rounded_minute_counts)`` — the second element is the
      evidence, so a caller can report *why* rows were downgraded.
    """
    if not records:
        return [], {}
    counts = Counter(r.birth_minute for r in records)
    threshold = excess * len(records) / 60.0
    rounded = {minute: n for minute, n in counts.items() if n > threshold}

    out = [
        GauquelinRecord(
            **{
                **asdict(r),
                # A row with a suspect field cannot claim the top time tier: the
                # defect we can see casts doubt on the fields we cannot check.
                "time_tier": "B" if (r.birth_minute in rounded or r.data_quality != "ok") else "A",
            }
        )
        for r in records
    ]
    if rounded:
        logger.info(
            "rounding test: minutes %s exceed %.0fx uniform (threshold %.1f) — %d rows -> tier B",
            sorted(rounded),
            excess,
            threshold,
            sum(rounded.values()),
        )
    return out, rounded


def import_all(
    volumes: Iterable[str] = tuple(VOLUMES),
    *,
    refresh: bool = False,
    cache_dir: Path = _CACHE_DIR,
) -> tuple[list[GauquelinRecord], dict[str, int]]:
    """Fetch, parse, tier, and de-duplicate every requested volume.

    Returns:
      ``(records, stats)``. Duplicates are dropped on :func:`natural_key`; the
      count is reported rather than hidden, since CURA itself documents at least
      one intentional duplicate (A1 numbers 513 and 1153 are the same person).
    """
    raw: list[GauquelinRecord] = []
    stats: dict[str, int] = {}
    for volume in volumes:
        html = fetch_volume(volume, refresh=refresh, cache_dir=cache_dir)
        parsed = parse_volume(html, volume)
        stats[f"parsed_{volume}"] = len(parsed)
        raw.extend(parsed)

    tiered, rounded = assign_time_tiers(raw)

    seen: set[str] = set()
    deduped: list[GauquelinRecord] = []
    for record in tiered:
        if record.source_id in seen:
            continue
        seen.add(record.source_id)
        deduped.append(record)

    stats["parsed_total"] = len(raw)
    stats["duplicates_dropped"] = len(raw) - len(deduped)
    stats["records"] = len(deduped)
    stats["tier_A"] = sum(1 for r in deduped if r.time_tier == "A")
    stats["tier_B"] = sum(1 for r in deduped if r.time_tier == "B")
    stats["rounded_minutes"] = len(rounded)
    stats["flagged_quality"] = sum(1 for r in deduped if r.data_quality != "ok")
    return deduped, stats


def write_csv(path: str | Path, records: Sequence[GauquelinRecord]) -> None:
    """Write records to CSV with a stable column order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [f.name for f in fields(GauquelinRecord)]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for record in sorted(records, key=lambda r: (r.birth_year, r.birth_month, r.birth_day, r.source_id)):
            writer.writerow(asdict(record))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Import the Gauquelin/CURA series-A archive.")
    parser.add_argument("--out", required=True, help="output CSV path")
    parser.add_argument("--volume", action="append", choices=sorted(VOLUMES),
                        help="limit to one or more volumes (default: all six)")
    parser.add_argument("--refresh", action="store_true", help="re-fetch even if cached")
    parser.add_argument("--cache-dir", default=str(_CACHE_DIR), help="where raw HTML is cached")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    records, stats = import_all(
        args.volume or tuple(VOLUMES),
        refresh=args.refresh,
        cache_dir=Path(args.cache_dir),
    )
    write_csv(args.out, records)

    logger.info("wrote %s", args.out)
    for key in sorted(stats):
        logger.info("  %-22s %d", key, stats[key])
    by_profession = Counter(r.profession for r in records)
    for profession, count in by_profession.most_common():
        logger.info("  profession %-22s %d", profession, count)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
