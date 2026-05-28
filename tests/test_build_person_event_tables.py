"""Tests for app/medini/etl/build_person_event_tables.py.

The ETL collapses two long-format scraped corpora (Astro-Databank +
Wikidata) into a clean star schema. These tests pin the relational
invariants we care about: stable person_id keys, FK integrity, no date
overflow on pre-1677 historicals, and harmonized event taxonomy.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.medini.etl.build_person_event_tables import (
    ADB_EVENT_ROOT_TO_CLASS,
    EVENT_COLS,
    PERSON_COLS,
    _adb_person_id,
    _to_iso_date_string,
    _wd_person_id,
    load_adb_events,
    load_adb_persons,
    load_wd_events,
    load_wd_persons,
)


@pytest.fixture
def adb_birth_parquet(tmp_path: Path) -> Path:
    """Minimal ADB birth-data fixture with one pre-1677 historical."""
    p = tmp_path / "dasha_corpus_birth_data.parquet"
    pd.DataFrame({
        "name_norm": ["agatha christie", "isaac newton"],
        "birth_jd": [2411626.0931, 2332895.5],  # 1890 + 1665 (Newton — pre-1677)
        "latitude": [50.468, 52.7975],
        "longitude": [-3.532, -0.6383],
        "tz_offset": [0.0, 0.0],
        "date_of_birth": ["1890-09-15", "1665-01-04"],
        "time_of_birth": ["14:14:00", "01:30:00"],
    }).to_parquet(p, index=False)
    return p


@pytest.fixture
def adb_events_parquet(tmp_path: Path) -> Path:
    """Minimal ADB event corpus matching adb_birth_parquet's birth_jds."""
    p = tmp_path / "event_corpus_all.parquet"
    pd.DataFrame({
        "name": ["Agatha Christie", "Agatha Christie", "Isaac Newton"],
        "birth_jd": [2411626.0931, 2411626.0931, 2332895.5],
        "event_date": ["1914-12-24", "1976-01-12", "1727-03-31"],
        "event_root": ["Marriage", "Death, Cause unspecified", "Death, Cause unspecified"],
        "event_subtype": ["First marriage", pd.NA, pd.NA],
    }).to_parquet(p, index=False)
    return p


@pytest.fixture
def wd_events_parquet(tmp_path: Path) -> Path:
    """Minimal Wikidata-style events with denormalized birth fields."""
    p = tmp_path / "wikidata_dated_events.parquet"
    pd.DataFrame({
        "person_id": ["Q35064", "Q35064", "Q937"],
        "person_name": ["Agatha Christie", "Agatha Christie", "Albert Einstein"],
        "birth_date": ["1890-09-15", "1890-09-15", "1879-03-14"],
        "birth_lat": [50.468, 50.468, 48.401],
        "birth_lon": [-3.532, -3.532, 9.987],
        "event_class": ["marriage", "death_cause_unspecified", "fame"],
        "event_date_iso": ["1914-12-24", "1976-01-12", "1921-12-10"],
        "event_label": ["Archibald Christie", "", "Nobel Prize in Physics"],
    }).to_parquet(p, index=False)
    return p


class TestPersonIdKeys:
    """person_id must be stable, unique, and namespace-prefixed."""

    def test_adb_person_id_from_jd_is_deterministic(self):
        """Same JD must always produce the same ADB id."""
        assert _adb_person_id(2411626.0931) == _adb_person_id(2411626.0931)

    def test_adb_person_id_has_namespace_prefix(self):
        """ADB ids must start with 'ADB:' to keep namespaces disjoint."""
        assert _adb_person_id(2411626.0931).startswith("ADB:")

    def test_wd_person_id_has_namespace_prefix(self):
        """Wikidata ids must start with 'WD:' to keep namespaces disjoint."""
        assert _wd_person_id("Q35064") == "WD:Q35064"

    def test_adb_persons_have_unique_ids(self, adb_birth_parquet: Path):
        """Two charts -> two distinct person_ids."""
        persons = load_adb_persons(adb_birth_parquet)
        assert persons["person_id"].nunique() == len(persons)


