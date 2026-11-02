# Pre-registration: learned predictive test (Phases 0-2), 2026-11-02

Committed BEFORE any feature has been computed against any outcome. Design document:
`/mnt/project-files/astro/design/PREDICTIVE_SYSTEM_DESIGN_2026-11-02.md` (project folder).
Owner instruction: "Go" (2026-11-02, project thread "Design a predictive system from scratch").

Only population descriptives were looked at before this commit: tier sizes (A 20,500, B 26,536,
C 22,946 people) and event counts by mapped type and date precision (Phase 3 loader). No chart
feature has been computed for anyone in this project's new code, and no outcome has been compared
with any chart quantity in it.

## Question

Does the birth sky carry information about life outcomes that a flexible learned model can find,
beyond season of birth, birth cohort, age and place? This is the first test in the project that is
free to use any chart pattern, not only the rules the texts name (the "Phase 5 composite/ML" that
`docs/validation/VALIDATION_SUMMARY.md` left unrun).

## Data and samples

- Source: `person_master.parquet`, `person_events.parquet` (derived Astro-Databank copy, Raman
  build), the activation stores `activation_lahiri_AB.parquet` (Parashara engine) and
  `raman_activation_raman_AB.parquet` (Raman engine), `rule_fires.parquet` (Raman engine) and
  Parashara `verdicts.parquet`.
- **Development:** quality tiers A and B with a full `YYYY-MM-DD` birth date, a time, latitude,
  longitude and tz offset (about 47,000 people). These people were used by earlier rule tests, but
  never by any fitted model; that is why they are development data here.
- **Sealed:** all of tier C. C1 = `assign_holdout(tier-C ids, fraction=0.5, salt="tierC-split-v1")`
  (manifest `tools/validation/holdout_manifest_tierC1.json`), C2 = the rest. Neither is read in
  Phases 0-2. Note recorded now: tier C birth times are mostly rounded to the hour (22,591 of
  22,946), so C1 can confirm only effects that survive a ±30-minute time error. Time-sensitive
  features (ascendant, houses, cusps) are judged inside development by null N1.
- `data/private/` is never read. No personal or relatives' data is used.

## Task A: natal traits (one row per person)

Twelve binary targets from `categories_raw` (tag present = 1). Chart-derived tags (`Asc …`,
`Sun …`, `Moon …`) are never used as targets or features.

| # | Target | Tag rule |
|---|---|---|
| A1 | Actor | `Vocation : Entertainment : Actor/ Actress` |
| A2 | Public office | `Vocation : Politics : Public office` |
| A3 | Writer | any `Vocation : Writers : …` except `… : Astrology` |
| A4 | Sports | any `Vocation : Sports : …` |
| A5 | Military | any `Vocation : Military : …` |
| A6 | Music | any `Vocation : Entertain/Music : …` |
| A7 | Law | any `Vocation : Law : …` |
| A8 | Divorces noted | `Family : Relationship : Number of Divorces` |
| A9 | More than 3 children | `Family : Parenting : Kids more than 3` |
| A10 | Cancer | `Diagnoses : Major Diseases : Cancer` |
| A11 | Homicide victim | `Passions : Criminal Victim : Homicide victim` |
| A12 | Short life (< 29) | `Personal : Death : Short Life less than 29 Yrs`, only among people with a `NNNN deaths` tag |

## Task B: event timing (case-crossover, within person)

- Events: Phase 3 loader and event map (`tools/validation/riskset_timing.py`, frozen), tiers A+B,
  **day-precision only**, ages 5-95, **own death excluded** (in a within-person design the death date
  is always the last date of the life, so age alone identifies it). Event type = the mapped house
  set (relationship 7, career 10, health/legal 6, children 5, parents 4/9, siblings 3, money 2/11,
  arrest 12, inheritance 8). About 1,364 events.
- Controls: 10 dates per event from the **same person**. Each control's age is drawn from the case
  ages of the same event type among other people; its calendar day-of-year is within ±15 days of
  the case's; it must fall at age ≥ 5, on or before 2024-12-31, before any recorded death, and more
  than 365 days from any event of the same type for that person. Seed 20261102.
- Year-precision events are not in the primary test (fast-moving features are undefined for a year).

## Features

**Confound baseline (both tasks):** birth year, birth day-of-year (sin, cos), latitude, longitude,
tier, population source. Task B adds age at the date, calendar year and day-of-year of the date, and
event type. Season of birth fixes the Sun's sign, so Sun-sign astrology is inside the baseline and
cannot be credited to astrology by this test.

**Track G, geometry (Lahiri sidereal, mean node, Swiss Ephemeris):**
- Natal: for Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu: longitude (sin, cos), sign,
  nakshatra, retrograde, whole-sign house from the Lagna, Placidus diurnal position (house number +
  fraction); Lagna and MC longitude (sin, cos), Lagna sign; for every pair of bodies the sign
  distance (1-12).
- Timing (at the date): for every transiting body its sign counted from the natal Moon and from the
  natal Lagna; for Jupiter, Saturn and Rahu the angular separation (sin, cos) to natal Sun, Moon,
  Mars, Venus, Jupiter, Saturn, Lagna and MC; Vimshottari MD, AD and PD lords (Lahiri, Moon-based).

