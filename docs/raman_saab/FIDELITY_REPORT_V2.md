# Run-5 Fidelity Report v2 — calibration phase (pre-freeze)

Registry: 57 NH cases, 48 validated by the objective OCR filter (printed-Moon
MD anchor + label-blind date repair; see `nh_golden_validation.json`).
Seeded split (20260704): 24 calibration / 24 held-out.

## Calibration half (weights tuned HERE ONLY — scripted coordinate descent,
## pinned coarse grid, doctrine ordering constraints enforced)

| metric | defaults | calibrated |
|---|---|---|
| median death-window percentile | 0.184 | **0.090** |
| mean percentile | — | 0.237 |
| fraction below 50th pct | — | 0.79 |
| killer hit-rate (named ∈ top-4) | 0.64 | 0.57 |

Search log + per-case table: `data/ml_runs/raman_saab/run5/calibration.json`.
Weights frozen to `data/raman_saab/run5_weights.json`.

## Pre-registered transit inclusion rule — OUTCOME: EXCLUDED

Adding the Raman-frame transit terms (sadesathi-3rd-cycle, HPA p.127
composite point) changed the calibration median by **−0.006** (worse), below
the ≥ +0.05 required gain. `tr2.*` weights are zeroed in the frozen set;
transits will be reported as a non-gating secondary only.

## Held-out half

**NOT SCORED.** It is evaluated exactly once, after RUN5_PREREG.md freezes
the weight/registry/method shas (step F). Gate: HG1 median ≤ 0.35 proceed;
≥ 0.45 ABORT (population unspent); HG2 ≥ 65% below the 50th percentile;
HG3 (soft) killer hit-rate ≥ 0.70.

Caveat carried forward: the calibration median is optimistic by
construction (it is the tuned quantity); the held-out number is the honest
fidelity estimate. Band-statement hit-rate on the 2 calibration cases with
explicit ayurdaya statements is 0/2 — the band classifier's population
informativeness is P3's question, flagged, not hidden.
