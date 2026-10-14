# Validation program: final summary (2026-10-14)

Branch `validation` (local only; worktree `E:\tmp\astro-validation`). Every test was pre-registered
and committed before its numbers existed, with sham/planted controls run first. Engines were frozen
throughout. All four holdouts are unread.

## The answer
**Neither engine predicts real lives, and this is now bounded, not merely "not significant".**
Every core question ends BOUNDED_NULL, and each has its machinery shown able to see an effect of
that size:

| core question | test | result | machinery check |
|---|---|---|---|
| 1. Do house verdicts match life outcomes? | Phase 1 pool (both engines); 4.2 rule-level pool + dose-response | AUC 0.49–0.51; rule RR 1.007 (0.996–1.019), τ² = 0; OR 0.984 per extra rule | sham gates pass |
| 2. Do dashas time events? | Phase 3 risk sets, 13,034 events, Raman's four tiers | AD −0.010 (−0.030..+0.009); MD −0.003 (−0.015..+0.008) | planted +0.030 recovered (+0.0305) |
| 3. Does a life identify its chart? | Phase 4.3, true chart vs 4 decoys within ±3 days | hit rate 0.1999 vs 0.20 | planted 0.312 |
| (pipeline sees real effects?) | Phase 4.1 Gauquelin Mars on his own file | +4.7 pts (CI +2.0..+7.2), PASS | n/a |

## What was learned along the way
- **Instrument reliability** (Phase 2): ±30 min of birth-time error leaves AD timing κ ≈ 0.64.
  Lahiri vs Raman ayanamsa flips about half of AD calls, worse than a 30-minute error.
- **The two engines barely agree**: Raman vs Parashara house verdicts κ = 0.00–0.05 on 22k charts,
  and still near zero when the ayanamsa is matched. "Vedic astrology" is not one testable object;
  each test bounds one implementation.
- **Why it fails** (measured, two mirror images):
  - static: the median chart carries 19 afflicted + 31 favourable significations at once;
  - timing: one dasha lord influences 5.8 of 12 houses, 85% of AD periods activate some house at
    "ordinary or better", and a house is activated for 27–45% of a life.
  Indications abundant enough to fit any life, at any date, cannot discriminate one.
- **"Did the test fail?" Checked, and no** (Phase 3 deep look): no filler-date heaping; four
  narrower activation instruments (including "the dasha of the house's own lord") are all null; the
  tier mix at events matches matched controls within 0.7 points; the placebo dasha equals the real one.
- Leans worth noting, all non-findings: the marriage double-transit lean (+3.4% on 314) vanished
  when pooled (+0.3%); the suicide thread never replicated; Raman's rules lean the wrong way more
  often than the right way (35% predicted-direction, p = 0.006).

## Process notes (honest record)
- Pre-run audits caught real bugs **before** any result: 4.6k unmapped deaths, duplicate events, a
  missing stop rule, an off-prereg health mapping, the "+120° sham" that would have reproduced the
  real dasha, and the missing Raman factor (f).
- Two amendments, both committed before the affected comparison: Phase 3 gates moved from a single
  draw to 500-draw calibration (a 1%-chance gate failure; user decision), and the double-transit
  tier-C confirmation was withdrawn in favour of the C1/C2 split (user decision).
- Deviations recorded in the results files: the Phase 4.2 estimator (separation), 11 Gauquelin rows
  with a missing tz, and one wrong statement in Phase 1 (per-rule results were in fact persisted).

## Addendum (2026-10-14): Phase 3R, Raman's own engine (user request)
The one open path, "Raman's own judge driving the timing", was pre-registered and run: the Raman
engine's `timer_set` + `bhukti_tier` + `lords_associated`, its own dashas, Raman ayanamsa and
`maraka_set`. **AD level: bounded null (+0.003). MD level: negative (−0.018)**, the opposite of the
prediction, traced by diagnostic to a chart-level selection effect (cases' charts are activated ~1 point
less over their whole lives; identical under a scrambled dasha). Within-person: null at both levels.
C1 stays unread. Full reading: `PHASE3R_READING.md`.
**Phase 3P (pratyantar level, Raman engine; user request):** the PD lord activating the event's house
+0.009 (−0.010..+0.029) and MD+AD+PD convergence −0.005 (−0.022..+0.012), both BOUNDED_NULL, with the
within-person effect null too. The placebo is indistinguishable. See `PHASE3P_READING.md`.

## Stopping rule: triggered, and honoured
No new outcome questions are opened. Not run, by design: 4.4 vocation, 4.5 lifespan, 4.6 H5 codings,
4.7 time twins, Phase 5 composite/ML. Holdouts C1 (11,542), C2 (11,404), Gauquelin (25%) and
Wikidata stay unread, kept for any future instrument that is genuinely new: a different dasha system
(Yogini, Ashtottari, Jaimini), or Raman's own judge driving the timing. Each would need its own
pre-registration and would get one read.

## What the engines are
Faithful scholarly instruments: "what would Raman / Parashara say", measured against their own books
(the fidelity axis). They are not validated predictors of lives, and must not be presented as one.
The two axes are reported side by side, never averaged.

## Files
`docs/validation/`: SESOI_PREREG, BOUNDS + PHASE1_READING, RELIABILITY + PHASE2_READING,
PHASE3_TIMING_PREREG + AMENDMENT_1 + RESULTS + DEEP + READING, PHASE4_{1,2,3}_*_PREREG + RESULTS,
PHASE4_READING. Code: `tools/validation/`. Result records: `E:/astro/data/validation/results.jsonl`.
