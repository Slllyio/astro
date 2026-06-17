"""Import Astro-Databank's XML export into the project's chart/event schema.

Astro-Databank publishes a bulk XML export (`adb_export_DATE.xml`; the format TkAstroDb
consumes). Its structure is::

    <astrodatabank_export>
      <adb_entry>
        <public_data>           <!-- PUBLIC DOMAIN -->
          <name>…</name> <sflname>…</sflname> <gender>…</gender>
          <roddenrating rrc="…">AA</roddenrating>
          <bdata>
            <sbdate_dmy>14.3.1879</sbdate_dmy>  <sbtime>11:30</sbtime>
            <place>Ulm, Germany, 48n24, 10e00</place> <country>…</country>
          </bdata>
        </public_data>
        <text_data>…</text_data>           <!-- NOT public domain (biographies) -->
        <research_data><categories>…</categories>…</research_data>  <!-- NOT public domain -->
      </adb_entry>
    </astrodatabank_export>

**Licensing matters here.** Astrodienst declares only ``public_data`` public domain;
``text_data`` (biographies) and ``research_data`` (categories / life events) are *not*,
and the full dated-events dump is gated behind a signed research licence. So:

  • **Charts** (``public_data``) are always extracted → ``raw.csv`` (AA/A filtered
    downstream) — safe for everyone. This makes ADB a large *chart* source.
  • **Events** are extracted from ``research_data`` categories / event tags *only if
    present* in the file you supply (i.e. a licensed dump). On the public-domain
    birth-only export, the event pass simply yields nothing — no error.

Hence ADB's role for *this* project is primarily birth-time charts; the dated-event
shortfall is better closed by VedAstro (MIT, dated marriages) and Wikidata (CC0).

Streamed with ``iterparse`` so multi-hundred-MB exports use bounded memory.

CLI::

    python -m app.medini.etl.astrodatabank_xml_importer \\
        --xml adb_export_200814.xml --raw data/adb/raw.csv --events data/adb/events.csv
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
from pathlib import Path
from typing import Iterator
from xml.etree import ElementTree as ET

from app.medini.etl.lunarastro_importer import EVENT_COLUMNS, MAX_YEAR, MIN_YEAR

logger = logging.getLogger(__name__)

# raw.csv column order (kept in sync with scraper.CSV_COLUMNS; inlined to avoid
# importing scraper.py, which pulls in BeautifulSoup at module load).
CSV_COLUMNS: tuple[str, ...] = (
    "name", "date_of_birth", "time_of_birth", "latitude", "longitude",
    "tz_offset", "rodden_rating", "categories", "source_url",
)

# Astro-Databank coordinate strings, e.g. "48n24", "48n24'15", "10e00", "12S30".
_COORD_DMS_RE = re.compile(r"^\s*(\d+)\s*([nsewNSEW])\s*(\d+)?\s*(?:[.'](\d+))?\s*$")
_COORD_DECIMAL_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([nsewNSEW])?\s*$")


def parse_coordinate(text: str) -> float | None:
    """Astro-Databank coordinate string → signed decimal degrees (N/E +, S/W −).
    Mirrors ``scraper.parse_coordinate``; None if unrecognised."""
    if not text:
        return None
    s = text.strip()
    m = _COORD_DMS_RE.match(s)
    if m:
        deg = int(m.group(1))
        minutes = int(m.group(3)) if m.group(3) else 0
        seconds = int(m.group(4)) if m.group(4) else 0
        decimal = deg + minutes / 60.0 + seconds / 3600.0
        return -decimal if m.group(2).upper() in ("S", "W") else decimal
    m = _COORD_DECIMAL_RE.match(s)
    if m:
        decimal = float(m.group(1))
        hem = (m.group(2) or "").upper()
        return -decimal if hem in ("S", "W") else decimal
    return None

_DMY_RE = re.compile(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{3,4})\s*$")
_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})(?::(\d{2}))?")
# trailing "48n24, 10e00" coordinate pair in a place string.
_PLACE_COORD_RE = re.compile(
    r"(\d+(?:\.\d+)?[nsNS]\d*(?:'?\d+)?)\s*[, ]\s*(\d+(?:\.\d+)?[ewEW]\d*(?:'?\d+)?)")
_YEAR_RE = re.compile(r"(?<!\d)(\d{3,4})(?!\d)")


def _text(el: ET.Element | None, *tags: str) -> str:
    """First non-empty descendant text among `tags` (case-insensitive local name)."""
    if el is None:
        return ""
    want = {t.lower() for t in tags}
    for node in el.iter():
        if node.tag.rsplit("}", 1)[-1].lower() in want and (node.text or "").strip():
            return node.text.strip()
    return ""


def _iso_date(dmy: str) -> str:
    m = _DMY_RE.match(dmy)
    if not m:
        return ""
    d, mo, y = int(m[1]), int(m[2]), int(m[3])
    if not (1 <= d <= 31 and 1 <= mo <= 12 and MIN_YEAR <= y <= MAX_YEAR):
        return ""
    return f"{y:04d}-{mo:02d}-{d:02d}"


def _hms(text: str) -> str:
    m = _TIME_RE.search(text or "")
    if not m:
        return ""
    hh, mm, ss = int(m[1]), int(m[2]), int(m[3] or 0)
    if not (0 <= hh < 24 and 0 <= mm < 60 and 0 <= ss < 60):
        return ""
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def _coords(place: str) -> tuple[float | None, float | None]:
    m = _PLACE_COORD_RE.search(place or "")
    if not m:
        return None, None
    return parse_coordinate(m[1]), parse_coordinate(m[2])


def parse_public_data(entry: ET.Element) -> dict[str, str] | None:
    """One <adb_entry> → a raw.csv chart row (or None if no usable birth data)."""
    pub = next((c for c in entry if c.tag.rsplit("}", 1)[-1].lower() == "public_data"),
               entry)
    name = _text(pub, "sflname", "name", "birthname")
    if not name:
        return None
    date_iso = _iso_date(_text(pub, "sbdate_dmy", "sbdate"))
    if not date_iso:                                   # no usable date → not chartable
        return None
    hms = _hms(_text(pub, "sbtime"))
    lat, lon = _coords(_text(pub, "place"))
    rating = _text(pub, "roddenrating").upper()
    return {
        "name": name,
        "date_of_birth": date_iso,
        "time_of_birth": hms,
        "latitude": "" if lat is None else f"{lat:.6f}",
        "longitude": "" if lon is None else f"{lon:.6f}",
        "tz_offset": "",                               # derived later from place/LMT
        "rodden_rating": rating,
        "categories": "",
        "source_url": "https://www.astro.com/astro-databank/",
    }


def parse_events(entry: ET.Element, name: str) -> list[dict[str, str]]:
    """Dated life events from <research_data>/<event> tags, when present (licensed
    dumps only). Each event needs a recognisable root + a 3–4 digit year."""
    out: list[dict[str, str]] = []
    for i, ev in enumerate(entry.iter()):
        if ev.tag.rsplit("}", 1)[-1].lower() != "event":
            continue
        root = (ev.get("type") or ev.get("class")
                or _text(ev, "type", "category", "name")).strip()
        when = (ev.get("date") or ev.get("year") or _text(ev, "date", "year")).strip()
        ym = _YEAR_RE.search(when)
        if not root or not ym:
            continue
        year = int(ym[1])
        if not (MIN_YEAR <= year <= MAX_YEAR):
            continue
        root_l = root.lower().replace(" ", "_")
        out.append({
            "name": name, "event_code": root, "event_root": root_l,
            "event_subtype": "", "event_date": "", "event_year": str(year),
            "source_url": "https://www.astro.com/astro-databank/#event-%d" % i,
        })
    return out


def iter_entries(xml_path: Path) -> Iterator[ET.Element]:
    """Stream <adb_entry> elements, clearing each to bound memory."""
    for _, el in ET.iterparse(str(xml_path), events=("end",)):
        if el.tag.rsplit("}", 1)[-1].lower() == "adb_entry":
            yield el
            el.clear()


def import_adb_xml(xml_path: Path, raw_csv: Path, events_csv: Path | None) -> dict[str, int]:
    if not xml_path.exists():
        raise FileNotFoundError(f"ADB XML missing: {xml_path}")
    raw_csv.parent.mkdir(parents=True, exist_ok=True)
    stats = {"entries": 0, "charts": 0, "events": 0, "skipped_no_birth": 0}

    ev_writer = ev_file = None
    if events_csv is not None:
        events_csv.parent.mkdir(parents=True, exist_ok=True)
        ev_file = events_csv.open("w", encoding="utf-8", newline="")
        ev_writer = csv.DictWriter(ev_file, fieldnames=list(EVENT_COLUMNS))
        ev_writer.writeheader()

    try:
        with raw_csv.open("w", encoding="utf-8", newline="") as rf:
            rw = csv.DictWriter(rf, fieldnames=list(CSV_COLUMNS))
            rw.writeheader()
            for entry in iter_entries(xml_path):
                stats["entries"] += 1
                row = parse_public_data(entry)
                if row is None:
                    stats["skipped_no_birth"] += 1
                    continue
                rw.writerow(row)
                stats["charts"] += 1
                if ev_writer is not None:
                    for ev in parse_events(entry, row["name"]):
                        ev_writer.writerow(ev)
                        stats["events"] += 1
    finally:
        if ev_file is not None:
            ev_file.close()
    return stats


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m app.medini.etl.astrodatabank_xml_importer",
        description="Parse an Astro-Databank XML export into raw.csv (+ events.csv).")
    p.add_argument("--xml", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True, help="raw.csv output (charts).")
    p.add_argument("--events", type=Path, default=None,
                   help="events.csv output (only meaningful on a licensed dump "
                        "containing <event> tags).")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    s = import_adb_xml(args.xml, args.raw, args.events)
    logger.info("ADB XML: %d entries → %d charts, %d events (%d skipped no-birth)",
                s["entries"], s["charts"], s["events"], s["skipped_no_birth"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
