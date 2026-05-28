# AD-level timing test — `marriage` (BPHS Ch.46-47)

**Score**: AD-mutual-relation only (no chart-structural HR).

```
1.0 * (mutual_aspect_md_to_ad > 0) + 1.0 * (mutual_aspect_ad_to_md > 0) + 1.0 * dispositor_md_is_ad + 1.0 * dispositor_ad_is_md + 0.5 * (mutual_house_distance in {1,5,9}) - 0.5 * (mutual_house_distance in {6,8,12})
```

## Test corpus

- AD-window rows: 688,302
- Events of class `marriage`: 619
- Stratification: per (corpus, MD lord); within-MD AD-quintile binning

## Per-stratum RRs (real)

| Stratum (corpus::md_lord) | n_top | n_bot | RR |
|---|---:|---:|---:|
| ADB::Ketu | 5 | 2 | 2.13 |
| ADB::Mercury | 12 | 8 | 1.47 |
| ADB::Jupiter | 30 | 21 | 1.36 |
| ADB::Rahu | 22 | 21 | 1.36 |
| ADB::Mars | 8 | 6 | 1.32 |
| ADB::Saturn | 16 | 13 | 1.17 |
| ADB::Venus | 17 | 15 | 1.02 |
| ADB::Sun | 9 | 10 | 0.95 |
| ADB::Moon | 6 | 13 | 0.48 |

## Pooled (Mantel-Haenszel)

| Quantity | Value |
|---|---|
| n strata | 9 |
| Pooled RR | **1.174** |
| 95% CI | 0.91–1.52 |
| p-value | **0.113** |
| Cochran Q_p | 0.764 |

## Permutation falsifier (K=50)

| Quantity | Value |
|---|---|
| Real RR | 1.174 |
| Null mean | 1.232 |
| Null median | 1.235 |
| Null min | 0.979 |
| Null max | 1.524 |
| z-score | **-0.44** |
| Empirical p-value | **0.627** |
| Shuffled ≥ real | 31/50 |

## Verdict

> 🚫 **NULL** — Mutual-relation score doesn't beat the permutation null. AD-level timing signal not recoverable at population scale with these features.
