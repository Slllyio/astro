"""Tests for Fork-A Stage D Cox PH baseline."""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.stage_d_baseline import (
    fit_cause_specific_cox,
    split_train_test,
    PENALIZER,
)


class TestFitCauseSpecificCox:
    def test_returns_c_index_in_range(self) -> None:
        """Single-class Cox PH on smoke returns C-index in [0.4, 0.7]."""
        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        train, test = split_train_test(smoke, seed=42)
        result = fit_cause_specific_cox(train, test, event_class="career", seed=42)
        assert 0.4 <= result.c_index <= 0.7, f"got {result.c_index:.3f}"
        assert result.converged is True

    def test_penalizer_is_locked_at_0_01(self) -> None:
        """L1 penalty is fixed (no tune)."""
        assert PENALIZER == 0.01
