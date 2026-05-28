# AD-level timing test — `personal` (BPHS Ch.46-47)

**Score**: AD-mutual-relation only (no chart-structural HR).

```
1.0 * (mutual_aspect_md_to_ad > 0) + 1.0 * (mutual_aspect_ad_to_md > 0) + 1.0 * dispositor_md_is_ad + 1.0 * dispositor_ad_is_md + 0.5 * (mutual_house_distance in {1,5,9}) - 0.5 * (mutual_house_distance in {6,8,12})
```

## Test corpus

- AD-window rows: 688,302
- Events of class `personal`: 681
- Stratification: per (corpus, MD lord); within-MD AD-quintile binning

## Per-stratum RRs (real)

| Stratum (corpus::md_lord) | n_top | n_bot | RR |
|---|---:|---:|---:|
| ADB::Sun | 9 | 6 | 1.58 |
| ADB::Moon | 15 | 10 | 1.57 |
| ADB::Saturn | 23 | 14 | 1.57 |
| ADB::Rahu | 31 | 26 | 1.55 |
| ADB::Mercury | 11 | 7 | 1.54 |
| ADB::Jupiter | 24 | 15 | 1.53 |
| ADB::Mars | 8 | 6 | 1.32 |
| ADB::Venus | 17 | 14 | 1.09 |
| ADB::Ketu | 10 | 8 | 1.07 |

## Pooled (Mantel-Haenszel)

| Quantity | Value |
|---|---|
| n strata | 9 |
| Pooled RR | **1.433** |
| 95% CI | 1.12–1.84 |
| p-value | **0.00238** |
| Cochran Q_p | 0.996 |

## Permutation falsifier (K=50)

| Quantity | Value |
|---|---|
| Real RR | 1.433 |
| Null mean | 1.294 |
| Null median | 1.280 |
| Null min | 1.071 |
| Null max | 1.645 |
| z-score | **1.06** |
| Empirical p-value | **0.216** |
| Shuffled ≥ real | 10/50 |

## Verdict

> 🤔 **PARTIAL/AMBIGUOUS** — z=1.06. Some lift above null but margin requires larger K to resolve.
