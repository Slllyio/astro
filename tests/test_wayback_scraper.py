"""Tests for app.medini.etl.wayback_scraper.

Pure-function tests for the URL filter / dedup / replay-URL builder.
The CDX client + crawler IO paths are exercised live via the CLI smoke
test; here we just pin the small functions that drive them.
"""
from __future__ import annotations

from app.medini.etl.scraper import parse_tz_offset
from app.medini.etl.wayback_scraper import (
    _canonicalize_entry_url,
    _wb_extract_categories,
    _wb_extract_rodden,
    _wb_split_born,
    _wb_split_place,
    dedupe_to_latest_snapshot,
    is_entry_url,
    parse_wayback_entry,
    wayback_replay_url,
)


# ---------- wayback_replay_url ----------

def test_wayback_replay_url_uses_id_suffix() -> None:
    """The id_ suffix on the timestamp asks Wayback for raw archived
    HTML — without it, we'd get the Wayback toolbar overlay injected
    into the page and our parser would see the wrong DOM."""
    url = wayback_replay_url(
        "20240115013910",
        "https://www.astro.com/astro-databank/Bowie,_David",
    )
    assert url == (
        "https://web.archive.org/web/20240115013910id_/"
        "https://www.astro.com/astro-databank/Bowie,_David"
    )


# ---------- is_entry_url ----------

def test_is_entry_url_accepts_real_entries() -> None:
    assert is_entry_url("https://www.astro.com/astro-databank/Bowie,_David")
    assert is_entry_url("https://www.astro.com/astro-databank/Trump,_Donald")
    assert is_entry_url(
        "http://www.astro.com/astro-databank/%C3%89lie,_Am%C3%A9lie"
    )


def test_is_entry_url_rejects_categories() -> None:
    assert not is_entry_url(
        "https://www.astro.com/astro-databank/Category:All_Astro-Databank_pages"
    )
    assert not is_entry_url(
        "https://www.astro.com/astro-databank/Special:Search"
    )
    assert not is_entry_url(
        "https://www.astro.com/astro-databank/Help:Editing"
    )


def test_is_entry_url_rejects_main_page_and_meta() -> None:
    assert not is_entry_url("https://www.astro.com/astro-databank/Main_Page")
    assert not is_entry_url("https://www.astro.com/astro-databank/Bad_astrology")
    assert not is_entry_url(
        "https://www.astro.com/astro-databank/License/cc-by-3.0"
    )


def test_is_entry_url_rejects_assets() -> None:
    """CDX returns CSS/JS/PNGs mixed in even with mimetype filter applied."""
    assert not is_entry_url("https://www.astro.com/astro-databank/style.css")
    assert not is_entry_url("https://www.astro.com/astro-databank/icon.png")


def test_is_entry_url_rejects_root_and_unrelated() -> None:
    assert not is_entry_url("https://www.astro.com/astro-databank/")
    assert not is_entry_url("https://www.astro.com/astro-databank")
    assert not is_entry_url("https://google.com/astro-databank/Foo")


def test_is_entry_url_strips_query_string_before_filter() -> None:
    """A URL with a tracking query string is still an entry — don't reject
    it just because it has a `?cid=...` suffix."""
    assert is_entry_url(
        "http://www.astro.com/astro-databank/(Soccer)_Arcari,_Bruno?nhor=1&cid=j32q7"
    )


# ---------- _canonicalize_entry_url ----------

def test_canonicalize_drops_query_and_fragment() -> None:
    assert _canonicalize_entry_url(
        "https://www.astro.com/astro-databank/Bowie,_David?foo=1#bar"
    ) == "https://www.astro.com/astro-databank/Bowie,_David"


def test_canonicalize_normalizes_protocol_and_port() -> None:
    """CDX returns http://www.astro.com:80/... and https://www.astro.com/...
    for the same logical entry; canonicalize collapses them so dedup works."""
    a = _canonicalize_entry_url("http://www.astro.com:80/astro-databank/Trump,_Donald")
    b = _canonicalize_entry_url("https://www.astro.com/astro-databank/Trump,_Donald")
    assert a == b


# ---------- dedupe_to_latest_snapshot ----------

def test_dedupe_to_latest_snapshot_keeps_newest() -> None:
    """Multiple snapshots of the same entry should collapse to the most
    recent timestamp — that's what we want at fetch time (latest content
    is most likely to be intact and complete)."""
    rows = [
        ("20210101000000", "https://www.astro.com/astro-databank/Trump,_Donald"),
        ("20240615120000", "https://www.astro.com/astro-databank/Trump,_Donald"),
        ("20230328093045", "https://www.astro.com/astro-databank/Trump,_Donald"),
        ("20220101000000", "http://www.astro.com:80/astro-databank/Trump,_Donald"),
    ]
    result = dedupe_to_latest_snapshot(rows)
    assert len(result) == 1
    canonical = "https://www.astro.com/astro-databank/Trump,_Donald"
    assert result[canonical] == "20240615120000"


def test_dedupe_to_latest_snapshot_preserves_distinct_entries() -> None:
    rows = [
        ("20240101000000", "https://www.astro.com/astro-databank/Bowie,_David"),
        ("20240201000000", "https://www.astro.com/astro-databank/Trump,_Donald"),
    ]
    result = dedupe_to_latest_snapshot(rows)
    assert len(result) == 2


# ---------- parse_tz_offset extension for Astro-Databank h*w/h*e notation ----------

def test_parse_tz_offset_astro_databank_compact_west() -> None:
    """'h4w' = 4 hours west of UTC = -4. Astro-Databank's compact notation."""
    assert parse_tz_offset("h4w") == -4.0
    assert parse_tz_offset("EDT h4w") == -4.0
    assert parse_tz_offset("EDT h4w (is daylight saving time)") == -4.0


