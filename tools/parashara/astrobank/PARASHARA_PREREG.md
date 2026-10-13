# Pre-registration — Parashara synthesis layer on real outcomes (astrobank)

Committed BEFORE any Parashara real-outcome number was computed (2026-10-13). Git commit order is the
date-lock, as for the Raman runs (`tools/raman_saab/astrobank/METHODOLOGY.md`). Nothing in the engine
is tuned from these results: they are a monitoring axis, reported beside Raman's, never averaged.

## Prior (stated in advance)
The Raman engine's verdicts, raw rules, 91 classical conditionals and dasha/maraka timing were all
NULL on this data (`docs/raman_saab/REAL_OUTCOME_GENERALIZATION.md`). The expected outcome here is
also null. A null result is a valid, reportable finding, not a failure of the run.

## Data (engine-independent, reused unchanged)
`E:\astro\data\astro_databank\derived\raman\`: `person_master`, `person_events`, `labels`
(mapping v3, already built), `store_population` (22,315: 14,318 labelled cohort + 7,997 stratified
controls). Charts are re-cast with the PARASHARA engine (Lahiri, its native ayanamsa — Raman's runs
used the Raman ayanamsa; a disclosed difference). Output: `derived\parashara\`.

Quality tiers: primary analysis = A+B. **Tier C stays HELD OUT** (not analysed) for any later
confirmatory run.

## Static test (house verdict vs life outcome)
Same 10 cohorts as Raman's `static_tests.py` (mapping v3): H5 children, H8 longevity (numeric),
H12 prison, H7 divorce-vs-long-marriage, H7 widowed, H2 bankrupt-vs-wealthy, H8 suicide / accident
(exploratory), H9 father, H4 mother. Parashara gives ONE verdict per house, so each test reads the
house verdict (not a signification).

**Ordinal score (locked):** denied 0 < difficult 1 < mixed = ordinary 2 < delayed 3 < granted 4;
indeterminate = missing (dropped, as Raman's insufficient-evidence). "Delayed" = promised-but-late,
so it ranks above the obstruction verdicts for a static outcome.
**Longevity axis:** `nisargayu_full.total_years` (case = short-life, lower expected).
**Direction:** every test pre-registered "afflicted" (case cohort scores LOWER).

Statistics exactly as METHODOLOGY.md (`tools/raman_saab/astrobank/_stats.py`, unchanged): oriented
AUC (one-sided Mann-Whitney), 1,000-resample bootstrap CI, stratified AUC (birth-decade x latitude
band), within-stratum permutation p, Benjamini-Hochberg q=0.10 over core+supporting.
**Pass bar:** AUC >= 0.55 = supported; 0.50-0.55 with BH pass = weak signal; otherwise null.

**Sham gate (runs FIRST, hard stop):** expatriate -> H5 must be null (CI spans 0.5), else the run
stops before any real result is printed. **Specificity:** each core cohort scored against all 12
house verdicts; the mapped house should rank top-3.

## Timing test (dasha windows vs dated events)
Raman's design, unchanged: each real event vs K = min(20, span-1) control dates from the SAME
person's eligible span [age 15, min(death-1yr, 75)], +/-1yr blackout around same-type events,
paired lift, person-clustered bootstrap (2,000), day-precision events -> AD windows, year-only ->
MD windows, never mixed. **Saturation gate: coverage >= 0.6 -> WITHHELD.**

Instruments (locked; window = Vimshottari period, Lahiri):
| test | events | AD-level window | MD-level window |
|---|---|---|---|
| marriage_H7_ausp | marriage | H7-targeting AD periods graded **auspicious** | MD lord targets H7 |
| divorce_H7_adverse | divorce | H7-targeting AD periods graded **adverse** | MD lord targets H7 |
| death_maraka_both (primary) | own death | AD periods with BOTH lords marakas | MD lord a maraka |
| death_maraka_either (sensitivity) | own death | AD periods with either lord a maraka | MD lord a maraka |

"Targets" = `activation.influences` (owns/occupies/aspects the house or its lord). Quality = the
dual-frame `window_quality` (ascendant + dasha-lord + dignity). Marakas = `reading.maraka_planets`.

**Cross-chart control (new, committed code — the control that exposed Raman's death-window
artefact):** each real event is also tested against the same instrument computed on OTHER people's
charts at the same age; the chart-specific excess = own-chart hit minus cross-chart mean hit.
**Pass bar for timing:** the within-person lift CI excludes 0 AND the cross-chart excess CI
excludes 0. Anything else is null.

## What would change after seeing results
Nothing. Any redesign gets a new pre-registration and a new run; this run's numbers are kept.
