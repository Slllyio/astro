"""Paired tests for stage_d_dataset_v2.py.

Tests: schema correctness, JD math (event_jd - birth_jd), censoring logic.

Usage:
    py -3.12 -m pytest tests/test_stage_d_dataset_v2.py -v
"""
from __future__ import annotations

import pytest

pytest.importorskip("torch")  # Stage-D heavy dep — see requirements-stage-d.txt

import numpy as np
import pandas as pd
import pytest
import torch

from app.medini.ml.stage_d_dataset import K_BINS, assign_time_bin
from app.medini.ml.stage_d_dataset_v2 import (
    _feature_columns_v2,
    build_dataset_v2,
)
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES


# ── Fixtures ─────────────────────────────────────────────────────────────


def _make_person_row(
    name_norm: str,
    event_class: str | None,
    event_jd: float,
    birth_jd: float,
    *,
    asc_sign: int = 1,
    sun_sign: int = 2,
    moon_lon: float = 150.0,
) -> dict:
    """Build one synthetic row matching the v2 parquet schema."""
    time_to_event = event_jd - birth_jd
    row: dict = {
        "person_id": f"WD:Q_{name_norm}",
        "name_norm": name_norm,
        "event_class": event_class,
        "window_duration_days": time_to_event,
        "md_lord_at_event": "Saturn" if event_class else None,
        "ad_lord_at_event": "Mars" if event_class else None,
        "md_seq": 5 if event_class else None,
        "ad_seq": 3 if event_class else None,
        "md_elapsed_years": 5.2 if event_class else None,
        "ad_elapsed_years": 1.1 if event_class else None,
        "ad_duration_days": 1095.0 if event_class else None,
        # Chart cols
        "asc_lon": 30.5,
        "asc_sign": asc_sign,
        "sun_lon": 90.0,
        "sun_sign": sun_sign,
        "sun_house": 3,
        "sun_nakshatra": 7,
        "moon_lon": moon_lon,
        "moon_sign": 5,
        "moon_house": 5,
        "moon_nakshatra": 12,
        "mars_lon": 120.0,
        "mars_sign": 4,
        "mars_house": 4,
        "mars_nakshatra": 10,
        "mercury_lon": 80.0,
        "mercury_sign": 3,
        "mercury_house": 3,
        "mercury_nakshatra": 6,
        "jupiter_lon": 200.0,
        "jupiter_sign": 7,
        "jupiter_house": 7,
        "jupiter_nakshatra": 20,
        "venus_lon": 60.0,
        "venus_sign": 2,
        "venus_house": 2,
        "venus_nakshatra": 4,
        "saturn_lon": 300.0,
        "saturn_sign": 10,
        "saturn_house": 10,
        "saturn_nakshatra": 25,
        "rahu_lon": 170.0,
        "rahu_sign": 6,
        "rahu_house": 6,
        "rahu_nakshatra": 15,
        "ketu_lon": 350.0,
        "ketu_sign": 12,
        "ketu_house": 12,
        "ketu_nakshatra": 27,
    }
    # One-hot lord columns
    lords = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
             "Venus", "Saturn", "Rahu", "Ketu")
    for level in ("md", "ad"):
        active = "Saturn" if (level == "md" and event_class) else (
            "Mars" if (level == "ad" and event_class) else None
        )
        for lord in lords:
            row[f"{level}_lord_at_event_is_{lord.lower()}"] = (
                1 if (lord == active) else 0
            )
    # Event label columns
    for cls in QUALIFYING_EVENT_CLASSES:
        row[f"event_{cls}"] = 1 if (cls == event_class) else 0
    return row


def _make_synthetic_df() -> pd.DataFrame:
    """Return a small synthetic v2 DataFrame (5 rows).

    Row 0: person 'alice' — marriage event, born JD 2400000, event JD 2415000
           → window_duration_days = 15000
    Row 1: person 'bob'   — fame event, born JD 2400000, event JD 2440000
           → window_duration_days = 40000
    Row 2: person 'carol' — censored (no qualifying event), max_jd - birth_jd = 35000
    Row 3: person 'dave'  — career event, JD diff = 20000
    Row 4: person 'eve'   — death_cause_unspecified, JD diff = 50000
    """
    rows = [
        _make_person_row("alice", "marriage",                 2415000.0, 2400000.0),
        _make_person_row("bob",   "fame",                     2440000.0, 2400000.0),
        _make_person_row("carol", None,                       2435000.0, 2400000.0),
        _make_person_row("dave",  "career",                   2420000.0, 2400000.0),
        _make_person_row("eve",   "death_cause_unspecified",  2450000.0, 2400000.0),
    ]
    return pd.DataFrame(rows)


