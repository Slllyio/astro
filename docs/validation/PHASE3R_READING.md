# Phase 3R: how to read PHASE3R_RESULTS.md (hand-written; the table itself is generated)

Run 2026-10-14 under `PHASE3R_RAMAN_TIMING_PREREG.md` (025b4744). **Raman engine, unchanged**:
`timer_set` (lord, **karaka**, occupants, aspecters, lord's associates/aspecters, lord-from-Moon,
**node via its dispositor**) + `_EVENT_AUX_HOUSES` (2↔11, 9↔12) + `lords_associated` + `bhukti_tier`,
the engine's own Vimshottari, Raman ayanamsa, `maraka_set().primary` for death. The store is tested to
reproduce the engine's own `active_houses` par-excellence set. 47,016 A+B charts; the same 13,034
risk sets as Phase 3. All four control gates pass.

## The headline
**Raman's house-activation technique, run through his own engine, does not time real events.**

| test | E | 95% CI | registered verdict | what it actually means |
|---|---|---|---|---|
| P1: AD level (both lords activate, tier ≥ 3) | +0.003 | −0.016..+0.023 | BOUNDED_NULL | null; an effect ≥ 3 points is excluded |
| P2: MD level (the MD lord activates) | **−0.018** | −0.030..−0.007 | "SIGNAL" | **the OPPOSITE of the prediction**, and explained below as a chart-level artefact |

**The P2 "SIGNAL" label is two-sided.** `result.py` calls any CI that excludes 0 a SIGNAL. The
hypothesis is one-sided (events MORE often in activating periods), so a negative effect is evidence
against it, never for it. The prereg's condition for spending holdout C1 (SIGNAL **and** placebo
below real **and** S2 positive) is not met on any count: placebo −0.011, S2 −0.015.
**C1 stays unread.**

## Why P2 is negative: a chart-level selection effect, not timing (exploratory diagnostic)
`tools/validation/phase3r_diag.py`, on the same risk sets:

| | lifetime activation coverage, cases − controls (event date ignored) | within-person E (event date vs the person's own lifetime) |
|---|---|---|
| MD, real dasha | **−0.010** (−0.016..−0.004) | −0.006 (−0.014..+0.003): null |
| MD, placebo dasha | **−0.009** (−0.015..−0.003) | −0.007 (−0.016..+0.002): null |
| AD, real | +0.004 (−0.007..+0.014) | −0.003 (−0.019..+0.013): null |
| AD, placebo | +0.003 (−0.009..+0.013) | −0.005 (−0.020..+0.012): null |

People who have recorded events have charts whose relevant houses are MD-activated about 1 point less
often **over their whole lives** than the control pool. It is the same with a scrambled dasha, so it is
a property of the chart, not the date. The risk-set excess inherits it. Compared with their own
lifetime, the event date is **no more activated than any other date**, at either level.

Likely cause: the risk sets match on birth decade and tier but not on birthplace latitude. Latitude
shifts the lagna distribution, and through it Raman's timer sets. This is a real gap in the risk-set
design (the Phase 0 chartless-baseline standard included latitude and was deferred). It does not rescue
the hypothesis: the within-person comparison, which is immune to it, is null. **Lesson recorded:** a
future risk-set design must also match on latitude band, or report within-person E alongside.

## Everything else
- Placebo indistinguishable from the real dasha (AD −0.003, MD −0.011).
- S1 dose-response over Raman's own tiers: log-odds +0.008 per tier (p 0.61). Par excellence is not
  more often running at events than feeble.
- S2 specificity: AD +0.003, MD −0.015.
- S3 dasha + double transit: +0.004 (−0.009..+0.018).
- **Lahiri frame** (same Raman instrument): AD −0.008, MD −0.017. Same picture in both frames.
- Precision gradient: AA +0.019 (−0.004..+0.041), A −0.055. The same split pattern as Phase 3, one of
  ~13 descriptive arms. Not a finding.

## Phase 3 (Parashara inputs) vs Phase 3R (Raman engine), side by side

| | Phase 3 | Phase 3R |
|---|---|---|
| AD-level E | −0.010 (−0.030..+0.009) | +0.003 (−0.016..+0.023) |
| MD-level E | −0.003 (−0.015..+0.008) | −0.018 (chart-level selection; within-person −0.006, null) |
| activation coverage per house (AD tier ≥ 3 / MD) | 0.27 / 0.49 | 0.34 / 0.57 (broader: karaka + node-dispositor) |
| dose-response over tiers | −0.018 / tier | +0.008 / tier |
| verdict | bounded null | bounded null at AD; MD negative-by-selection, within-person null |

Raman's fuller significator set makes activation **broader** (34% / 57% of life), which is exactly the
engine docstring's warning ("broad-recall / low-precision by design: a slow lord times most houses").
Broader activation can only make the windows less able to single out a date.
