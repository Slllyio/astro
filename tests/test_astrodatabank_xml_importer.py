"""Tests for the Astro-Databank XML importer (charts always, events if present)."""
from __future__ import annotations

import csv

from app.medini.etl import astrodatabank_xml_importer as ax

# Minimal export: one full public_data entry + an entry with a licensed <event>,
# and one entry with no usable birth date (must be skipped).
_XML = """<?xml version="1.0"?>
<astrodatabank_export>
  <adb_entry>
    <public_data>
      <name>Albert Einstein</name>
      <sflname>Albert Einstein</sflname>
      <gender>M</gender>
      <roddenrating rrc="10">AA</roddenrating>
      <bdata>
        <sbdate_dmy>14.3.1879</sbdate_dmy>
        <sbtime>11:30</sbtime>
        <place>Ulm, Germany, 48n24, 10e00</place>
        <country>Germany</country>
      </bdata>
    </public_data>
    <research_data>
      <event type="Marriage" date="1903"/>
      <event type="Death" date="18 April 1955"/>
    </research_data>
  </adb_entry>
  <adb_entry>
    <public_data>
      <name>No Birthdate Person</name>
      <roddenrating rrc="0">X</roddenrating>
      <bdata><sbtime>09:00</sbtime></bdata>
    </public_data>
  </adb_entry>
</astrodatabank_export>
"""


def test_coordinate_parsing() -> None:
    assert ax.parse_coordinate("48n24") == 48.4
    assert ax.parse_coordinate("10e00") == 10.0
    assert ax.parse_coordinate("12S30") == -12.5
    assert ax.parse_coordinate("garbage") is None


def test_iso_date_and_time() -> None:
    assert ax._iso_date("14.3.1879") == "1879-03-14"
    assert ax._iso_date("32.1.1900") == ""          # invalid day
    assert ax._hms("11:30") == "11:30:00"
    assert ax._hms("no time") == ""


def test_charts_and_events_end_to_end(tmp_path) -> None:
    xml = tmp_path / "adb.xml"
    xml.write_text(_XML, encoding="utf-8")
    raw = tmp_path / "raw.csv"
    events = tmp_path / "events.csv"
    stats = ax.import_adb_xml(xml, raw, events)

    assert stats["entries"] == 2
    assert stats["charts"] == 1 and stats["skipped_no_birth"] == 1
    assert stats["events"] == 2

    rows = list(csv.DictReader(raw.open(encoding="utf-8")))
    assert set(rows[0]) == set(ax.CSV_COLUMNS)
    r = rows[0]
    assert r["name"] == "Albert Einstein" and r["date_of_birth"] == "1879-03-14"
    assert r["time_of_birth"] == "11:30:00" and r["rodden_rating"] == "AA"
    assert abs(float(r["latitude"]) - 48.4) < 1e-6
    assert abs(float(r["longitude"]) - 10.0) < 1e-6

    evs = list(csv.DictReader(events.open(encoding="utf-8")))
    assert {e["event_root"] for e in evs} == {"marriage", "death"}
    assert {e["event_year"] for e in evs} == {"1903", "1955"}


def test_public_domain_only_export_yields_no_events(tmp_path) -> None:
    # strip the research_data → birth-only public-domain export.
    xml = tmp_path / "pub.xml"
    pub_only = _XML.replace(
        '<research_data>\n      <event type="Marriage" date="1903"/>\n'
        '      <event type="Death" date="18 April 1955"/>\n    </research_data>', "")
    xml.write_text(pub_only, encoding="utf-8")
    raw = tmp_path / "raw.csv"
    events = tmp_path / "events.csv"
    stats = ax.import_adb_xml(xml, raw, events)
    assert stats["charts"] == 1 and stats["events"] == 0   # no error, just empty

    assert list(csv.DictReader(events.open(encoding="utf-8"))) == []


def test_charts_only_when_no_events_path(tmp_path) -> None:
    xml = tmp_path / "adb.xml"
    xml.write_text(_XML, encoding="utf-8")
    raw = tmp_path / "raw.csv"
    stats = ax.import_adb_xml(xml, raw, None)
    assert stats["charts"] == 1 and stats["events"] == 0
