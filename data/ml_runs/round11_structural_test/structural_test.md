# Test (a): Karaka-stripped scorer — `personal` event class

Scorer: **s6_structural** (HR + func_mod only; no KR)

## Real pooled RR (karaka-stripped)

- Per-corpus: ADB=1.56, WD=NA, LA=0.22
- Pooled: **1.443** (95% CI 1.07-1.95), p=0.00847, Q_p=0.0148

## Shuffled-chart null distribution (K=20)

| Statistic | Value |
|---|---|
| mean | 1.469 |
| min  | 1.297 |
| median | 1.467 |
| max  | 1.869 |

## Verdict

- z-score real vs null: **-0.18**
- empirical p-value:    **0.571**
- n shuffled ≥ real:    11/20

> ⚠️ **PERSISTENT LIFECYCLE LEAKAGE** — even with karaka stripped, the shuffled null tracks the real RR. The lifecycle confound enters via HR or func_mod through some other mechanism (likely func_mod's rulership-dependence on chart-pattern frequencies).
