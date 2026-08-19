"""Drift-guard for the A2 learned-combine LANDING test — pins the definitive refusal.

The learned model collapses to 0/8 within-one on the house-1 live-representation anchor under EVERY
training regime, including one injecting the strong-heavy NH pool (the documented landing
prerequisite). Adding strong training signal does not cure the OOD collapse — so the learned combine
is NOT landable, and its transferable gain (Gate B) is already live in synthesis_v2. This test pins
that: any future run that credits the anchor above the floor must update it explicitly.
"""
from __future__ import annotations

from app.medini.doctrine.validation import learned_combine_landing as L


def test_learned_combine_cannot_land_on_the_live_anchor():
    r = L.run()
    assert r["n_anchor"] == 8 and r["nh_strong"] >= 10, (r["n_anchor"], r["nh_strong"])
    for regime, res in r["regimes"].items():
        # every regime collapses OOD on the house-1 anchor (well under the live engine's 2/8)
        assert res["ordinal"]["within1"] <= 1, (regime, res["ordinal"]["within1"])
        assert res["tree_d3"]["within1"] <= 1, (regime, res["tree_d3"]["within1"])
    # the decisive one: strong NH training signal does not lift it above the collapse
    assert r["regimes"]["heldout_plus_nh"]["tree_d3"]["within1"] == 0
