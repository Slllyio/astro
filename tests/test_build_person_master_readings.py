"""Tests for app.medini.etl.build_person_master_readings — master ETL."""
from __future__ import annotations

import json

import pandas as pd
import pytest

from app.medini.etl.build_person_master_readings import (
    _empty_master_row,
    _row_to_master_dict,
    build_master_readings,
)


def _fake_dossier_row(person_id: str = "TEST:1") -> dict:
    """Minimal dossier row matching person_dossier.parquet schema.

    Cloned from test_build_person_readings — same shape so the same
    Chart.from_dossier_row factory consumes it without surprise.
    """
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


class TestRowToMasterDict:
    """Per-row conversion produces a complete master reading record."""

    def test_returns_dict_with_identity(self):
        """Identity fields preserved from input row."""
        row = _fake_dossier_row("ABC:123")
        result = _row_to_master_dict(row)
        assert result["person_id"] == "ABC:123"
        assert result["corpus"] == "TEST"
        assert result["name"] == "Test Person"

    def test_contains_base_bhava_columns(self):
        """Every bhava 1..12 has label + composite (base layer)."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        for b in range(1, 13):
            assert f"b{b}_label" in result
            assert f"b{b}_composite" in result

    def test_contains_sav_per_bhava(self):
        """All 12 SAV-per-bhava columns present (Ashtakavarga)."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        for b in range(1, 13):
            assert f"sav_b{b}" in result
            assert result[f"sav_b{b}"] is not pd.NA

    def test_arudha_triplet_present(self):
        """Arudha Lagna / Upapada Lagna / Dara Pada signs all populated."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        assert 1 <= result["arudha_lagna_sign"] <= 12
        assert 1 <= result["upapada_lagna_sign"] <= 12
        assert 1 <= result["dara_pada_sign"] <= 12

    def test_karakamsa_absent_without_ak(self):
        """Without explicit Atmakaraka input, Karakamsa is None per composer."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        assert result["karakamsa_present"] is False
        assert result["karakamsa_sign"] is None
        assert result["atmakaraka"] is None

    def test_sensitive_points_present(self):
        """Bhrigu Bindu + Pranapada always present (no caller input needed)."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        assert 1 <= result["bhrigu_bindu_sign"] <= 12
        assert 0.0 <= result["bhrigu_bindu_lon"] <= 360.0
        assert 1 <= result["pranapada_sign"] <= 12
        # Without day_of_week / is_day_birth, Maandi is None
        assert result["maandi_sign"] is None

    def test_per_planet_vimsopaka_columns(self):
        """Each of 7 visible grahas has a vimsopaka column (D1-only fallback ≤5).

        Rahu/Ketu omitted: classical Vimsopaka Bala doesn't apply to
        shadow grahas — they have no physical occupation of a varga.
        """
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        for p in ("sun", "moon", "mars", "mercury", "jupiter",
                  "venus", "saturn"):
            col = f"vimsopaka_{p}"
            assert col in result
            assert 0.0 <= result[col] <= 5.5  # D1-only cap

    def test_per_planet_avastha_multiplier_columns(self):
        """Each visible graha has an avastha multiplier column (7 total).

        Rahu/Ketu omitted: Baladi/Deeptadi avastha are dasha-states of a
        physical graha; nodes don't carry one classically.
        """
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        for p in ("sun", "moon", "mars", "mercury", "jupiter",
                  "venus", "saturn"):
            assert f"avastha_mult_{p}" in result

    def test_remedies_summary_consistent(self):
        """remedy_planets and remedy_caveats have matching length."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        assert len(result["remedy_planets"]) == result["n_prescribed_remedies"]
        assert len(result["remedy_caveats"]) == result["n_prescribed_remedies"]
        for caveat in result["remedy_caveats"]:
            assert caveat in {"PROCEED", "TRIAL_REQUIRED", "AVOID"}

    def test_json_blobs_are_valid_json(self):
        """All *_json columns parse back to dict/list cleanly."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        for col in ("upagrahas_json", "all_arudhas_json",
                    "varga_confirmations_json", "bhavat_chains_json",
                    "triple_lagna_json"):
            json.loads(result[col])  # raises if invalid

    def test_varga_confirmations_all_unknown_without_input(self):
        """Without varga_pillar_scores, all 12 confirmations land UNKNOWN."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        decoded = json.loads(result["varga_confirmations_json"])
        for label in decoded.values():
            assert label == "UNKNOWN"


class TestEmptyMasterRow:
    """The empty-row stub preserves identity and uses safe sentinels."""

    def test_identity_preserved(self):
        row = _fake_dossier_row("FAIL:1")
        empty = _empty_master_row(row)
        assert empty["person_id"] == "FAIL:1"
        assert empty["corpus"] == "TEST"

    def test_asc_sign_is_na(self):
        empty = _empty_master_row(_fake_dossier_row())
        assert empty["asc_sign"] is pd.NA

    def test_no_remedies(self):
        empty = _empty_master_row(_fake_dossier_row())
        assert empty["n_prescribed_remedies"] == 0
        assert empty["remedy_planets"] == []

    def test_json_blobs_are_empty_but_valid(self):
        empty = _empty_master_row(_fake_dossier_row())
        assert json.loads(empty["upagrahas_json"]) == {}
        assert json.loads(empty["bhavat_chains_json"]) == []


class TestBuildMasterReadings:
    """build_master_readings turns a small DataFrame into a parquet-ready DF."""

    def test_handles_single_row(self):
        df = pd.DataFrame([_fake_dossier_row("S:1")])
        result = build_master_readings(df, workers=1)
        assert len(result) == 1
        assert result.iloc[0]["person_id"] == "S:1"

    def test_handles_three_rows(self):
        df = pd.DataFrame([
            _fake_dossier_row("S:1"),
            _fake_dossier_row("S:2"),
            _fake_dossier_row("S:3"),
        ])
        result = build_master_readings(df, workers=1)
        assert len(result) == 3
        # Order-preserving in single-worker mode
        assert list(result["person_id"]) == ["S:1", "S:2", "S:3"]

    def test_output_columns_stable(self):
        """Single-row build produces the same column set as the empty stub."""
        df = pd.DataFrame([_fake_dossier_row()])
        result = build_master_readings(df, workers=1)
        # Sanity: expected columns subset
        expected_subset = {
            "person_id", "asc_sign", "bhrigu_bindu_sign",
            "arudha_lagna_sign", "sav_b1", "vimsopaka_sun",
            "avastha_mult_jupiter", "n_prescribed_remedies",
            "upagrahas_json", "bhavat_chains_json",
        }
        assert expected_subset.issubset(set(result.columns))
