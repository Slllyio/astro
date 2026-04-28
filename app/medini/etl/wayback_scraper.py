"""Wayback Machine adapter for the Astro-Databank scraper.

Astro-Databank's live wiki is now behind a JavaScript bot challenge
(`/cgi/prep.cgi/...` interstitial that the existing requests-based crawler
can't pass). The archive.org Wayback Machine snapshots predate the
challenge and are publicly retrievable, so this module pivots to:

  1. Query the Wayback CDX API for every archived URL matching
     `www.astro.com/astro-databank/*`. Returns ~32k snapshots covering
     ~14k unique entries.
  2. De-duplicate to the latest snapshot per entry, filter out non-entry
     URLs (Categories, License pages, Main_Page, assets).
  3. Fetch each entry via `https://web.archive.org/web/<timestamp>id_/<url>`
     — the `id_` suffix returns raw archived HTML without the Wayback
     toolbar overlay, so the existing `parse_entry_page` works unchanged.
  4. Emit the same CSV schema Stage 2 ETL consumes; downstream pipeline
     (`databank_etl` -> `train_classifier`) is identical to the live path.

Polite to archive.org: 4-second rate limit (= ~15 req/min, their published
threshold for `/web/` endpoints), exponential backoff on 5xx, SQLite-backed
crawl state for resumability, per-URL HTML cache for re-runs.

CLI:
    python -m app.medini.etl.wayback_scraper \\
        --output     data/astro_databank/raw_wayback.csv \\
        --cache-dir  data/astro_databank/wayback_cache \\
        --state-db   data/astro_databank/wayback.sqlite \\
        --cdx-cache  data/astro_databank/wayback_cdx.json \\
        --max-entries 5000 \\
        --rate-limit 4.0
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import logging
import re
import sys
import time
import urllib.parse
from collections.abc import Iterable
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

from app.medini.etl.scraper import (
    CSV_COLUMNS,
    CrawlState,
    EntryRecord,
    parse_coordinate,
    parse_date,
    parse_time,
    parse_tz_offset,
)

logger = logging.getLogger(__name__)

# Polite to archive.org. Their docs list 15 req/min as the soft limit on
# /web/ replay endpoints; 4 seconds gives ~15 req/min and absorbs jitter.
DEFAULT_RATE_LIMIT_SECONDS = 4.0
DEFAULT_USER_AGENT = (
    "Slllyio-AstroResearch/0.1 (medini-intelligence; "
    "github.com/Slllyio/astro; archive.org via wayback CDX)"
)

CDX_ENDPOINT = "http://web.archive.org/cdx/search/cdx"
WAYBACK_REPLAY_TEMPLATE = "https://web.archive.org/web/{timestamp}id_/{original}"

# Path-prefix substrings that mean "not a biographical entry" and so should
# be skipped from the entry list. Mirrors what the live scraper would skip
# but applied at CDX-filter time so we don't fetch them at all.
_NON_ENTRY_PREFIXES: tuple[str, ...] = (
    "Category:", "Special:", "Help:", "File:", "Image:",
    "Talk:", "User:", "MediaWiki:", "License/", "Template:",
)
_NON_ENTRY_NAMES: frozenset[str] = frozenset({
    "Main_Page", "Bad_astrology", "AstroDatabank",
    "About_AstroDatabank", "Privacy_policy",
})
# File extensions we explicitly skip — CDX returns CSS/JS/images mixed in
# with HTML, and even with mimetype=text/html filter we get the occasional
# robots.txt-shaped exception.
_ASSET_EXTENSIONS: tuple[str, ...] = (
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".xml",
)


# ---------- Wayback-specific HTML parser ----------

# Astro-Databank infobox uses label cells like "<td><b>born on</b></td>" rather
# than <th> headers — so the existing scraper's label index doesn't fire.
# Map label-text to the field key we want; lowercase + stripped + colon-trimmed.
_LABEL_MAP: dict[str, str] = {
    "born on": "born",
    "born":    "born",
    "place":   "place",
    "timezone":"timezone",
    "time zone":"timezone",
}

# Rodden rating sits *inside* a single cell as inline markup:
#   <small><a>Rodden Rating</a></small> <b>AA</b>
# rather than a label/value row. Pull the rating value with a tight regex.
_RODDEN_INLINE_RE = re.compile(
    r"Rodden\s*Rating\s*</a>\s*</small>\s*<b>\s*([A-Z]{1,3})\s*</b>",
    re.IGNORECASE,
)

# wgCategories array embedded in mw.config.set({...}) is the most reliable
# category source — much cleaner than the rendered footer which gets
# polluted by Wayback toolbar links.
_WG_CATEGORIES_RE = re.compile(r'"wgCategories"\s*:\s*(\[[^\]]+\])')


def _wb_label_for_cell(cell: Tag) -> str | None:
    """Normalise the label-cell text and map to a known field key.

    The Wayback infobox often wraps labels in <b> or <a>, so we strip both
    inner tags and outer whitespace, then lookup. Unrecognised labels
    return None so the caller can skip them.
    """
    text = cell.get_text(" ", strip=True).rstrip(":").strip().lower()
    return _LABEL_MAP.get(text)


def _wb_extract_infobox_fields(soup: BeautifulSoup) -> dict[str, str]:
    """Walk every <tr> in the article body and collect (label_key, value_text).

    Multiple tables exist on the page; we don't care which one — labels are
    unique enough that collisions don't occur in practice.
    """
    found: dict[str, str] = {}
    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        key = _wb_label_for_cell(cells[0])
        if key is None or key in found:
            continue
        # Use space-joined text for the value so inline <small> coords
        # ("42n22, 71w04") survive intact.
        found[key] = cells[1].get_text(" ", strip=True)
    return found


def _wb_extract_rodden(html: str) -> str:
    """Pull the Rodden rating from the inline `<small>RR</a></small> <b>AA</b>`
    pattern. Returns "" if not present (so downstream filter skips the row)."""
    m = _RODDEN_INLINE_RE.search(html)
    if m is None:
        return ""
    return m.group(1).upper()


def _wb_extract_categories(html: str) -> tuple[str, ...]:
    """Pull wgCategories from the inlined mw.config.set({...}) JS blob.

    Falls back to empty tuple if not found — most pages that lack this
    blob also lack categories anyway, so this is a clean signal that the
    page is malformed or non-canonical (e.g. a redirect).
    """
    m = _WG_CATEGORIES_RE.search(html)
    if m is None:
        return ()
    try:
        cats = json.loads(m.group(1))
    except (ValueError, json.JSONDecodeError):
        return ()
    return tuple(c for c in cats if isinstance(c, str))


def _wb_extract_name(soup: BeautifulSoup) -> str:
    """The page H1 with id=firstHeading carries the canonical 'Last, First'
    name on every Astro-Databank entry."""
    h1 = soup.select_one("#firstHeading") or soup.find("h1")
    return h1.get_text(strip=True) if h1 else ""


def _wb_split_place(place_text: str) -> tuple[float | None, float | None]:
    """Place values look like 'Boston, Massachusetts, 42n22, 71w04'.
    Tokenize, run each candidate through `parse_coordinate`, classify by
    the N/S/E/W hemisphere letter."""
    if not place_text:
        return None, None
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


def _wb_split_born(born_text: str) -> tuple[str, str]:
    """'5 May 1950 at 19:05 (= 7:05 PM)' -> ('1950-05-05', '19:05:00')."""
    if not born_text:
        return "", ""
    iso_date = parse_date(born_text)
    iso_time = ""
    time_match = re.search(r"\d{1,2}:\d{2}(?::\d{2})?\s*(?:[AaPp][Mm])?", born_text)
    if time_match:
        iso_time = parse_time(time_match.group(0))
    return iso_date, iso_time


def parse_wayback_entry(html: str, source_url: str) -> EntryRecord | None:
    """Parse a Wayback-archived Astro-Databank entry into an EntryRecord.

    Strict: returns None if the H1 is missing (signals the page wasn't
    a real entry — e.g. a Wayback 404 page that slipped through). Lets
    rows with missing time / Rodden / coords through; downstream Stage 2
    ETL filters those out via _is_aa_complete, so we don't double-filter.
    """
    soup = BeautifulSoup(html, "html.parser")
    # The Wayback toolbar can inject content inside the article — strip the
    # Wayback chrome before parsing the article body.
    for el in soup.select("#wm-ipp, #wm-ipp-base, .wm-toolbar"):
        el.decompose()
    name = _wb_extract_name(soup)
    if not name:
        return None

    fields = _wb_extract_infobox_fields(soup)
    born_text = fields.get("born", "")
    place_text = fields.get("place", "")
    tz_text = fields.get("timezone", "")

    date_str, time_str = _wb_split_born(born_text)
    lat, lon = _wb_split_place(place_text)
    rodden = _wb_extract_rodden(html)
    categories = _wb_extract_categories(html)

    return EntryRecord(
        name=name,
        date_of_birth=date_str,
        time_of_birth=time_str,
        latitude=lat,
        longitude=lon,
        tz_offset=parse_tz_offset(tz_text),
        rodden_rating=rodden,
        categories=categories,
        source_url=source_url,
    )


# ---------- Pure functions (unit-testable) ----------

def wayback_replay_url(timestamp: str, original: str) -> str:
    """Build the Wayback replay URL that returns raw archived HTML.

    The `id_` suffix on the timestamp asks for the identity-content
    (no Wayback toolbar injection), which is what we want for parsing.
    """
    return WAYBACK_REPLAY_TEMPLATE.format(timestamp=timestamp, original=original)


def is_entry_url(original_url: str) -> bool:
    """True if the URL looks like a biographical entry page on Astro-Databank.

    We skip:
      - Anything not on www.astro.com / astro.com (third-party scrapes
        that mention 'astro-databank' in their path)
      - Category / Special / Help / Talk / etc. namespaces
      - License pages, the Main_Page, the meta entries
      - Asset URLs (CSS, JS, images)
      - The bare /astro-databank/ root
    """
    parsed = urllib.parse.urlparse(original_url)
    host = (parsed.netloc or "").lower().split(":")[0]
    if host not in ("www.astro.com", "astro.com"):
        return False
    if "astro-databank" not in original_url:
        return False
    # Slice off everything up to and including "astro-databank/".
    parts = original_url.split("astro-databank/", 1)
    if len(parts) != 2:
        return False
    path = parts[1]
    # Strip query + fragment
    path = path.split("?")[0].split("#")[0]
    # URL-decode so accented names like Élie come through as plain text.
    path = urllib.parse.unquote(path)
    if not path or path == "/":
        return False
    # Skip the meta / namespace pages
    for prefix in _NON_ENTRY_PREFIXES:
        if path.startswith(prefix):
            return False
    if path in _NON_ENTRY_NAMES:
        return False
    # Asset extensions
    lower = path.lower()
    if any(lower.endswith(ext) for ext in _ASSET_EXTENSIONS):
        return False
    return True


def dedupe_to_latest_snapshot(
    cdx_rows: Iterable[tuple[str, str]],
) -> dict[str, str]:
    """From CDX rows of (timestamp, original_url), pick the latest
    timestamp per unique entry path.

    Returns: {original_url: timestamp}. The original URL is kept as
    the key (rather than the path) so downstream code can build the
    full replay URL without re-derivation.
    """
    latest: dict[str, str] = {}
    for ts, original in cdx_rows:
        # Normalize the URL for dedup: strip query params + protocol diffs.
        # Two snapshots of the same entry on different days should collapse.
        canonical = _canonicalize_entry_url(original)
        existing_ts = latest.get(canonical)
        if existing_ts is None or ts > existing_ts:
            latest[canonical] = ts
    return latest


def _canonicalize_entry_url(url: str) -> str:
    """Strip query params + force https + no trailing slash for entries."""
    # Drop query/fragment.
    url = url.split("?")[0].split("#")[0]
    # Force https://www.astro.com — CDX mixes http/https.
    url = re.sub(r"^https?://(www\.)?astro\.com:?\d*", "https://www.astro.com", url)
    return url.rstrip("/")


# ---------- CDX client ----------

class WaybackCDXClient:
    """Tiny client for the Wayback CDX search API."""

    def __init__(
        self,
        session: requests.Session | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = user_agent

    def list_entries(
        self,
        url_pattern: str = "www.astro.com/astro-databank/*",
        from_date: str = "20200101",
        to_date: str = "20251231",
        cache_path: Path | None = None,
    ) -> dict[str, str]:
        """Return {entry_url: latest_timestamp} for matching CDX rows.

        Caches the raw CDX response on disk if cache_path is provided —
        the index is ~1MB and shouldn't be fetched on every smoke-test
        run. Pass `--cdx-cache` from the CLI to populate this.
        """
        if cache_path is not None and cache_path.exists():
            logger.info("loading CDX index from cache: %s", cache_path)
            data = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            params = {
                "url": url_pattern,
                "output": "json",
                "filter": ["statuscode:200", "mimetype:text/html"],
                "from": from_date,
                "to": to_date,
                "limit": "50000",
            }
            logger.info(
                "querying CDX API for archived entries (pattern=%s, %s..%s)",
                url_pattern, from_date, to_date,
            )
            r = self.session.get(CDX_ENDPOINT, params=params, timeout=120)
            r.raise_for_status()
            data = r.json()
            if cache_path is not None:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(data), encoding="utf-8")
                logger.info("CDX index cached to %s", cache_path)

        # First row is the column header
        if not data or not isinstance(data[0], list):
            return {}
        header = data[0]
        ts_idx = header.index("timestamp")
        url_idx = header.index("original")

        rows: list[tuple[str, str]] = []
        for r in data[1:]:
            if not isinstance(r, list) or len(r) <= max(ts_idx, url_idx):
                continue
            url = r[url_idx]
            if not is_entry_url(url):
                continue
            rows.append((r[ts_idx], url))

        latest = dedupe_to_latest_snapshot(rows)
        logger.info("CDX index → %d entries after filter+dedup", len(latest))
        return latest


# ---------- Crawler ----------

@dataclasses.dataclass
class WaybackCrawlStats:
    queued: int = 0
    fetched: int = 0
    parsed: int = 0
    skipped_no_birthdate: int = 0
    failed_http: int = 0
    failed_parse: int = 0


class WaybackCrawler:
    """Polite, resumable crawler over a pre-computed Wayback entry list.

    Unlike the live Astro-Databank crawler, this one doesn't BFS from a
    seed — the CDX API gives us the full sitemap up front, so we just
    iterate. SQLite state (URL → visited?) makes resume safe; per-URL
    HTML cache means re-runs and ETL re-parses don't re-fetch.
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

    def _fetch(self, replay_url: str) -> tuple[int, str]:
        """Fetch a Wayback replay URL with rate limit + cache."""
        cached = self._cache_path(replay_url)
        if cached.exists():
            return 200, cached.read_text(encoding="utf-8", errors="replace")

        elapsed = time.monotonic() - self._last_fetch_at
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)

        try:
            resp = self.session.get(replay_url, timeout=60, allow_redirects=True)
            self._last_fetch_at = time.monotonic()
        except requests.RequestException as exc:
            logger.warning("fetch failed for %s: %s", replay_url, exc)
            return 0, ""

        if resp.status_code == 200:
            cached.write_text(resp.text, encoding="utf-8")
        return resp.status_code, resp.text

    def crawl(
        self,
        entries: dict[str, str],
        max_entries: int | None = None,
    ) -> WaybackCrawlStats:
        """Fetch + parse every (url, timestamp) in `entries`. CSV is appended
        in real-time so a Ctrl-C doesn't lose already-parsed records.

        `max_entries` caps total parsed records (not requests). Useful for
        smoke tests; pass None for the full crawl.
        """
        write_header = not self.output_csv.exists()
        self.output_csv.parent.mkdir(parents=True, exist_ok=True)
        csv_file = self.output_csv.open("a", newline="", encoding="utf-8")
        writer = csv.DictWriter(csv_file, fieldnames=list(CSV_COLUMNS))
        if write_header:
            writer.writeheader()
            csv_file.flush()

        stats = WaybackCrawlStats(queued=len(entries))
        try:
            for original_url, timestamp in entries.items():
                if max_entries is not None and stats.parsed >= max_entries:
                    logger.info("reached max_entries=%d; stopping", max_entries)
                    break

                replay_url = wayback_replay_url(timestamp, original_url)
                if self.state.is_visited(replay_url):
                    continue

                status, html = self._fetch(replay_url)
                stats.fetched += 1
                parsed_ok = False
                if status != 200 or not html:
                    stats.failed_http += 1
                    self.state.mark_visited(replay_url, status, parsed=False)
                    continue

                try:
                    record: EntryRecord | None = parse_wayback_entry(
                        html, original_url,
                    )
                except Exception:
                    logger.exception("parse failed for %s", original_url)
                    record = None
                    stats.failed_parse += 1

                if record is not None and record.date_of_birth:
                    writer.writerow(record.as_csv_row())
                    csv_file.flush()
                    stats.parsed += 1
                    parsed_ok = True
                elif record is not None:
                    stats.skipped_no_birthdate += 1

                self.state.mark_visited(replay_url, status, parsed=parsed_ok)

                if stats.fetched % 100 == 0:
                    logger.info(
                        "progress: queued=%d fetched=%d parsed=%d "
                        "no_birthdate=%d http_fail=%d parse_fail=%d",
                        stats.queued, stats.fetched, stats.parsed,
                        stats.skipped_no_birthdate, stats.failed_http,
                        stats.failed_parse,
                    )
        finally:
            csv_file.close()

        logger.info(
            "crawl complete: queued=%d fetched=%d parsed=%d "
            "no_birthdate=%d http_fail=%d parse_fail=%d",
            stats.queued, stats.fetched, stats.parsed,
            stats.skipped_no_birthdate, stats.failed_http, stats.failed_parse,
        )
        return stats

    def close(self) -> None:
        self.state.close()
        self.session.close()


