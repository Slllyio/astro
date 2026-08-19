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

---

## Step F — held-out read-out (scored ONCE, post-freeze; sha check passed)

| gate | value | threshold | outcome |
|---|---|---|---|
| HG1 median death-window percentile | **0.123** | ≤ 0.35 proceed / ≥ 0.45 abort | **PASS — proceed** |
| HG2 fraction below 50th percentile | 0.625 (15/24) | ≥ 0.65 | miss (marginal) |
| HG3 killer hit-rate (soft) | 0.62 | ≥ 0.70 | miss (reported) |

Full per-case table: `data/ml_runs/raman_saab/run5/heldout_readout.json`.

**Reading:** the tuned encoder generalizes within the book far better than
run 4 (held-out median 0.123 vs run-4's calibrated-set 0.21): 16/24 unseen
cases score below the 20th percentile, including sub-5% hits on Sankara,
Sayaji Rao, Narasimha Bharathi, Ashutosh, Jesus, Aurangzeb. The failures are
bimodal and BAND-DRIVEN: the placement-class classifier mis-assigns ALPAYU
to several long-lived natives (Gandhi 78, Einstein 76, Victoria 82,
Havelock Ellis 79, Rajendra Prasad 78 — the latter stated PURNAYU by Raman)
and the band gate then crushes their true late windows (percentiles
0.92–0.98). On the 5 held-out cases with explicit ayurdaya statements the
classifier is wrong 5/5 — an anti-pattern, reported as the strongest
interpretive caveat for P3. Weights are frozen; per the pre-registration the
population run PROCEEDS on HG1, carrying HG2/HG3 misses as prior.