def test_parse_tz_offset_astro_databank_compact_east() -> None:
    assert parse_tz_offset("h5e") == 5.0
    assert parse_tz_offset("IST h5.5e") == 5.5


def test_parse_tz_offset_astro_databank_with_decimal() -> None:
    """Half-hour offsets (India, Newfoundland) and 45-min (Nepal, Chatham)
    must decode correctly — full offset value, not 'hours+minutes'."""
    assert parse_tz_offset("h5.5e") == 5.5
    assert parse_tz_offset("h12.75w") == -12.75


# ---------- Wayback parser — small unit cases ----------

def test_wb_split_born_combines_date_and_time() -> None:
    """Wayback infobox cell value: '5 May 1950 at 19:05  (= 7:05 PM )'.
    Returns ISO date + HH:MM:SS time."""
    date_str, time_str = _wb_split_born("5 May 1950 at 19:05  (= 7:05 PM )")
    assert date_str == "1950-05-05"
    assert time_str == "19:05:00"


def test_wb_split_born_no_time_returns_empty_time() -> None:
    date_str, time_str = _wb_split_born("14 March 1879")
    assert date_str == "1879-03-14"
    assert time_str == ""


def test_wb_split_born_blank() -> None:
    assert _wb_split_born("") == ("", "")


def test_wb_split_place_extracts_dms_coords() -> None:
    """Place cell: 'Boston, Massachusetts, 42n22, 71w04'.
    Hemisphere letter classifies the token as lat (N/S) or lon (E/W)."""
    lat, lon = _wb_split_place("Boston, Massachusetts, 42n22,  71w04 ")
    assert lat is not None and abs(lat - (42 + 22/60.0)) < 1e-6
    assert lon is not None and abs(lon - -(71 + 4/60.0)) < 1e-6


def test_wb_split_place_no_coords_returns_nones() -> None:
    assert _wb_split_place("Boston, Massachusetts") == (None, None)


def test_wb_extract_rodden_inline_pattern() -> None:
    """Wayback HTML embeds Rodden Rating inline:
    '<small><a>Rodden Rating</a></small> <b>AA</b>'."""
    html = (
        '<small><a href="/Help:RR" title="Help:RR">Rodden Rating</a></small> '
        '<b>AA</b>'
    )
    assert _wb_extract_rodden(html) == "AA"


def test_wb_extract_rodden_returns_blank_when_absent() -> None:
    assert _wb_extract_rodden("<p>No rating here</p>") == ""


def test_wb_extract_categories_from_mw_config() -> None:
    """wgCategories is a JSON array embedded in mw.config.set({...}).
    Pull every string entry, preserve order."""
    html = (
        '<script>(window.RLQ=window.RLQ||[]).push(function(){'
        'mw.config.set({"wgPageName":"X","wgCategories":'
        '["1950 births","Birthday 5 May","Vocation : Politics : Politician"]});'
        '});</script>'
    )
    cats = _wb_extract_categories(html)
    assert cats == (
        "1950 births",
        "Birthday 5 May",
        "Vocation : Politics : Politician",
    )


def test_wb_extract_categories_returns_empty_when_no_blob() -> None:
    assert _wb_extract_categories("<p>nothing here</p>") == ()


# ---------- parse_wayback_entry — integration ----------

_WAYBACK_FIXTURE_HTML = """<!DOCTYPE html>
<html>
<head><title>Joseph Abboud, horoscope - Astro-Databank</title>
<script>(window.RLQ=window.RLQ||[]).push(function(){mw.config.set({"wgPageName":"Abboud,_Joseph","wgCategories":["1950 births","Birthday 5 May","Vocation : Beauty : Designer/ Fashion"]});});</script>
</head><body>
<h1 id="firstHeading" class="firstHeading">Abboud, Joseph</h1>
<table><tbody>
<tr><td><b>born on</b></td><td>5 May 1950 at 19:05  <small>(= 7:05 PM )</small></td></tr>
<tr><td><b>Place</b></td><td>Boston, Massachusetts, <small>42n22,  71w04 </small></td></tr>
<tr><td><b><a href="/Help:Timezone">Timezone</a></b></td><td>EDT h4w (is daylight saving time)</td></tr>
<tr><td><small><a href="/Help:RR">Rodden Rating</a></small> <b>AA</b></td></tr>
</tbody></table>
</body></html>
"""


def test_parse_wayback_entry_full_extraction() -> None:
    """End-to-end on a synthetic-but-realistic Wayback HTML — every field
    should populate, mirroring what the live cache produces."""
    rec = parse_wayback_entry(
        _WAYBACK_FIXTURE_HTML,
        "https://www.astro.com/astro-databank/Abboud,_Joseph",
    )
    assert rec is not None
    assert rec.name == "Abboud, Joseph"
    assert rec.date_of_birth == "1950-05-05"
    assert rec.time_of_birth == "19:05:00"
    assert rec.latitude is not None and abs(rec.latitude - (42 + 22/60.0)) < 1e-6
    assert rec.longitude is not None and abs(rec.longitude - -(71 + 4/60.0)) < 1e-6
    assert rec.tz_offset == -4.0
    assert rec.rodden_rating == "AA"
    assert "Vocation : Beauty : Designer/ Fashion" in rec.categories
    assert rec.source_url.endswith("Abboud,_Joseph")


def test_parse_wayback_entry_returns_none_without_h1() -> None:
    """A Wayback 404 page (or any non-entry HTML) lacks the firstHeading
    element. Parser must return None so the crawler skips it cleanly."""
    rec = parse_wayback_entry("<html><body><p>nope</p></body></html>", "x")
    assert rec is None
