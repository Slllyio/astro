# Test (c): Combined karaka-stripped + stratified RR — `personal`

Scorer: structural (HR + func_mod, NO karaka baseline)
Stratification: per-(corpus, dasha_lord) cell, within-lord quintile binning

## Per-stratum RRs (karaka-stripped, within-lord)

| Stratum | n_top | n_bot | RR |
|---|---|---|---|
| ADB::Mercury | 11 | 3 | 3.65 |
| ADB::Moon | 12 | 4 | 3.05 |
| ADB::Mars | 7 | 4 | 1.77 |
| ADB::Sun | 10 | 6 | 1.69 |
| ADB::Venus | 14 | 9 | 1.57 |
| ADB::Jupiter | 19 | 13 | 1.47 |
| ADB::Saturn | 14 | 11 | 1.29 |

## Overall combined pool

| Quantity | Value |
|---|---|
| n strata | 7 |
| Pooled RR | **1.721** |
| 95% CI | 1.21-2.45 |
| p-value | **0.00125** |
| Cochran Q_p | 0.801 |

## Permutation falsifier (shuffle charts within strata)

| Quantity | Value |
|---|---|
| K permutations | 100 |
| Null mean | 1.576 |
| Null median | 1.553 |
| Null min | 1.064 |
| Null max | 2.343 |
| Real RR | 1.721 |
| z-score | **0.55** |
| Empirical p-value | **0.307** |
| Shuffled ≥ real | 30/100 |

## Verdict

> 🚫 **NO CHART STRUCTURAL SIGNAL** — Even with both controls applied, the shuffled null tracks the real RR. The entire RR ~1.5 is residual lifecycle leakage that neither karaka-stripping nor stratification can remove.