**Track T, text rules:**
- Natal: Raman engine rule fires (`rule_fires`, rules firing for 1%-99% of development people),
  Parashara house verdicts (12 houses, one-hot), KP natal indications fired (`app.kp.indications`)
  and KP cusp sub-lord verdicts for marriage, children, health, wealth, service.
- Timing: activation tiers for all 12 houses and maraka from both activation stores (Parashara
  engine Lahiri, Raman engine Raman ayanamsa) for the period running at the date; for the KP
  Vimshottari MD, AD and antara lords at the date, whether each signifies each of the 12 houses
  (ladder A-D, `app.kp.significators`).

## Models (fixed now, no tuning)

- **Primary model M2:** LightGBM, 300 rounds, learning rate 0.05, num_leaves 8, min_data_in_leaf
  50, feature_fraction 0.5, bagging 0.8, lambda_l2 1.0, seed 20261102.
- **Secondary M1:** L1 logistic regression (C = 0.05, standardised inputs).
- The neural set-encoder (M3) runs only if M2 passes Phase 2.
- Evaluation: 5-fold cross-validation with folds by person (Task B: all rows of a person in one fold).

## Statistics

- **Task A primary statistic:** ΔAUC = mean over the 12 targets of [CV AUC(baseline + G + T) −
  CV AUC(baseline)].
- **Task B primary statistic:** ΔC = within-set concordance (share of controls the case outranks,
  ties half) of the full model minus that of the baseline model.
- **Family scan (co-primary, both tasks):** the same Δ for the baseline plus one feature family at a
  time (one family per body, plus Lagna/MC, pairwise distances, dasa lords, each T source). The
  statistic is the maximum Δ over families; the same maximum is taken in every null run, which
  controls the family-wise error. Co-primary alphas are 0.025 each (full model, family scan).

## Nulls

- **N2, season-and-cohort donor shuffle (Task A primary null):** every G and T feature row is moved,
  as a block, to another person of the same birth year, the same half-month of the birth date and
  the same latitude band (|lat| < 30, 30-45, > 45, by hemisphere). Strata of one person keep their
  own row (the share is reported). 100 runs.
- **N3, within-set label permutation (Task B primary null):** in every set the case label is moved
  to a random row of the set. 100 runs.
- **N1, same-day random clock time (secondary, both tasks):** G features (and KP T features) are
  recomputed for a uniform random time on the real birth date and place; store-based T features are
  kept. 50 runs.
- p = (1 + runs with Δ ≥ observed) / (1 + runs).

## Pass rules (decided now)

- **SESOI:** Task A ΔAUC 0.02 above the null mean; Task B ΔC 0.03 above the null mean.
- **Phase 2 passes for a task** if the full model or the family scan beats its primary null at
  p < 0.025 AND the observed Δ is at least SESOI above the null mean.
- **If neither task passes: stop.** Write the bounded result. C1 and C2 stay sealed.
- If a task passes, Phase 3 (one read of C1, then C2) needs its own short pre-registration naming
  the frozen model, written before C1 is opened.
- N1 is reported for every result: a pass that N1 matches means the effect does not depend on the
  birth time (it is in the slow, date-level sky).

## Phase 1: the instrument must work first

1. **Gauquelin positive control.** Gauquelin persons (holdout `gauquelin-screening-v1` excluded, the
   AstroDatabank overlaps excluded, `needs_geocoding` excluded), target = sports champion against
   all other professions. Natal G features only, Task A pipeline, null N1 (same-day random time,
   50 runs), plus a baseline of birth year, day-of-year, latitude, longitude. Pass if the full model
   or the family scan beats N1 at p < 0.05. The phase 4.1 result (+4.7 points) says the effect is
   there; this checks the learned pipeline can see it.
2. **Planted effects (synthetic labels only, never real outcomes).**
   - Task A: a synthetic target with prevalence 10%, risk ratio 2.0 for people whose Moon is in
     three named nakshatras (Ashwini, Magha, Mula), and a second with risk ratio 2.0 when Mars and
     Venus share a sign. Five replicates each, N2 with 20 runs.
   - Task B: case dates chosen in each real set with odds 3 for rows where transiting Jupiter is in
     sign 1, 5 or 9 from the natal Moon. Five replicates, N3 with 20 runs.
   - Pass if each plant is detected at p < 0.05 in at least 4 of 5 replicates.
3. **All-null check.** Fully random labels (same prevalence) must not pass: at most 1 of 5
   replicates at p < 0.05.

If Phase 1 fails, the pipeline is fixed and Phase 1 re-run before Phase 2. If the Gauquelin control
alone fails while the plants pass, that is recorded and Phase 2 goes ahead, with the result read as
"this instrument cannot see an effect of the Gauquelin size".

## What will be reported

Every number above, pass or fail, per target and per family, with N1, in
`docs/predictive/PREDICTIVE_RESULTS_*.md`. No change of target, feature, model, null or rule after
this commit without a dated addendum written before the affected number is computed.
