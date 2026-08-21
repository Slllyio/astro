# The persona study — results

Twenty-three documented lives answered the feedback instrument blind. Pre-registration:
`PERSONA_STUDY_PREREG.md`, committed before any chart was cast. Every number here comes from
`tools/raman_saab/persona_study.py score`.

> ## ⚠ PROVENANCE CORRECTION — this run's raw data no longer exists
>
> **The figures below cannot be re-derived.** A container restart destroyed
> `data/persona_study/` in its entirety: all 23 blind answer files, the SHA-256 manifest this
> document cites as evidence the answers were hashed before scoring, the roster, the payloads,
> the verdicts and the scorecard. Nothing of the raw data survives anywhere.
>
> The cause was mine and it was structural, not bad luck. The persona answers are *collected*
> data — irreproducible, since a language model does not answer identically twice — and I wrote
> them to `data/`, which this repository gitignores for *derived* artifacts that can always be
> rebuilt. A container reset then did exactly what a reset does.
>
> So this section stands on the numbers as published and on nothing else. The blinding claim in
> §3 is no longer auditable: the manifest that evidenced it is gone. Read every figure below
> with that attached.
>
> A second run re-collects both arms and commits the answers to `tests/fixtures/persona_study/`,
> alongside the engine SHA they were scored under, so the chain holds next time. Its numbers
> will differ — the answerers are not deterministic — and it will supersede this section rather
> than overwrite it.

---

## What this cannot show, first

n = 23. The real-outcome question is closed at n = 22,177 charts and 47k dated events, sham-gated
at exactly 0.500 (`REAL_OUTCOME_GENERALIZATION.md`). **This study is about a thousandth of that
size and cannot reopen it.** Its pre-registered role was a consistency check, and its power was
computed in advance: significance begins at **0.562**, a +6.2 point deviation, which is almost
exactly this project's own measured noise floor (|AUC−0.5| p95 = 0.061). It can only see effects
larger than the field's own noise, so **a null here is weak evidence of absence.**

The respondents are language models reading biographies, not the people. The roster is famous
people, which is the one confound the existing programme has never closed.

---

## The headline

| | result | |
|---|---|---|
| **Sham gate — primary** | coin flip **132/267 = 0.494**, p = .90 | **PASS** |
| **Primary — blind forced choice** | **141/267 = 0.528**, p = **.39** | **NULL** |
| rarity-weighted | 0.533 | null |
| **Cross-chart contrast** | +0.0494, permutation p = .044 | **REJECTED as an artifact** |
| **Sham gate — contrast** | coin flip contrast **+0.0309** | **FAIL** |

The primary is null. The one number that came out nominally significant did not survive its own
control, and that is the most interesting thing the study produced.

---

## The finding: a control that caught its own statistic

The cross-chart contrast — each persona's claims scored against their own chart, minus the same
claims scored against the other 22 — came out at **+0.0494 with a permutation p of .044**. Taken
alone that reads as a signal: the real persona-to-chart pairing agreed more than 95.6% of random
pairings did.

It is not a signal. Running **coin-flip answers through the identical machinery** produces a
contrast of **+0.0309** — the same sign, and **63% of the size** — from an answerer that knows
nothing whatsoever. The gate (|contrast| < 0.02) fails, and the observed contrast cannot be read
as evidence. The residual after subtracting the sham is **+0.0185**, comfortably inside noise.

**Why the statistic is biased.** Part C selects each chart's **rarest** readings. A persona's
significations are therefore unusual for their own chart and comparatively typical on anyone
else's, so the two arms of the contrast are not looking at comparable items. The poles compound
it: `one_way` agrees with a favourable *or* an afflicted verdict while `mixed` agrees only with
`mixed`. Either asymmetry manufactures a positive contrast from nothing.

The primary's own sham gate would never have caught this, because the primary is scored against
a 0.5 that holds by construction. **A control validated for one statistic is not validated for
another** — this gate was added post-hoc, and is recorded as Deviation 2 in the pre-registration.

---

## Everything else, also null

**Every split.** Not one subgroup departs from chance:

| split | | | |
|---|---|---|---|
| **stratum** | 1 long success 24/48 (p=1.00) · 2 early death 25/48 (p=.89) · 3 imprisonment 26/48 (p=.67) | 4 chronic illness 19/36 (p=.87) · 5 childless/rupture 27/48 (p=.47) · 6 wealth↔ruin 24/48 (p=1.00) | |
| **Rodden** | AA 111/204 = 0.544 (p=.23) | A 34/72 = 0.472 (p=.72) | |
| **time precision** | minute 71/132 = 0.538 | quarter 57/108 = 0.528 | round hour 17/36 = 0.472 |

The catastrophe strata were included precisely so agreement could not come from base rate alone.
They score the same as the success stratum.

