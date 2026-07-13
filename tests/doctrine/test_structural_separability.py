"""Increment 30 drift-guard: pin the structural-feature NEGATIVE.

The candidate features (yoga-participation, dispositor-strength, benefic-cluster) were proposed to
close the strong-side under-credit Gate F (incr. 29) could not. The separability diagnostic showed
they ANTI-separate — each signal is at least as common on Raman's afflicted-graded factors as on his
strong-graded ones, so a gate on them cannot help. This test pins that finding so a future claim of
separation must update it explicitly.
"""
from __future__ import annotations

from app.medini.doctrine.validation import structural_separability as SS


def test_structural_tokens_do_not_separate_strong_from_afflicted():
    s = SS.summarize(SS.collect())
    strong, aff = s["strong"], s["afflicted"]
    assert strong["n"] >= 25 and aff["n"] >= 50, (strong["n"], aff["n"])

    def frac(d, key):
        return d[key] / d["n"] if d["n"] else 0.0

    # dispositor-strength barely fires on the strong slice (the strong factors' dispositors are mostly
    # not themselves strong). Increment 31's Gate D lifts a couple of dispositor grades through
    # grade_factor, so this is a small count, not exactly 0 — the anti-separation below is the real
    # claim (disp_ge5 stays MORE common on the afflicted slice regardless).
    assert strong["disp_ge5"] <= 3, strong["disp_ge5"]
    # every signal is at least as common on the afflicted slice as on the strong slice (a gate on
    # any of them would lift afflicted rows at least as much → cannot close the strong gap).
    for key in ("yoga_pos", "disp_ge5", "cluster", "any"):
        assert frac(aff, key) >= frac(strong, key) - 1e-9, (key, frac(strong, key), frac(aff, key))
