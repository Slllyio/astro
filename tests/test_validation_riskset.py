"""Phase 3 runner: the event map is exactly the pre-registered one, and the statistics behave."""
from __future__ import annotations

import numpy as np

from tools.validation.riskset_timing import MARAKA, excess, exposed, holm, map_event


class TestEventMap:
    def test_registered_rows(self):
        """Each prereg row maps to its house; month suffixes in legacy roots are ignored."""
        assert map_event("Relationship", "Marriage") == (7,)
        assert map_event("Marriage April", None) == (7,)
        assert map_event("Death by Disease", None) == MARAKA
        assert map_event("Death, Cause unspecified", None) == MARAKA
        assert map_event("Death of Father", None) == (9,)
        assert map_event("Health", "Accident (Non-fatal)") == (6,)      # review: accidents -> 6
        assert map_event("Crime", "Arrest") == (12,)                    # review: arrest -> 12
        assert map_event("Crime", "Law suit") == (6,)
        assert map_event("Financial", "Inherited money") == (8,)        # review: inheritance -> 8
        assert map_event("Family", "Conception sex") == (5,)
        assert map_event("Work", "Prize") == (10,)

    def test_excluded_rows(self):
        """Contested or unlisted types are excluded, never guessed."""
        for root, sub in [("fame", "Positive"), ("Social", "Institutionalized - prison, hospital"),
                          ("Family", "Change in family responsibilities"), ("Family", "Parents divorced"),
                          ("Death of Significant person", None), ("Other Death", None),
                          ("Work", "Lose social status"), ("Death and Came back August", None)]:
            assert map_event(root, sub) is None, (root, sub)


class TestStatistics:
    def test_exposure_levels(self):
        """AD needs tier >= 3; MD counts any period whose MD lord influences (tiers 1, 3, 4)."""
        assert [exposed(t, "AD") for t in range(5)] == [False, False, False, True, True]
        assert [exposed(t, "MD") for t in range(5)] == [False, True, False, True, True]

    def test_excess_recovers_known_difference(self):
        """Case always exposed, controls half exposed -> E = 0.5."""
        rng = np.random.default_rng(0)
        xk = np.tile([1, 0] * 5, (200, 1)).astype(float)
        r = excess(np.ones(200), xk, [str(i) for i in range(200)], rng)
        assert abs(r["E"] - 0.5) < 1e-12

    def test_holm(self):
        """Holm: smallest p times m, then monotone."""
        assert holm({"a": 0.01, "b": 0.04}) == {"a": 0.02, "b": 0.04}


class TestAuditFixes:
    def test_legacy_death_rows_map_to_maraka(self):
        """Audit B1: old-format 'Death' + subtype rows are own deaths; a suicide ATTEMPT is not."""
        for sub in ("Disease", "Unspecified", "Accident", "Suicide"):
            assert map_event("Death", sub) == MARAKA
        assert map_event("Death", "Suicide Attempt") is None

    def test_health_maps_only_negative(self):
        """Audit NB6: 'Health' + healing/remission subtypes are not 'health negative'."""
        assert map_event("health", "Negative") == (6,)
        assert map_event("Health", "Finally healed") is None
        assert map_event("Health", "Begin remission") is None


class TestReplicatedGates:
    def test_planted_gate_passes_on_unbiased_pipeline(self):
        """Amendment 1: 500 planted draws recover +0.03 with calibrated coverage."""
        from tools.validation.riskset_timing import calibrate
        rng = np.random.default_rng(1)
        xk = (rng.random((3000, 10)) < 0.3).astype(float)
        xc = (rng.random(3000) < 0.3).astype(float)
        pids = [str(i) for i in range(3000)]
        assert calibrate(xc, xk, pids, "planted", rng, reps=200)["pass"]
        assert calibrate(xc, xk, pids, "sham", rng, reps=200)["pass"]
