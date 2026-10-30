# Amendment 1 to PHASE3_TIMING_PREREG.md: replicated control gates

Committed 2026-10-14 (user decision), BEFORE the real case-vs-control exposure was ever compared.

## What happened
The first run (runner `1f33733e`) stopped at the control stage, as the prereg requires:
- Permutation sham: passed (AD E +0.0005, CI −0.0185..+0.0187; MD −0.0007, CI −0.0113..+0.0093).
- Planted recovery, MD: recovered (+0.0311, CI +0.0223..+0.0401).
- **Planted recovery, AD: FAILED.** Target +0.030, got +0.0071, CI −0.0098..+0.0252.

The real exposure was not computed. The runner exits before reaching it.

## Diagnosis (control exposures only; case exposures discarded unread)
500 repeat planted draws on the same risk sets: AD mean E **+0.0302** (target +0.0300), SD 0.0094,
95% CI coverage 93.8%. MD: +0.0302, coverage 96.0%. A draw as low as +0.0071 has probability 0.010.
The estimator is unbiased and its intervals are calibrated. **The gate was the flaw.** A single
stochastic draw judged by its own 95% CI halts a sound pipeline ~5% of the time by construction.
The permutation sham has the same property (also noted by the pre-run audit, NB1).

## What changes (gates only; instruments, map, risk sets, statistic, SESOI, Holm all unchanged)
Both gates become **replicated calibration checks over 500 draws**, judged with a cluster-robust SE:
- **Sham:** mean E within ±0.005 of 0, and 95%-CI coverage of 0 between 90% and 99%.
- **Planted (+0.030):** mean E within ±0.005 of +0.030, and coverage of +0.030 between 90% and 99%.
Failing either still stops the run before the real comparison. The failed single draw above is
reported in PHASE3_RESULTS.md, not hidden.
The seed is unchanged (20261014), so the risk sets are identical to the first run's.