**The dated spine.** 433 dated turning points across 23 lives; **7 fell within ±3 months of a
Mahadasha boundary** against a computed chance rate of 0.0228, p = .52. Slightly *below* chance.

**Events against their own house.** 71 of 133 dated events (53.4%) fell in a period the engine
graded top for that matter. No pooled p-value is offered — each chart's null is its own set of
per-house base rates, which cannot simply be added.

**Confidence runs the wrong way.** Items the personas answered *confidently* scored
**64/132 = 0.485**; items answered *unsure* scored **21/35 = 0.600**. Small numbers, and the
difference is not significant, but the direction is the one the scorer explicitly warns about:
scoring no better where the respondent was more certain is the signature of agreeing with
whatever is in front of you, not of recognising a life.

**Inverted channels:** 4/9. Too few to read.

**Part D is empty.** Every persona declined it, unprompted, on the grounds that no reading had
been shown to them — which is the correct answer and a small piece of evidence that the blind
held.

---

## What the study actually bought: eight defects

This is the part with unambiguous value. Filling the instrument end to end for the first time
found eight real defects, each now fixed with a failing test written first.

**Two were crashes reachable in ordinary use.**

1. **A reader ticking three boxes got a 422.** `InstrumentAnswer.answer` was capped at 40
   characters while the instrument's own vocabularies run far past it — three trade families join
   to 50, three work modes to 54, all nineteen trades to 236. Worse, anything that squeaked past
   was stored as `answer[:40]`, cut mid-code into something no longer parseable. The bound is now
   derived from the widest vocabulary.
2. **An undated event beside a dated one in the same year crashed the scorer.** Events sort as
   `(year, month-or-None, kind)` and `None < 3` raises. Only a *shared* year fires it, which is
   why it hid — and why it is ordinary, since remembering the month of one turning point and only
   the year of another is the normal case. It took down both measurements that read events.
3. **The trade comparison read a dict's keys instead of its frames.** `career_frames` is a dict,
   not a list; iterating it yielded the string `"frames"`, and `.get("trade")` on a string raised.
   Two defects in one — the crash, and a comparison that had been silently running on half its
   evidence.

**Three silently discarded answers a reader had taken the trouble to give.** `_score_life`
dispatches on `maps_to`, which is not unique: A10/A11 share `h9.father` and A28/A29 share
`h5.children`, but only the first question's vocabulary was mapped, so every answer to the second
fell out as `not_scoreable` forever. A31 had no entry at all and produced no item whatsoever.

**One reported a p-value against a null the data never had.** `aggregate` tested the pooled spine
count against a hard-coded 0.25 while each chart computes its own chance rate; it is now
event-weighted from those rates.

**One was a 500 from the public API.** Any birth more than ~140 years back — the Vimshottari
sequence is unrolled 140 years, so `dasha_on` returns None and `synthesize` dereferenced it. The
API accepts `year >= 1800`.

**The eighth is this document's own subject:** a control that validated the primary but not the
contrast.

---

## The roster, and what the gate refused

23 of 48 registered candidates admitted; 17 AA and 6 A. The admission gate did real work:

- 4 refused for a weak Rodden rating (Mandela DD, Capone C, Hope C, Hawking C);
- 4 refused because the birthplace was on **local mean time** at that date — Einstein (1879 Ulm),
  Kahlo (1907 Mexico City), Keller (1880 Alabama), Roosevelt (1882 New York). `zoneinfo` answers
  such dates with the *zone's* LMT, which belongs to the reference city rather than the birth
  city: Berlin's +00:53:28 against Ulm's own +00:39:58, about 3.5° of ascendant;
- 4 because no nativity is published;
- 1 — Martin Luther King's 12:00 — as a noon default, under Deviation 1.

Stratum 4 admitted only three: its candidate list was exhausted, and a shortfall is reported
rather than filled by promoting a name out of registered order.

---

## Reading this beside the closed programme

The primary lands where `REAL_OUTCOME_GENERALIZATION.md` says it should, and the mechanism named
in `WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md` is visible in the per-reading breakdown: with 56
significations judged on every chart and both poles available on 97.1% of them, agreement on any
one of them is close to a coin toss whichever life is attached.

What this study adds is not another null — the null was already established far more powerfully.
It adds a worked demonstration that **the controls are load-bearing**. A perfectly reasonable
statistic, applied to real blinded data, returned p = .044; the coin flip put two-thirds of that
straight back. Anyone reading engine output for agreement with a life should assume the same of
their own impressions, which have no sham arm at all.

---

## Provenance

- Answers hashed before any answer key was computed: `data/persona_study/answers_manifest.json`.
- Roster, payloads, verdicts and results under `data/persona_study/` (gitignored — derived).
- Operator scorecard: `data/persona_study/scorecard.html`.
- Golden ratchet byte-identical throughout: **exact 259/293 · within-1 283/293 · real-errors 10**.
  Nothing in this study touches the verdict path.
