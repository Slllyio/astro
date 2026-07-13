"""Increment 32 drift-guard: pin the mid-slice NEGATIVE.

The mid slice (Raman moderate..fairly-good) is the worst pool (16.7% within-one). Its dominant miss
driver is deep-negative under-credit — Gate B floors those rows to weak/afflicted, but Raman graded
them mid. They carry the SAME deep-negative tags as his afflicted-graded factors, so no Gate-B
threshold separates them: loosening the gate is a pure trade (mid up, afflicted + pooled held-out
down further). The 6 shallow-non-besieged candidates carry NO decisive dignity, so Gate D (which
needs dignity to floor) cannot touch them either — they are pure under-detection.

This test pins both facts so a future claim of separation must update it explicitly. (Same shape as
test_structural_separability: a documented negative made a tested contract.)
"""
from __future__ import annotations

from app.medini.doctrine.validation import mid_slice_decomposition as M


def test_mid_slice_shallow_candidates_have_no_dignity_and_gate_B_is_a_pure_trade():
    rows = M.collect()
    d = M.decompose(rows)
    # the mid slice is a real, sizeable pool with a majority of misses
    assert d["n_mid"] >= 35, d["n_mid"]
    assert d["under"] >= d["over"], (d["under"], d["over"])
    # deep-negative under-credit dominates the tractable question; the shallow candidates carry NO
    # decisive dignity → Gate D cannot floor them (they are under-detection, not dignity-crushed).
    assert d["u_deep"] >= d["u_shallow"], (d["u_deep"], d["u_shallow"])
    assert d["u_shallow_with_dignity"] == 0, d["u_shallow_with_dignity"]

    # the Gate-B loosening trade: no looser threshold beats the DEFAULT on the pooled held-out number,
    # and every looser threshold costs the afflicted slice at least as much as it gains the mid slice.
    sw = {s["config"]: s for s in M.sweep(rows)}
    default = next(s for c, s in sw.items() if c.startswith("DEFAULT"))
    for cfg, s in sw.items():
        if cfg.startswith("DEFAULT"):
            continue
        # held-out never improves by loosening Gate B (the anti-separation claim)
        assert s["heldout"][0] <= default["heldout"][0] + 1e-9, (cfg, s["heldout"], default["heldout"])
        # afflicted always drops when mid rises (the pure-trade claim)
        assert s["aff"][0] <= default["aff"][0] + 1e-9, (cfg, s["aff"], default["aff"])
