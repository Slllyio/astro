# Pre-registration: Phase 4.2, rule-level effects and dose-response (Raman engine)

Committed 2026-10-14, BEFORE the pooling or dose-response below has been computed. Plan: Phase 4.2.

## Why
House-verdict AUC cannot see a rare conditional rule (a rule firing in 4% of charts with RR 2 gives
AUC ≈ 0.52). Raman's claims are conditional: "if X, then outcome Y". The published Stage-6
rule-enrichment run (`raman/rule_enrichment.parquet`, 91 rule × outcome tests, 0 passing BH q=0.10)
tested each rule alone. This phase asks the two family-level questions that per-rule BH cannot answer.
Note: Phase 1 wrongly said these per-rule results were not persisted. They are, and they are used here.

## Q1: pooled rule effect and heterogeneity
- Unit: one rule × outcome row (the 91 published rows, read as published).
- Effect: log RR = log(rate / base), with SE from the binomial delta method, sqrt((1 − rate) / k_case)
  (k_case = 0 gets a +0.5 continuity correction).
- DerSimonian–Laird pool across all 91 (`tools/validation/stats.random_effects`): pooled log RR,
  τ², I². TOST at SESOI **log 1.20** (`SESOI_PREREG.md`).
- Sign test: the share of rules with RR > 1 in the direction Raman predicted (null 0.5).
- What it means: BOUNDED_NULL with τ² ≈ 0 says rules do not work on average and no subfamily stands
  out. A large τ² with a null mean says some rules may work in either direction. Those rules then
  become per-rule hypotheses for holdout data, never findings.

## Q2: dose-response (the doctrine's "more testimonies, stronger result")
- For each outcome in the Stage-6 `OUTCOMES` table (same case / contrast universes, tiers A+B, store
  population): exposure = **number of registered-polarity rules fired** for that outcome's
  signification. Outcome = case (1) vs contrast (0).
- Statistic: logistic slope of case status on the rule count, adjusted for birth decade; pooled
  across outcomes by DL. TOST on the pooled slope at log(1.20) per extra rule.
- Raman's preponderance principle predicts a positive slope.

## Verdicts
Per `tools/validation/result.py` (sham: none available at this level; marked as such). Both are
analyses of the same discovery data the Stage-6 run used. A positive result is a hypothesis for
holdout confirmation, not a finding.
