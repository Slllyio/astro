"""Tests for Layer A (SCCS IRR) and Layer B (discrimination) timing metrics."""
from __future__ import annotations

import numpy as np

from app.medini.ml import dasha_timing_metrics as tm


def _rec(ev_idx, graded, dur=None):
    g = np.array(graded)
    d = np.ones(len(g)) if dur is None else np.array(dur, float)
    return {"dur": d, "graded": g, "binary": g == 4, "ev_idx": ev_idx}


def test_sccs_irr_planted_signal() -> None:
    # 8 windows, one is strength=4 (exposed ~1/8 of time); 85% of events land on
    # it, 15% elsewhere (strong but finite → resolvable IRR with a CI).
    rng = np.random.default_rng(5)
    recs = []
    for _ in range(300):
        ev = 3 if rng.random() < 0.85 else int(rng.choice([0, 1, 2, 4, 5, 6, 7]))
        recs.append(_rec(ev, [0, 1, 2, 4, 1, 0, 2, 1]))
    out = tm.sccs_irr(recs)
    assert out["irr"] > 3 and out["ci_lo"] > 1 and out["p"] < 1e-6


def test_sccs_irr_null_includes_one() -> None:
    rng = np.random.default_rng(0)
    recs = []
    for _ in range(300):
        g = rng.integers(0, 5, size=8)
        dur = np.ones(8)
        # event drawn ∝ duration (uniform here) → null
        ev = int(rng.integers(0, 8))
        recs.append({"dur": dur, "graded": g, "binary": g == 4, "ev_idx": ev})
    out = tm.sccs_irr(recs)
    assert out["ci_lo"] < 1.0 < out["ci_hi"]            # CI straddles 1
    assert out["p"] > 0.05


def test_irr_recovers_lift_direction() -> None:
    # IRR and lift should agree in sign relative to 1.
    recs = [_rec(0, [4, 0, 0, 0]) for _ in range(50)]   # event always exposed
    out = tm.sccs_irr(recs)
    assert out["irr"] > 1 and out["lift"] > 1


def test_discrimination_planted_and_null() -> None:
    # planted: event always on the highest-scored window → C-index ~1, hit@1 high.
    recs = [_rec(0, [4, 1, 0, 2, 1]) for _ in range(150)]
    sig = tm.discrimination(recs, k=500, seed=1)
    assert sig["c_index"] > 0.9 and sig["hit_at_1"] > 0.9 and sig["c_index_p"] < 0.01
    # null: event ∝ duration → C-index ~0.5.
    rng = np.random.default_rng(2)
    nrecs = []
    for _ in range(200):
        g = rng.integers(0, 5, size=6)
        d = np.ones(6)
        nrecs.append({"dur": d, "graded": g, "binary": g == 4,
                      "ev_idx": int(rng.integers(0, 6))})
    nul = tm.discrimination(nrecs, k=500, seed=3)
    assert abs(nul["c_index"] - 0.5) < 0.07 and nul["c_index_p"] > 0.05


def test_hit_at_k_optimistic_ties() -> None:
    g = np.array([2, 2, 0, 1])
    assert tm._hit_at_k(g, 0, 1)            # tied for top → counts as hit@1
    assert not tm._hit_at_k(g, 2, 1)        # lowest, not in top-1
    assert tm._hit_at_k(g, 3, 3)            # rank-3 value in top-3
