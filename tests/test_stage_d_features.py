"""Tests for Fork-A Stage D feature pipeline."""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.stage_d_features import (
    QUALIFYING_EVENT_CLASSES,
    load_corpus,
)


class TestQualifyingClasses:
    def test_count_is_30(self) -> None:
        """Spec §1 + Appendix A — K=30 qualifying event classes."""
        assert len(QUALIFYING_EVENT_CLASSES) == 30

    def test_career_and_fame_first(self) -> None:
        """Appendix A is sorted by descending positives; fame=2297 > career=2243."""
        assert QUALIFYING_EVENT_CLASSES[0] == "fame"
        assert QUALIFYING_EVENT_CLASSES[1] == "career"

    def test_no_excluded_classes_present(self) -> None:
        """The 26 excluded classes (e.g., mental_health n=4) must NOT appear."""
        excluded = {"mental_health", "death_by_homicide", "misc.", "mundane"}
        assert excluded.isdisjoint(QUALIFYING_EVENT_CLASSES)


class TestLoadCorpus:
    def test_load_smoke_returns_dataframe(self) -> None:
        """load_corpus(smoke=True) returns a DataFrame with the leaf-window schema."""
        df = load_corpus(smoke=True)
        assert isinstance(df, pd.DataFrame)
        required_cols = {"name_norm", "md_lord", "ad_lord", "pd_lord",
                         "window_duration_days"}
        assert required_cols.issubset(df.columns)

    def test_load_full_returns_dataframe(self) -> None:
        """load_corpus(smoke=False) loads the full mdadpd corpus."""
        df = load_corpus(smoke=False)
        assert len(df) > 0


class TestJoinNatalTensor:
    def test_join_preserves_window_count(self) -> None:
        """Joining natal Vedic Tensor doesn't drop windows (left-join)."""
        from app.medini.ml.stage_d_features import join_natal_vedic_tensor

        corpus = load_corpus(smoke=True)
        joined = join_natal_vedic_tensor(corpus)
        assert len(joined) == len(corpus), "left-join must not drop rows"

    def test_join_adds_193_columns_minus_meta(self) -> None:
        """Tensor adds ~193 cols (Base 70 + Kinematic 63 + Vedic 50 + meta 10)."""
        from app.medini.ml.stage_d_features import join_natal_vedic_tensor

        corpus = load_corpus(smoke=True)
        joined = join_natal_vedic_tensor(corpus)
        new_cols = set(joined.columns) - set(corpus.columns)
        # Allow ±20% tolerance — the Vedic Tensor schema may have evolved.
        assert 150 <= len(new_cols) <= 230, f"got {len(new_cols)} new cols"
