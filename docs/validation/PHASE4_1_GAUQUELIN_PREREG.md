# Pre-registration: Phase 4.1, Gauquelin Mars-sector positive control

Committed 2026-10-14, BEFORE any sector position has been computed. Plan: Phase 4.1.

## Purpose
This is a machinery check, not an astrology claim. Gauquelin published that sports champions are born
with Mars just past rising or culmination more often than chance (his "key sectors"), in his own
civil-register data. If this pipeline reproduces that excess on his own file, it shows the pipeline
can see a real-data effect of about that size, so the Vedic nulls are not blindness. If it cannot,
either the machinery is blind or the original effect came from data handling. Either answer matters.
**The outcome does not bear on Vedic doctrine** and is never cited as support for it.

## Data
`gauquelin_persons.parquet`. Excluded, all decided now:
- the Gauquelin holdout, `assign_holdout(ids, salt="gauquelin-screening-v1")` (25%), not read;
- the 5,526 AstroDatabank overlaps (`gauquelin_dedup_review.csv`);
- `needs_geocoding` rows.

Target group: `profession == "sports_champion"`. Comparison groups (no Mars claim): `painter`, `writer`,
`actor`, reported separately and pooled.

## Instrument
Mars's diurnal position in Gauquelin's **36 sectors**, counted clockwise from rising: 1–9 rise→upper
culmination, 10–18 →set, 19–27 →lower culmination, 28–36 →rise. Arcs are proportional within the
semi-diurnal / semi-nocturnal arc, from hour angle and declination (Swiss Ephemeris, equatorial,
geometric horizon, no refraction).
**Key sectors = {36, 1, 2, 3, 9, 10, 11, 12}** (Gauquelin's plus zones just after rise and culmination).

## Expected frequency
Gauquelin's own method: 100 shuffles. Each subject's date, clock time and place are re-combined from
three different random subjects of the same group (seed 20261014). Expected rate = mean key-sector
share across the shuffles.

## Statistic and pass bar
Excess = observed key-sector share − expected share, in percentage points, with a bootstrap 95% CI
(subjects resampled, expected recomputed per resample from 20 shuffles).
- **Positive control PASSES** if the sports-champion excess CI excludes 0 and the point estimate is ≥ +2.0
  points (Gauquelin's printed figure is about +4.5).
- The comparison groups are expected near 0. If they show the same excess, it is an artefact of
  the method, not a Mars effect.
- Failure is reported as such: "this pipeline does not reproduce Gauquelin on his own data".
