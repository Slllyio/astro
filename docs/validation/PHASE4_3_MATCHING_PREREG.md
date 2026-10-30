# Pre-registration: Phase 4.3, whole-chart blind matching (the third core question)

Committed 2026-10-14, BEFORE any decoy has been cast or scored. Plan: Phase 4.3 + stopping rule.

## Question
Given what is known of a person's life, can the engine pick their **true chart** out of 5? The
other 4 are decoys born at the same place **within ±3 days, at a random clock time**. Same-day decoys
share the season, the era and the slow-planet positions, so only chart-specific content (lagna,
houses, Moon) can separate them. This is the cleanest test of astrology-specific information.

## Data
- Discovery: tiers A + B (`person_master.quality_tier`), people with ≥ 1 label in `labels.parquet`
  on the **verdict axis**, strength core or supporting. Exploratory-strength labels and the ayurdaya
  axis are excluded. Tier C is untouched (C2 is reserved for Phase 5).
- A person's **profile** = their set of (house, direction) labels: H2 wealthy / bankrupt, H4 / H9
  mother / father in childhood (good / early loss), H5 prolific / childless, H7 long marriage /
  divorced / widowed, H12 prison.

## Engine and score (fixed now)
- Parashara engine (Lahiri): `synthesize(read(cast(...)))` house verdicts, mapped to 3 poles with
  the report card's `SYNTH_TO_RAMAN`.
- Score(chart, profile) = Σ over profile labels of +1 (pole equals direction), −1 (opposite pole),
  0 (mixed / abstain).
- The 5 charts are ranked by score. Ties split the credit, so a k-way tie at the top gives 1/k of a hit.

## Decoys (seed 20261014)
- **Primary, regime S (same days):** 4 decoys per person, date = true date + d with d uniform on
  {−3..+3}, clock time uniform on [00:00, 24:00), same place and tz offset.
- **Secondary, regime Y (same year):** 4 decoys, date uniform within the true birth year, time
  uniform, same place.

## Statistic, power and verdict
- Hit rate (tie-split top-1 share). Null = 0.20 exactly. Effect = hit rate − 0.20, with a
  person-bootstrap 95% CI. SESOI = 0.03 (hit rate 0.23). Verdict per `tools/validation/result.py`.
- Power: the null SE for n ≈ 10k is about 0.004, so MDE80 ≈ 0.011, well below the SESOI.
- Also reported: the mean rank of the true chart (null 3.0).

## Controls (run first; failure stops before the real profile is scored)
1. **Planted recovery:** a synthetic profile generated from the TRUE chart's own verdicts (each
   label set to the true pole with probability 0.75, otherwise the opposite) must give a hit rate
   far above 0.20, with a lower CI bound > 0.23. This shows the matching can find a chart when the
   profile truly reflects it.
2. **Sham:** real profiles scored against 5 DECOY charts, with one decoy relabelled as "true".
   The hit rate must be compatible with 0.20.

## What each outcome means (and the stopping rule)
- **SIGNAL** on regime S → confirm once on held-out data under a new pre-registration.
- **BOUNDED_NULL** on regime S → all three core questions are BOUNDED_NULL (static pooled: Phase 1;
  timing: Phase 3; matching: here). **The plan's stopping rule then applies: no new outcome questions
  are opened.** Remaining Phase 4 items run only as already-registered machinery checks or descriptive
  summaries, and engine work continues on the fidelity axis only.
