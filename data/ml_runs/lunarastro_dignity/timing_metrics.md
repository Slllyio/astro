# Timing metrics — the benefic-AD strength effect in practitioner terms

The surviving signal (Finding 15) reported as a **self-controlled incidence-rate ratio** (Layer A, SCCS / conditional-Poisson) and as **within-person discrimination** on a graded 0–4 weight-of-evidence (Layer B: C-index/AUC and top-k). Each native is its own control; permutation K=5000.

## Layer A — incidence-rate ratio (SCCS), vs the old lift

| group | n (informative) | exposed events | **IRR (95% CI)** | old lift |
|---|---:|---:|---|---:|
| **auspicious pooled** | 2217 | 284 | **1.134 (95% CI 0.998–1.288, p=0.054)** | 1.111 |
| marriage | 702 | 88 | 1.109 (95% CI 0.881–1.395, p=0.378) | 1.09 |
| career | 1344 | 167 | 1.105 (95% CI 0.936–1.304, p=0.239) | 1.087 |
| education | 171 | 29 | 1.461 (95% CI 0.967–2.209, p=0.0721) | 1.356 |
| death | 948 | 115 | 1.105 (95% CI 0.905–1.349, p=0.327) | 1.088 |

## Layer B — discrimination (graded 0–4 strength score)

| group | n | **C-index** (null 0.5) | p | hit@1 (exp) | hit@3 (exp) |
|---|---:|---:|---:|---:|---:|
| **auspicious pooled** | 3530 | **0.503** | 0.539 | 0.1884 (0.1808) | 0.2827 (0.2764) |
| marriage | 1147 | 0.5095 | 0.259 | 0.1892 (0.1854) | 0.3165 (0.3054) |
| career | 2107 | 0.4971 | 0.628 | 0.1875 (0.1779) | 0.2572 (0.2541) |
| education | 276 | 0.5212 | 0.229 | 0.192 (0.1846) | 0.337 (0.328) |
| death | 1435 | 0.4929 | 0.341 | 0.1756 (0.1704) | 0.2181 (0.2098) |

## Reading

- **Layer A** restates the effect as a rate ratio with a confidence interval — the estimand epidemiology uses for self-controlled timing (SCCS). A CI that includes 1.0 means the effect is not resolved; the point estimate is the practitioner-legible 'events N× more frequent'.
- **Layer B** asks the astrologer's question directly: does the rule **rank** the true period high? C-index 0.5 = no discrimination; hit@k vs its duration-aware expectation says whether the true period lands in the rule's top-k more than chance.
