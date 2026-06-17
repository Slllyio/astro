"""Geocode ASTROCRM's `astro_people.csv` into the Stage-2 `raw.csv` schema.

ASTROCRM ships `place_of_birth` as free text (a bare city name like
``"Strasbourg"`` or ``"Aba (Sichuan)"``) but NOT latitude/longitude — which the
Vedic-Tensor ETL needs to cast a chart. This importer closes that gap entirely
offline (no API keys, consistent with the project's Leaflet+OSM stance):

  1. **Geocode** the city name → (lat, lon) using ``geonamescache``'s bundled
     cities dataset. With only a city name to go on, we disambiguate by
     **population** (the most-populous match — a sound prior for "famous person
     born in <city>"). City names + their alternate names are indexed.
  2. **Timezone** → numeric UTC offset at the *birth instant* via
     ``timezonefinder`` (lat/lon → IANA zone) + ``zoneinfo`` (historical
     DST/tz-history rules), mirroring ``lunarastro_importer``.
  3. **Emit** a ``raw.csv`` row (name, date_of_birth, time_of_birth, latitude,
     longitude, tz_offset, rodden_rating, categories, source_url) that
     ``databank_etl`` consumes verbatim.

Names are preserved exactly so the output joins back to the dated-event corpus
produced by ``events_extractor`` (``data/astro_databank/events.csv``) on the
``name`` key — enabling ``event_corpus`` → an event-timing model.

CLI:
    python -m app.medini.etl.astrocrm_geocode_importer \\
        --input data/holos/astro_people.csv \\
        --output data/astro_databank/raw_astrocrm.csv \\
        [--require-time]   # drop timeless births (chart houses need a time)
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

csv.field_size_limit(10 ** 7)

# Same column order databank_etl expects (see vedastro_importer / scraper).
RAW_COLUMNS: tuple[str, ...] = (
    "name", "date_of_birth", "time_of_birth",
    "latitude", "longitude", "tz_offset",
    "rodden_rating", "categories", "source_url",
)

_PAREN = re.compile(r"\(.*?\)")


def _normalize_city(place: str) -> str:
    """Reduce a free-text place to a bare, lowercased, accent-free city name.

    "Aba (Sichuan)" -> "aba"; "Thonon les Bains" -> "thonon les bains";
    "New York, NY, USA" -> "new york".
    """
    s = _PAREN.sub("", place)          # drop parentheticals
    s = s.split(",")[0]                # keep the part before the first comma
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


@dataclass(frozen=True)
class _City:
    lat: float
    lon: float
    population: int


def _build_city_index() -> dict[str, _City]:
    """Map normalized city name → most-populous (lat, lon).

    Indexes both the canonical name and any alternate names geonamescache
    ships, so "Munich"/"München" both resolve. Higher population wins on
    collision — the right prior when all we have is a bare city string.
    """
    import geonamescache

    gc = geonamescache.GeonamesCache()
    index: dict[str, _City] = {}

    def _consider(name: str, city: _City) -> None:
        key = _normalize_city(name)
        if not key:
            return
        prev = index.get(key)
        if prev is None or city.population > prev.population:
            index[key] = city

    for rec in gc.get_cities().values():
        try:
            city = _City(
                lat=float(rec["latitude"]),
                lon=float(rec["longitude"]),
                population=int(rec.get("population") or 0),
            )
        except (KeyError, TypeError, ValueError):
            continue
        _consider(rec.get("name", ""), city)
        for alt in rec.get("alternatenames", []) or []:
            _consider(alt, city)

    logger.info("built city index: %d distinct names", len(index))
    return index


def _parse_date(text: str) -> str | None:
    """ASTROCRM dates are 'YYYY/MM/DD' (or already ISO). Return ISO or None."""
    text = (text or "").strip()
    if not text:
        return None
    text = text.replace("/", "-")
    parts = text.split("-")
    if len(parts) != 3:
        return None
    try:
        y, m, d = (int(p) for p in parts)
        return dt.date(y, m, d).isoformat()
    except ValueError:
        return None


def _parse_time(text: str) -> str | None:
    """'HH:MM' or 'HH:MM:SS' → 'HH:MM:SS'. Empty/garbage → None."""
    text = (text or "").strip()
    if not text:
        return None
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", text)
    if not m:
        return None
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    if not (0 <= h < 24 and 0 <= mi < 60 and 0 <= s < 60):
        return None
    return f"{h:02d}:{mi:02d}:{s:02d}"


def _tz_offset(lat: float, lon: float, iso_date: str, tf) -> float | None:
    """Numeric UTC offset (decimal hours) at the birth date for (lat, lon).

    Uses timezonefinder for the IANA zone and zoneinfo for the historical
    offset on the birth date (so pre-1970 / DST-era births get the right
    offset). Returns None if the zone can't be resolved.
    """
    zone_name = tf.timezone_at(lat=lat, lng=lon)
    if not zone_name:
        return None
    try:
        zone = ZoneInfo(zone_name)
    except ZoneInfoNotFoundError:
        return None
    y, m, d = (int(p) for p in iso_date.split("-"))
    # noon avoids DST-midnight ambiguity; offset granularity is the day.
    moment = dt.datetime(y, m, d, 12, 0, tzinfo=zone)
    off = moment.utcoffset()
    if off is None:
        return None
    return round(off.total_seconds() / 3600.0, 4)


def import_astrocrm(
    input_path: Path,
    output_path: Path,
    *,
    require_time: bool = True,
) -> dict[str, int]:
    """Geocode astro_people.csv → raw.csv. Returns a stats dict."""
    from timezonefinder import TimezoneFinder

    city_index = _build_city_index()
    tf = TimezoneFinder()

    stats = {
        "input_rows": 0, "written": 0,
        "skipped_no_place": 0, "skipped_no_date": 0, "skipped_no_time": 0,
        "skipped_geocode_miss": 0, "skipped_tz_miss": 0,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open(encoding="utf-8") as fin, \
            output_path.open("w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=RAW_COLUMNS)
        writer.writeheader()

        for row in reader:
            stats["input_rows"] += 1
            place = (row.get("place_of_birth") or "").strip()
            if not place:
                stats["skipped_no_place"] += 1
                continue

            iso_date = _parse_date(row.get("date_of_birth", ""))
            if not iso_date:
                stats["skipped_no_date"] += 1
                continue

            iso_time = _parse_time(row.get("time_of_birth", ""))
            if iso_time is None:
                if require_time:
                    stats["skipped_no_time"] += 1
                    continue
                iso_time = "12:00:00"

            city = city_index.get(_normalize_city(place))
            if city is None:
                stats["skipped_geocode_miss"] += 1
                continue

            tz = _tz_offset(city.lat, city.lon, iso_date, tf)
            if tz is None:
                stats["skipped_tz_miss"] += 1
                continue

            writer.writerow({
                "name": (row.get("name") or "").strip(),
                "date_of_birth": iso_date,
                "time_of_birth": iso_time,
                "latitude": f"{city.lat:.6f}",
                "longitude": f"{city.lon:.6f}",
                "tz_offset": f"{tz:.4f}",
                "rodden_rating": (row.get("rodden_rating") or "").strip(),
                "categories": (row.get("occupation") or "").strip(),
                "source_url": (
                    f"https://github.com/jfsagro-glitch/ASTROCRM"
                    f"#person:{row.get('page_id', '').strip()}"
                ),
            })
            stats["written"] += 1

    logger.info(
        "geocoded %d/%d rows (no_place=%d no_date=%d no_time=%d "
        "geocode_miss=%d tz_miss=%d)",
        stats["written"], stats["input_rows"], stats["skipped_no_place"],
        stats["skipped_no_date"], stats["skipped_no_time"],
        stats["skipped_geocode_miss"], stats["skipped_tz_miss"],
    )
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.astrocrm_geocode_importer",
        description="Geocode ASTROCRM astro_people.csv into the raw.csv schema.",
    )
    parser.add_argument("--input", type=Path, required=True,
                        help="Path to astro_people.csv.")
    parser.add_argument("--output", type=Path, required=True,
                        help="Destination raw.csv path.")
    parser.add_argument("--require-time", action="store_true", default=True,
                        help="Drop births with no recorded time (default on).")
    parser.add_argument("--allow-timeless", dest="require_time",
                        action="store_false",
                        help="Keep timeless births, defaulting to 12:00 noon.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = import_astrocrm(
        args.input, args.output, require_time=args.require_time,
    )
    print(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
