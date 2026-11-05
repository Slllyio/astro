# Birth-time policy (2026-11-05)

## The rule

The engine uses the birth time **as recorded** and says where it came from. It never moves
the birth time to fit a person's dated life events, and never moves it to fit life facts
judged by the same house rules the reading itself uses.

## Why event-based rectification was removed

Rectification "by a consideration of pronounced life incidents" (Raman, HPA ch.12) works
like this: take the stated time, search an hour or two either side, and keep the moment
whose dasha and bhukti periods best line up with the person's marriage, first job,
children, a parent's death. The reading is then cast at that moment and reads the same
dasha periods back to the person.

That is circular. Within a one- or two-hour window the Vimshottari periods at any date
shift through many lords, so there is nearly always some time whose periods "explain" a
handful of events. The fit is guaranteed by construction, so it is not evidence that the
method works, and every later reading built on the fitted time inherits a match that was
put in rather than found. This project's own measurements point the same way: on
Astro-Databank marriages the KP windows hit at the chance rate, random birth times scored
the same as real ones, and the learned predictive test found event-day skies no
different from ordinary days (see `docs/kp/KP_REAL_OUTCOME_RESULTS_ADB*` and the
predictive results). Published blind tests (Carlson 1985; Dean & Kelly 2003, 2,101 time
twins; Narlikar 2009) found no chart-based skill either. A rectified time cannot be
trusted when the thing used to rectify it has never been shown to work.

Natal-fact rectification ("the mother is chronically unwell, so the 4th house must be
afflicted") has the same flaw: the house rules being used to choose the time are the
house rules the reading will later apply.

## What the engine does instead

1. **Records the source of the time.** The feedback form asks where the time came from
   (hospital record, birth certificate, family recollection, a rounded hour, unknown) and
   whether an astrologer has already changed it. A time an astrologer "corrected" from
   events is flagged, because it carries the circularity in with it.
2. **Reports sensitivity instead of correcting.** The detailed report's "Rectification
   confidence" chapter (`app/raman_saab/rect_confidence.py`) re-casts the chart minute by
   minute to ±60 minutes and names which pillars (lagna, navamsa lagna, Moon nakshatra,
   each planet's house) flip and at what offset. The cited reader
   (`app/raman_saab/cited/reading.py`) re-judges each house at −20 … +20 minutes and says
   when a verdict changes inside that range. Both are measurements of how much the reading
   depends on the time; neither changes the time.
3. **Physical, non-event observations only, and never automatic.** The feedback form may
   ask closed physical questions (build, apparent age, and the two-sign portrait when the
   ascendant sits near a cusp). They are recorded and shown to the user next to the
   sensitivity report. They are not fed into any search that picks a time, and the engine
   makes no claim that they are reliable (appearance-by-lagna is itself untested here).

## What was removed

- `app/raman_saab/rectification/` (candidates, scoring, session, suggest, report, the HPA
  ch.12 arithmetic channel) and its tests
- `app/core/birth_time_rectification.py` and its test
- `tools/raman_saab/rectify.py` (CLI)
- `POST /rectify`, `GET /rectify/event-types` (now 410 Gone; `GET /rectify/policy` explains)
- `tests/fixtures/rect_case_01.json` and the pratyantar pins taken from it (a real
  person's life events)
- the feedback form's B6 grid of "events a birth time is corrected against"
- the unmerged KP rectifier in PR #30 is not carried forward

## What stays

- `app/raman_saab/life_events.py`: the cited event-to-house taxonomy (moved out of the
  rectification package). It is used only to **check** the engine against real lives at a
  birth time fixed independently of those events.
- `app/raman_saab/primitives/sunrise.py`: the sunrise helper the hold-out builder uses.
- `app/kp/horary/rectify.py` (KP Reader 6 ruling-planet candidates): it uses the moment
  of judgment, not life events, lists candidates and never picks one. It is kept as a
  cited reference, unvalidated, like the rest of the KP layer.
