"""Tests for app.medini.etl.scraper.

Three test layers, in increasing scope:
  1. Pure-function parsers (parse_coordinate / _date / _time / _tz_offset).
  2. HTML parsing against fixture pages in tests/fixtures/astro_databank/.
  3. Crawler state-machine tests (SQLite persistence, no network).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.medini.etl.scraper import (
    CSV_COLUMNS,
    AstroDatabankCrawler,
    CrawlState,
    EntryRecord,
    _extract_followable_links,
    _normalize_rodden,
    parse_coordinate,
    parse_date,
    parse_entry_page,
    parse_time,
    parse_tz_offset,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "astro_databank"


# ---------- Coordinate parser ----------

@pytest.mark.parametrize("text,expected", [
    ("48n24", 48.4),                      # 48 deg 24 min N
    ("48N24", 48.4),                      # case insensitive
    ("48n00", 48.0),
    ("12s30", -12.5),                     # South is negative
    ("10e00", 10.0),                      # East
    ("77E35", 77.0 + 35 / 60.0),          # East with non-zero minutes
    ("122w30", -(122.0 + 30 / 60.0)),     # West is negative
    ("48.4N", 48.4),                      # decimal form
    ("48.4", 48.4),                       # bare decimal
    ("-48.4", -48.4),                     # signed
    ("12s30'15", -(12.0 + 30 / 60.0 + 15 / 3600.0)),  # with seconds
])
def test_parse_coordinate(text: str, expected: float) -> None:
    result = parse_coordinate(text)
    assert result is not None
    assert result == pytest.approx(expected, abs=1e-4)


@pytest.mark.parametrize("garbage", ["", "not a coordinate", "abc", "  ", "999z99"])
def test_parse_coordinate_returns_none_for_garbage(garbage: str) -> None:
    assert parse_coordinate(garbage) is None


# ---------- Date parser ----------

@pytest.mark.parametrize("text,expected", [
    ("14 March 1879", "1879-03-14"),
    ("March 14, 1879", "1879-03-14"),
    ("March 14 1879", "1879-03-14"),
    ("1879-03-14", "1879-03-14"),
    ("1879-3-14", "1879-03-14"),
    ("14/03/1879", "1879-03-14"),         # DD/MM/YYYY (European)
    ("1 Jan 2000", "2000-01-01"),
    ("31 December 1999", "1999-12-31"),
])
def test_parse_date(text: str, expected: str) -> None:
    assert parse_date(text) == expected


@pytest.mark.parametrize("garbage", ["", "not a date", "1879", "March", "0/0/0000"])
def test_parse_date_returns_empty_for_unparseable(garbage: str) -> None:
    assert parse_date(garbage) == ""


# ---------- Time parser ----------

@pytest.mark.parametrize("text,expected", [
    ("11:30", "11:30:00"),
    ("11:30:45", "11:30:45"),
    ("00:00", "00:00:00"),
    ("23:59", "23:59:00"),
    ("2:30 PM", "14:30:00"),
    ("12:00 AM", "00:00:00"),             # midnight
    ("12:00 PM", "12:00:00"),             # noon
    ("11:30 (= 11:30 AM)", "11:30:00"),   # parenthetical clarification stripped
])
def test_parse_time(text: str, expected: str) -> None:
    assert parse_time(text) == expected


@pytest.mark.parametrize("garbage", ["", "no time", "25:00", "11:60", "abc"])
def test_parse_time_returns_empty_for_unparseable(garbage: str) -> None:
    assert parse_time(garbage) == ""


# ---------- TZ offset parser ----------

@pytest.mark.parametrize("text,expected", [
    ("5:30 east", 5.5),
    ("8:00 west", -8.0),
    ("+5:30", 5.5),
    ("-8:00", -8.0),
    ("GMT", 0.0),
    ("UT", 0.0),
    ("UTC", 0.0),
])
def test_parse_tz_offset(text: str, expected: float) -> None:
    result = parse_tz_offset(text)
    assert result is not None
    assert result == pytest.approx(expected, abs=1e-4)


@pytest.mark.parametrize("text", [
    "LMT m10e00",   # local mean time, intentionally unparseable
    "",
    "not a tz",
])
def test_parse_tz_offset_returns_none_for_unsupported(text: str) -> None:
    assert parse_tz_offset(text) is None


# ---------- Rodden rating normalization ----------

@pytest.mark.parametrize("text,expected", [
    ("AA", "AA"),
    ("aa", "AA"),
    ("AA (verified)", "AA"),
    ("A", "A"),
    ("DD", "DD"),
    ("DR", "DR"),
    ("XX", "XX"),
    ("X", "X"),
    ("", ""),
    ("Z9", ""),                           # unknown rating
])
def test_normalize_rodden(text: str, expected: str) -> None:
    assert _normalize_rodden(text) == expected


# ---------- HTML page parser (fixture-backed) ----------

def test_parse_entry_page_einstein_fixture() -> None:
    html = (FIXTURE_DIR / "einstein_sample.html").read_text(encoding="utf-8")
    record = parse_entry_page(html, "https://www.astro.com/astro-databank/Albert_Einstein")

    assert record is not None
    assert record.name == "Albert Einstein"
    assert record.date_of_birth == "1879-03-14"
    assert record.time_of_birth == "11:30:00"
    assert record.latitude == pytest.approx(48.4, abs=1e-4)
    assert record.longitude == pytest.approx(10.0, abs=1e-4)
    # LMT timezone is intentionally unsupported — yields None, not an error.
    assert record.tz_offset is None
    assert record.rodden_rating == "AA"
    # Categories: at least the three from the fixture present.
    assert any("Scientist" in c for c in record.categories)
    assert any("Physicist" in c for c in record.categories)
    assert record.source_url == "https://www.astro.com/astro-databank/Albert_Einstein"


def test_parse_entry_page_incomplete_fixture() -> None:
    """Partial entries (year-only birth, X-rated) parse without crashing
    and surface empty fields rather than guessed values."""
    html = (FIXTURE_DIR / "incomplete_sample.html").read_text(encoding="utf-8")
    record = parse_entry_page(html, "https://example/Mystery_Person")

    assert record is not None
    assert record.name == "Mystery Person"
    # "1955" alone isn't enough to produce an ISO date.
    assert record.date_of_birth == ""
    assert record.time_of_birth == ""
    assert record.latitude is None
    assert record.longitude is None
    assert record.rodden_rating == "X"


def test_parse_entry_page_no_infobox_returns_record_with_empty_fields() -> None:
    """Pages without infobox tables still parse if there's an h1 — the
    record will have an empty rating and be filtered out by the ETL."""
    html = (FIXTURE_DIR / "no_infobox.html").read_text(encoding="utf-8")
    record = parse_entry_page(html, "https://example/Category:Politicians")
    assert record is not None
    assert record.name == "Category:Politicians"
    assert record.rodden_rating == ""
    assert record.date_of_birth == ""


def test_parse_entry_page_no_h1_returns_none() -> None:
    """Pages with no h1 tag at all (truly malformed) return None."""
    html = "<html><body><p>nothing useful here</p></body></html>"
    assert parse_entry_page(html, "https://example/garbage") is None


# ---------- EntryRecord serialization ----------

def test_entry_record_as_csv_row() -> None:
    record = EntryRecord(
        name="Test Subject",
        date_of_birth="1990-07-15",
        time_of_birth="12:00:00",
        latitude=12.97,
        longitude=77.59,
        tz_offset=5.5,
        rodden_rating="AA",
        categories=("Vocation : Test", "Notable"),
        source_url="https://example/test",
    )
    row = record.as_csv_row()
    assert set(row.keys()) == set(CSV_COLUMNS)
    assert row["name"] == "Test Subject"
    assert row["latitude"] == "12.970000"
    assert row["longitude"] == "77.590000"
    assert row["tz_offset"] == "5.5000"
    assert row["categories"] == "Vocation : Test;Notable"


def test_entry_record_as_csv_row_handles_none_coordinates() -> None:
    record = EntryRecord(
        name="No Coords", date_of_birth="2000-01-01", time_of_birth="",
        latitude=None, longitude=None, tz_offset=None,
        rodden_rating="DD", categories=(), source_url="https://example/x",
    )
    row = record.as_csv_row()
    assert row["latitude"] == ""
    assert row["longitude"] == ""
    assert row["tz_offset"] == ""
    assert row["categories"] == ""


# ---------- Followable-link extraction ----------

def test_extract_followable_links_keeps_only_astro_databank_paths() -> None:
    html = """
        <a href="/astro-databank/Albert_Einstein">Einstein</a>
        <a href="https://www.astro.com/astro-databank/Marie_Curie">Curie</a>
        <a href="https://example.com/elsewhere">External link</a>
        <a href="/wiki/Other_Article">Other path</a>
        <a href="/astro-databank/Albert_Einstein#section">Hash variant (deduped)</a>
    """
    links = list(_extract_followable_links(html, "https://www.astro.com/astro-databank/Seed"))
    assert "https://www.astro.com/astro-databank/Albert_Einstein" in links
    assert "https://www.astro.com/astro-databank/Marie_Curie" in links
    assert all("example.com" not in url for url in links)
    assert all("/wiki/" not in url for url in links)
    # Hash variants dedupe to the canonical URL.
    assert sum(1 for u in links if u.endswith("Albert_Einstein")) == 1


# ---------- Crawler state (SQLite persistence) ----------

def test_crawl_state_visited_and_queue_round_trip(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    state = CrawlState(db)
    try:
        url = "https://example/page1"
        assert not state.is_visited(url)
        state.enqueue(url)
        assert state.next_url() == url

        state.mark_visited(url, status=200, parsed=True)
        assert state.is_visited(url)
        assert state.next_url() is None  # queue drained
        assert state.visited_count() == 1
    finally:
        state.close()


def test_crawl_state_persists_across_reopens(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    s1 = CrawlState(db)
    s1.enqueue("https://example/a")
    s1.enqueue("https://example/b")
    s1.mark_visited("https://example/a", 200, True)
    s1.close()

    s2 = CrawlState(db)
    try:
        assert s2.is_visited("https://example/a")
        assert not s2.is_visited("https://example/b")
        assert s2.next_url() == "https://example/b"
    finally:
        s2.close()


def test_crawl_state_enqueue_does_not_duplicate(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    state = CrawlState(db)
    try:
        state.enqueue("https://example/a")
        state.enqueue("https://example/a")  # duplicate
        state.enqueue("https://example/a")
        # Only one row in the queue.
        cur = state.conn.execute("SELECT COUNT(*) FROM queue")
        assert cur.fetchone()[0] == 1
    finally:
        state.close()


def test_crawl_state_enqueue_skips_already_visited(tmp_path: Path) -> None:
    db = tmp_path / "state.sqlite"
    state = CrawlState(db)
    try:
        state.mark_visited("https://example/a", 200, True)
        state.enqueue("https://example/a")
        assert state.next_url() is None
    finally:
        state.close()


# ---------- Crawler integration (HTML cache, no network) ----------

def test_crawler_uses_html_cache_when_present(tmp_path: Path) -> None:
    """Pre-populate the cache directory with an HTML file; the crawler
    must read from it instead of attempting a network fetch."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    output = tmp_path / "raw.csv"
    state_db = tmp_path / "state.sqlite"

    # The cache key is derived from the URL — match the scraper's slug rule.
    url = "https://www.astro.com/astro-databank/Albert_Einstein"
    crawler = AstroDatabankCrawler(
        output_csv=output, cache_dir=cache_dir, state_db=state_db,
        rate_limit_seconds=0.0,
    )
    cached_path = crawler._cache_path(url)
    cached_path.write_text(
        (FIXTURE_DIR / "einstein_sample.html").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    try:
        # Network fetch would fail (no monkeypatch needed — this URL would
        # normally hit astro.com but the cache short-circuits).
        status, html = crawler._fetch(url)
        assert status == 200
        assert "Albert Einstein" in html
    finally:
        crawler.close()
