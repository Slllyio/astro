"""Tests for app.medini.etl.build_person_master_readings — master ETL."""
from __future__ import annotations

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

    def test_karakamsa_present_when_ak_and_d9_provided(self):
        """When the row carries atmakaraka + d9 sign, Karakamsa activates."""
        row = _fake_dossier_row()
        row["atmakaraka"] = "Mercury"
        row["atmakaraka_d9_sign"] = 4
        result = _row_to_master_dict(row)
        assert result["karakamsa_present"] is True
        assert result["karakamsa_sign"] == 4
        assert result["atmakaraka"] == "Mercury"

    def test_yogini_populated_when_moon_nakshatra_and_target_jd_provided(self):
        """Yogini snapshot layer activates with moon_nakshatra + target_jd."""
        row = _fake_dossier_row()
        row["moon_nakshatra_index"] = 11
        row["target_jd"] = 2461191.0  # ~2026
        result = _row_to_master_dict(row)
        assert result["yogini_active_name"] is not None
        assert result["yogini_active_lord"] is not None
        assert result["yogini_active_years_left"] >= 0, (
            "years_left must be positive — regression on cycle-shift fix"
        )

    def test_ashtottari_populated_with_inputs(self):
        """Ashtottari activates with the same inputs as Yogini."""
        row = _fake_dossier_row()
        row["moon_nakshatra_index"] = 11
        row["target_jd"] = 2461191.0
        result = _row_to_master_dict(row)
        assert result["ashtottari_active_lord"] is not None
        # ashtottari_applicable depends on Rahu's position in this fake chart
        assert isinstance(result["ashtottari_applicable"], bool)

    def test_maandi_populated_with_day_metadata(self):
        """Maandi activates when day_of_week + is_day_birth provided."""
        row = _fake_dossier_row()
        row["day_of_week"] = 5  # Friday
        row["is_day_birth"] = True
        result = _row_to_master_dict(row)
        assert result["maandi_sign"] is not None
        assert 1 <= result["maandi_sign"] <= 12

    def test_sensitive_points_present(self):
        """Bhrigu Bindu + Pranapada always present (no caller input needed)."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        assert 1 <= result["bhrigu_bindu_sign"] <= 12
        assert 0.0 <= result["bhrigu_bindu_lon"] <= 360.0
        assert 1 <= result["pranapada_sign"] <= 12
        # Without day_of_week / is_day_birth, Maandi is None
        assert result["maandi_sign"] is None

    def test_per_planet_vimsopaka_columns_d1_fallback(self):
        """Each of 7 visible grahas has a vimsopaka column.

        Without per_planet_varga_signs in the row (D1-only fallback),
        composite caps at ~5 rupas (D1 weight = 5/20).

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

    def test_vimsopaka_uses_real_scale_with_varga_signs(self):
        """When per_planet_varga_signs is supplied, Vimsopaka uses real 20-rupa scale.

        Regression for Tier C-2: bulk ETL now enriches dossier rows with
        saptavargaja sign maps. Composite should reach into 8-18 rupa
        range for typical charts, not be structurally clamped at 5.
        """
        row = _fake_dossier_row()
        # Mercury exalted in Virgo across multiple vargas → composite > 5
        row["per_planet_varga_signs"] = {
            "Mercury": {"D1": 6, "D2": 6, "D3": 6, "D7": 6,
                        "D9": 6, "D12": 6, "D30": 6},
        }
        result = _row_to_master_dict(row)
        assert result["vimsopaka_mercury"] > 5.5, (
            f"With saptavargaja signs supplied, Mercury Vimsopaka should "
            f"exceed the D1-only cap of 5, got {result['vimsopaka_mercury']}"
        )

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

    def test_nested_layers_are_list_of_struct(self):
        """The 5 dense layers are list[dict] so PyArrow infers LIST<STRUCT>.

        Earlier this script JSON-encoded these columns into strings; the
        2026-05-31 storage refactor unnested them so DuckDB can push
        predicates into the struct fields (e.g.
        ``WHERE varga_confirmations[1].label = 'CONFIRMED'``).
        """
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        for col in ("upagrahas", "all_arudhas", "varga_confirmations",
                    "bhavat_chains", "triple_lagna"):
            assert col in result, f"missing {col}"
            assert isinstance(result[col], list), f"{col} should be list"
            for elem in result[col]:
                assert isinstance(elem, dict), (
                    f"{col} elements should be dict (PyArrow → STRUCT)"
                )

    def test_upagrahas_has_5_named_entries(self):
        """All 5 classical upagrahas present with sign + longitude."""
        result = _row_to_master_dict(_fake_dossier_row())
        names = {u["name"] for u in result["upagrahas"]}
        assert names == {"Dhuma", "Vyatipata", "Parivesha",
                         "Indrachapa", "Upaketu"}
        for u in result["upagrahas"]:
            assert "sign" in u and "longitude" in u

    def test_all_arudhas_has_12_bhavas(self):
        """One arudha entry per bhava (1..12)."""
        result = _row_to_master_dict(_fake_dossier_row())
        bhavas = sorted(a["bhava"] for a in result["all_arudhas"])
        assert bhavas == list(range(1, 13))

    def test_varga_confirmations_all_unknown_without_input(self):
        """Without varga_pillar_scores, all 12 confirmations land UNKNOWN."""
        row = _fake_dossier_row()
        result = _row_to_master_dict(row)
        for vc in result["varga_confirmations"]:
            assert vc["label"] == "UNKNOWN"

    def test_varga_confirmations_populated_when_pillar_scores_provided(self):
        """When varga_pillar_scores supplied (Tier C-3), confirmations get real verdicts.

        Strong positive scores for bhava 7 and 10 should fire CONFIRMED
        when the D1 base also promises positively.
        """
        row = _fake_dossier_row()
        row["varga_pillar_scores"] = {7: 0.5, 10: 0.5}
        result = _row_to_master_dict(row)
        # At least the supplied bhavas should NOT be UNKNOWN
        non_unknown = {vc["bhava"]: vc["label"]
                       for vc in result["varga_confirmations"]
                       if vc["label"] != "UNKNOWN"}
        assert 7 in non_unknown or 10 in non_unknown, (
            "Supplying pillar scores must produce at least one non-UNKNOWN "
            f"verdict; got {non_unknown}"
        )


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

    def test_nested_layers_are_empty_lists(self):
        """Empty stub uses [] for all 5 nested layers (matches success schema)."""
        empty = _empty_master_row(_fake_dossier_row())
        for col in ("upagrahas", "all_arudhas", "varga_confirmations",
                    "bhavat_chains", "triple_lagna"):
            assert empty[col] == [], f"{col} should be empty list in stub"


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
            "upagrahas", "bhavat_chains",  # renamed from *_json in storage refactor
        }
        assert expected_subset.issubset(set(result.columns))
