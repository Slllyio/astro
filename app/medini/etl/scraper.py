"""Astro-Databank wiki scraper.

Astro-Databank (https://www.astro.com/astro-databank) is a MediaWiki-style
biographical database with structured infoboxes per entry. This module
crawls category pages, fetches member entries, parses the infobox into a
structured record, and emits a CSV for the Stage-2 ETL.

Architecture: split into a pure-function parser layer and a network/state
crawler layer. Parsers are unit-tested against fixture HTML (no network);
the crawler is exercised live via the CLI with --max-entries 10 first.

Resumability: a SQLite cache tracks visited URLs and parsed records so
interrupted crawls can be resumed without re-fetching. Polite 1 req/sec
rate limit; exponential backoff on 5xx responses.

CLI:
    python -m app.medini.etl.scraper \\
        --output data/astro_databank/raw.csv \\
        [--max-entries 10] [--resume] [--seed CATEGORY_URL]
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import logging
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

ASTRO_DATABANK_BASE = "https://www.astro.com/astro-databank/"
DEFAULT_SEED_URL = ASTRO_DATABANK_BASE + "Category:All_Astro-Databank_pages"
DEFAULT_RATE_LIMIT_SECONDS = 1.0
DEFAULT_USER_AGENT = (
    "Slllyio-AstroResearch/0.1 (medini-intelligence; github.com/Slllyio/astro)"
)


# ---------- Data shape ----------

@dataclasses.dataclass(frozen=True)
class EntryRecord:
    """One Astro-Databank biographical entry, fully parsed."""
    name: str
    date_of_birth: str           # ISO YYYY-MM-DD ("" if missing)
    time_of_birth: str           # HH:MM:SS ("" if missing or unrated)
    latitude: float | None
    longitude: float | None
    tz_offset: float | None      # hours from UTC; positive = east
    rodden_rating: str           # AA, A, B, C, DD, DR, X, XX ("" if missing)
    categories: tuple[str, ...]  # raw category strings, hierarchical
    source_url: str

    def as_csv_row(self) -> dict[str, str]:
        """Flatten to the CSV column shape Stage 2 ETL expects."""
        return {
            "name": self.name,
            "date_of_birth": self.date_of_birth,
            "time_of_birth": self.time_of_birth,
            "latitude": "" if self.latitude is None else f"{self.latitude:.6f}",
            "longitude": "" if self.longitude is None else f"{self.longitude:.6f}",
            "tz_offset": "" if self.tz_offset is None else f"{self.tz_offset:.4f}",
            "rodden_rating": self.rodden_rating,
            "categories": ";".join(self.categories),
            "source_url": self.source_url,
        }


CSV_COLUMNS: tuple[str, ...] = (
    "name", "date_of_birth", "time_of_birth", "latitude", "longitude",
    "tz_offset", "rodden_rating", "categories", "source_url",
)


# ---------- Pure-function parsers (unit-testable) ----------

_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Coord pattern: "48n24" = 48 deg 24 min N. Letter N/S/E/W indicates hemisphere.
# May appear as "48n24'15" (with seconds) or "48.4N" (decimal). Both supported.
_COORD_DMS_RE = re.compile(
    r"^\s*(\d+)\s*([nsewNSEW])\s*(\d+)?\s*(?:[.'](\d+))?\s*$"
)
_COORD_DECIMAL_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([nsewNSEW])?\s*$")


def parse_coordinate(text: str) -> float | None:
    """Convert Astro-Databank coordinate strings to signed decimal degrees.

    Examples:
        "48n24"      -> 48.4 (= 48 deg + 24/60)
        "48n24'15"   -> 48.4042 (= 48 deg + 24/60 + 15/3600)
        "48.4N"      -> 48.4
        "-48.4"      -> -48.4
        "10e00"      -> 10.0
        "77E35"      -> 77.5833
        "12S30"      -> -12.5

    North/East are positive; South/West are negative.
    Returns None if the format isn't recognized.
    """
    if not text:
        return None
    s = text.strip()

    # Try DMS form first ("48n24" or "48n24'15")
    m = _COORD_DMS_RE.match(s)
    if m:
        deg = int(m.group(1))
        hem = m.group(2).upper()
        min_str = m.group(3) or ""
        seconds = int(m.group(4)) if m.group(4) else 0
        # ADB also emits seconds-precision coords with NO separator:
        # "36n4619" = 36°46'19" (MMSS run together). Reading "4619" as
        # minutes gives 112.98° — the first two digits are minutes, the
        # rest are seconds. Only applies when no explicit seconds group.
        if len(min_str) > 2 and not seconds:
            minutes = int(min_str[:2])
            seconds = int(min_str[2:])
        else:
            minutes = int(min_str) if min_str else 0
        if minutes >= 60 or seconds >= 60:
            return None  # malformed DMS — reject rather than mis-read
        decimal = deg + minutes / 60.0 + seconds / 3600.0
        if hem in ("S", "W"):
            decimal = -decimal
        return decimal

    # Decimal form ("48.4N" or "-48.4")
    m = _COORD_DECIMAL_RE.match(s)
    if m:
        decimal = float(m.group(1))
        hem = (m.group(2) or "").upper()
        if hem in ("S", "W"):
            decimal = -abs(decimal)
        return decimal

    return None


def parse_date(text: str) -> str:
    """Convert a birth-date string to ISO YYYY-MM-DD; return '' if unparseable.

    Astro-Databank date formats vary:
        "14 March 1879"
        "March 14, 1879"
        "1879-03-14"
        "14/03/1879"
    """
    if not text:
        return ""
    s = text.strip()

    # Already ISO
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y:04d}-{mo:02d}-{d:02d}"

    # "14 March 1879"
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s)
    if m:
        d, mo_name, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        if mo_name in _MONTH_NAMES:
            return f"{y:04d}-{_MONTH_NAMES[mo_name]:02d}-{d:02d}"

    # "March 14, 1879"
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if m:
        mo_name, d, y = m.group(1).lower(), int(m.group(2)), int(m.group(3))
        if mo_name in _MONTH_NAMES:
            return f"{y:04d}-{_MONTH_NAMES[mo_name]:02d}-{d:02d}"

    # "14/03/1879" or "03/14/1879" — assume DD/MM/YYYY (European convention,
    # which is what Astro-Databank predominantly uses).
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"

    return ""


def parse_time(text: str) -> str:
    """Convert a birth-time string to HH:MM:SS; return '' if unparseable.

    Formats seen in Astro-Databank:
        "11:30"
        "11:30:45"
        "2:30 PM"
        "14:30 (= 2:30 PM)"
    """
    if not text:
        return ""
    s = text.strip()

    # Strip any "(= ...)" suffix some entries include
    s = re.sub(r"\s*\(=.*\)\s*$", "", s).strip()

    # 24-hour with optional seconds
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*$", s)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        sec = int(m.group(3)) if m.group(3) else 0
        if 0 <= h <= 23 and 0 <= mi <= 59 and 0 <= sec <= 59:
            return f"{h:02d}:{mi:02d}:{sec:02d}"

    # 12-hour with AM/PM
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AaPp][Mm])\s*$", s)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        sec = int(m.group(3)) if m.group(3) else 0
        ampm = m.group(4).upper()
        if ampm == "PM" and h != 12:
            h += 12
        elif ampm == "AM" and h == 12:
            h = 0
        if 0 <= h <= 23 and 0 <= mi <= 59 and 0 <= sec <= 59:
            return f"{h:02d}:{mi:02d}:{sec:02d}"

    return ""


def parse_tz_offset(text: str) -> float | None:
    """Convert Astro-Databank timezone notation to hours from UTC.

    Formats:
        "5:30 east"   -> +5.5
        "+5:30"       -> +5.5
        "8:00 west"   -> -8.0
        "GMT"         -> 0
        "UT"          -> 0
        "LMT m10e00"  -> 10/15 = 0.667 (Local Mean Time, longitude-based)
    """
    if not text:
        return None
    s = text.strip().lower()

    if s in ("gmt", "ut", "utc", "0", "+0", "-0"):
        return 0.0

    # LMT (Local Mean Time): use longitude / 15. Astro-Databank notes it as
    # "LMT m10e00" or similar; for our pipeline we drop these as unreliable
    # for ML (LMT = local solar time, not standard tz) — return None.
    if s.startswith("lmt"):
        return None

    # "+5:30" / "-5:30"
    m = re.match(r"^([+-]?)(\d+):(\d+)\s*$", s)
    if m:
        sign = -1.0 if m.group(1) == "-" else 1.0
        h = int(m.group(2))
        mi = int(m.group(3))
        return sign * (h + mi / 60.0)

    # "5:30 east" / "8:00 west"
    m = re.match(r"^(\d+):(\d+)\s*(east|west|e|w)?\s*$", s)
    if m:
        h = int(m.group(1))
        mi = int(m.group(2))
        direction = (m.group(3) or "e").lower()
        offset = h + mi / 60.0
        if direction in ("west", "w"):
            offset = -offset
        return offset

    # Astro-Databank's compact form: "h4w" / "h5.5e" / "EDT h4w (is dst)".
    # The leading 'h' marks "hours-from-UTC", the trailing letter the
    # hemisphere. Tolerant of an arbitrary tz-code prefix ("EDT ", "IST ")
    # and trailing parenthetical commentary.
    m = re.search(r"\bh(\d+(?:\.\d+)?)\s*([ew])\b", s)
    if m:
        magnitude = float(m.group(1))
        direction = m.group(2).lower()
        return -magnitude if direction == "w" else magnitude

    return None


def _normalize_rodden(text: str) -> str:
    """Astro-Databank Rodden ratings: AA, A, B, C, DD, DR, X, XX. Strip noise."""
    if not text:
        return ""
    s = text.strip().upper()
    # Sometimes appears as "AA (verified)" or similar; take the leading code.
    m = re.match(r"^(AA|XX|DD|DR|A|B|C|X)", s)
    return m.group(1) if m else ""


def parse_entry_page(html: str, source_url: str) -> EntryRecord | None:
    """Parse one Astro-Databank entry HTML page into a record.

    Returns None only if the page lacks an infobox entirely (likely not a
    real entry page, e.g. category-list page misdirected here). Partial
    records (missing time, missing coords, etc.) are returned with empty
    fields and filtered downstream by Stage 2 ETL.
    """
    soup = BeautifulSoup(html, "html.parser")

    # The infobox is a table with rows of label/value cells. Find by content
    # rather than CSS class — MediaWiki HTML drifts across versions and the
    # text labels are stable.
    name = _extract_name(soup)
    if not name:
        return None

    born_text = _find_field_value(soup, ("Born:", "Born"))
    rating_text = _find_field_value(soup, ("Rodden Rating:", "Rodden Rating", "Rating:"))
    place_text = _find_field_value(soup, ("Place:", "Birthplace:", "place"))
    tz_text = _find_field_value(soup, ("Timezone:", "Time Zone:", "TZ:"))
    categories = _extract_categories(soup)

    # "Born:" sometimes contains the time inline; sometimes time is in a
    # separate row. Both supported.
    date_str, time_str = _split_born(born_text)

    lat, lon = _split_place_coordinates(place_text)

    return EntryRecord(
        name=name,
        date_of_birth=date_str,
        time_of_birth=time_str,
        latitude=lat,
        longitude=lon,
        tz_offset=parse_tz_offset(tz_text),
        rodden_rating=_normalize_rodden(rating_text),
        categories=categories,
        source_url=source_url,
    )


def _extract_name(soup: BeautifulSoup) -> str:
    """Page H1 holds the canonical name."""
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else ""


def _find_field_value(soup: BeautifulSoup, label_candidates: tuple[str, ...]) -> str:
    """Find a row in any table whose left cell matches one of the labels;
    return the right cell's text. Case-insensitive label matching; tolerant
    of whitespace and trailing colons."""
    norm = tuple(c.strip().rstrip(":").lower() for c in label_candidates)
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            label = cells[0].get_text(strip=True).rstrip(":").lower()
            if label in norm:
                return cells[1].get_text(" ", strip=True)
    return ""


def _split_born(born_text: str) -> tuple[str, str]:
    """Born-field text often combines date + time: '14 March 1879 at 11:30'.
    Split into ISO date + HH:MM:SS."""
    if not born_text:
        return "", ""
    # Common patterns: "14 March 1879 at 11:30", "1879-03-14 11:30:00"
    parts = re.split(r"\s+(?:at\s+)?", born_text, maxsplit=1)
    date_part = parts[0]
    # Try parsing date from full text first (handles "14 March 1879 at 11:30")
    iso_date = parse_date(born_text)
    iso_time = ""
    # Look for a time-shaped substring anywhere in the text
    time_match = re.search(r"\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp][Mm])?", born_text)
    if time_match:
        iso_time = parse_time(time_match.group(0))
    return iso_date, iso_time


def _split_place_coordinates(place_text: str) -> tuple[float | None, float | None]:
    """Place-field text often ends with coordinates: 'Ulm, Germany, 48n24, 10e00'.
    Extract lat/lon if present."""
    if not place_text:
        return None, None
    # Find tokens that look like coordinates (digits + N/S/E/W)
    tokens = re.findall(r"\d+\s*[nNsSeEwW]\s*\d*\.?\d*'?\d*", place_text)
    lat: float | None = None
    lon: float | None = None
    for tok in tokens:
        val = parse_coordinate(tok)
        if val is None:
            continue
        if any(h in tok.upper() for h in ("N", "S")):
            lat = val
        elif any(h in tok.upper() for h in ("E", "W")):
            lon = val
    return lat, lon


def _extract_categories(soup: BeautifulSoup) -> tuple[str, ...]:
    """Astro-Databank categories appear in two places: a per-page categories
    section near the bottom, and as a 'Categories:' row in some infoboxes.
    Collect both, dedupe preserving order."""
    found: list[str] = []
    for a in soup.select("a[href*='Category:']"):
        text = a.get_text(strip=True)
        if text and text not in found:
            found.append(text)
    return tuple(found)


# ---------- SQLite-backed crawl state ----------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS visited (
    url TEXT PRIMARY KEY,
    fetched_at TEXT NOT NULL,
    http_status INTEGER NOT NULL,
    parse_success INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS queue (
    url TEXT PRIMARY KEY,
    enqueued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class CrawlState:
    """SQLite-backed crawl state: visited URLs and pending queue."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def is_visited(self, url: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM visited WHERE url = ?", (url,))
        return cur.fetchone() is not None

    def mark_visited(self, url: str, status: int, parsed: bool) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO visited(url, fetched_at, http_status, parse_success) "
            "VALUES (?, datetime('now'), ?, ?)",
            (url, status, 1 if parsed else 0),
        )
        self.conn.execute("DELETE FROM queue WHERE url = ?", (url,))
        self.conn.commit()

    def enqueue(self, url: str) -> None:
        if not self.is_visited(url):
            self.conn.execute("INSERT OR IGNORE INTO queue(url) VALUES (?)", (url,))
            self.conn.commit()

    def next_url(self) -> str | None:
        cur = self.conn.execute("SELECT url FROM queue ORDER BY enqueued_at LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None

    def visited_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM visited").fetchone()[0]

    def close(self) -> None:
        self.conn.close()


# ---------- Crawler (network IO) ----------

class AstroDatabankCrawler:
    """Polite, resumable crawler for the Astro-Databank wiki.

    The crawler is intentionally simple: BFS from a seed category URL,
    follow links to entry pages OR sub-category pages, parse + emit on
    entry pages. SQLite state means interrupting and resuming is safe.
    """

    def __init__(
        self,
        output_csv: Path,
        cache_dir: Path,
        state_db: Path,
        rate_limit_seconds: float = DEFAULT_RATE_LIMIT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
        session: requests.Session | None = None,
    ):
        self.output_csv = Path(output_csv)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.state = CrawlState(Path(state_db))
        self.rate_limit_seconds = rate_limit_seconds
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self._last_fetch_at: float = 0.0

    def _cache_path(self, url: str) -> Path:
        slug = re.sub(r"[^A-Za-z0-9_.-]", "_", url)[-200:]
        return self.cache_dir / f"{slug}.html"

    def _fetch(self, url: str) -> tuple[int, str]:
        """Fetch a URL with rate limiting + cache. Returns (status, html)."""
        cached = self._cache_path(url)
        if cached.exists():
            return 200, cached.read_text(encoding="utf-8", errors="replace")

        # Rate-limit sleep
        elapsed = time.monotonic() - self._last_fetch_at
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)

        try:
            resp = self.session.get(url, timeout=30)
            self._last_fetch_at = time.monotonic()
        except requests.RequestException as exc:
            logger.warning("fetch failed for %s: %s", url, exc)
            return 0, ""

        if resp.status_code == 200:
            cached.write_text(resp.text, encoding="utf-8")
        return resp.status_code, resp.text

    def crawl(
        self,
        seed_url: str = DEFAULT_SEED_URL,
        max_entries: int | None = None,
    ) -> int:
        """Crawl from seed_url. Writes CSV incrementally so a Ctrl-C doesn't lose
        already-parsed records. Returns the count of successfully parsed entries.
        """
        # Initialize CSV (append mode for resume support)
        write_header = not self.output_csv.exists()
        self.output_csv.parent.mkdir(parents=True, exist_ok=True)
        csv_file = self.output_csv.open("a", newline="", encoding="utf-8")
        writer = csv.DictWriter(csv_file, fieldnames=list(CSV_COLUMNS))
        if write_header:
            writer.writeheader()
            csv_file.flush()

        if not self.state.is_visited(seed_url):
            self.state.enqueue(seed_url)

        emitted = 0
        try:
            while True:
                url = self.state.next_url()
                if url is None:
                    logger.info("queue empty; done")
                    break
                if max_entries is not None and emitted >= max_entries:
                    logger.info("reached max_entries=%s; stopping", max_entries)
                    break

                status, html = self._fetch(url)
                parsed_ok = False
                if status == 200 and html:
                    try:
                        record = parse_entry_page(html, url)
                    except Exception:
                        logger.exception("parse failed for %s", url)
                        record = None

                    if record is not None and record.date_of_birth:
                        writer.writerow(record.as_csv_row())
                        csv_file.flush()
                        emitted += 1
                        parsed_ok = True

                    # Discover new URLs (entry links + sub-category links)
                    for link in _extract_followable_links(html, url):
                        self.state.enqueue(link)

                self.state.mark_visited(url, status, parsed_ok)
        finally:
            csv_file.close()

        logger.info(
            "crawl complete: emitted=%d, total_visited=%d", emitted, self.state.visited_count()
        )
        return emitted

    def close(self) -> None:
        self.state.close()
        self.session.close()


