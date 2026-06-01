# Round-11 follow-up — Pooled doctrine RR (Mantel-Haenszel)

Cross-corpus deduplicated: dropped 591 duplicate persons (ADB > WD > LA precedence).

Bonferroni α = 0.01/12 = 0.0008333

## Per-class table

| Class | Scorer | k | ADB RR | WD RR | LA RR | Pooled RR (95% CI) | p | Q_p |
|---|---|---|---|---|---|---|---|---|
| `personal` | s6 | 2 | 2.44 | — | 0.95 | **2.31** (1.73–3.08) | **7.37e-09** | 0.129 |
| `family` | s5 | 2 | 0.90 | — | 1.25 | 1.17 (0.98–1.40) | 0.0412 | 0.161 |
| `education` | s5 | 1 | 1.15 | — | — | 1.15 (0.79–1.69) | 0.23 | 1 |
| `finance` | s5 | 1 | 1.11 | — | — | 1.11 (0.86–1.44) | 0.211 | 1 |
| `career` | s5 | 3 | 0.93 | 1.25 | 0.76 | **1.11** (1.04–1.17) | **0.000569** | ⚠️3.53e-08⚠️ |
| `fame` | s6 | 3 | 1.43 | 1.04 | 0.97 | 1.09 (1.03–1.15) | 0.00117 | ⚠️5.72e-05⚠️ |
| `health` | s5 | 2 | 1.14 | — | 0.92 | 1.02 (0.87–1.20) | 0.388 | 0.192 |
| `legal` | s5 | 2 | 1.13 | — | 0.84 | 0.99 (0.81–1.20) | 0.446 | 0.135 |
| `marriage` | s5 | 3 | 1.06 | 1.00 | 0.72 | 0.96 (0.91–1.02) | 0.0924 | ⚠️0.000257⚠️ |
| `death_by_disease` | s5 | 2 | 0.93 | — | 1.01 | 0.96 (0.77–1.20) | 0.369 | 0.717 |
| `relationships` | s8_3 | 3 | 2.28 | 0.85 | 0.48 | **0.86** (0.80–0.92) | **1.27e-05** | ⚠️1.44e-15⚠️ |
| `work` | s5 | 2 | 0.73 | — | 0.88 | 0.82 (0.69–0.96) | 0.00827 | 0.287 |
| `death_cause_unspecified` | s5 | 2 | 1.02 | 0.77 | — | **0.81** (0.76–0.86) | **8.5e-11** | ⚠️0.00129⚠️ |
| `relationship` | s5 | 2 | 0.32 | — | 0.53 | **0.42** (0.35–0.50) | **1.29e-23** | ⚠️0.00424⚠️ |
| `death` | s5 | 0 | — | — | — | — (—–—) | 1 | 1 |

**Aggregate**: 8/12 pooled p<0.05, 5/12 Bonferroni

⚠️ in Q_p column = significant cross-corpus heterogeneity (corpora disagree)
** = pooled estimate clears Bonferroni
