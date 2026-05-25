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


class TestFitAllClasses:
    def test_parallel_matches_sequential_and_returns_30(self) -> None:
        """Parallel + sequential produce identical C-indices on all 30 classes.

        Slow test (~25 min on 8-core CPU): 30 sequential Cox fits + 30
        parallel Cox fits. The parity check covers BOTH Task 8 (sequential)
        and Task 9 (parallel) — the standalone sequential test from Task 8's
        plan is intentionally skipped (would duplicate ~21 min of Cox work
        that Task 9's parity test already covers).
        """
        import pandas as pd
        from app.medini.ml.stage_d_baseline import fit_all_classes, split_train_test
        from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

        smoke = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        train, test = split_train_test(smoke, seed=42)

        seq = fit_all_classes(train, test, seed=42, parallel=False)
        par = fit_all_classes(train, test, seed=42, parallel=True)

        assert len(seq) == len(QUALIFYING_EVENT_CLASSES) == 30
        assert {r.event_class for r in seq} == set(QUALIFYING_EVENT_CLASSES)

        seq_map = {r.event_class: r.c_index for r in seq}
        par_map = {r.event_class: r.c_index for r in par}
        for cls, seq_c in seq_map.items():
            par_c = par_map[cls]
            if pd.isna(seq_c) and pd.isna(par_c):
                continue
            assert abs(seq_c - par_c) < 1e-9, f"{cls}: seq={seq_c}, par={par_c}"
