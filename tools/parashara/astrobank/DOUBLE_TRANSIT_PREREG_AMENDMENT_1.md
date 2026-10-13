# Amendment 1 to DOUBLE_TRANSIT_PREREG.md — sample extension + held-out confirmation

Committed BEFORE any extension or tier-C number was computed (2026-10-13), after the primary run
(RESULTS.md: null, underpowered — marriage +3.8%, CI −2.2..+10.1, n=199).

## What changes: ONLY the sample. The rule, instruments, controls and pass bar are IDENTICAL.
No instrument, house, aspect set, span cap (age 15 .. min(death−1yr, 75)), blackout, K, M, seed
or threshold is altered. Deaths after age ~76 remain excluded by the original span cap — changing
that after seeing results would be post-hoc redesign.

## Two new, separately reported analyses
1. **Extension (tier A+B, outside the original store):** every person with a day-precision
   marriage/divorce/own-death event in tiers A/B who was not in `store_population` (the original
   store was a labelled cohort + an 8k random control sample, not everyone). Available before
   filters: +125 marriages, +16 divorces, +439 deaths. Reported alone AND pooled with the primary
   A+B run (pooled = the main updated estimate).
2. **Confirmation (tier C, held out since the start):** tier-C people (any non-noon birth time —
   less precise than A/B) with such events, in or out of the store: 178 marriages, 20 divorces,
   1,027 deaths before filters. Run ONCE, reported alone. Tier C birth-time imprecision can shift
   house cusps and dasha dates; a tier-C null therefore weighs less than an A+B null, and that
   caveat is stated with the result.

## Pass bar (unchanged)
Lift CI AND cross-chart excess CI exclude 0 in the predicted (positive) direction. The pooled A+B
estimate is the headline; tier C confirms or does not. Divorce remains under-powered whatever the
outcome (≈ 50 A+B events) and is reported as such.

## What happens after
Whatever the result, this design is closed. Any further change is a new pre-registration on new data.
