"""Phase 3 — the tournament machinery, and the honesty spine that makes it mean something.

The machinery is deliberately buildable and testable before any corpus exists:
it is validated on synthetic data, where the ground truth is known and the
pipeline must both **recover a planted signal** and **return null on noise**.

Modules:
  prereg     one CSV row per test; only ``locked`` rows score; the file is hashed
  holdout    deterministic person-level 25% freeze, touched exactly once
  controls   the mandatory arms: sham, chartless twin, era strata, person leak
  scoring    sham-before-real gate, delta-over-chartless, BH at q=0.10
  synthetic  planted-signal and pure-noise corpora for validating all of the above

The two rules everything else hangs off:

1. **The sham is read first.** A real result cannot be recorded until a permuted
   target has come back at ~0.500. Round 11 read its result first and then spent
   five analyses arguing a headline p=7.4e-9 down to a null; this ordering closes
   that in one step.
2. **A chart model scores as its delta over its own chartless twin.** Birth
   latitude, longitude and date alone reach AUC 0.744 on marriage, so a raw chart
   statistic is not evidence of anything.
"""

from __future__ import annotations

__all__ = ["controls", "holdout", "prereg", "scoring", "synthetic"]
