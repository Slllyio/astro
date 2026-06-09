"""Tests for the pure parsers in lunarastro_kundli_pipeline.

The chart/dasha path needs swisseph + real birth data and is exercised by
the CLI end-to-end; here we pin the text/coordinate/event parsing rules
that decide what gets into the corpus.
"""
from __future__ import annotations

import pytest

from app.medini.etl.lunarastro_kundli_pipeline import (
    classify_label,
    extract_events,
    lmt_offset,
    parse_birth_date,
    parse_coord,
    parse_time,
    split_top_level,
)


# ---------- birth fields ----------

def test_parse_birth_date_ddmmyyyy() -> None:
    assert parse_birth_date("14:03:1879") == (1879, 3, 14)
    assert parse_birth_date("22:06:1933") == (1933, 6, 22)


def test_parse_birth_date_rejects_bad() -> None:
    assert parse_birth_date("09:13:1916") is None    # month 13
    assert parse_birth_date("") is None
    assert parse_birth_date("notadate") is None
    assert parse_birth_date("01:01:3000") is None     # year out of range


def test_parse_time_and_default() -> None:
    assert parse_time("02:59:00") == pytest.approx(2 + 59 / 60)
    assert parse_time("12:00:00") == 12.0
    assert parse_time("bad") == 12.0                  # default noon
    assert parse_time("25:00:00") == 12.0             # invalid hour → noon


def test_parse_coord_formats() -> None:
    assert parse_coord("9.9876° E") == pytest.approx(9.9876)
    assert parse_coord("48.4011° N") == pytest.approx(48.4011)
    assert parse_coord("122.4194° W") == pytest.approx(-122.4194)
    assert parse_coord("-118.25") == pytest.approx(-118.25)
    assert parse_coord("33.0° S") == pytest.approx(-33.0)
    assert parse_coord("garbage") is None


def test_lmt_offset_from_longitude() -> None:
    assert lmt_offset(15.0) == pytest.approx(1.0)
    assert lmt_offset(-75.0) == pytest.approx(-5.0)


# ---------- event extraction ----------

def test_split_top_level_respects_parens() -> None:
    s = "Marriage 1903 (First marriage, Mileva Maric),Prize 1922 (Nobel)"
    parts = split_top_level(s)
    assert parts == ["Marriage 1903 (First marriage, Mileva Maric)",
                     "Prize 1922 (Nobel)"]


def test_extract_events_year_full_and_monthyear() -> None:
    desc = ("Prize 1922 (Nobel Prize),"
            "Institutionalized 13 April 1955 (hospital),"
            "New Job November 1992 (Senator),"
            "Public speaker,For Numbers")
    evs = extract_events(desc)
    by_label = {e["label"]: e for e in evs}
    # year-only → mid-year July 1
    assert by_label["Prize"]["event_date"] == "1922-07-01"
    assert by_label["Prize"]["event_year"] == 1922
    # full date parsed exactly
    assert by_label["Institutionalized"]["event_date"] == "1955-04-13"
    # month+year → day 15
    assert by_label["New Job"]["event_date"] == "1992-11-15"
    # undated traits dropped
    assert "Public speaker" not in by_label
    assert "For Numbers" not in by_label


def test_extract_events_ignores_non_year_numbers() -> None:
    # "16 years" / "15 Yrs" are not in-range years → not a dated event.
    assert extract_events("Marriage more than 15 Yrs (16 years)") == []


# ---------- label classification ----------

def test_classify_label_polarity_and_class() -> None:
    assert classify_label("Marriage") == ("marriage", "Beneficial")
    assert classify_label("Divorce dates") == ("divorce", "Adverse")
    assert classify_label("Prize") == ("career", "Beneficial")
    assert classify_label("Lose social status") == ("career", "Adverse")
    assert classify_label("Death of Mate") == ("death", "Adverse")
    assert classify_label("Accident") == ("health", "Adverse")
    assert classify_label("Something unmapped") == ("other", "Neutral")


def test_divorce_beats_marriage_substring() -> None:
    # 'divorce' rule must win even though the word 'marriage' may co-occur.
    cls, pol = classify_label("Divorce dates")
    assert cls == "divorce" and pol == "Adverse"
