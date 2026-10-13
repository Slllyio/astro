# Phase 3: how to read PHASE3_RESULTS.md (hand-written; the table itself is generated)

Run 2026-10-14 under `PHASE3_TIMING_PREREG.md` (08058ff6) + `PHASE3_AMENDMENT_1.md` (5eef675f).
Parashara engine (Lahiri), Raman's four-tier activation (doctrine-reviewed), 13,034 risk sets of
1 case + 10 same-tier, same-decade controls scored on their own charts. Discovery tiers A+B.
**Holdout C1 was not read**: it opens only on a discovery SIGNAL, and none occurred.

## The headline
**Dasha activation does not time real events in this corpus. An effect as large as +3 percentage
points is excluded at both dasha levels.**

| test | events | E (case − matched controls) | 95% CI | 90% CI | verdict |
|---|---|---|---|---|---|
| P1: AD level (Raman tier ≥ 3: both lords influence the house) | 2,365 day-dated | −0.010 | −0.030..+0.009 | −0.026..+0.006 | BOUNDED_NULL |
| P2: MD level (the MD lord influences the house) | 10,669 year-dated | −0.003 | −0.015..+0.008 | −0.013..+0.006 | BOUNDED_NULL |

- **Corrected for measurement error** (Phase 2 reliability: ρ_AD 0.64–0.82, ρ_MD 0.75–0.88), the largest
  positive effect still compatible with the data is about **+0.008 to +0.010 at AD level and
  +0.008 at MD level**. A true effect that small would add about 1 event in 100 over chance.
- Conditional-logistic ORs agree: 0.95 (AD) and 0.99 (MD).
- Both point estimates lean **negative**, the opposite of the hypothesis. Neither excludes 0.

## The controls did their job
- Replicated gates (500 draws): sham mean −0.0004 / +0.0001; planted +0.030 recovered as
  +0.0305 / +0.0299, with CI coverage 93–95%. The pipeline can see a +3-point effect when one is there.
- **Placebo dasha** (right chart, dasha seeded one nakshatra ahead): +0.010 (AD) and −0.008 (MD).
  It is indistinguishable from the real dasha. The engine's actual dasha sequence carries no timing
  information that a wrong sequence lacks.

## Secondaries: none positive
- S1 dose-response over Raman's tiers (feeble → par excellence): log-odds slope −0.018 per tier
  (p 0.25, Holm 0.75). Higher activation tiers are **not** more often running at the event.
  Conjunction-only association gives the same answer.
- S2 specificity: the target house is no more active than the other houses (−0.005 AD, −0.003 MD).
- S3 dasha + double transit: +0.003 (CI −0.010..+0.015). This supersedes the earlier
  double-transit amendment's marriage lean (+0.034 on n=314). Pooled across event types, the
  conjunction carries nothing.

## Sensitivity arms (descriptive; 13 arms, so ~0.65 nominal "hits" expected by chance)
- **Raman ayanamsa:** −0.010 (AD) and −0.009 (MD). Same answer in both frames, so the null is not
  an artefact of the ayanamsa choice (Phase 2 showed the two frames disagree on about half of AD calls).
- **Precision gradient:** the prediction fixed in advance was "if real, AA ≈ 1.3× A". Observed: AA
  +0.004 (CI −0.018..+0.027), A **−0.060** (CI −0.099..−0.021). The prediction fails, and A goes the
  wrong way. With 13 descriptive arms this is the kind of single nominal excursion chance produces.
  It is not a finding, and no claim is made on it.
- **By family:** career +0.020, health/legal +0.008, other −0.013, own death −0.010, relationship
  **−0.048** (CI −0.088..−0.005, nominal). That is the wrong direction again and not
  multiplicity-corrected. It is not a finding.

## What this closes (decision framework)
- The user's hypothesis, "dashas select which promises activate", is now tested at the power the
  earlier single-type tests lacked, with Raman's own grading, both ayanamsas, a placebo dasha and
  matched controls. Result: **bounded null**.
- Together with Phase 1 (static house verdicts: pooled bounded null), **two of the three core
  questions are BOUNDED_NULL.** The third, whole-chart same-day blind matching (Phase 4.3), decides
  the stopping rule.
- Holdouts preserved: C1 and C2 both unread, along with Gauquelin and Wikidata.

## Honest limits
- One engine (Parashara synthesis, Lahiri). Phase 2 showed the Raman engine's house verdicts are
  near-independent of Parashara's, so this bounds this implementation of activation timing.
  Raman's own engine timing (Raman ayanamsa) is approximated by the Raman-ayanamsa arm, not run
  through his judge.
- Event dates come from a celebrity database. Recording and selection biases affect cases and
  controls alike, so they cannot create or hide a chart-specific effect, but they limit generalising
  beyond this population.
- Five significations (mother → 4th etc.) are approximations of Raman's fuller rules, noted in the prereg.
