# Pre-registration: does birth-time rectification recover a known birth time?

Committed 2026-10-31, before any recovery number exists. Code: `app/kp/rectify.py`,
`tools/kp/rectify_recovery.py`. Constants in the tool (`SEED`, `MAX_OFFSET`, `WINDOW`, `SESOI`,
`T0_PASS`, `ADB_MAP`, `RAMAN_TYPE`, `MIN_RECT_EVENTS`, `T1_MAX_PEOPLE`) are frozen by this commit.

## Question

If a person's birth time is off by up to 30 minutes, does scoring candidate minutes against their
dated life events put the true minute nearer the top than chance? This decides whether a rectified
time can be fed to the KP engine as *more true* than the stated one.

## Prior

The validation program found Vimshottari MD/AD/PD timing null across 13,034 dated events
(docs/validation/). If the dasa-event link is null, event rectification cannot beat chance on real
people. A null here is an acceptable, expected result.

## Design (same for every test)

- For each person with a known exact time: hidden offset = seeded uniform whole minutes in
  [-30, +30] (`SEED|offset|pid`). Stated time = true + offset. Search stated ± 45 minutes in 1-minute
  steps (91 candidates; the true minute is always inside).
- **Primary metric**: percentile rank of the true minute among the 91 (0 best, 1 worst, ties at
  mid-rank). Chance = 0.5. Mean over people, person bootstrap 95% CI (2,000 resamples).
- **Labels** (SESOI 0.05): SIGNAL if CI upper < 0.5 and mean ≤ 0.45; BOUNDED_NULL if the CI lies
  inside [0.45, 0.55]; WORSE_THAN_CHANCE if CI lower > 0.5; otherwise UNDERPOWERED.
- **Tracks**, same people and windows: `kp` (app.kp.rectify, rulings RR1-RR5), `raman` (existing
  Raman rectifier event channels, Raman ayanamsa), `moon_arith` (HPA ch.12 arithmetic channel),
  `kp_placebo` (kp with each event moved a seeded 2-6 years).
- **Gates**: `kp_placebo` must not be SIGNAL, otherwise the run is void (the scorer would be finding
  structure that is not in the events).
- **Secondary** (reported, not labelled): KP hit rate (true minute in the top set) against its chance
  rate (mean top-set share of the window); mean |rectified centre − truth| against mean |stated −
  truth| (≈15 min by construction); share of people where the rectified centre is closer.

## T0: machinery check (synthetic, cloud)

200 synthetic births (1950-1995, ten Indian cities, tz +5.5, true time 02:00-21:59). For 4 randomly
chosen event types, one day-dated event is planted inside a dasa-bhukti-antara (ages 18-60) whose
three lords all signify the type's houses *at the true time*. People with fewer than 3 plantable
events are redrawn. All events are used (no split). This tests the search code only.
**Pass: kp mean percentile rank ≤ 0.30.** If T0 fails, T1 is not interpreted.

## T1: real recovery (Astro-Databank, PC)

- Population: `derived/raman/person_master.parquet`, `quality_tier` A or B and `rodden_rating` AA or
  A. **Tier C (and so the sealed C1 holdout) is never read.** Birth time at least 75 minutes from
  midnight (window stays inside the day).
- Events: `person_events.parquet`, day precision only, at least 5 years after birth, mapped by
  `ADB_MAP` (first match wins; deaths and divorces excluded; anything unmapped dropped). The mapped
  category table is printed in the results.
- **Event split** (the standing rule): each person's mapped events are split by
  `split_events` (salt `kp-rect-split-v1`, 50%) into a rectification set and a sealed set. Only the
  rectification set is used here. The sealed set is never read by this test and stays available to
  test KP on the same people later. The ledger of both sets is written to disk.
- People need at least 3 rectification events. If more than 1,000 qualify, 1,000 are drawn with the
  seed.
- Same metric, labels and gates as above, all four tracks.

## What each outcome means

- **kp SIGNAL**: rectified times carry real information; the KP engine may take the rectified time
  with its top-set window.
- **kp BOUNDED_NULL / UNDERPOWERED**: rectification does not find the truth better than chance. The
  KP engine should keep the stated time and report its sub-lord stability band across the
  uncertainty window instead.
- Raman and Moon tracks are judged the same way, separately. No track is blended into another.

## Not encoded (and why)

KSK's ruling-planet rectification (lagna sub-lord among the ruling planets at the moment of
judgment) is not in Reader 3, and Readers 1 and 6 are not held (ruling RR4). Prenatal epoch
(HPA ch.12) and Prasna-based discovery are deferred, as in the Raman module.
