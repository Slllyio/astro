# Phase 4.2 results: Raman rule-level effects

Per `docs/validation/PHASE4_2_RULES_PREREG.md` (PHASE4_2_RULES_PREREG@0c3d2f66). SESOI log 1.20 (RR 1.20).

## Q1: pooled effect of the 91 published rule × outcome tests

| k | pooled RR | 95% CI | 90% CI | τ² | I² | p_TOST | RR>1 share (sign p) | verdict |
|---|---|---|---|---|---|---|---|---|
| 91 | 1.007 | 0.996–1.019 | 0.998–1.017 | 0.0000 | 0.00 | 0.0000 | 0.35 (0.006) | **BOUNDED_NULL** |

## Q2: dose-response (number of registered-polarity rules fired → outcome)

| outcome | n | cases | mean rules fired | slope (log-odds per extra rule) | 95% CI |
|---|---|---|---|---|---|
| childless | 1866 | 391 | 1.01 | -0.095 | -0.213..+0.022 |
| prolific | 1866 | 1475 | 1.66 | +0.009 | -0.078..+0.097 |
| prison (fallback) | 8170 | 430 | 0.17 | +0.208 | -0.027..+0.442 |
| divorced | 2236 | 793 | 0.96 | -0.026 | -0.135..+0.083 |
| long_marriage | 2236 | 1529 | 0.56 | -0.013 | -0.136..+0.110 |
| widowed (fallback) | 6951 | 477 | 1.68 | -0.040 | -0.129..+0.048 |
| bankrupt | 504 | 37 | 1.91 | -0.217 | -0.509..+0.075 |
| wealthy | 504 | 467 | 1.77 | -0.072 | -0.321..+0.176 |
| suicide (fallback) | 8094 | 341 | 0.97 | +0.037 | -0.058..+0.132 |

**Pooled slope:** -0.0158 log-odds per extra rule (OR 0.984 per rule; 95% CI 0.942–1.028), τ² 0.0005, p_TOST 0.0000 → **BOUNDED_NULL**

Deviation (implementation, recorded): the first run used decade dummies in an ordinary logit; 5 of 9 fits failed by separation (decades with only cases or only contrasts). Decade adjustment is now done by conditional logistic regression with decade strata, which is the same adjustment without the failure. The 4 slopes visible in the failed run were childless −0.097, widowed −0.040, bankrupt −0.222, suicide +0.037. For the three large control universes (prison, widowed, suicide) the conditional likelihood fails on very large strata; those use an ordinary logit with dummies for informative decades only (marked fallback).
