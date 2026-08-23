"""Cross-engine agreement guard — the parashara engine on the same 293 Raman goldens.

Two jobs: (1) prove the comparison is VALID by re-deriving the Raman engine's own 259/293 through this
tool's harness, and (2) guard the parashara measurement against a silent collapse (the earlier
empty-stated-positions bug drove agreement to 21/293). It prints the headline the way the ratchets do.

This is a MEASUREMENT, not an accuracy target: parashara's agreement with Raman is overlap +
attributed divergence, never "BPHS accuracy" — where BPHS revises Raman, divergence is correct.
"""
from __future__ import annotations

from tools.parashara.cross_engine_agreement import score


def test_harness_reproduces_the_raman_number(capsys):
    """If the tool's harness is valid, the Raman engine scores its known 259/293 on it."""
    s = score()
    assert s["total"] == 293
    assert s["raman_exact"] == 259 and s["raman_within1"] == 283
    with capsys.disabled():
        n = s["total"]
        print(f"\n[cross-engine] parashara vs Raman's published verdicts: "
              f"exact={s['para_exact']}/{n} within-1={s['para_within1']}/{n} "
              f"(inversions={s['inversion']}, boundary={s['boundary']}, off-axis={s['off_axis']})")


def test_parashara_agreement_does_not_silently_collapse():
    """A floor, not a target — catches a regression like the empty-positions bug (which gave 21).
    The number moving UP or DOWN within band is fine; a collapse means the tool broke."""
    s = score()
    assert s["para_exact"] >= 100          # currently 123
    assert s["para_within1"] >= 170        # currently 198


def test_divergences_are_categorised():
    s = score()
    # every divergence is one of the three attributed kinds; they sum to the total mismatches.
    assert s["off_axis"] + s["boundary"] + s["inversion"] == len(s["divergences"])
    assert s["para_exact"] + len(s["divergences"]) == s["total"]
