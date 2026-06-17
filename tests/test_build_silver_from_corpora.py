"""Tests for the canonical-store adapter build_silver_from_corpora.

Covers the pure helpers and a tiny end-to-end build (calculate_jd is dependency-
free; no parquet fixtures needed beyond a temp dir) verifying the persons union,
person_id namespacing, event→person FK linkage, orphan drop, and event-class
harmonization.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.medini.etl.build_person_event_tables import EVENT_COLS, PERSON_COLS
from app.medini.etl.build_silver_from_corpora import (
    _confidence,
    _decimal_hour,
    _name_norm,
    build_events,
    build_persons,
)


class TestPureHelpers:
    def test_name_norm_accents_and_case(self) -> None:
        assert _name_norm("Gérard Depardieu") == "gerard depardieu"
        assert _name_norm("  Multiple   Spaces ") == "multiple spaces"

    def test_decimal_hour(self) -> None:
        assert _decimal_hour("18:30:00") == pytest.approx(18.5)
        assert _decimal_hour("06:15") == pytest.approx(6.25)
        assert _decimal_hour("") == 12.0      # noon fallback
        assert _decimal_hour("garbage") == 12.0

    def test_confidence_from_rodden(self) -> None:
        assert _confidence("AA") == 1.0
        assert _confidence("A") == 1.0
        assert _confidence("B") == 0.2
        assert _confidence("C") == 0.0
        assert _confidence("") == 0.0


_RAW_HEADER = "name,date_of_birth,time_of_birth,latitude,longitude,tz_offset,rodden_rating,categories,source_url\n"


def _write_corpora(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "raw.csv").write_text(
        _RAW_HEADER
        + "Alice Example,1970-01-01,12:00:00,12.97,77.59,5.5,AA,marriage : happiness,u1\n",
        encoding="utf-8",
    )
    (raw_dir / "raw_astrocrm.csv").write_text(
        _RAW_HEADER
        + "Bob Sample,1980-06-15,09:30:00,48.85,2.35,1.0,A,,u2\n",
        encoding="utf-8",
    )
    (raw_dir / "events.csv").write_text(
        "name,event_code,event_root,event_subtype,event_date,event_year,source_url\n"
        "Bob Sample,Death,Death by Disease,,2020-03-01,2020,u2\n"   # links to Bob
        "Bob Sample,Rel,Relationship,,1999,1999,u2\n"               # year-only -> dropped
        "Ghost Person,X,Work,,2005-05-05,2005,u9\n"                 # orphan -> dropped
        "Alice Example,M,Marriage,,2001-02-02,2001,u1\n",           # links to Alice
        encoding="utf-8",
    )


def test_build_persons_unions_and_namespaces(tmp_path: Path) -> None:
    _write_corpora(tmp_path)
    persons = build_persons(tmp_path)
    assert list(persons.columns) == list(PERSON_COLS)
    assert len(persons) == 2
    assert set(persons["source"]) == {"vedastro", "astrocrm"}
    # person_id namespacing by corpus
    prefixes = {pid.split(":")[0] for pid in persons["person_id"]}
    assert prefixes == {"VA", "AC"}
    # names normalized; confidence from rodden
    assert set(persons["name"]) == {"alice example", "bob sample"}
    assert set(persons["birth_time_confidence"].astype(float)) == {1.0}


def test_build_events_links_and_drops(tmp_path: Path) -> None:
    _write_corpora(tmp_path)
    # Write the real taxonomy so harmonization maps ADB roots to the 6-class set.
    from app.medini.etl.build_event_class_taxonomy import build_taxonomy
    tax_path = tmp_path / "event_class_taxonomy.parquet"
    build_taxonomy().to_parquet(tax_path, index=False)

    persons = build_persons(tmp_path)
    events = build_events(tmp_path, persons, taxonomy_path=tax_path)
    assert list(events.columns) == list(EVENT_COLS)
    # year-only ("1999") and the orphan ("Ghost Person") are dropped; 2 remain
    assert len(events) == 2
    assert set(events["event_date"]) == {"2020-03-01", "2001-02-02"}
    # every event FK resolves into persons
    assert set(events["person_id"]).issubset(set(persons["person_id"]))
    # Death by Disease harmonizes to the death class via the taxonomy
    classes = set(events["event_class"])
    assert "death_cause_unspecified" in classes
    assert events["event_date_precision"].eq("day").all()