class TestDateOverflow:
    """pandas Timestamps overflow for pre-1677 dates — verify we sidestep."""

    def test_to_iso_handles_pre_1677_dates(self):
        """A 1665 date must round-trip as 'YYYY-MM-DD' without overflow."""
        s = pd.Series(["1665-01-04", "1890-09-15"])
        result = _to_iso_date_string(s)
        assert list(result) == ["1665-01-04", "1890-09-15"]

    def test_adb_persons_preserves_1665_birthdate(self, adb_birth_parquet: Path):
        """Newton's 1665 birth must survive the persons-table build."""
        persons = load_adb_persons(adb_birth_parquet)
        newton = persons[persons["name"] == "isaac newton"].iloc[0]
        assert newton["birth_date"] == "1665-01-04"

    def test_adb_events_preserves_pre_pandas_event_date(self, adb_events_parquet: Path):
        """An event date in 1727 must survive (predates pandas ns lower bound)."""
        events = load_adb_events(adb_events_parquet)
        newton_death = events[events["person_id"] == _adb_person_id(2332895.5)].iloc[0]
        assert newton_death["event_date"] == "1727-03-31"


class TestEventClassHarmonization:
    """Raw event_root must map to the 5-bucket harmonized vocabulary."""

    def test_marriage_root_maps_to_marriage_class(self):
        """'Marriage' is the canonical seed of the marriage bucket."""
        assert ADB_EVENT_ROOT_TO_CLASS["Marriage"] == "marriage"

    def test_death_by_disease_maps_to_death_class(self):
        """Disease deaths roll up into the same bucket as cause-unspecified."""
        assert ADB_EVENT_ROOT_TO_CLASS["Death by Disease"] == "death_cause_unspecified"

    def test_unmapped_root_becomes_other(self, adb_events_parquet: Path, tmp_path: Path):
        """A novel event_root must fall through to 'other', not error."""
        p = tmp_path / "novel.parquet"
        pd.DataFrame({
            "name": ["X"], "birth_jd": [2411626.0931],
            "event_date": ["2000-01-01"], "event_root": ["NovelEventType"],
            "event_subtype": [pd.NA],
        }).to_parquet(p, index=False)
        events = load_adb_events(p)
        assert events.iloc[0]["event_class"] == "other"


class TestWikidataPersonsCollapse:
    """Wikidata stores birth fields on every event row — must collapse cleanly."""

    def test_three_events_two_persons(self, wd_events_parquet: Path):
        """3 event rows for {Christie, Christie, Einstein} -> 2 persons."""
        persons = load_wd_persons(wd_events_parquet)
        assert len(persons) == 2

    def test_persons_have_namespaced_ids(self, wd_events_parquet: Path):
        """Every Wikidata person_id must have the 'WD:' namespace prefix."""
        persons = load_wd_persons(wd_events_parquet)
        assert persons["person_id"].str.startswith("WD:").all()


class TestForeignKeyIntegrity:
    """Every event.person_id must resolve to a row in persons."""

    def test_adb_event_person_ids_match_persons(
        self, adb_birth_parquet: Path, adb_events_parquet: Path
    ):
        """Every ADB event's person_id is present in ADB persons table."""
        persons = load_adb_persons(adb_birth_parquet)
        events = load_adb_events(adb_events_parquet)
        assert set(events["person_id"]).issubset(set(persons["person_id"]))

    def test_wd_event_person_ids_match_persons(self, wd_events_parquet: Path):
        """Every Wikidata event's person_id is present in Wikidata persons."""
        persons = load_wd_persons(wd_events_parquet)
        events = load_wd_events(wd_events_parquet)
        assert set(events["person_id"]).issubset(set(persons["person_id"]))


class TestSchemaContract:
    """The canonical column order is part of the data contract."""

    def test_person_cols_constant_matches_loaders(self, adb_birth_parquet: Path):
        """ADB persons loader must emit every column declared in PERSON_COLS."""
        persons = load_adb_persons(adb_birth_parquet)
        assert set(PERSON_COLS).issubset(set(persons.columns))

    def test_event_cols_constant_documents_all_event_fields(
        self, adb_events_parquet: Path
    ):
        """ADB events loader must emit every event column except event_id (added by build_tables)."""
        events = load_adb_events(adb_events_parquet)
        # event_id is assigned during the concat step, not per-loader.
        expected = set(EVENT_COLS) - {"event_id"}
        assert expected.issubset(set(events.columns))