# ── Test 1: Schema correctness ──────────────────────────────────────────


class TestStageDDatasetV2Schema:
    """Verify the StageDDataset returned by build_dataset_v2 has correct dtypes."""

    def test_features_dtype_and_shape(self) -> None:
        """Features tensor must be float32 with (N, n_features) shape."""
        df = _make_synthetic_df()
        all_names = set(df["name_norm"].unique())
        ds = build_dataset_v2(df, name_norms=all_names)

        assert ds.features.dtype == torch.float32, (
            f"features.dtype should be float32, got {ds.features.dtype}"
        )
        assert ds.features.ndim == 2
        assert ds.features.shape[0] == len(df)

    def test_time_bins_dtype_and_range(self) -> None:
        """time_bins must be long int in [0, K_BINS-1]."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms=set(df["name_norm"].unique()))

        assert ds.time_bins.dtype == torch.long
        assert int(ds.time_bins.min()) >= 0
        assert int(ds.time_bins.max()) <= K_BINS - 1

    def test_event_classes_dtype_and_range(self) -> None:
        """event_classes must be long int in [0, 30]."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms=set(df["name_norm"].unique()))

        assert ds.event_classes.dtype == torch.long
        assert int(ds.event_classes.min()) >= 0
        assert int(ds.event_classes.max()) <= len(QUALIFYING_EVENT_CLASSES)

    def test_durations_dtype_and_positive(self) -> None:
        """durations must be float64 np.ndarray with all positive values."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms=set(df["name_norm"].unique()))

        assert isinstance(ds.durations, np.ndarray)
        assert ds.durations.dtype == np.float64
        assert np.all(ds.durations > 0), "All durations must be positive"

    def test_lengths_consistent(self) -> None:
        """All four dataset arrays must have identical length."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms=set(df["name_norm"].unique()))

        assert (
            len(ds.features)
            == len(ds.time_bins)
            == len(ds.event_classes)
            == len(ds.durations)
        ), "Inconsistent lengths across dataset arrays"

    def test_no_feature_columns_leak_survival_target(self) -> None:
        """window_duration_days must NOT appear as a feature column."""
        df = _make_synthetic_df()
        feat_cols = _feature_columns_v2(df)
        assert "window_duration_days" not in feat_cols, (
            "window_duration_days (survival target) must not appear in feature columns"
        )

    def test_no_feature_columns_leak_event_labels(self) -> None:
        """event_<class> columns must NOT appear as feature columns."""
        df = _make_synthetic_df()
        feat_cols = _feature_columns_v2(df)
        leaked = [c for c in feat_cols if c.startswith("event_")]
        assert not leaked, (
            f"Event label columns leaked into features: {leaked[:5]}"
        )


# ── Test 2: JD math ─────────────────────────────────────────────────────


