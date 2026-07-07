# Held-out timing validation — Raman's stated event daśās (Phase C)

**Does the engine's Vimśottarī period arithmetic place Raman's stated events in the
mahādaśā (MD) and bhukti (AD) he names?** Seeding the timeline from Raman's *printed*
"Balance of X Dasa at birth" line (no ephemeris, degrees, or timezone needed) and placing
each event by age:

**MD exact 4/4 (100%); AD exact 2/4 (50%), but 4/4 within one bhukti (100%).**

Both AD "misses" are age-rounding, not arithmetic error — the event falls right at a
bhukti boundary and Raman's age phrasing is coarse ("about 32", "the 36th year").

## Method
Raman prints, per worked chart, a balance-of-daśā line and states when events fell. The
balance line `(lord₀, years_remaining)` alone fixes the entire MD/AD timeline (Route 2),
so timing is testable from sign-diagram charts with no degree/ephemeris recompute. The
harness (`app/medini/doctrine/validation/timing_validate.py`) seeds the MD sequence from
the printed balance — mirroring the live engine's `_maha_sequence` — and reuses the live
engine's own bhukti builder **`_antardasha_spans`** (with `elapsed_into_md = total(lord₀)
− remaining` on the birth MD, so its windows are birth-clipped exactly as the engine does
it). Locked constants `DASHA_LORDS` + `DAYS_PER_VEDIC_YEAR` are shared with production, so
the test judges the engine's arithmetic, not a re-implementation.

## Results
| chart | event (age) | Raman MD | engine MD | Raman AD | engine AD | note |
|---|---|---|---|---|---|---|
| 72 | mother died, age 3 | Venus | **Venus** ✓ | Venus | **Venus** ✓ | exact |
| 92 | father died, 41st yr | Jupiter | **Jupiter** ✓ | Mercury | **Mercury** ✓ | exact |
| 71 | mother died, ~36th yr | Mars | **Mars** ✓ | Saturn | Jupiter | ±1 bhukti (Sat starts age 36.06) |
| 93 | father died, ~age 32 | Jupiter | **Jupiter** ✓ | Ketu | Venus | ±1 bhukti (Ketu ends age 31.97) |

The two AD boundary cases: ch71's Mars-Saturn bhukti begins at age **36.06** (Raman: "the
36th year"); ch93's Jupiter-Ketu bhukti ends at age **31.97** (Raman: "about 32"). A
sub-year age adjustment inside Raman's own phrasing makes both exact — the engine's bhukti
boundaries agree with Raman to within the precision he states.

## Interpretation
This is a **new validation dimension** orthogonal to the strength verdicts (bhāva/lord/
kāraka) the rest of the held-out project scores. It confirms the engine's daśā period
math — the `_maha_sequence` seeding, the `_antardasha_spans` birth-clipping, and the
365.2425-day Vedic year — reproduces Raman's worked timings exactly at the MD level and to
within his age precision at the AD level. No arithmetic discrepancy was found.

## Caveats & next
- N=4 events (charts with a clean balance line + a dated event + a stated MD/AD). More
  can be back-filled from the mother/father-death examples across Ch VII and Vol 2.
- **Provenance:** ch71/ch72 are Ch VII (Vol I); ch92/ch93 are Vol 2 Ch XIII — the
  strength-tuned `h9` chapter. That does **not** taint this test: the tuned corpus is
  strength-only tokens with no daśā content, and the engine's Vimśottarī period arithmetic
  was never fit to any chart. Timing here is untuned regardless of chart provenance.
- **Not validated here:** the balance-of-daśā *itself* (i.e. the engine computing the
  balance from the Moon). That needs a birth-data recompute in the Raman ayanamsa
  (`raman_saab/dasha.py` is Lahiri + approximate tz; the precise path mirrors
  `golden_registry`'s `SIDM_RAMAN` + IST/LMT handling) — deferred to the Phase D
  degree-based recompute, which also validates the ephemeris/timezone chain end-to-end
  against Raman's exact printed balance.
- Measurement only; no engine change. Guarded by `tests/doctrine/test_timing_validate.py`.
