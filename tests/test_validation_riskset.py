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
