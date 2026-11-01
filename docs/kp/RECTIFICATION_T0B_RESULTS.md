# Rectification recovery: synthetic

Pre-registration: `docs/kp/RECTIFICATION_PREREG_2026-10-31.md`.

People scored: 200 (failed casts: 0). Mean events used to rectify: 3.99.

Percentile rank of the true minute among the 91 candidates (0 best, 1 worst, chance 0.5):

| track | n | mean | 95% CI | label |
|---|---|---|---|---|
| kp | 200 | 0.2454 | 0.22 to 0.2716 | **SIGNAL** |
| kp_placebo | 200 | 0.4985 | 0.4599 to 0.5346 | **BOUNDED_NULL** |

KP: true minute inside the top-scoring set 0.315 of the time; chance for sets that size 0.113.
KP: mean distance of the rectified centre from the truth 14.56 min, against 15.71 min for the shifted stated time; rectified closer in 0.55 of people.
Placebo gate ok: True.
T0 machinery check (kp mean ≤ 0.3): **PASS**.