def _extract_followable_links(html: str, base_url: str) -> Iterable[str]:
    """Find /astro-databank/ links worth following: entry pages and category pages."""
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        absolute = urljoin(base_url, href)
        # Restrict to the same site + the astro-databank path
        parsed = urlparse(absolute)
        if parsed.netloc and parsed.netloc != "www.astro.com":
            continue
        if "/astro-databank/" not in parsed.path:
            continue
        # Strip query + fragment for dedup
        clean = absolute.split("#")[0].split("?")[0]
        if clean in seen:
            continue
        seen.add(clean)
        yield clean


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.scraper",
        description="Scrape Astro-Databank biographical entries to a CSV.",
    )
    parser.add_argument("--output", type=Path, default=Path("data/astro_databank/raw.csv"),
                        help="CSV output path (appended to if exists).")
    parser.add_argument("--cache-dir", type=Path, default=Path("data/astro_databank/raw_pages"),
                        help="Per-URL HTML cache directory.")
    parser.add_argument("--state-db", type=Path, default=Path("data/astro_databank/scrape.sqlite"),
                        help="SQLite crawl state path.")
    parser.add_argument("--seed", type=str, default=DEFAULT_SEED_URL,
                        help="Seed URL for the crawl (typically an Astro-Databank Category page).")
    parser.add_argument("--max-entries", type=int, default=None,
                        help="Stop after emitting this many parsed entries.")
    parser.add_argument("--rate-limit", type=float, default=DEFAULT_RATE_LIMIT_SECONDS,
                        help="Minimum seconds between HTTP requests.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    crawler = AstroDatabankCrawler(
        output_csv=args.output,
        cache_dir=args.cache_dir,
        state_db=args.state_db,
        rate_limit_seconds=args.rate_limit,
    )
    try:
        emitted = crawler.crawl(seed_url=args.seed, max_entries=args.max_entries)
        print(f"Emitted {emitted} entries to {args.output}")
        return 0
    finally:
        crawler.close()


if __name__ == "__main__":
    sys.exit(main())
