# KP real-outcome test, addendum A: Astro-Databank data (2026-11-02)

Status: **registered before any KP result on this data exists.** Committed before the `lock`
step. Tool: `tools/kp/adb_test.py`. The main registration
(`KP_REAL_OUTCOME_PREREG_2026-11-02.md`) still holds for the user's own data; this addendum adds a
second, public sample and a trait test of Reader 2's sign rules (ruling R29).

## Why this source

The user asked for the most accurate birth data findable online, with life events and traits.
That is Astro-Databank (astro.com): each record carries a Rodden rating, and **AA** means the time
comes from a birth certificate or birth record. The project already holds a harvested copy
(`E:/astro/data/astro_databank/derived/raman/person_master.parquet` and `person_events.parquet`),
with dated events and Astro-Databank's own category tags ("Kids none", "Married late/never",
"Voice/Speech", "Stutter").

Known history: tiers A and B of this copy were used by the earlier validation of the Raman and
Parashara engines. **The KP engine has never been run on it, and no KP rule was built or tuned on
it.** Tier C (the C1/C2 holdouts, 22,946 people) is not read, here or later.

## Population (fixed now, uses birth data only)

1. `population == "celebrity_databank"` (the Astro-Databank part; app-user records are excluded).
2. `quality_tier` A or B. Tier A = Rodden AA and a minute-precise time; tier B = AA or A, minute or
   quarter-hour. Tier C and untiered rows are excluded.
3. **Ascendant gate.** Astro-Databank publishes each chart's tropical Ascendant ("Asc 18
   Aquarius") in the record. The record is kept only if the tropical Placidus Ascendant cast from
   its date, time, zone and place is within 1.5 degrees of that published value (taken as the
   middle of the printed degree). This removes records whose place or zone was mis-coded in the
   harvest (for example a Honolulu birth coded with Chicago's coordinates). Records without a
   published Ascendant, or that cannot be cast, are excluded.

## Part A: timing (the registered harness, constants unchanged)

- Matters: **marriage** (`Relationship | Marriage`) and **service** (`Work | New Job`), events with
  day precision only. Children are not run: the copy has almost no dated births of children.
- The event used is the person's **earliest** day-precise event of that matter. Astro-Databank
  does not always list earlier marriages, so "first marriage" means the first one recorded.
- People locked: everyone passing the gate who has at least one such event (chosen by the event's
  presence, before any date is read).
- **Primary: marriage, R25, tier A** (time from a certificate, given to the minute; entered as
  `time_source = "certificate"`, `uncertainty_minutes = 1`). Tier B enters only the secondary
  `--all-times` run. Verdict rules, shuffle baseline, seed and the 40-event floor are exactly those
  of the main registration.

## Part B: Reader 2's sign rules against Astro-Databank's tags

Rules are computed for every gated person and locked (SHA-256 digest) before any tag is read.

| Test | Cases | Controls | Primary rule (predicted direction) | Secondary |
|---|---|---|---|---|
| T1 children | tag "Family : Parenting : Kids none" | "Kids 1-3" or "Kids more than 3", and not "Kids none" | `progeny.lessened` more often in cases | `progeny.promised_either` less often in cases |
| T2 marriage | "Family : Relationship : Married late/never" | "Number of Marriages" or "Marriage more than 15 Yrs", and not late/never | `marriage.late` more often in cases | none |
| T3 voice | "Traits : Body : Voice/Speech" or "Vocation : Education : Public speaker" | everyone else | `voice.second` more often in cases | `voice.second_venus_mercury` |
| T4 speech | "Diagnoses : Psychological : Stutter, Tics" | everyone else | any of `speech.mercury6`, `speech.mercury_moon`, `speech.saturn_lagna` more often in cases | none |

- Statistic: one-sided Fisher exact test in the predicted direction; risk ratio (cases vs
  controls firing) with a 95% interval.
- **Verdicts:** UNDERPOWERED if fewer than 40 cases. SIGNAL if p < 0.0125 (0.05 split over the four
  primaries) in the predicted direction. Otherwise BOUNDED_NULL, reported with the risk-ratio
  interval so the largest effect that could have been missed is visible.
- **Primary sample: tiers A and B together** (these rules read cusp signs, which a quarter-hour
  error rarely moves). Secondary: tier A alone.
- Diagnostic only, not a verdict: mean absolute latitude and median birth year of cases and
  controls, because Ascendant signs depend on latitude and family size on era.
- Rules that cannot fire (R29: `progeny.promised`, `progeny.none`, `marriage.early`) are not tested.

## What a result would mean

A SIGNAL on one sample is a lead to repeat on fresh data, not a finding. A BOUNDED_NULL means the
rule as printed did no better than chance on these people. Either way the engine stays described
as a faithful rendering of Krishnamurti's books, not a validated predictor.
