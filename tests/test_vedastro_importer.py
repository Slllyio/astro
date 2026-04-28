"""Tests for app.medini.etl.vedastro_importer.

Pinned against a synthetic mini-corpus that mimics the real PersonList-15k
+ MarriageInfoDataset cell shapes (JSON-in-CSV, Azure Table Storage style)
so the importer's parsers stay strict to the actual schema.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.medini.etl.vedastro_importer import (
    _parse_birth_json,
    _parse_stdtime,
    derive_marriage_category,
    import_vedastro,
)


# ---------- StdTime parser ----------

def test_parse_stdtime_basic() -> None:
    """Pin the exact format VedAstro emits: "HH:MM dd/MM/YYYY ±HH:MM"."""
    out = _parse_stdtime("19:55 26/06/1954 +01:00")
    assert out == ("1954-06-26", "19:55:00", 1.0)


def test_parse_stdtime_negative_offset() -> None:
    out = _parse_stdtime("13:55 07/12/1944 -04:00")
    assert out == ("1944-12-07", "13:55:00", -4.0)


def test_parse_stdtime_half_hour_offset() -> None:
    """Indian Standard Time is +05:30 — the importer must surface 5.5,
    not 5.0 or 530, so downstream JD math is correct."""
    out = _parse_stdtime("12:00 15/07/1990 +05:30")
    assert out == ("1990-07-15", "12:00:00", 5.5)


def test_parse_stdtime_rejects_malformed() -> None:
    assert _parse_stdtime("not a timestamp") is None
    assert _parse_stdtime("12:00 1990-07-15 +05:30") is None  # ISO date, wrong fmt
    assert _parse_stdtime("25:00 15/07/1990 +05:30") is None  # bad hour


def test_parse_stdtime_rejects_invalid_date() -> None:
    assert _parse_stdtime("12:00 31/02/1990 +05:30") is None  # Feb 31


# ---------- BirthTime JSON parser ----------

VALID_BIRTH_JSON = json.dumps({
    "StdTime": "19:55 26/06/1954 +01:00",
    "Location": {
        "Name": "Edinburgh, United Kingdom",
        "Longitude": -3.188,
        "Latitude": 55.95,
    },
})


def test_parse_birth_json_success() -> None:
    out = _parse_birth_json(VALID_BIRTH_JSON)
    assert out is not None
    date_iso, hms, lat, lon, tz = out
    assert date_iso == "1954-06-26"
    assert hms == "19:55:00"
    assert lat == pytest.approx(55.95)
    assert lon == pytest.approx(-3.188)
    assert tz == pytest.approx(1.0)


def test_parse_birth_json_missing_location() -> None:
    bad = json.dumps({"StdTime": "12:00 01/01/2000 +00:00"})
    assert _parse_birth_json(bad) is None


def test_parse_birth_json_out_of_range_latitude() -> None:
    bad = json.dumps({
        "StdTime": "12:00 01/01/2000 +00:00",
        "Location": {"Latitude": 95.0, "Longitude": 0.0},
    })
    assert _parse_birth_json(bad) is None


def test_parse_birth_json_invalid_json() -> None:
    assert _parse_birth_json("not json") is None
    assert _parse_birth_json("") is None


# ---------- Marriage outcome derivation ----------

def test_derive_marriage_category_dissolution_wins() -> None:
    """Any single Dissolution outcome flips the row to 'dissolution'
    even if other marriages were Happy. This matches the trainer's
    `--target dissolution` semantics: the question is "did at least one
    marriage end" — not "were all marriages happy"."""
    info = json.dumps({"marriages": [
        {"outcome": "Happiness", "spouse": "x"},
        {"outcome": "Dissolution", "spouse": "y"},
    ]})
    assert derive_marriage_category(info) == "marriage : dissolution"


def test_derive_marriage_category_all_happy() -> None:
    info = json.dumps({"marriages": [
        {"outcome": "Happiness", "spouse": "x"},
        {"outcome": "Happiness", "spouse": "y"},
    ]})
    assert derive_marriage_category(info) == "marriage : happiness"


def test_derive_marriage_category_unknown_outcome_strings_skipped() -> None:
    """VedAstro has ~1500 rows whose outcome string is neither Dissolution
    nor Happiness ('Bigamy', 'Annulled', etc.). We skip these so the
    target stays clean."""
    info = json.dumps({"marriages": [
        {"outcome": "Bigamy", "spouse": "x"},
    ]})
    assert derive_marriage_category(info) is None


