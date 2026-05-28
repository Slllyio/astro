# Permutation test: structural vs cyclical for `personal` doctrine RR

## Setup

- Real pooled RR (from Round-11 pooled analysis): **2.308** (95% CI 1.73-3.08), p=7.37e-09
- Real per-corpus RRs: ADB=2.44, WD=NA, LA=0.95
- Permutations: 20
- Procedure: shuffle every natal chart's feature columns across persons within corpus; keep events, dasha windows, ages intact; recompute s6 score; recompute Mantel-Haenszel pooled RR.

## Null distribution (shuffled charts)

| Statistic | Value |
|---|---|
| mean (geometric) | 2.250 |
| log-RR std | 0.095 |
| min | 1.997 |
| 25th percentile | 2.126 |
| median | 2.220 |
| 75th percentile | 2.322 |
| max | 3.010 |

## Verdict

- z-score of real RR vs null:  **0.27**
- parametric p-value:          **0.395**
- empirical p-value:           **0.381** (7/20 shuffled reps exceeded real)

> ⚠️ **LIFECYCLE ARTIFACT**: the shuffled null distribution includes RR values close to the real RR. The s6 personal finding can be reproduced even with scrambled charts, indicating the signal comes from age/dasha-lord-identity cycling, not chart structure.
