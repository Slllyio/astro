# Event timing: transits do not identify the month of death

**Date**: 2026-08-12
**Corpus**: Wikidata, 683,426 people with day-precision birth *and* death dates
**Screened**: 14,880 people × (1 real date + 4 of their own control dates) = 74,400 rows
**Holdout**: 4,996 people, frozen and unread
**Status**: screening, exploratory — the pre-registration is still all drafts

## Result

| | within-person AUC |
|---|---:|
| Sham (label permuted inside each person) | **0.5000** |
| Chartless twin: age + calendar harmonics | **0.5982** |
| Chartless + 90 transit features | 0.5919 |
| **Delta** | **−0.0064** |

**NULL.** Transits of Jupiter, Saturn, Uranus, Neptune and Pluto to natal
positions add nothing over a person's age and the calendar when asked which of
their own candidate months was the month they died.

## Why the design is worth trusting

Each person is their own control. A person contributes their real death date
plus four counterfactual dates drawn from their own final years. Every candidate
carries the **same natal chart, same birth era, same birthplace, same selection
into Wikidata** — held byte-identical, not statistically adjusted.

This matters because it forecloses the confound that destroyed the profession
test (`TIME_BASIS_CONFOUND.md`). There, sin/cos chart features acted as a Fourier
basis over *birth date* and beat a baseline that entered time linearly. Here that
mechanism cannot operate: the natal chart is constant within a person, so it
cannot discriminate between their own candidate dates. Only the transiting sky
and the age vary.

The sham reading exactly 0.5000 against a 0.0071 tolerance is about as clean as
that gate gets.

## Two errors this test caught before producing a number

**The sham permuted globally.** This design carries exactly one true date per
person. A global shuffle left 32% of people with none and 25% with two or more.
That structural damage — not any pipeline leak — pushed the sham to 0.4911, and
the gate refused to compute the real result. Fixed by permuting inside each
person's own candidate block.

**The first control window made the answer trivial.** Death is terminal, so
controls necessarily precede it; sampling across the whole adult life made the
real date always the person's *latest* candidate, identifiable by age alone by
construction. The baseline scored **0.9877**, leaving 1.2% of headroom — the
transits could not have shown signal even if they carried it. That run's
"NULL, delta −0.0201" was near-vacuous.

Narrowing controls to the final three years dropped the baseline to 0.5982 and
opened ~40 points of headroom. Only then was the question answerable, and the
answer is the one above.

Both errors surfaced from an implausibly *good* number rather than a failing
test. Neither would have been visible in the output of a system without a sham
gate and a chartless twin.

## What this null does and does not cover

**Covers**: slow-planet transits (Jupiter → Pluto) to six natal points, encoded
as harmonics of the separation, against death dated to the day, at monthly
resolution, within person, on 14,880 people.

**Does not cover**:

* **Other event classes.** Only death. Marriage, career changes, honours,
  illness — untested here. Death is also the event most dominated by age, so it
  is the hardest case for any timing claim; a null here does not transfer
  automatically to events with flatter age profiles.
* **Fast-moving bodies.** Wikidata carries no birth times (tier C), so the Moon,
  the ascendant, the houses and every angle-derived technique are excluded by
  construction — not tested and found wanting, but *not testable on this corpus
  at all*. Any doctrine resting on those is untouched.
* **Finer than a month.** Controls sit within three years of the event, so this
  asks "why this month rather than a nearby one", not "why this year of life".
  A whole-life-scale claim needs the age-matched between-person design described
  below.
* **Confirmation.** This is screening. The 4,996-person holdout has never been
  read and no pre-registration row is locked, so nothing here is a finding.

## The better design, for whenever it is wanted

The within-person design cannot ask a whole-life-scale timing question about a
terminal event, because age and lateness are the same thing. The standard fix is
**risk-set (density) sampling**: match each person who died at age *A* in year
*Y* against other people who were alive at age *A* in year *Y*. Age and era are
matched across people rather than within one, so the full lifespan is back in
scope. It is a larger build and needs the survival-analysis machinery already in
`app/medini/ml/stage_d_baseline.py`.

## Reproduce

```bash
python -m app.empirical.acquire.wikidata_import --from-year 1880 --to-year 1929 \
    --persons data/empirical/wikidata_persons.csv \
    --events  data/empirical/wikidata_events.csv
python -m app.empirical.tournament.run_event_timing \
    --persons data/empirical/wikidata_persons.csv \
    --events  data/empirical/wikidata_events.csv \
    --sample 20000 --out data/empirical/event_timing_report.json
```

To reproduce the degenerate first version, widen `_CONTROL_WINDOW_YEARS` to span
the whole adult life: the baseline returns to ~0.99 and the test stops being able
to answer anything.
