"""Tests for the VedAstro dated-marriage event extractor (schema-tolerant)."""
from __future__ import annotations

import csv
import json

import pytest

from app.medini.etl import vedastro_events_importer as vei


# ── helpers ─────────────────────────────────────────────────────────────────
def test_extract_year_from_many_formats() -> None:
    assert vei.extract_year("1954") == 1954
    assert vei.extract_year("26/06/1954") == 1954
    assert vei.extract_year("1954-06-26") == 1954
    assert vei.extract_year("June 1954") == 1954
    assert vei.extract_year(1954) == 1954
    assert vei.extract_year("06/26") is None          # no 4-digit year
    assert vei.extract_year("3000") is None            # out of MIN..MAX range
    assert vei.extract_year(None) is None


def test_clean_name_strips_birth_year_suffix() -> None:
    assert vei.clean_name("Albert Einstein - 1879") == "Albert Einstein"
    assert vei.clean_name("Albert_Einstein_1879") == "Albert Einstein"
    assert vei.clean_name("Frida Kahlo (1907)") == "Frida Kahlo"
    assert vei.clean_name("Cher") == "Cher"            # no suffix → unchanged


# ── flat-column layout ───────────────────────────────────────────────────────
def test_flat_row_marriage_and_divorce() -> None:
    row = {"Person Identifier": "John Doe 1950", "Marriage Date": "1972",
           "Divorce Date": "1980", "Spouse": "Jane", "Marriage Type": "Love",
           "Outcome": "Dissolution"}
    evs = vei.parse_person_marriages(row, src_base="X")
    roots = [(e["event_root"], e["event_year"]) for e in evs]
    assert ("marriage", "1972") in roots and ("divorce", "1980") in roots
    mar = next(e for e in evs if e["event_root"] == "marriage")
    assert mar["name"] == "John Doe" and mar["event_subtype"] == "love"


def test_flat_row_marriage_only_when_no_divorce() -> None:
    row = {"Name": "Jane Roe", "MarriageYear": "1999", "Spouse": "Sam"}
    evs = vei.parse_person_marriages(row, src_base="X")
    assert len(evs) == 1 and evs[0]["event_root"] == "marriage"
    assert evs[0]["event_year"] == "1999"


# ── JSON Info layout (like the old MarriageInfoDataset shape, with dates) ─────
def test_json_info_multiple_marriages() -> None:
    info = json.dumps({"marriages": [
        {"MarriageDate": "1903", "Spouse": "Mileva", "outcome": "Dissolution",
         "DivorceDate": "1919"},
        {"MarriageDate": "1919", "Spouse": "Elsa", "outcome": "Happiness"},
    ]})
    row = {"Name": "Albert Einstein - 1879", "Info": info}
    evs = vei.parse_person_marriages(row, src_base="X")
    years = sorted(e["event_year"] for e in evs if e["event_root"] == "marriage")
    assert years == ["1903", "1919"]
    assert any(e["event_root"] == "divorce" and e["event_year"] == "1919"
               for e in evs)
    assert all(e["name"] == "Albert Einstein" for e in evs)


def test_no_name_or_no_dates_yields_nothing() -> None:
    assert vei.parse_person_marriages({"Marriage Date": "1972"}, src_base="X") == []
    assert vei.parse_person_marriages({"Name": "Nobody"}, src_base="X") == []


# ── end-to-end CSV write ─────────────────────────────────────────────────────
def test_import_writes_events_csv(tmp_path) -> None:
    src = tmp_path / "mar.csv"
    with src.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Name", "Marriage Date", "Divorce Date"])
        w.writeheader()
        w.writerow({"Name": "A B 1900", "Marriage Date": "1925", "Divorce Date": ""})
        w.writerow({"Name": "C D 1910", "Marriage Date": "1935", "Divorce Date": "1940"})
        w.writerow({"Name": "", "Marriage Date": "1950", "Divorce Date": ""})  # skip
    out = tmp_path / "events.csv"
    stats = vei.import_vedastro_events(src, out)
    assert stats["marriages"] == 2 and stats["divorces"] == 1
    assert stats["events_written"] == 3 and stats["people_with_events"] == 2

    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert set(rows[0].keys()) == set(vei.EVENT_COLUMNS)
    assert {r["event_root"] for r in rows} == {"marriage", "divorce"}


def test_missing_input_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        vei.import_vedastro_events(tmp_path / "nope.csv", tmp_path / "o.csv")