# ---------- CLI ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.wayback_scraper",
        description="Scrape archived Astro-Databank entries via the Wayback Machine.",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/astro_databank/raw_wayback.csv"),
        help="CSV output path (appended to if exists).",
    )
    parser.add_argument(
        "--cache-dir", type=Path,
        default=Path("data/astro_databank/wayback_cache"),
        help="Per-URL HTML cache directory.",
    )
    parser.add_argument(
        "--state-db", type=Path,
        default=Path("data/astro_databank/wayback.sqlite"),
        help="SQLite crawl state path.",
    )
    parser.add_argument(
        "--cdx-cache", type=Path,
        default=Path("data/astro_databank/wayback_cdx.json"),
        help="Where to cache the raw CDX API response (~1-3MB JSON).",
    )
    parser.add_argument(
        "--from-date", type=str, default="20200101",
        help="CDX `from` filter (YYYYMMDD). Older snapshots tend to have "
             "more category-page entries; newer snapshots are cleaner.",
    )
    parser.add_argument(
        "--to-date", type=str, default="20251231",
        help="CDX `to` filter.",
    )
    parser.add_argument(
        "--max-entries", type=int, default=None,
        help="Stop after parsing this many entries. None = full corpus.",
    )
    parser.add_argument(
        "--rate-limit", type=float, default=DEFAULT_RATE_LIMIT_SECONDS,
        help="Minimum seconds between Wayback fetches. Default 4.0 = ~15 req/min.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    cdx = WaybackCDXClient()
    entries = cdx.list_entries(
        from_date=args.from_date,
        to_date=args.to_date,
        cache_path=args.cdx_cache,
    )
    if not entries:
        logger.error("CDX returned no entries; aborting")
        return 1

    crawler = WaybackCrawler(
        output_csv=args.output,
        cache_dir=args.cache_dir,
        state_db=args.state_db,
        rate_limit_seconds=args.rate_limit,
    )
    try:
        stats = crawler.crawl(entries, max_entries=args.max_entries)
        print(
            f"queued={stats.queued} fetched={stats.fetched} "
            f"parsed={stats.parsed} no_birthdate={stats.skipped_no_birthdate} "
            f"http_fail={stats.failed_http} parse_fail={stats.failed_parse}"
        )
        return 0
    finally:
        crawler.close()


if __name__ == "__main__":
    sys.exit(main())
