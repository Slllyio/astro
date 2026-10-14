"""Cross-engine agreement guard — parashara (ch.11 and the richer verdict) on the 293 Raman goldens.

Three jobs: (1) prove the comparison is VALID by re-deriving the Raman engine's own 259/293 through
this harness; (2) guard both parashara measurements against a silent collapse (the earlier
empty-positions bug drove agreement to 21/293); (3) assert the richer verdict was NOT tuned toward
Raman — it agrees with Raman about the same as, or LESS than, bare ch.11 (a tuned version would jump
up). This is a MEASUREMENT, not an accuracy target.
"""
from __future__ import annotations

from tools.parashara.cross_engine_agreement import score


def test_harness_reproduces_the_raman_number(capsys):
    """If the harness is valid, the Raman engine scores its known 259/293 on it."""
    s = score()
    assert s["total"] == 293
    assert s["raman_exact"] == 259 and s["raman_within1"] == 283
    with capsys.disabled():
        n = s["total"]
        print(f"\n[cross-engine] ch.11={s['ch11_exact']}/{n} exact "
              f"(within-1 {s['ch11_within1']}/{n}, inv {s['ch11_inversion']});  "
              f"richer={s['richer_exact']}/{n} exact "
              f"(within-1 {s['richer_within1']}/{n}, inv {s['richer_inversion']})")


def test_neither_verdict_silently_collapses():
    """A floor, not a target — catches a regression like the empty-positions bug (which gave 21)."""
    s = score()
    assert s["ch11_exact"] >= 100 and s["ch11_within1"] >= 170
    assert s["richer_exact"] >= 100 and s["richer_within1"] >= 170


def test_richer_verdict_is_not_chasing_raman():
    """Integrity check: the richer verdict must not be a backdoor to chase Raman agreement.

    The real guarantee is STRUCTURAL — richer_bhava imports nothing Raman-directed and reads no
    goldens (test_engine_isolation.py). This is the behavioural tripwire on top: richer's agreement
    stays deep in "overlap" territory, far below Raman's own 259, and never towers over bare ch.11.
    A version tuned toward Raman would push richer_exact up toward 200+.

    History: the earlier form asserted richer <= ch11 + 3, on the premise that bare ch.11 was a fixed
    no-enrichment floor. The BPHS-11:16(b) antidote fix (2026-08-23, doctrine-pure and Raman-blind)
    improved BOTH engines' fidelity but moved bare ch.11's EXACT Raman-agreement down (123->118,
    inversions 94->93) while richer went 120->124 — a legitimate divergence (Raman doesn't apply
    those antidotes), opening a +6 gap. Improving ch.11 itself invalidated the premise, so the
    tripwire was re-framed to the invariant above. Recorded in DOCTRINE_BACKLOG. USER-signed-off.
    """
    s = score()
    assert s["richer_exact"] < 170                     # far below Raman's 259 — not chasing
    assert s["richer_exact"] <= s["ch11_exact"] + 15   # no towering backdoor over bare ch.11
