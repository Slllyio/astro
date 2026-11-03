# Why the KP windows did not time the marriages (2026-11-02)

Exploratory follow-up to `KP_REAL_OUTCOME_RESULTS_ADB_2026-11-02.md`. It uses the same people and
dates, which are already spent, so nothing here is a new test. Numbers:
`kp_adb_timing_diagnostics_2026-11-02.json`, from `tools/kp/adb_timing_diagnostics.py`. The sample
is the 197 people whose first recorded day-dated marriage falls between ages 18 and 45 (88 of them
tier A, birth certificate times).

## Short answer

The windows fail because **almost every planet signifies marriage, and almost every planet also
signifies its denial**. So the rule cannot pick out a part of life where marriage is more likely; it
picks out about a third of adult life, and real marriages land in it about a third of the time. The
birth-time precision, the sample size and the shuffled baseline are not the cause: each was checked
directly and ruled out.

## The reasons, ranked by how much they explain

### 1. Saturation: the significator ladder hands the marriage houses to nearly every planet

With the four-level ladder (occupant, star of occupant, lord, star of lord), counted over 2, 7 and
11 together:

| Bodies (of 9) signifying 2, 7 or 11 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|
| People | 3 | 9 | 26 | 43 | 45 | 45 | 26 |

The median chart has 7 of the 9 bodies as marriage significators, and 7 to 8 of them **also**
signify the denial houses 1, 6 or 10. A Vimshottari period is ruled by one of nine planets, so
"the lords signify 2, 7 or 11" is true most of the time for most people. This is the same mechanism
found earlier for the Raman engine: indications are so abundant that they are present both when
the event happens and when it does not.

### 2. The windows cover a third to a half of adult life, and the hit rate equals the coverage

| Rule | Share of ages 18-45 inside a window (mean) | Share of real marriages inside a window |
|---|---|---|
| R25 (fruitful significators) | 37.0% | 35.0% |
| R17 (all significators) | 53.2% | 52.8% |

A window that covers 37% of life will catch about 37% of any dates, real or random. The real
marriages were caught at exactly that rate. Krishnamurti's own narrowing steps (R25's fruitfulness
test) cut the coverage, but cut the real marriages by the same proportion.

### 3. No level of the dasa system points at the marriage, even inside each person's own life

This check needs no shuffling: it compares the period running at the marriage with the same
person's own periods across ages 18-45.

| Level | Lord signifies 2/7/11 at the marriage | Expected from that person's own life | Lord is fruitful (R25) at the marriage | Expected |
|---|---|---|---|---|
| Dasa | 163 | 159.6 | 126 | 124.3 |
| Bhukti | 142 | 150.6 | 113 | 121.7 |
| Antara | 145 | 152.2 | 120 | 122.5 |
| Sookshma | 153 | 152.3 | 127 | 122.5 |

At no level does the running lord signify marriage more often at the wedding than at any other
time in that person's life. So the null is not an artefact of comparing one person with another.

### 4. Birth time is not the reason

- **Same-day control.** Windows cast for 20 random clock times on the same birth date and place
  caught 35.9% of the marriages; the recorded time caught 35.0%. The exact birth time adds nothing.
- **Sensitivity.** Moving a tier A birth time by 2 minutes changes the 7th cusp sub-lord for about
  30% of people, but the R25 windows stay about 85-90% the same and only 2-7% of hits flip. The
  windows run on the Moon's dasa and on significators that mostly survive small shifts.
- **Simulation.** If KP were exactly true (marriages planted inside the windows of the true chart)
  and the recorded time were wrong by up to 5 minutes, the windows would still catch 90% of the
  marriages (up to 10 minutes: 82%), against 37% by chance. A real effect of that kind would have
  shown clearly. What was seen was 35%.
- The recorded times are rounded: 62% of tier A times fall on a multiple of 5 minutes (20%
  expected), so most are uncertain by about ±2.5 minutes. The simulation shows that is not enough
  to hide an effect.

