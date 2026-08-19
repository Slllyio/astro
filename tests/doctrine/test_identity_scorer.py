"""Increment 33 drift-guard: pin the identity-scorer NEGATIVE.

The identity-preserving representation (criterion/placement/aspect-source-nature features, uniform across
held-out + NH + the live anchor) does NOT beat A2's aggregation-level (delta,frame) token model on LOCO,
overfits more, and fails the live anchor gate. This pins the two robust structural claims so a future
"identity wins" result must update them. (Same shape as test_structural_separability / test_mid_slice_*.)
"""
from __future__ import annotations

from app.medini.doctrine.validation import identity_scorer as I


def test_identity_features_does_not_beat_aggregation_and_fails_anchor_gate():
    o = I.run()
    assert o["n"]["heldout"] >= 50 and o["n"]["anchor"] >= 8, o["n"]

    id_best = max(v["loco"] for k, v in o["loco_grid"].items() if k.startswith("identity"))
    a2_best = max(v["loco"] for k, v in o["loco_grid"].items() if k.startswith("a2_token"))
    # identity does NOT beat the lower-dimensional A2 token model (the whole point of the increment)
    assert id_best <= a2_best + 1.0, (id_best, a2_best)

    # every identity ordinal config carries at least as large an overfit gap as its A2 counterpart's best
    a2_min_gap = min(v["gap"] for k, v in o["loco_grid"].items() if k.startswith("a2_token"))
    id_min_gap = min(v["gap"] for k, v in o["loco_grid"].items() if k.startswith("identity"))
    assert id_min_gap >= a2_min_gap - 1e-9, (id_min_gap, a2_min_gap)

    # the full-fit identity model FAILS the live anchor gate (does not reach the engine's within-one)
    ag = o["anchor_gate"]
    assert ag["pass"] is False, ag
    assert ag["n_within1"] <= ag["engine_within1"], ag
