"""Tests for app.medini.etl.events_extractor.

Pin the wiki-template parser, date normalisation, and event-code splitting
since those are the rules the trainer-side joins will rely on.
"""
from __future__ import annotations

import csv
from pathlib import Path

from app.medini.etl.events_extractor import (
    _normalise_date,
    _parse_event_block,
    _split_event_code,
    extract_events,
    extract_events_from_row,
)


# ---------- _split_event_code ----------

def test_split_event_code_basic_hierarchy() -> None:
    assert _split_event_code("Relationship : Marriage") == ("Relationship", "Marriage")
    assert _split_event_code("Work : Prize") == ("Work", "Prize")
    assert _split_event_code("Crime : Trial dates") == ("Crime", "Trial dates")


def test_split_event_code_no_colon_returns_root_only() -> None:
    """'Death by Disease' has no `:` separator — keep the whole string
    as the root, blank subtype."""
    assert _split_event_code("Death by Disease") == ("Death by Disease", "")
    assert _split_event_code("Death of Father") == ("Death of Father", "")


def test_split_event_code_strips_whitespace() -> None:
    assert _split_event_code("  Work  :  New Career  ") == ("Work", "New Career")


# ---------- _normalise_date ----------

def test_normalise_date_full_iso() -> None:
    assert _normalise_date("2015/11/13") == ("2015-11-13", 2015)
    assert _normalise_date("1971/03/14") == ("1971-03-14", 1971)


def test_normalise_date_year_only() -> None:
    assert _normalise_date("1971") == ("", 1971)


def test_normalise_date_year_with_zero_components() -> None:
    """Astro-Databank stores year-only events as '1971/00/00' — return
    the year but no ISO date so callers know precision is degraded."""
    assert _normalise_date("1971/00/00") == ("", 1971)


def test_normalise_date_invalid_returns_blank() -> None:
    assert _normalise_date("") == ("", None)
    assert _normalise_date("not a date") == ("", None)
    assert _normalise_date("2015/13/45") == ("", 2015)


# ---------- _parse_event_block ----------

def test_parse_event_block_extracts_fields() -> None:
    block = """
    |CodeID=784
    |sevcode=Relationship : Marriage
    |sevdate=1976/06/06
    |sevdate_dmy=6 June 1976
    """
    fields = _parse_event_block(block)
    assert fields["sevcode"] == "Relationship : Marriage"
    assert fields["sevdate"] == "1976/06/06"
    assert fields["CodeID"] == "784"


# ---------- extract_events_from_row ----------

_FIXTURE_WIKITEXT = """
==Events==
{{ASTRODATABANK_evn
|CodeID=784
|sevcode=Relationship : Marriage
|sevdate=1976/06/06
|sevdate_dmy=6 June 1976
}}
{{ASTRODATABANK_evn
|CodeID=900
|sevcode=Work : Prize
|sevdate=1989
|sevdate_dmy=1989
}}
{{ASTRODATABANK_evn
|CodeID=99
|sevcode=Death, Cause unspecified
|sevdate=2014/03/05
|sevdate_dmy=5 March 2014
}}
"""


def test_extract_events_from_row_parses_three_events() -> None:
    events = extract_events_from_row("Test Person", _FIXTURE_WIKITEXT, page_id="42")
    assert len(events) == 3

    marriage = events[0]
    assert marriage["event_code"] == "Relationship : Marriage"
    assert marriage["event_root"] == "Relationship"
    assert marriage["event_subtype"] == "Marriage"
    assert marriage["event_date"] == "1976-06-06"
    assert marriage["event_year"] == "1976"
    assert marriage["name"] == "Test Person"
    # source_url carries the page_id and event index for traceback.
    assert "page_id" in marriage["source_url"] or "42" in marriage["source_url"]


def test_extract_events_from_row_handles_year_only_dates() -> None:
    events = extract_events_from_row("X", _FIXTURE_WIKITEXT)
    prize = events[1]
    assert prize["event_year"] == "1989"
    assert prize["event_date"] == ""


def test_extract_events_from_row_returns_empty_for_no_events() -> None:
    assert extract_events_from_row("X", "no events here") == []
    assert extract_events_from_row("X", "") == []


def test_extract_events_from_row_skips_block_without_sevcode() -> None:
    """A malformed event block lacking sevcode should be silently skipped."""
    bad = """
    {{ASTRODATABANK_evn
    |CodeID=1
    |sevdate=2000/01/01
    }}
    """
    assert extract_events_from_row("X", bad) == []


# ---------- extract_events end-to-end ----------

def test_extract_events_writes_csv(tmp_path: Path) -> None:
    """Build a synthetic astro_people-shaped CSV with raw_wikitext, run
    extract_events, verify the output CSV contents."""
    in_csv = tmp_path / "ap.csv"
    with in_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "page_id", "raw_wikitext"])
        w.writeheader()
        w.writerow({"name": "Person A", "page_id": "1",
                    "raw_wikitext": _FIXTURE_WIKITEXT})
        w.writerow({"name": "Person B", "page_id": "2",
                    "raw_wikitext": "no events"})

    out_csv = tmp_path / "events.csv"
    stats = extract_events(in_csv, out_csv)
    assert stats["people_with_events"] == 1
    assert stats["events_written"] == 3

    with out_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    assert all(r["name"] == "Person A" for r in rows)
    roots = {r["event_root"] for r in rows}
    assert "Relationship" in roots
    assert "Work" in roots
    assert "Death, Cause unspecified" in roots  # no-colon root


def test_extract_events_with_root_filter(tmp_path: Path) -> None:
    """--filter-event-root keeps only matching events."""
    in_csv = tmp_path / "ap.csv"
    with in_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "page_id", "raw_wikitext"])
        w.writeheader()
        w.writerow({"name": "X", "page_id": "1",
                    "raw_wikitext": _FIXTURE_WIKITEXT})

    out_csv = tmp_path / "rel.csv"
    stats = extract_events(in_csv, out_csv, filter_event_root="Relationship")
    assert stats["events_written"] == 1
    assert stats["events_filtered_out"] == 2

    with out_csv.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["event_root"] == "Relationship"
