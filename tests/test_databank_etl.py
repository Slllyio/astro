"""Tests for app.medini.etl.databank_etl — the Stage 2 multiprocessing
pipeline that converts a scraper CSV into an ML-ready parquet file.

The actual multiprocessing.Pool is exercised here (not mocked) so we
catch the per-worker pyswisseph initializer issue if it ever regresses.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
import pytest

from app.medini.etl.databank_etl import (
    LABEL_COLUMNS,
    _is_aa_complete,
    _normalize_categories,
    _process_row,
    _row_to_jd,
    run_etl,
)
from app.medini.etl.feature_engineering import expected_feature_columns
from app.medini.etl.lahiri_worker import init_worker


# ---------- Filtering ----------

def test_is_aa_complete_accepts_full_row() -> None:
    row = {
        "rodden_rating": "AA",
        "date_of_birth": "1990-07-15",
        "time_of_birth": "12:00:00",
        "latitude": "12.97",
        "longitude": "77.59",
        "tz_offset": "5.5",
    }
    assert _is_aa_complete(row) is True


def test_is_aa_complete_rejects_non_aa() -> None:
    row = {
        "rodden_rating": "A",  # Rodden A, not AA
        "date_of_birth": "1990-07-15", "time_of_birth": "12:00:00",
        "latitude": "12.97", "longitude": "77.59", "tz_offset": "5.5",
    }
    assert _is_aa_complete(row) is False


@pytest.mark.parametrize("missing_field", [
    "date_of_birth", "time_of_birth", "latitude", "longitude", "tz_offset",
])
def test_is_aa_complete_rejects_any_missing_field(missing_field: str) -> None:
    row = {
        "rodden_rating": "AA",
        "date_of_birth": "1990-07-15",
        "time_of_birth": "12:00:00",
        "latitude": "12.97",
        "longitude": "77.59",
        "tz_offset": "5.5",
    }
    row[missing_field] = ""
    assert _is_aa_complete(row) is False


# ---------- JD conversion ----------

def test_row_to_jd_bangalore_baseline() -> None:
    """Same JD as test_dasha_dates / test_lagna pin: 1990-07-15 12:00 IST."""
    row = {
        "date_of_birth": "1990-07-15",
        "time_of_birth": "12:00:00",
        "tz_offset": "5.5",
    }
    jd = _row_to_jd(row)
    assert jd is not None
    # 12:00 IST → 06:30 UT → julday(1990, 7, 15, 6.5) = 2448087.7708...
    assert jd == pytest.approx(2448087.770833, abs=1e-5)


def test_row_to_jd_returns_none_for_missing_field() -> None:
    assert _row_to_jd({"date_of_birth": "", "time_of_birth": "12:00:00", "tz_offset": "0"}) is None
    assert _row_to_jd({"date_of_birth": "1990-07-15", "time_of_birth": "", "tz_offset": "0"}) is None
    assert _row_to_jd({"date_of_birth": "1990-07-15", "time_of_birth": "12:00:00", "tz_offset": ""}) is None


def test_row_to_jd_returns_none_for_unparseable() -> None:
    assert _row_to_jd({
        "date_of_birth": "garbage", "time_of_birth": "12:00:00", "tz_offset": "0"
    }) is None


# ---------- Category normalization ----------

def test_normalize_categories_simple() -> None:
    result = _normalize_categories("Vocation : Politics : Politician;Vocation : Awards")
    assert result["categories_raw"] == "Vocation : Politics : Politician;Vocation : Awards"
    assert "vocation : politics : politician" in result["categories_lower"]
    assert "politician" in result["categories_tokens"]
    assert "awards" in result["categories_tokens"]


def test_normalize_categories_empty() -> None:
    result = _normalize_categories("")
    assert result["categories_raw"] == ""
    assert result["categories_lower"] == ""
    assert result["categories_tokens"] == []


def test_normalize_categories_dedupes_tokens() -> None:
    """Tokens preserve order but drop duplicates across categories."""
    result = _normalize_categories(
        "Vocation : Politics : Politician;Vocation : Politics : Diplomat"
    )
    # "vocation" and "politics" appear twice in the raw string but only once in tokens
    counts = {tok: result["categories_tokens"].count(tok) for tok in result["categories_tokens"]}
    assert counts["vocation"] == 1
    assert counts["politics"] == 1


# ---------- Per-row processing ----------

def test_process_row_bangalore_baseline_succeeds() -> None:
    """The worker function on the Bangalore baseline produces a full feature dict."""
    init_worker()  # required since this test runs in main process, not a Pool worker
    row = {
        "name": "Test Subject",
        "rodden_rating": "AA",
        "date_of_birth": "1990-07-15",
        "time_of_birth": "12:00:00",
        "latitude": "12.97",
        "longitude": "77.59",
        "tz_offset": "5.5",
        "categories": "Vocation : Test",
        "source_url": "https://example/test",
    }
    result = _process_row(row)
    assert result is not None
    # Has all 193 features + label columns
    expected_features = set(expected_feature_columns())
    assert expected_features.issubset(result.keys())
    # Label columns also present
    for col in LABEL_COLUMNS:
        assert col in result
    # Sanity: known-good values
    assert result["lagna_sign"] == 6  # Virgo
    assert result["nak_moon"] == 26   # Revati


def test_process_row_returns_none_for_unparseable() -> None:
    row = {
        "name": "Bad Row", "rodden_rating": "AA",
        "date_of_birth": "garbage", "time_of_birth": "12:00:00",
        "latitude": "12.97", "longitude": "77.59", "tz_offset": "5.5",
        "categories": "", "source_url": "",
    }
    assert _process_row(row) is None


# ---------- End-to-end ETL through multiprocessing.Pool ----------

@pytest.fixture
def synthetic_csv(tmp_path: Path) -> Path:
    """Hand-crafted CSV with a mix of valid + filterable rows. Pinned charts
    cross-reference the existing Bangalore + March-2030 baselines."""
    rows = [
        # Bangalore baseline (valid AA)
        {
            "name": "Bangalore Baseline",
            "date_of_birth": "1990-07-15",
            "time_of_birth": "12:00:00",
            "latitude": "12.97",
            "longitude": "77.59",
            "tz_offset": "5.5",
            "rodden_rating": "AA",
            "categories": "Vocation : Test : Reference",
            "source_url": "https://example/bangalore",
        },
        # March 2030 anchor (valid AA)
        {
            "name": "March 2030 Anchor",
            "date_of_birth": "2030-03-14",
            "time_of_birth": "12:00:00",
            "latitude": "0.0",
            "longitude": "0.0",
            "tz_offset": "0.0",
            "rodden_rating": "AA",
            "categories": "Vocation : Test : Reference",
            "source_url": "https://example/march2030",
        },
        # Non-AA — must be filtered out
        {
            "name": "B-Rated Person",
            "date_of_birth": "1980-01-01",
            "time_of_birth": "08:30:00",
            "latitude": "40.0",
            "longitude": "-74.0",
            "tz_offset": "-5.0",
            "rodden_rating": "B",
            "categories": "Notable",
            "source_url": "https://example/brated",
        },
        # Missing time — must be filtered out even though AA
        {
            "name": "AA But No Time",
            "date_of_birth": "1970-06-01",
            "time_of_birth": "",
            "latitude": "0.0",
            "longitude": "0.0",
            "tz_offset": "0.0",
            "rodden_rating": "AA",
            "categories": "Notable",
            "source_url": "https://example/notime",
        },
    ]
    csv_path = tmp_path / "raw.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def test_run_etl_filters_and_succeeds(synthetic_csv: Path, tmp_path: Path) -> None:
    output = tmp_path / "features.parquet"
    stats = run_etl(synthetic_csv, output, n_workers=2)

    assert stats["input_count"] == 4
    assert stats["after_filter"] == 2  # only the 2 AA-rated complete rows
    assert stats["succeeded"] == 2
    assert stats["failed"] == 0
    assert output.exists()


def test_run_etl_parquet_has_expected_schema(synthetic_csv: Path, tmp_path: Path) -> None:
    output = tmp_path / "features.parquet"
    run_etl(synthetic_csv, output, n_workers=2)

    df = pd.read_parquet(output)
    # 2 surviving rows
    assert len(df) == 2
    # All 193 feature columns present
    for col in expected_feature_columns():
        assert col in df.columns, f"missing feature column: {col}"
    # Label columns also present
    for col in LABEL_COLUMNS:
        assert col in df.columns, f"missing label column: {col}"


def test_run_etl_workers_get_lahiri_initialized(synthetic_csv: Path, tmp_path: Path) -> None:
    """Critical regression: if init_worker() doesn't fire in each subprocess,
    workers silently use tropical longitudes. The Bangalore baseline's Virgo
    Lagna depends on Lahiri sidereal mode being active.
    """
    output = tmp_path / "features.parquet"
    run_etl(synthetic_csv, output, n_workers=2)
    df = pd.read_parquet(output)

    # Bangalore row should have Virgo Lagna (sign 6) under Lahiri.
    # Under tropical, the Lagna would be different (Libra-ish, sign ~7).
    bangalore_row = df[df["name"] == "Bangalore Baseline"].iloc[0]
    assert bangalore_row["lagna_sign"] == 6, (
        "Workers are NOT using Lahiri sidereal — got sign "
        f"{bangalore_row['lagna_sign']}, expected 6 (Virgo). "
        "This means init_worker() failed to set sidereal mode in subprocesses."
    )


def test_run_etl_raises_when_no_rows_survive_filter(tmp_path: Path) -> None:
    """An all-non-AA CSV should raise a clear error rather than silently produce
    an empty parquet."""
    csv_path = tmp_path / "all_bad.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "name", "date_of_birth", "time_of_birth", "latitude", "longitude",
            "tz_offset", "rodden_rating", "categories", "source_url",
        ])
        writer.writeheader()
        writer.writerow({
            "name": "C-Rated", "date_of_birth": "1990-01-01", "time_of_birth": "00:00:00",
            "latitude": "0", "longitude": "0", "tz_offset": "0",
            "rodden_rating": "C", "categories": "", "source_url": "",
        })

    output = tmp_path / "should_not_exist.parquet"
    with pytest.raises(RuntimeError, match="no rows survived filtering"):
        run_etl(csv_path, output, n_workers=1)


def test_run_etl_raises_for_missing_input_file(tmp_path: Path) -> None:
    nonexistent = tmp_path / "does_not_exist.csv"
    output = tmp_path / "out.parquet"
    with pytest.raises(FileNotFoundError):
        run_etl(nonexistent, output)
