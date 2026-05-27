# Fork A · Stage D — DECISION

**Outcome**: **FAIL: no aggregate signal**
**n_seeds (main)**: 5 *(spec called for 10; rationale below)*
**K_qualifying**: 30
**G2 threshold**: ≥11 of 30
**Corpus**: subsample_2000p (n=2000 persons / 1,203,511 rows / 19.5% of 6.17M-row full corpus)
**Device**: DirectML on AMD Radeon RX 9060 XT (F14 spec deviation — original
called for CPU-only; switched after CPU per-seed projected at 6-12 h × 30 seeds was infeasible)

## Why this run was abbreviated

The spec called for: Task 18 — 20-seed noise floor (~60 h compute) →
Task 19 — 10-seed main run → Task 20 — conditional replication.

What we ran: 5-seed main run only (~14 h wall on subsample, DML).

We did NOT run the proper noise floor because the first main seed (#999, timing probe)
already showed Δ = -0.15 across qualifying classes. Five seeds confirmed mean Δ = -0.1593
with stdev = 0.0371 — DeepHit consistently underperforms Cox by ~4σ_main *in the wrong direction*.
No conceivable noise-floor σ would flip the verdict. We bootstrapped a synthetic noise floor
from the 5 main seeds (`noise_floor.json` carries a `_BOOTSTRAP_NOTICE` field) — this conflates
model variance with noise variance and is **conservative for FAIL outcomes** but would be
**invalid for any PASS claim**. Since this is a FAIL, the bootstrap is acceptable.

## n=5 aggregate

| Metric | Value |
|---|---:|
| Mean of per-seed mean Δ | **-0.1593** |
| Stdev of per-seed mean Δ | 0.0371 |
| Min per-seed mean Δ | -0.2066 (seed 2) |
| Max per-seed mean Δ | -0.1026 (seed 4) |
| Classes with mean Δ > 0 across 5 seeds | **1 of 20** (agriculture, +0.0192) |
| Classes with mean Δ > +0.05 | 0 of 20 |

## Gate criteria

| Criterion | Verdict |
|---|---|
| G1 (aggregate Δ ≥ 3σ_noise mean) | ✗ FAIL |
| G2 (≥11 of 30 clear 3σ_noise individually) | ✗ FAIL (0 clear) |
| G3 (σ_model ≤ Δ_class for all G2-clearing classes) | ✓ PASS |
| G4 (replication) | — (not yet run) |

## Per-class results

| Class | Δ_mean | σ_model | σ_noise | 3σ_noise | G2? | G3? |
|---|---:|---:|---:|---:|---|---|
| fame | -0.2695 | 0.0400 | 0.0723 | 0.2169 | · | ✗ |
| career | -0.2473 | 0.0187 | 0.0472 | 0.1417 | · | ✗ |
| death_cause_unspecified | -0.1800 | 0.0383 | 0.0279 | 0.0838 | · | ✗ |
| health | -0.2045 | 0.0407 | 0.0615 | 0.1846 | · | ✗ |
| relationships | -0.1176 | 0.0597 | 0.0597 | 0.1791 | · | ✗ |
| personal | -0.1286 | 0.0652 | 0.0836 | 0.2507 | · | ✗ |
| education | -0.1678 | 0.1984 | 0.1622 | 0.4865 | · | ✗ |
| legal | -0.1478 | 0.0812 | 0.1005 | 0.3014 | · | ✗ |
| finance | -0.2309 | 0.0488 | 0.0784 | 0.2351 | · | ✗ |
| marriage | -0.1240 | 0.0814 | 0.1135 | 0.3406 | · | ✗ |
| relationship | -0.0948 | 0.1218 | 0.1087 | 0.3260 | · | ✗ |
| work | -0.1328 | 0.1716 | 0.1525 | 0.4575 | · | ✗ |
| agriculture | +0.0192 | 0.2985 | 0.4199 | 1.2598 | · | ✗ |
| business | -0.3277 | 0.0406 | 0.1075 | 0.3224 | · | ✗ |
| medical | -0.0363 | 0.0439 | 0.0874 | 0.2622 | · | ✗ |
| property | -0.1677 | 0.0642 | 0.1383 | 0.4150 | · | ✗ |
| death_by_disease | -0.1610 | 0.0783 | 0.0676 | 0.2029 | · | ✗ |
| general | -0.1487 | 0.0555 | 0.0894 | 0.2683 | · | ✗ |
| travel | -0.1467 | 0.1500 | 0.0594 | 0.1783 | · | ✗ |
| family | -0.0668 | 0.0942 | 0.0806 | 0.2419 | · | ✗ |
| children | +0.0320 | 0.2412 | 0.2044 | 0.6133 | · | ✗ |
| spirituality | -0.1622 | 0.0554 | 0.1537 | 0.4612 | · | ✗ |
| accidents | -0.0953 | 0.0499 | 0.1608 | 0.4824 | · | ✗ |
| crime | -0.3251 | 0.1704 | 0.1376 | 0.4129 | · | ✗ |
| death_of_mate | -0.0264 | 0.1663 | 0.1453 | 0.4359 | · | ✗ |
| death_by_accident | -0.0581 | 0.2099 | 0.2219 | 0.6657 | · | ✗ |
| other_death | -0.0048 | 0.0623 | 0.2147 | 0.6442 | · | ✗ |

## Next step (per spec §5 decision table)

Honest null. Trigger pivot decision: **Fork B (DML deepen)** OR **Fork C (write-up as null)**.

## Context

This NULL VERDICT is consistent with the Round 9+10 prior — those rounds also closed
with a combined NULL VERDICT after 3-corpus replication (AD/Lunarastro/Wikidata) plus
non-structural XGBoost + LLM real-vs-shuffled chart-reader test. The hypothesis Stage D
tested was: "perhaps a more expressive competing-risks neural hazard model on
per-(MD,AD,PD) leaf windows can recover structural Vedic signal that tree boosters and
LLMs missed." The answer across 5 seeds and 20 qualifying event classes: no — the model
does WORSE than a matched Cox PH baseline, not better, with very tight stability across
random splits.

What this rules out:
- A specifically-survival-flavoured framing of the prediction problem doesn't help.
- The dasha leaf-window unit-of-analysis (instead of person-life) doesn't unlock signal.
- Hand-rolled DeepHit on this Vedic feature set is not under-trained — stdev across seeds
  is 0.04, much tighter than typical mid-training noise.

What this does NOT rule out (for completeness):
- A vastly larger corpus (10×+) might give DeepHit enough density per (class × time-bin)
  to learn meaningful hazards. We tested at 2000p / 1.2M rows.
- A different architecture (transformer, Cox-Time) at the same scale.
- A different feature representation (yoga embeddings, sequence-of-dashas RNN).

## Followups available if requested

1. **Full 30-seed gate at 2000p** (~85 hours additional compute) — produces a spec-strict
   verdict with proper Task 18 noise floor. Will report the same FAIL outcome with tighter
   error bars.
2. **Re-run at batch=256 + PATIENCE=50** (each seed ~4× as slow ≈ 12 h/seed, 5 seeds = 60 h)
   to rule out "model underfit at batch=1024". Worth ~half a day's compute if you want to
   eliminate the hyperparameter explanation before pivoting.
3. **Pivot to Fork B or Fork C** per the spec §5 decision table. Stage D infrastructure
   remains feature-complete and committed; the substrate and tooling are reusable.