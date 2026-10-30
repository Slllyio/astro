# Phase 1: how to read BOUNDS.md (hand-written; the table itself is generated)

Run 2026-10-13 under `SESOI_PREREG.md` (commit a52ccb63, committed before any bound was computed).

## The headline in one line
**Pooled, every family is bounded. Test by test, almost nothing is.** The average effect is
excluded at practically useful sizes. Individual tests mostly could not tell AUC 0.53 from 0.50.

## Per test: 7 BOUNDED_NULL, 1 SIGNAL, 29 UNDERPOWERED, 4 WITHHELD (of 41 non-sham rows)
- Most single tests have **MDE80 = 0.034–0.045, above the 0.03 SESOI**. They were never able to
  rule out AUC 0.53, so "null" from them was always uninformative. This is the methodology audit's
  point, now quantified test by test.
- Bounded individually (an effect ≥ SESOI is excluded): Parashara H7 marriage, H12 prison,
  H8 accident; both Parashara maraka death-timing rows; Raman H8 ayurdaya; Raman maraka-primary timing.
- **The one SIGNAL is not a finding.** Raman `H8_suicide` (AUC 0.535) is the *exploratory* run.
  It is not corrected for the ~10 tests in its family, and its pre-registered held-out confirmation
  (`S1_suicide_confirmatory`, AUC 0.528, CI includes 0.5) is UNDERPOWERED in the same table. Under
  the decision framework (discovery signal + failed holdout) it is **non-replicating**.
- All three sham gates pass.

## Pools (secondary)
| engine · family | pooled effect | 90% CI | what is excluded |
|---|---|---|---|
| Parashara · static (k=10) | +0.000 | −0.008..+0.009 | mean AUC outside 0.492–0.509 |
| Raman · static (k=11) | +0.004 | −0.007..+0.015 | mean AUC outside 0.493–0.515 |
| Parashara · timing (k=10) | −0.003 | −0.012..+0.006 | mean hit lift outside −1.2..+0.6 pts |
| Raman · rule conditionals (k=5) | log OR +0.044 | −0.038..+0.126 | mean OR outside 0.96–1.13 |

These are **optimistic**. Read them as the best case for the null, not a final bound:
1. Static tests within an engine share contrast groups (pre-declared caveat).
2. The Parashara timing pool double-counts. `maraka_both` and `maraka_either` score the same events
   (and share MD windows), and each double-transit row has a transit-only twin on the same events.
   The effective k is closer to 4–5 than 10, so the true CI is wider. It is still most likely
   inside ±0.03, since the widest single bounded row is ±0.019.
3. τ² ≈ 0 everywhere except Raman static (I² 0.49, driven by the H8 suicide/H5 pair): no house
   stands out from the rest.

## What the pre-registered decision rule says
The stop rule ("every non-withheld static test in an engine is BOUNDED_NULL → stop house-AUC tests")
is **NOT met** on either engine: most tests are UNDERPOWERED, not bounded. Honest conclusion:
- The **average** house-verdict effect is excluded (the pool).
- **Individual houses** are not excluded at AUC 0.53. A single house could still carry a small effect
  that the current n cannot see. More cases per house, or the rule-level form (Phase 4.2), is the
  only way to close them. More house-AUC tests at the same n add nothing.

## Not covered
- Raman 91-rule enrichment: moved to Phase 4.2. **Correction (2026-10-14):** the per-rule results WERE persisted (`raman/rule_enrichment.parquet`, 91 rows); the claim that they were not was wrong. Phase 4.2 pools them.
- Raman `H8_class_match`: a bare rate with no null reference.
- Clerical: the prereg names `transit_results_pooled.json`. It was written to `parashara_ext/`,
  because the extension store was listed first, to keep the primary store untouched. Same file;
  the prereg text is left as committed.