def test_derive_marriage_category_empty_marriages_list() -> None:
    assert derive_marriage_category(json.dumps({"marriages": []})) is None


def test_derive_marriage_category_invalid_json() -> None:
    assert derive_marriage_category("not json") is None


# ---------- Full import ----------

def _write_persons(path: Path) -> None:
    """Mini PersonList CSV with two valid rows + one malformed row to
    exercise the skip path."""
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["RowKey", "BirthTime", "Gender", "Name", "Notes"],
        )
        w.writeheader()
        w.writerow({
            "RowKey": "TestPerson1900",
            "BirthTime": json.dumps({
                "StdTime": "12:00 15/07/1990 +05:30",
                "Location": {"Name": "Bangalore",
                             "Latitude": 12.97, "Longitude": 77.59},
            }),
            "Gender": "Male", "Name": "Test Person",
            "Notes": "{'rodden': 'AA'}",
        })
        w.writerow({
            "RowKey": "Other2000",
            "BirthTime": json.dumps({
                "StdTime": "08:30 01/01/2000 -05:00",
                "Location": {"Name": "NYC",
                             "Latitude": 40.71, "Longitude": -74.0},
            }),
            "Gender": "Female", "Name": "Other Person",
            "Notes": "{'rodden': 'AA'}",
        })
        # A malformed row — importer must skip, not crash.
        w.writerow({
            "RowKey": "BadRow",
            "BirthTime": "not json",
            "Gender": "Male", "Name": "Bad Row",
            "Notes": "{'rodden': 'AA'}",
        })


def _write_marriages(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["PartitionKey", "RowKey", "Info"])
        w.writeheader()
        # TestPerson1900 had a dissolved marriage.
        w.writerow({
            "PartitionKey": "TestPerson1900", "RowKey": "",
            "Info": json.dumps({"marriages": [
                {"outcome": "Dissolution", "spouse": "Spouse A"},
            ]}),
        })
        # Other2000 had a happy marriage.
        w.writerow({
            "PartitionKey": "Other2000", "RowKey": "",
            "Info": json.dumps({"marriages": [
                {"outcome": "Happiness", "spouse": "Spouse B"},
            ]}),
        })


def test_import_vedastro_writes_two_rows(tmp_path: Path) -> None:
    persons = tmp_path / "persons.csv"
    marriages = tmp_path / "marriages.csv"
    output = tmp_path / "raw.csv"
    _write_persons(persons)
    _write_marriages(marriages)

    stats = import_vedastro(persons, marriages, output)
    assert stats["written"] == 2
    assert stats["skipped_no_birthdata"] == 1  # the BadRow
    assert stats["with_marriage_label"] == 2

    with output.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    by_name = {r["name"]: r for r in rows}
    assert by_name["Test Person"]["categories"] == "marriage : dissolution"
    assert by_name["Test Person"]["date_of_birth"] == "1990-07-15"
    assert by_name["Test Person"]["tz_offset"] == "5.5000"
    assert by_name["Test Person"]["rodden_rating"] == "AA"
    assert by_name["Other Person"]["categories"] == "marriage : happiness"


def test_import_vedastro_skips_unlabeled_persons_by_default(tmp_path: Path) -> None:
    """A person who exists in PersonList but not MarriageInfo should be
    dropped under the default require_marriage_label=True."""
    persons = tmp_path / "persons.csv"
    marriages = tmp_path / "marriages.csv"
    output = tmp_path / "raw.csv"
    _write_persons(persons)
    # Empty marriages CSV (just the header).
    with marriages.open("w", encoding="utf-8", newline="") as f:
        f.write("PartitionKey,RowKey,Info\n")

    stats = import_vedastro(persons, marriages, output)
    assert stats["written"] == 0
    assert stats["skipped_no_label"] == 2  # both valid persons, no labels


def test_import_vedastro_allow_unlabeled(tmp_path: Path) -> None:
    """When --allow-unlabeled is used, unlabeled persons get
    categories='marriage : unknown' so they survive Stage 2's filter."""
    persons = tmp_path / "persons.csv"
    output = tmp_path / "raw.csv"
    _write_persons(persons)

    stats = import_vedastro(
        persons, marriages_csv=None, output_csv=output,
        require_marriage_label=False,
    )
    assert stats["written"] == 2
    with output.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert all(r["categories"] == "marriage : unknown" for r in rows)