The verdicts (promise or denial) are a different matter: they rest on the cusp sub-lord, which is
fragile at ±2 minutes. That fragility is real but is not what made the timing fail.

### 5. Not sample size

With 92 primary events, a lift above about 1.16 would have registered; with all 206, about 1.12.
The observed lifts were 0.96 and 0.92. A modest real effect is ruled out on this sample; a very
small one (a few percent) cannot be.

### 6. Data noise, a minor factor

- For 33 of the 226 people with a day-dated marriage, Astro-Databank also lists an earlier marriage
  with only a year. Their "first recorded" date is a later marriage. That is about 15% of events,
  which could dilute an effect by about that much, not erase it.
- The people are celebrities (entertainment, writing, politics), median birth year 1947. There is
  no sign this matters, but it is not a random population.

### 7. Why the books' own examples work

Krishnamurti's printed cases are worked backwards from known events: the chart is often corrected
until the sub-lords fit, and the significators are chosen by judgment among many candidates (here,
7 of 9). With that freedom, almost any date can be matched after the fact. The engine cannot use
the outcome, so it gets the rule without the hindsight. This matches the earlier finding on Raman's
verdicts (his stated reasons fit the known lives; chart-only rules do not generalise).

## Krishnamurti's own fixes, tested

He saw this problem himself. Reader 6 (p.166), on a second-marriage chart: "All the nine planets
are significators of houses 2 & 11. When many signify, the best course to eliminate the tempters
and select the beneficial ones is to go for Ruling planets ... at the moment of judgement." The
Readers give four ways to cut the list. Three can be applied to past charts; each was tried on the
same 197 marriages (`kp_adb_filter_check_2026-11-02.json`, `tools/kp/adb_filter_check.py`), on top
of R25:

| Filter (source) | Share of ages 18-45 covered | Marriages caught | Hit ÷ coverage | Random times, same day | People left with no window |
|---|---|---|---|---|---|
| R25 alone (KPR4 p.118) | 37.0% | 35.0% | 0.95 | 35.8% | 24 |
| Drop significators in a retrograde planet's star (KPR6 pp.146-147) | 26.0% | 25.9% | 1.00 | 26.5% | 31 |
| Drop "tempters": sub-lord also signifies 1, 6 or 10 (KPR5 pp.201-202) | 2.2% | 1.0% | 0.46 | 2.5% | 150 |
| Strong significators only (KPR4 p.118, KPR5 pp.208-209) | 17.9% | 18.3% | 1.02 | 17.7% | 44 |
| Retrograde + strong | 13.1% | 14.2% | 1.09 | 13.7% | 54 |
| All three | 1.0% | 1.0% | 1.01 | 1.0% | 169 |

Every filter shrinks the windows and the catches by the same proportion. None lifts the hit rate
above the share of life covered, and random birth times on the same day do as well. The "tempter"
filter shows the saturation again from the other side: sub-lords nearly always also signify a
denial house, so applying it strictly leaves 150 of 197 people with no marriage window at all,
though all of them married.

The fourth fix, **ruling planets at the moment of judgment**, is the one he leans on most, and it
cannot be tested on past lives: it needs the moment a question is put to the astrologer, before
the event.

**The promise rule fails the same way** (`tools/kp/adb_verdict_check.py`). All 220 of these people
married, yet the 7th cusp sub-lord says DENIED for 109 of them (50%). Charts cast for random clock
times on the same day say DENIED 47% of the time. His Saturn-delay sign (Saturn among the fruitful
significators) is on 70% of these charts (62% at random times), and their median marriage age is
29.0 against 28.4 without it.

## What is left untested

Ruling planets at the moment of a question (R26, and horary) cannot be tested retrospectively,
because there was no moment of judgment. The only fair test of that part is forward: questions
logged with their time, judged, and scored after the event.
