# The time-basis confound

**Date**: 2026-08-12
**Corpus**: Gauquelin series A via CURA, 9,390 tier-A persons, 9 professions
**Status**: measured, decisive, and it changes how every chart-feature result in
this repo should be read

## The claim

**Sin/cos-encoded chart features are a Fourier basis over birth date.** Handing
them to any model silently grants it the ability to fit a smooth non-linear era
trend. If the comparison baseline enters time linearly, the chart wins on
*functional form* and the result looks like astrology.

## The evidence

Screening ran three times over the same corpus, same split, same protocol. Only
the chartless twin changed.

| Twin | military | musician | politician | scientist | survivors |
|---|---:|---:|---:|---:|---:|
| `birth_year` (integer) + season | **+0.058** | **+0.034** | **+0.040** | **+0.037** | 8 of 18 |
| + full date (`decimal_year`) | **+0.058** | **+0.034** | **+0.040** | **+0.037** | 8 of 18 |
| + date harmonics at planetary periods | **−0.011** | **−0.015** | **−0.019** | **−0.006** | **0 of 18** |

Adding *date precision* changed nothing. Adding *date flexibility* removed the
entire effect.

The mechanism is visible in which number moved:

| profession | chart AUC | chartless AUC |
|---|---|---|
| military | 0.6060 → 0.6092 | 0.5482 → **0.6206** |
| musician | 0.7907 → 0.7885 | 0.7571 → **0.8036** |
| politician | 0.7844 → 0.7853 | 0.7447 → **0.8041** |

The chart model barely moved. The baseline caught up and passed it. The chart
was never contributing astrology — it was contributing a curve.

## Why it works

`sin(longitude(t))` for a planet of period *P* is a periodic function of time.
Eleven bodies give periods of 1.9, 11.9, 29.5, 84, 165 and 248 years. That is a
Fourier expansion of the birth date, and a linear model equipped with it can fit
almost any smooth era trend.

Profession in this corpus has a strong non-linear era trend: the six volumes
were collected over different date ranges, so `military` and `musician` cluster
in particular decades. A straight line in `decimal_year` cannot express that. Six
sine pairs can.

## The corroborating tell, noticed before the test

`raw_astronomy` — ecliptic latitude, distance and speed, with no signs, houses,
or aspects — matched or beat the full Western bank on three of the four apparent
survivors. If astrological *encoding* were doing the work, the Western bank
should have won. That both banks performed identically was the clue that
whatever they shared (planetary position ≈ time) was the active ingredient.

## The control that must now be standard

Any chart-feature comparison in this repo must score against a baseline carrying
`_date_harmonics()` — sin/cos of decimal year at the planetary periods, computed
from the calendar with no ephemeris. Implemented in
`app/empirical/tournament/build_feature_banks.py`.

Without it, a positive result is uninterpretable.

## Implication for prior work

This casts doubt on the one surviving positive in the earlier programme:
Round 11's **+0.043 AUC lift on Wikidata marriage**
(`data/ml_runs/round11_followup_verdict.md`). That experiment tested against
*cyclic date* controls — `birth_month`, `birth_day_of_year` — which are annual
harmonics only. They do not span the 11.9/29.5/84/165/248-year periods where the
slow planets live, so a multi-decade era trend would pass straight through them.

The Round 11 write-up already flagged "era-specific documentation bias" as the
live alternative explanation and proposed birth-century stratification to test
it. This is the same confound with a sharper mechanism and a cheaper test.

**Not re-litigated here** — that corpus is not reachable from this session. But
re-running `xgboost_date_disambiguation.py` with a harmonic date basis added to
condition B is a small change with a real chance of closing the last open
positive in the programme.

## What this result is not

It is not a refutation of astrology. It is a refutation of *these features on
this corpus against this target*, and specifically a demonstration that the
apparent effect was a modelling artifact.

It also does not touch `sport_champion`, which was negative in every
configuration (−0.006 to −0.014). That is the Gauquelin Mars effect's own data
and target; a null there is a null on the field's most-tested claim, obtained
without needing this confound at all.

## Reproduce

```bash
python -m app.empirical.acquire.gauquelin_import --out data/empirical/gauquelin.csv
python -m app.empirical.tournament.build_feature_banks \
    --corpus data/empirical/gauquelin.csv --out data/empirical/feature_banks.parquet
python -m app.empirical.tournament.run_screening \
    --banks data/empirical/feature_banks.parquet --out data/empirical/screening_report.json
```

To reproduce the confound, delete `_date_harmonics()` from the chartless bank and
re-run: the eight survivors return.
