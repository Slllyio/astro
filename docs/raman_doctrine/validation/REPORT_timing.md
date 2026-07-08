# Held-out timing validation — Raman's stated event daśās (Phase C)

**Does the engine's Vimśottarī period arithmetic place Raman's stated events in the
mahādaśā (MD) and bhukti (AD) he names?** Seeding the timeline from Raman's *printed*
"Balance of X Dasa at birth" line (no ephemeris, degrees, or timezone needed) and placing
each event by age:

**MD exact 4/4 (100%); AD exact 2/4 (50%), but 4/4 within one bhukti (100%).**

Both AD "misses" are age-rounding, not arithmetic error — the event falls right at a
bhukti boundary and Raman's age phrasing is coarse ("about 32", "the 36th year").

> **Scale-up — 8th house (Ch XII, longevity), 2026-07-08. The N=4 result now holds at
> N=8:** pooling the four Ch VII / Vol II parental-death events with four hand-verified
> **death-of-native** events from the 8th-house longevity chapter gives **MD 8/8 exact
> (100%), AD 4/8 exact (50%), AD 8/8 within one bhukti (100%)**. The MD arithmetic
> reproduces Raman at double the sample with no discrepancy. See "Scale-up (8th house)".

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

## Scale-up (8th house) — Ch XII longevity, held-out
The 8th-house chapter is a longevity/Balarishta set: Raman routinely names the **death
daśā**. Its prose is machine-readable text (only the sign *diagrams* need vision), so the
death events were extracted directly from `htjah_vol2.pdf` and tied to the already-gate-
verified 8th-house charts by their unique birth-line — no re-extraction of positions.

| chart | event (age) | Raman MD | engine MD | Raman AD | engine AD | note |
|---|---|---|---|---|---|---|
| 43 | died at 16 | Mars | **Mars** ✓ | Ketu | Venus | ±1 bhukti |
| 57 | died ~89 (June 1969, "90th year") | Mars | **Mars** ✓ | Rahu | Mars | ±1 bhukti (year-only age) |
| 58 | died ~84 (in 1903) | Mercury | **Mercury** ✓ | Saturn | **Saturn** ✓ | exact |
| 70 | shot, died 2-1-1930 (age 38.22) | Mercury | **Mercury** ✓ | Sun | **Sun** ✓ | exact (full death date) |

**Pooled with the original four: MD 8/8 (100%), AD exact 4/8 (50%), AD within-one 8/8
(100%).** The one full-death-date case (ch70, age 38.22) is exact on both MD and AD — the
AD "misses" track age precision exactly: ch43/ch57 have only a stated/ordinal age, so the
bhukti (which turns over in months) can't be pinned, while the year-derived ch58 still
lands the AD. The MD (which spans years) is robust to all of this — hence 8/8.

### Yield & integrity (honest limits)
- The 8th house names a **death Dasa/Bhukti for 19 of its 42 charts**, but only **4 state a
  death age cleanly enough to place** (the binding constraint is Raman's age phrasing, not
  chart supply — the same finding as the strength side). The other **15 death-daśās are
  retained** (`retained_death_dasas` in the corpus, MD/AD auto-extracted, age unavailable)
  for reuse, not scored.
- Two extraction bugs were **caught by hand-verification before scoring**, not after: (1)
  ch72 (Marie Antoinette) — the scraper read "French revolution of 1791" as a death year
  (age 36); she was guillotined in 1793 and Raman prints no clean death age, so the chart is
  **dropped**, not guessed; (2) ch58 — the balance line "7 years and 3 months" (no "days")
  had its months silently dropped by the parser, a quarter-year shift that wrongly tipped one
  MD boundary Mercury→Ketu; fixed, and ch58 is now MD+AD exact. Every one of the 4 scoreable
  events was cross-checked against Raman's prose (birth line, balance, death age, MD, AD).

## Interpretation
This is a **new validation dimension** orthogonal to the strength verdicts (bhāva/lord/
kāraka) the rest of the held-out project scores. It confirms the engine's daśā period
math — the `_maha_sequence` seeding, the `_antardasha_spans` birth-clipping, and the
365.2425-day Vedic year — reproduces Raman's worked timings exactly at the MD level and to
within his age precision at the AD level. No arithmetic discrepancy was found.

## Caveats & next
- N=8 events (charts with a clean balance line + a placeable-age event + a stated MD/AD):
  4 parental-death (Ch VII / Vol II) + 4 death-of-native (8th house). Further back-fill is
  gated by *stated death age*, not chart supply (15 more 8th-house death-daśās are captured
  but age-less, plus the 9th/10th/12th houses print fewer dated events).
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
