"""Tests for Fork-A Stage D pre-flight diagnostics."""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.stage_d_preflight import (
    PreflightResult,
    check_class_qualification,
    check_co_occurrence_rate,
    check_no_jd_in_features,
    check_person_leak_assertion,
    run_preflight,
)


class TestPreflight:
    def test_class_qualification_on_full_smoke(self) -> None:
        df = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        K, dropped = check_class_qualification(df, min_positives=1)
        assert K >= 19  # smoke covers 19+ of 30 classes (per sub-gate D.0 finding)

    def test_no_jd_in_features(self) -> None:
        df = pd.read_parquet("app/medini/data/dasha_stage_d_features_smoke.parquet")
        result = check_no_jd_in_features(df)
        assert result.passed, f"forbidden cols: {result.detail}"

    def test_person_leak_check_returns_pass(self) -> None:
        """The synthetic leak check should always return PASS (the assertion
        path is in place)."""
        result = check_person_leak_assertion()
        assert result.passed