class TestStageDDatasetV2JDMath:
    """Verify that survival duration = event_jd - birth_jd for a known row."""

    def test_alice_duration_matches_manual_calculation(self) -> None:
        """alice: event_jd=2415000, birth_jd=2400000 → duration=15000 days."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms={"alice"})

        assert len(ds.durations) == 1
        expected_days = 15000.0
        actual_days = float(ds.durations[0])
        assert abs(actual_days - expected_days) < 0.001, (
            f"JD math error: expected {expected_days}, got {actual_days}"
        )

    def test_alice_time_bin_matches_assign_time_bin(self) -> None:
        """alice's time_bin must equal assign_time_bin(15000 days)."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms={"alice"})

        expected_bin = assign_time_bin(15000.0)
        actual_bin = int(ds.time_bins[0])
        assert actual_bin == expected_bin, (
            f"Time bin mismatch: expected {expected_bin}, got {actual_bin}"
        )

    def test_eve_duration_matches_manual_calculation(self) -> None:
        """eve: event_jd=2450000, birth_jd=2400000 → duration=50000 days."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms={"eve"})

        expected_days = 50000.0
        actual_days = float(ds.durations[0])
        assert abs(actual_days - expected_days) < 0.001, (
            f"JD math error for eve: expected {expected_days}, got {actual_days}"
        )

    def test_duration_not_window_length_confound(self) -> None:
        """Two persons with same dasha-window length but different event ages
        must get DIFFERENT durations (the v1 bug would give them the same duration).

        alice: event at birth+15000 days
        dave:  event at birth+20000 days
        Both have all the same dasha features; only event_jd differs.
        The v1 bug assigned the SAME duration based on the dasha window length.
        v2 must give different durations.
        """
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms={"alice", "dave"})

        # Sort by person (alice=15000, dave=20000)
        durations = sorted(ds.durations.tolist())
        assert durations[0] != durations[1], (
            "alice and dave should have different survival durations "
            "(v1 bug would give them the same dasha-window-length duration)"
        )
        assert abs(durations[0] - 15000.0) < 0.001
        assert abs(durations[1] - 20000.0) < 0.001


# ── Test 3: Censoring logic ──────────────────────────────────────────────


class TestStageDDatasetV2Censoring:
    """Verify the censoring logic is applied correctly."""

    def test_censored_person_gets_event_class_zero(self) -> None:
        """carol has no qualifying event → event_class must be 0 (censored)."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms={"carol"})

        assert len(ds.event_classes) == 1
        assert int(ds.event_classes[0]) == 0, (
            f"Censored person should have event_class=0, got {int(ds.event_classes[0])}"
        )

    def test_censored_duration_is_positive(self) -> None:
        """carol's censored duration (max_event_jd - birth_jd) must be positive."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms={"carol"})

        assert float(ds.durations[0]) > 0, (
            "Censored person duration must be positive"
        )

    def test_event_persons_get_nonzero_event_class(self) -> None:
        """alice, bob, dave, eve must each have event_class > 0."""
        df = _make_synthetic_df()
        event_persons = {"alice", "bob", "dave", "eve"}
        ds = build_dataset_v2(df, name_norms=event_persons)

        assert all(int(ec) > 0 for ec in ds.event_classes), (
            "All event persons should have event_class > 0"
        )

    def test_marriage_class_index_is_nonzero(self) -> None:
        """alice's event_class index must correspond to 'marriage'."""
        from app.medini.ml.stage_d_dataset import _CLASS_TO_IDX

        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms={"alice"})

        expected_idx = _CLASS_TO_IDX["marriage"]
        actual_idx = int(ds.event_classes[0])
        assert actual_idx == expected_idx, (
            f"alice's event_class should be {expected_idx} (marriage), got {actual_idx}"
        )

    def test_person_subset_isolation(self) -> None:
        """build_dataset_v2 must only include rows for the requested name_norms."""
        df = _make_synthetic_df()
        ds = build_dataset_v2(df, name_norms={"alice", "bob"})

        assert len(ds.features) == 2, (
            f"Requested 2 persons but got {len(ds.features)} rows"
        )

    def test_empty_name_norms_raises(self) -> None:
        """An empty name_norms set that matches nothing must raise ValueError."""
        df = _make_synthetic_df()
        with pytest.raises(ValueError, match="empty"):
            build_dataset_v2(df, name_norms={"nonexistent_person"})

    def test_censored_and_event_mix_event_class_distribution(self) -> None:
        """Mixed dataset: censored=0 count must match number of censored persons."""
        df = _make_synthetic_df()
        # 4 event persons + 1 censored (carol)
        ds = build_dataset_v2(df, name_norms=set(df["name_norm"].unique()))

        n_censored = int((ds.event_classes == 0).sum())
        assert n_censored == 1, (
            f"Expected 1 censored row (carol), got {n_censored}"
        )
        n_events = int((ds.event_classes > 0).sum())
        assert n_events == 4, (
            f"Expected 4 event rows, got {n_events}"
        )
