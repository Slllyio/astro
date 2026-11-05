"""Tests for Fork-A Stage D PyTorch Dataset + time-bin assignment."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from corpus_presence import needs_file

_needs_features_smoke = needs_file("app/medini/data/dasha_stage_d_features_smoke.parquet")
import torch

from app.medini.ml.stage_d_dataset import (
    K_BINS,
    StageDDataset,
    assign_time_bin,
    build_dataset,
)


class TestTimeBins:
    def test_k_bins_is_50(self) -> None:
        assert K_BINS == 50

    def test_one_day_window_in_lowest_bin(self) -> None:
        assert assign_time_bin(1.0) == 0

    def test_century_window_in_highest_bin(self) -> None:
        assert assign_time_bin(100 * 365.25) == K_BINS - 1


@_needs_features_smoke
class TestStageDDataset:
    def test_dataset_length_matches_dataframe(self) -> None:
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        # Use just 5 persons for speed (full smoke iterrows is ~1 min)
        first_5 = list(smoke["name_norm"].unique()[:5])
        slim = smoke[smoke["name_norm"].isin(first_5)]
        ds = build_dataset(slim, name_norms=first_5)
        assert len(ds) == len(slim)

    def test_dataset_item_shapes(self) -> None:
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        first_5 = list(smoke["name_norm"].unique()[:5])
        slim = smoke[smoke["name_norm"].isin(first_5)]
        ds = build_dataset(slim, name_norms=first_5)
        features, time_bin, event_class = ds[0]
        assert features.dtype == torch.float32
        assert time_bin.dtype == torch.long
        assert event_class.dtype == torch.long
        assert 0 <= int(time_bin) < K_BINS
        assert 0 <= int(event_class) <= 30  # 0 = censored, 1..30 = class

    def test_durations_attribute_aligned_with_features(self) -> None:
        """The .durations np array must be in the same row order as
        .features / .event_classes — Task 17 depends on this."""
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        first_5 = list(smoke["name_norm"].unique()[:5])
        slim = smoke[smoke["name_norm"].isin(first_5)]
        ds = build_dataset(slim, name_norms=first_5)
        assert hasattr(ds, "durations")
        assert isinstance(ds.durations, np.ndarray)
        assert len(ds.durations) == len(ds.features)

    def test_person_leak_assertion(self) -> None:
        """build_dataset must refuse a name_norms list disjoint from the df."""
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        # Use a very small slice for speed
        first_3_persons = list(smoke["name_norm"].unique()[:3])
        slim = smoke[smoke["name_norm"].isin(first_3_persons)].head(100)
        # Try to build dataset with a totally different person list
        other_persons = ["__nonexistent_person_xyz__"]
        with pytest.raises((AssertionError, ValueError)):
            build_dataset(slim, name_norms=other_persons)
