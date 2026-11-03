# KP real-outcome test: pre-registration (2026-11-02)

Status: **registered, not run.** No outcome data has been collected or read for this test. The
harness is `tools/kp/outcome_harness.py`; its constants are the ones fixed below, and changing any
of them after the `lock` step voids the test.

## Question

Do the KP engine's timing windows hold a person's real dated events more often than the same
windows taken from someone else's chart at the same age?

This is the only claim tested. It does not test promise/denial verdicts (most people in any
sample marry and work, so "promised" cannot be told from "always says yes").

## Data, and who supplies it

The user supplies two files, in two separate steps, under `data/private/kp_outcomes/`
(gitignored, never committed):

1. `births.json`: id, date, time, time zone, place, `time_source`, `uncertainty_minutes`.
2. `events.json`, given only after step 1 is locked: id, matter, date (day precision).

The earlier file `data/private/real_outcomes.json` is not used, and the harness refuses it.

**Primary sample:** people whose time comes from a document (`certificate`, `hospital_record`,
`horoscope_at_birth`) with at most 5 minutes uncertainty. KP's sub-lords move about every
2 minutes at the Ascendant, so a remembered time is not good enough. Everyone else enters only the
secondary run (`--all-times`). Rectified times are not allowed in either run.

## Matters and events (registered)

| Matter | Event counted | Engine houses |
|---|---|---|
| marriage | date of the first marriage | 2, 7, 11 (KPR4) |
| children | date of birth of each child | 2, 5, 11 (KPR3/KPR4) |
| service | start date of the first salaried job | 2, 6, 10 (ruling R15) |

Only events between age 16 and 50 count.

## Predictions

For each person and matter, from birth data alone:

- **R25 windows (primary rule):** dasa-bhukti-antara periods whose three lords are all fruitful
  significators (`selected_windows`, ruling R25).
- **R17 windows (secondary):** periods whose lords all signify a favourable house
  (`timing_windows`).
- R26 (ruling planets) is **not** used: it depends on the moment the question is judged, and a
  retrospective test has no such moment.

`lock` writes every window with a SHA-256 digest and the engine commit. `score` refuses a file
whose digest no longer matches.

## Baseline and statistic

- Hits = events that fall inside the person's own windows.
- Baseline: each person's event ages are laid on another person's windows (a random permutation of
  people), 2,000 times, seed 20261102. This matches age, so the common ages for marriage or a
  first job give no credit.
- One-sided p = (1 + shuffles with at least as many hits) / 2,001.
- Lift = hits / mean shuffled hits, reported with the shuffled 95th percentile.

## Verdicts (fixed now)

- **UNDERPOWERED:** fewer than 40 events for the matter. Pre-flight coverage for marriage under
  R25 is a median 27% of ages 20-40; 40 events give 80% power to detect a rise to about 45%
  at α = 0.05. Smaller effects need about 80 events or more.
- **SIGNAL:** at least 40 events, p < 0.05 and hits above the shuffled mean.
- **BOUNDED_NULL:** at least 40 events and not SIGNAL. Reported with the lift, so the size of
  any effect that was missed is visible.

**Primary test: marriage, R25, primary sample.** The other five (matter × rule) results are
secondary and exploratory, and are reported with all six p-values. None can rescue a failed
primary.

## What a result would mean

A SIGNAL supports the timing rule on this sample only; it needs a fresh sample before it means
more. A BOUNDED_NULL means the windows did no better than someone else's chart at the same age.
Either way the engine stays described as what it is: a faithful rendering of Krishnamurti's
Readers, not a validated predictor.
