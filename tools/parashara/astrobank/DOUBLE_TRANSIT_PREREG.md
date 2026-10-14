# Pre-registration — dasha + double transit on real outcomes (Parashara engine)

Committed BEFORE any double-transit number was computed (2026-10-13). Git order is the date-lock.
Companion to `PARASHARA_PREREG.md` (whose static + dasha-only timing run was NULL, `RESULTS.md`).

## Hypothesis (the user's, stated in the classical form)
A chart promises everything, but an event fructifies only when the DASHA activates the matter AND the
slow grahas TRIGGER it by transit — the "double transit": transiting Jupiter AND transiting Saturn
both bear on the matter's house or its lord, during a dasha period that activates that house. If
dashas + transits are the true clock, real events should fall inside such windows more often than
the same person's other dates, and more often than other people's charts at the same age.

## Instruments (locked)
Natal facts per person from the Parashara cast (Lahiri). Transits: Jupiter and Saturn sidereal
(Lahiri, Swiss Ephemeris, same flags as `app/parashara/chart/ephemeris.py`) at the test date.

**Transit bears on a house** = the transiting planet OCCUPIES or casts its FULL graha-drishti
(BPHS-26: Jupiter 5/7/9, Saturn 3/7/10) on EITHER the natal house sign OR the natal sign of that
house's lord.
**Double transit (DT)** = Jupiter bears on it AND Saturn bears on it, on the same date.
**Dasha activation** = the date falls in a Vimshottari AD period whose MD or AD lord targets the
house (`activation.influences`: owns / occupies / aspects the house or its lord) — the stored
AD-level windows, any quality.

| test | events | primary instrument |
|---|---|---|
| marriage_H7_DT | marriage (day-precision) | dasha activates H7 AND double transit on H7 |
| divorce_H7_DT | divorce (day-precision) | dasha activates H7 AND double transit on H7 |
| death_H8_DT (secondary) | own death (day-precision) | maraka AD (either lord) AND double transit on H8 |

Also reported, never as the headline: the same three with the transit leg ONLY (no dasha), to show
what the transit adds.

**Day-precision events only**: a year-only date cannot localise Jupiter's ~1-year / Saturn's
~2.5-year sign transits; such events are excluded, not approximated.

## Controls and pass bar (same as PARASHARA_PREREG.md)
Within-person: K = min(20, span-1) control dates in [age 15, min(death-1yr, 75)], +/-1yr blackout
around same-type events; paired lift; person-clustered bootstrap (2,000; seed 20260724).
Cross-chart: the same instrument on M=20 other people's charts at the event's age; chart-specific
excess. Coverage >= 0.6 -> WITHHELD. Tier A+B; tier C held out.
**Pass**: lift CI excludes 0 AND cross-chart excess CI excludes 0, in the PREDICTED (positive)
direction. Anything else is null.

## Prior
Null expected (every prior real-outcome test, both engines, was null). A null here is a real,
reportable finding about the dasha+transit hypothesis — not a failure of the run.
