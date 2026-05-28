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
| K permutations | 20 |
| Null mean | 1.485 |
| Null median | 1.424 |
| Null min | 1.255 |
| Null max | 2.011 |
| Real RR | 1.721 |
| z-score | **1.07** |
| Empirical p-value | **0.19** |
| Shuffled ≥ real | 3/20 |

## Verdict

> 🤔 **PARTIAL** — z=1.07. Some chart signal above noise but margin is small. Larger K needed.
