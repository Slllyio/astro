"""Tests for Fork-A Stage D evaluation / DECISION.md generator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.medini.ml.stage_d_evaluate import (
    GateVerdict,
    evaluate_gate,
    render_decision_md,
)


class TestEvaluateGate:
    def test_fail_no_signal_when_all_deltas_negative(self) -> None:
        from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
        nf = {"K_qualifying": 30, "g2_threshold": 11,
              "sigma_noise_per_class": {cls: 0.02 for cls in QUALIFYING_EVENT_CLASSES}}
        records = [{
            "seed": s,
            "per_class": {
                cls: {"delta_test": -0.01,
                      "c_index_test_stage_d": 0.5,
                      "c_index_test_cox": 0.51}
                for cls in QUALIFYING_EVENT_CLASSES
            }
        } for s in range(10)]
        verdict = evaluate_gate(records, noise_floor=nf)
        assert verdict.passes_g1 is False
        assert verdict.passes_g2 is False
        assert verdict.outcome == "FAIL: no aggregate signal"


class TestEvaluateGatePassPath:
    def test_pass_strong_when_main_and_replication_both_clear(self) -> None:
        from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
        nf = {
            "K_qualifying": 30, "g2_threshold": 11,
            "sigma_noise_per_class": {cls: 0.02 for cls in QUALIFYING_EVENT_CLASSES},
        }
        # Build records where 15 of 30 classes clear by ~0.09 (4.5σ); rest at 0.05
        # (below 3σ=0.06 so they don't clear G2 individually; mean_delta=0.07 > 0.06
        # threshold, so G1 passes; 0.05 chosen to avoid fp-accumulation boundary issues).
        clearing = set(QUALIFYING_EVENT_CLASSES[:15])

        def _rec(seed):
            return {
                "seed": seed,
                "per_class": {
                    cls: {
                        "delta_test": 0.09 if cls in clearing else 0.05,
                        "c_index_test_stage_d": 0.62,
                        "c_index_test_cox": 0.54 if cls in clearing else 0.62,
                    }
                    for cls in QUALIFYING_EVENT_CLASSES
                }
            }
        main = [_rec(s) for s in range(10)]
        rep = [_rec(s) for s in range(200, 210)]
        v = evaluate_gate(main, noise_floor=nf, replication_records=rep)
        assert v.passes_g1 and v.passes_g2 and v.passes_g3
        assert v.passes_g4 is True
        assert v.outcome == "PASS strong"


class TestRenderDecisionMd:
    def test_render_contains_outcome(self) -> None:
        from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
        nf = {"K_qualifying": 30, "g2_threshold": 11,
              "sigma_noise_per_class": {cls: 0.02 for cls in QUALIFYING_EVENT_CLASSES}}
        records = [{
            "seed": s,
            "per_class": {
                cls: {"delta_test": -0.01,
                      "c_index_test_stage_d": 0.5,
                      "c_index_test_cox": 0.51}
                for cls in QUALIFYING_EVENT_CLASSES
            }
        } for s in range(10)]
        v = evaluate_gate(records, noise_floor=nf)
        md = render_decision_md(v, noise_floor=nf)
        assert "FAIL: no aggregate signal" in md
        assert "Gate criteria" in md
        assert "Per-class results" in md
