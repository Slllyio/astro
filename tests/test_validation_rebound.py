"""Phase 1 re-bound: published results convert to the right scale and the sham gates its engine."""
from __future__ import annotations

from tools.validation.rebound import _static, _timing, judge, pools


class TestRebound:
    def test_auc_converted_to_zero_centred_effect(self):
        """AUC 0.52 becomes effect +0.02 with the stored SE."""
        (r,) = _static("e", {"H7": {"auc": 0.52, "se": 0.01, "n_case": 500, "n_contrast": 500,
                                    "ci_lo": 0.5, "ci_hi": 0.54}})
        assert abs(r["effect"] - 0.02) < 1e-12 and r["se"] == 0.01

    def test_withheld_timing_never_pooled(self):
        """A saturated (withheld) instrument is listed but excluded from the pool."""
        rows = _timing("e", {"a": {"n_events": 100, "mean_lift": 0.0, "ci_lo": -0.02, "ci_hi": 0.02},
                             "b": {"n_events": 100, "mean_lift": 0.0, "ci_lo": -0.02, "ci_hi": 0.02},
                             "c": {"n_events": 100, "mean_lift": 0.5, "ci_lo": 0.4, "ci_hi": 0.6,
                                   "withheld_saturated": True}})
        rows = judge(rows)
        assert rows[2]["verdict"].startswith("WITHHELD")
        (p,) = pools(rows)
        assert p["k"] == 2 and abs(p["effect"]) < 1e-12

    def test_failed_sham_poisons_static_family(self):
        """If an engine's sham is not null, none of its static tests can be read."""
        d = {"SHAM_x": {"auc": 0.60, "se": 0.01, "n_case": 300, "n_contrast": 300, "ci_lo": 0.58, "ci_hi": 0.62},
             "H7": {"auc": 0.50, "se": 0.005, "n_case": 3000, "n_contrast": 3000, "ci_lo": 0.49, "ci_hi": 0.51}}
        rows = judge(_static("e", d))
        assert rows[1]["verdict"] == "SHAM_FAIL"
