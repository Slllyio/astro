# Test (b): Stratified-by-dasha-lord pooled RR — `personal`

Scorer: s6 (original — karaka contribution INCLUDED)
Stratification: every (corpus, dasha_lord) cell binned independently by mix_score quintile, then Mantel-Haenszel pooled.

## Per-stratum RRs

| Stratum (corpus::lord) | n_top events | n_bot events | RR |
|---|---|---|---|
| ADB::Mercury | 11 | 3 | 3.65 |
| ADB::Mars | 7 | 4 | 1.77 |
| ADB::Sun | 10 | 6 | 1.69 |
| ADB::Venus | 14 | 9 | 1.57 |
| ADB::Jupiter | 19 | 13 | 1.47 |
| ADB::Saturn | 14 | 11 | 1.29 |
| ADB::Moon | 7 | 6 | 1.26 |

## Per-corpus stratified pool

| Corpus | Pooled RR | 95% CI | p | Cochran Q_p |
|---|---|---|---|---|
| ADB | **1.577** | 1.11-2.24 | **0.00547** | 0.904 |

## Overall stratified pool

| Quantity | Value |
|---|---|
| n strata | 7 |
| Pooled RR | **1.577** |
| 95% CI | 1.11-2.24 |
| p-value | **0.00547** |
| Cochran Q_p | 0.904 |

## Verdict

> 🤔 **MIXED** — Stratified pooled RR = 1.577. Some chart-attributable signal remains but the effect size is much smaller than the original between-lord RR. Most of the RR=2.31 was lifecycle; a small structural component may exist.
