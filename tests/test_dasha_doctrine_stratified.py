"""Tests for app/medini/ml/dasha_doctrine_stratified.py.

Pins the within-(corpus, dasha_lord) stratification logic — the lifecycle
control used in Round-11 test (b). Each stratum's rows are binned by
mix_score quintile, then a CorpusRR is emitted per (corpus, lord) cell.
"""
from __future__ import annotations

import pytest

pytest.importorskip("app.medini.ml.dasha_doctrine_score")  # in-flight module not present on this branch

import pandas as pd

from app.medini.ml.dasha_doctrine_stratified import _per_stratum_rrs


class TestPerStratumRRs:
    """Per (corpus, dasha_lord) stratum filtering + RR computation."""

    def test_no_strata_returned_when_below_min_events(self):
        """Strata with fewer than _MIN_STRATUM_EVENTS get filtered out."""
        annotated = {
            "ADB": pd.DataFrame({
                "dasha_lord": ["Moon"] * 200,
                "mix_score": [float(i) for i in range(200)],
                "dasha_start_jd": [0.0] * 200,
                "dasha_end_jd": [10.0] * 200,
                "event_personal": [1] * 2 + [0] * 198,  # only 2 events — below 10 threshold
            }),
        }
        strata = _per_stratum_rrs(annotated, event_class="personal")
        assert strata == []

    def test_stratum_returned_when_above_min_events(self):
        """A stratum with sufficient events should produce a CorpusRR."""
        annotated = {
            "ADB": pd.DataFrame({
                "dasha_lord": ["Moon"] * 200,
                "mix_score": [float(i) for i in range(200)],
                "dasha_start_jd": [0.0] * 200,
                "dasha_end_jd": [10.0] * 200,
                # 20 events well-distributed: 5 in bottom quintile, 5 in top quintile.
                "event_personal": (
                    [1] * 5 + [0] * 35
                    + [0] * 40
                    + [0] * 40
                    + [0] * 40
                    + [1] * 5 + [0] * 35
                ),
            }),
        }
        strata = _per_stratum_rrs(annotated, event_class="personal")
        # Should produce 1 stratum (ADB::Moon).
        assert len(strata) == 1
        assert strata[0].corpus == "ADB::Moon"
        # 5 events in top quintile, 5 in bottom → RR ≈ 1.0 (same rate).
        assert 0.5 < strata[0].rr < 2.0

    def test_multiple_corpora_multiple_lords_yield_separate_strata(self):
        """Each (corpus, lord) cell with enough events should appear as its own stratum."""
        annotated = {}
        for corpus in ("ADB", "WD"):
            annotated[corpus] = pd.concat([
                pd.DataFrame({
                    "dasha_lord": [lord] * 200,
                    "mix_score": [float(i) for i in range(200)],
                    "dasha_start_jd": [0.0] * 200,
                    "dasha_end_jd": [10.0] * 200,
                    "event_personal": (
                        [1] * 5 + [0] * 35 + [0] * 40 + [0] * 40
                        + [0] * 40 + [1] * 5 + [0] * 35
                    ),
                })
                for lord in ("Moon", "Sun")
            ], ignore_index=True)
        strata = _per_stratum_rrs(annotated, event_class="personal")
        assert len(strata) == 4  # 2 corpora × 2 lords
        stratum_ids = {s.corpus for s in strata}
        assert stratum_ids == {"ADB::Moon", "ADB::Sun", "WD::Moon", "WD::Sun"}
