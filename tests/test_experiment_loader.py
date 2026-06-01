"""Tests for app/medini/ml/experiment_loader.py.

Pins the loader contract:
- Only whitelisted view names are accepted (injection defense)
- cohort_filter rejects mutation keywords (injection defense)
- temporal_cutoff_jd applies the expected anti-leakage filter
- label_col rename works for sklearn-style downstream code
- Catalog is auto-initialised if absent
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from app.medini.ml.experiment_loader import (
    ALLOWED_VIEWS,
    CohortFilterError,
    build_experiment_matrix,
    _validate_cohort_filter,
)


@pytest.fixture
def tmp_data_dir_with_catalog(tmp_path: Path) -> Path:
    """Build a minimum-viable catalog so the loader can resolve a query.

    We craft a single Silver parquet (persons) and rely on the loader's
    own catalog-initialisation path to register it.
    """
    pd.DataFrame({
        "person_id": ["P:1", "P:2", "P:3"],
        "name": ["A", "B", "C"],
        "birth_date": ["1900-01-01", "1950-01-01", "2000-01-01"],
        "birth_time": [None, None, None],
        "birth_lat": [10.0, 20.0, 30.0],
        "birth_lon": [10.0, 20.0, 30.0],
        "tz_offset": [None, None, None],
        "birth_jd": [2415020.5, 2433282.5, 2451544.5],
        "source": ["astro_databank", "wikidata", "wikidata"],
    }).to_parquet(tmp_path / "persons.parquet", index=False)
    # Minimum-viable placeholders so Gold-view CREATE statements bind correctly.
    # An empty resolved_persons.parquet would leave source_ids untyped (DOUBLE),
    # which then breaks list_contains() in v_persons_canonical. Use one real row
    # so list<VARCHAR> survives the parquet round-trip.
    pd.DataFrame({c: [] for c in ["event_id", "person_id", "event_class",
                                   "event_root", "event_subtype", "event_date",
                                   "event_label", "source"]}).to_parquet(
        tmp_path / "events.parquet", index=False,
    )
    pd.DataFrame({c: [] for c in ["person_id", "birth_jd_used", "time_precision",
                                   "asc_lon", "asc_sign"]}).to_parquet(
        tmp_path / "charts.parquet", index=False,
    )
    pd.DataFrame({c: [] for c in ["window_id", "person_id", "md_lord", "ad_lord",
                                   "md_seq", "ad_seq", "start_jd", "end_jd",
                                   "duration_days"]}).to_parquet(
        tmp_path / "dasha_windows.parquet", index=False,
    )
    pd.DataFrame({
        "canonical_id": ["P:1"],
        "source_ids": [["P:1"]],
        "name_key": ["a"],
        "birth_date": ["1900-01-01"],
        "n_corpora": [1],
        "match_method": ["exact_name_date"],
    }).to_parquet(tmp_path / "resolved_persons.parquet", index=False)
    return tmp_path


class TestViewWhitelist:
    """Only views in ALLOWED_VIEWS may be queried."""

    def test_persons_is_in_whitelist(self):
        """persons is the canonical Silver table — must be queryable."""
        assert "persons" in ALLOWED_VIEWS

    def test_unknown_view_is_rejected(self, tmp_data_dir_with_catalog: Path):
        """A made-up view name raises ValueError before SQL runs."""
        with pytest.raises(ValueError, match="not in ALLOWED_VIEWS"):
            build_experiment_matrix(
                view="information_schema",
                data_dir=tmp_data_dir_with_catalog,
            )


class TestCohortFilterInjectionDefense:
    """Mutation keywords in cohort_filter must raise CohortFilterError."""

    @pytest.mark.parametrize("payload", [
        "name='A'; DROP TABLE persons",
        "1=1 OR DELETE FROM persons",
        "TRUE; UPDATE persons SET name = 'X'",
        "1=1; ATTACH DATABASE '/tmp/attack.db'",
    ])
    def test_forbidden_keyword_raises(self, payload: str):
        """Each variant of injection payload must be caught."""
        with pytest.raises(CohortFilterError):
            _validate_cohort_filter(payload)

    def test_benign_filter_passes(self):
        """A plain WHERE-clause fragment is accepted."""
        _validate_cohort_filter("source = 'astro_databank' AND birth_jd > 2400000")


class TestLabelColRename:
    """label_col is renamed to 'label' for sklearn-style consumers."""

    def test_rename_succeeds(self, tmp_data_dir_with_catalog: Path):
        """The named column becomes 'label' in the result."""
        df = build_experiment_matrix(
            view="persons",
            label_col="source",
            columns=["person_id", "source"],
            data_dir=tmp_data_dir_with_catalog,
        )
        assert "label" in df.columns
        assert "source" not in df.columns

    def test_missing_label_col_raises(self, tmp_data_dir_with_catalog: Path):
        """Asking for a non-existent label_col fails loudly."""
        with pytest.raises(KeyError, match="not in result columns"):
            build_experiment_matrix(
                view="persons",
                label_col="does_not_exist",
                columns=["person_id"],
                data_dir=tmp_data_dir_with_catalog,
            )


class TestTemporalCutoff:
    """temporal_cutoff_jd filters out rows at or after the cutoff."""

    def test_cutoff_excludes_later_rows(self, tmp_data_dir_with_catalog: Path):
        """Setting cutoff = 1950 JD should exclude the 2000-born person."""
        df = build_experiment_matrix(
            view="persons",
            columns=["person_id", "birth_jd"],
            temporal_cutoff_jd=2440000.0,  # ~1968
            temporal_cutoff_column="birth_jd",
            data_dir=tmp_data_dir_with_catalog,
        )
        assert len(df) == 2  # 1900 + 1950 born; 2000 born excluded

    def test_cutoff_none_returns_all(self, tmp_data_dir_with_catalog: Path):
        """No cutoff -> all rows."""
        df = build_experiment_matrix(
            view="persons",
            columns=["person_id"],
            data_dir=tmp_data_dir_with_catalog,
        )
        assert len(df) == 3


class TestAutoCatalogInit:
    """The loader auto-initialises the catalog if missing."""

    def test_first_call_creates_catalog(self, tmp_data_dir_with_catalog: Path):
        """If catalog.duckdb is absent the loader builds it on first call."""
        catalog_path = tmp_data_dir_with_catalog / "catalog.duckdb"
        # Pre-condition: catalog doesn't yet exist (fixture only wrote parquets).
        assert not catalog_path.exists()

        df = build_experiment_matrix(
            view="persons", columns=["person_id"],
            data_dir=tmp_data_dir_with_catalog,
        )
        assert catalog_path.exists()
        assert len(df) == 3


class TestColumnsList:
    """Explicit columns list returns only requested columns."""

    def test_columns_restricts_output(self, tmp_data_dir_with_catalog: Path):
        """Asking for [person_id, source] returns exactly those two cols."""
        df = build_experiment_matrix(
            view="persons",
            columns=["person_id", "source"],
            data_dir=tmp_data_dir_with_catalog,
        )
        assert set(df.columns) == {"person_id", "source"}
