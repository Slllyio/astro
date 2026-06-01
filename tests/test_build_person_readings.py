"""Tests for app.medini.etl.build_person_readings — bulk reading ETL."""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.etl.build_person_readings import (
    _empty_reading,
    _row_to_reading_dict,
    build_readings,
)


def _fake_dossier_row(person_id: str = "TEST:1") -> dict:
    """Minimal dossier row matching person_dossier.parquet schema."""
    base = {
        "person_id": person_id,
        "name": "Test Person",
        "corpus": "TEST",
        "source": "synthetic",
        "birth_date": "1990-07-15",
        "birth_time": "12:00:00",
        "birth_time_confidence": 1.0,
        "birth_lat": 12.97, "birth_lon": 77.59, "tz_offset": 5.5,
        "birth_jd": 2448087.5,
        "asc_lon": 173.99, "asc_sign": 6,
    }
    for graha in ("sun", "moon", "mars", "mercury", "jupiter",
                  "venus", "saturn", "rahu", "ketu"):
        base[f"{graha}_lon"] = 100.0
        base[f"{graha}_sign"] = 4
        base[f"{graha}_natal_house"] = 11
        base[f"{graha}_is_retrograde"] = False
    return base


class TestRowToReadingDict:
    """Per-row conversion produces a complete reading record."""

    def test_returns_dict_with_identity(self):
        """Identity fields preserved from input row."""
        row = _fake_dossier_row("ABC:123")
        result = _row_to_reading_dict(row)
        assert result["person_id"] == "ABC:123"
        assert result["corpus"] == "TEST"

    def test_contains_all_12_bhava_label_columns(self):
        """Every bhava 1..12 has label, composite, confirming, afflicting."""
        row = _fake_dossier_row()
        result = _row_to_reading_dict(row)
        for b in range(1, 13):
            assert f"b{b}_label" in result
            assert f"b{b}_composite" in result
            assert f"b{b}_confirming_yogas" in result
            assert f"b{b}_afflicting_yogas" in result

    def test_active_yoga_lists_have_aligned_lengths(self):
        """yoga_names / refs / intensities are parallel lists."""
        row = _fake_dossier_row()
        result = _row_to_reading_dict(row)
        n = len(result["active_yoga_names"])
        assert len(result["active_yoga_refs"]) == n
        assert len(result["active_yoga_intensities"]) == n

    def test_n_strong_and_n_afflicted_counted(self):
        """Counts integer-typed and in 0..12 range."""
        row = _fake_dossier_row()
        result = _row_to_reading_dict(row)
        assert 0 <= result["n_strong_bhavas"] <= 12
        assert 0 <= result["n_afflicted_bhavas"] <= 12


class TestEmptyReading:
    """Stub row used when chart construction fails."""

    def test_empty_reading_has_full_schema(self):
        """Stub row has every column the success path would write."""
        result = _empty_reading({"person_id": "FAIL:1", "corpus": "X"})
        # Same keys as a real reading dict
        success = _row_to_reading_dict(_fake_dossier_row())
        assert set(result.keys()) == set(success.keys())

    def test_empty_reading_preserves_person_id(self):
        """person_id round-trips through the empty path."""
        result = _empty_reading({"person_id": "FAIL:1"})
        assert result["person_id"] == "FAIL:1"


class TestBuildReadings:
    """End-to-end ETL builder works on small synthetic dataset."""

    def test_builds_one_row_per_input(self):
        """Three input dossier rows → three reading rows."""
        rows = [_fake_dossier_row(f"T:{i}") for i in range(3)]
        df_in = pd.DataFrame(rows)
        result = build_readings(df_in, workers=1)
        assert len(result) == 3

    def test_result_is_dataframe_with_expected_columns(self):
        """Output is pandas DataFrame with all framework columns."""
        rows = [_fake_dossier_row("T:1")]
        df_in = pd.DataFrame(rows)
        result = build_readings(df_in, workers=1)
        assert isinstance(result, pd.DataFrame)
        assert "asc_sign" in result.columns
        assert "active_yoga_names" in result.columns
        assert "b7_label" in result.columns

    def test_handles_malformed_row_gracefully(self):
        """Row missing required fields → empty-reading stub, not crash."""
        bad = {"person_id": "BAD:1", "corpus": "X"}
        good = _fake_dossier_row("GOOD:1")
        result = build_readings(pd.DataFrame([bad, good]), workers=1)
        assert len(result) == 2
        # The bad row has asc_sign=NA; the good row has asc_sign=6
        assert result["asc_sign"].notna().sum() == 1
