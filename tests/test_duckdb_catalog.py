"""Tests for app/medini/etl/build_duckdb_catalog.py.

Pins the catalog contract:
- Every Silver parquet is registered as a queryable DuckDB view
- Gold views (v_persons_canonical, v_chart_with_person) join correctly
- The catalog is idempotent (rerunning doesn't break or duplicate)
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from app.medini.etl.build_duckdb_catalog import (
    _OPTIONAL_SILVER, _SILVER_TABLES, initialise_catalog,
)


# Only the REQUIRED Silver tables get a fixture-row; optional ones (Phase 2's
# events_with_dasha) are skipped by the catalog when their parquet is absent.
_REQUIRED_SILVER: list[tuple[str, str]] = [
    (n, f) for (n, f) in _SILVER_TABLES if n not in _OPTIONAL_SILVER
]


@pytest.fixture
def tmp_catalog(tmp_path: Path) -> Path:
    """Build a catalog over tiny synthetic Silver parquets.

    Mirrors the production schema with the minimum columns each Gold view
    needs to resolve, so we test the SQL — not the production data volume.
    """
    pd.DataFrame({
        "person_id": ["ADB:1", "WD:2"],
        "name": ["A", "B"],
        "birth_date": ["1900-01-01", "1950-01-01"],
        "birth_time": ["12:00:00", None],
        "birth_lat": [10.0, 20.0],
        "birth_lon": [10.0, 20.0],
        "tz_offset": [0.0, None],
        "birth_jd": [2415020.5, 2433282.5],
        "source": ["astro_databank", "wikidata"],
    }).to_parquet(tmp_path / "persons.parquet", index=False)

    pd.DataFrame({
        "event_id": [0, 1],
        "person_id": ["ADB:1", "WD:2"],
        "event_class": ["fame", "marriage"],
        "event_root": ["Prize", "marriage"],
        "event_subtype": [None, None],
        "event_date": ["1920-01-01", "1975-06-15"],
        "event_label": ["L1", "L2"],
        "source": ["astro_databank", "wikidata"],
    }).to_parquet(tmp_path / "events.parquet", index=False)

    pd.DataFrame({
        "person_id": ["ADB:1", "WD:2"],
        "birth_jd_used": [2415020.5, 2433282.5],
        "time_precision": ["minute", "day"],
        "asc_lon": [173.99, 90.0],
        "asc_sign": [6, 4],
        "moon_lon": [356.32, 50.0],
        "moon_nakshatra": [26, 3],
    }).to_parquet(tmp_path / "charts.parquet", index=False)

    pd.DataFrame({
        "window_id": ["ADB:1::MD::Mercury::AD::Mercury::0"],
        "person_id": ["ADB:1"],
        "md_lord": ["Mercury"],
        "ad_lord": ["Mercury"],
        "md_seq": [0],
        "ad_seq": [0],
        "start_jd": [2415000.0],
        "end_jd": [2415100.0],
        "duration_days": [100.0],
    }).to_parquet(tmp_path / "dasha_windows.parquet", index=False)

    pd.DataFrame({
        "canonical_id": ["ADB:1", "WD:2"],
        "source_ids": [["ADB:1"], ["WD:2"]],
        "name_key": ["a", "b"],
        "birth_date": ["1900-01-01", "1950-01-01"],
        "n_corpora": [1, 1],
        "match_method": ["exact_name_date", "exact_name_date"],
    }).to_parquet(tmp_path / "resolved_persons.parquet", index=False)

    catalog_path = tmp_path / "catalog.duckdb"
    con = initialise_catalog(tmp_path, catalog_path)
    con.close()
    return catalog_path


class TestSilverViews:
    """All five Silver parquets must be queryable as catalog views."""

    @pytest.mark.parametrize("view_name,_fname", _REQUIRED_SILVER)
    def test_silver_view_is_queryable(self, tmp_catalog: Path, view_name: str, _fname: str):
        """A SELECT COUNT(*) on each REQUIRED Silver view must return >0 rows.

        Optional tables (events_with_dasha) are only present after Phase 2
        runs; the fixture skips them and the catalog initialiser tolerates
        their absence at startup.
        """
        con = duckdb.connect(str(tmp_catalog), read_only=True)
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
            assert count > 0, f"{view_name} returned no rows"
        finally:
            con.close()


class TestGoldViews:
    """Gold views must resolve their joins without error."""

    def test_v_persons_canonical_attaches_resolved_columns(self, tmp_catalog: Path):
        """v_persons_canonical exposes canonical_id and n_corpora."""
        con = duckdb.connect(str(tmp_catalog), read_only=True)
        try:
            row = con.execute("""
                SELECT person_id, canonical_id, n_corpora
                FROM v_persons_canonical
                WHERE person_id = 'ADB:1'
            """).fetchone()
            assert row is not None
            assert row[1] == "ADB:1"  # canonical_id
            assert row[2] == 1  # n_corpora
        finally:
            con.close()

    def test_v_chart_with_person_joins_correctly(self, tmp_catalog: Path):
        """v_chart_with_person joins charts to persons by person_id."""
        con = duckdb.connect(str(tmp_catalog), read_only=True)
        try:
            row = con.execute("""
                SELECT name, asc_sign, source
                FROM v_chart_with_person
                WHERE person_id = 'ADB:1'
            """).fetchone()
            assert row == ("A", 6, "astro_databank")
        finally:
            con.close()


class TestIdempotence:
    """Re-running the catalog initializer must not fail or duplicate views."""

    def test_double_init_is_safe(self, tmp_catalog: Path, tmp_path: Path):
        """Calling initialise_catalog twice on the same path is a no-op."""
        # First call already happened via the fixture. Run a second time.
        con = initialise_catalog(tmp_path, tmp_catalog)
        try:
            # Still queryable, no duplicate rows.
            n = con.execute("SELECT COUNT(*) FROM persons").fetchone()[0]
            assert n == 2
        finally:
            con.close()
