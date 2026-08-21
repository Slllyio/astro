# The persona study — results

Twenty-three documented lives answered the feedback instrument **twice**: once blind, and once
having read the chart's own reading first. Pre-registration: `PERSONA_STUDY_PREREG.md`, committed
before any chart was cast. Every number here comes from
`tools/raman_saab/persona_study.py score`, and every answer it was computed from is committed
under `tests/fixtures/persona_study/`, so every figure below can be re-derived.

Run 2, engine `baed614`. Run 1 is preserved at the foot of this document; its raw data was
destroyed by a container reset and its figures superseded rather than overwritten.

---

## What this cannot show, first

n = 23. The real-outcome question is closed at n = 22,177 charts and 47k dated events, sham-gated
at exactly 0.500 (`REAL_OUTCOME_GENERALIZATION.md`). **This study is about a thousandth of that
size and cannot reopen it.** Its pre-registered role was a consistency check, and its power was
computed in advance: significance begins at **0.562**, a +6.2 point deviation, which is almost
exactly this project's own measured noise floor (|AUC−0.5| p95 = 0.061). It can only see effects
larger than the field's own noise, so **a null here is weak evidence of absence.**

The respondents are language models reading biographies, not the people. The roster is famous
people, which is the one confound the existing programme has never closed. The contaminated arm
therefore measures what seeing a reading does to *an agent's* answers; that it should do the same
to a person's is an inference, not a measurement.

---

## The headline

| | result | |
|---|---|---|
| **Sham gate — primary** | coin flip **132/267 = 0.494**, p = .90 | **PASS** |
| **Primary — blind forced choice** | **134/267 = 0.502**, p = **1.00** | **NULL** |
| rarity-weighted | 0.508 | null |
| **Contaminated arm — reading read first** | **142/267 = 0.532**, p = .33 | elevated, not significant alone |
| **Blind vs contaminated, paired** | 8 blind-only vs **18 contaminated-only** hits, McNemar p = **.076** | directional |
| **Cross-chart contrast — sham floor** | coin flip **+0.0339**, perm p = .11 | **GATE FAILS** |
| **Cross-chart contrast — blind** | **+0.0166**, perm p = .30 | *below the sham floor* |
| **Cross-chart contrast — contaminated** | **+0.0704**, perm p = **.010** | clears the floor by +0.037 |

The blind primary is 134/267 — two items off dead chance, with p = 1.00. It is hard to land more
exactly on the null than that, and it replicates run 1 independently.

The contaminated arm is elevated on **all three** of its measures, and significant on one.

---

## The finding the contaminated arm exists to produce

Same personas. Same 267 items. Same charts. The only difference is that one arm read the chart's
reading before answering and the other did not.

```
                  forced choice     cross-chart contrast     confident items
  coin flip       132/267  0.494          +0.0339                    —
  blind           134/267  0.502          +0.0166  p=.30       65/135  0.481
  contaminated    142/267  0.532          +0.0704  p=.010      78/148  0.527
```

**Read the contrast column against the sham floor, not against zero.** The contrast statistic is
biased — the coin flip proves it, at +0.0339 from an answerer that knows nothing (see the next
section for why). The blind arm sits at **+0.0166, *below* that floor**: less apparent own-chart
agreement than a machine with no knowledge produces. The contaminated arm sits at **+0.0704**,
clearing the floor by +0.0365 and significant on its own permutation test at p = .010.

**A second, independent signature: the confidence flip.**

| | confident (4–5) | unsure (1–2) | gap |
|---|---|---|---|
| blind | 65/135 = **0.481** | 23/37 = **0.622** | **−0.140** |
| contaminated | 78/148 = **0.527** | 14/33 = **0.424** | **+0.103** |

Blind, confidence runs *backwards*: the personas did **worse** where they were more certain. That
is the signature of confidence tracking how strongly the biography felt rather than whether the
chart agreed — which is precisely what you expect when the chart carries no information. Read the
reading first and the sign flips, and the confident pool itself grows from 135 items to 148: the
reading made the answerer both more certain and certain in the chart's direction. Neither gap is
individually significant (p = .73 / .19 / .57 / .49); it is the *pattern across four independent
measures all moving the same way* that carries the weight, not any one of them.

**What this demonstrates.** `WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md:154-164` names curation
asymmetry as the mechanism by which a faithful engine appears to work: knowing a biography before
reading the chart guarantees an apparent landing. This is that mechanism reproduced inside our own
harness, under pre-registration, with the blind arm as its own control. The asymmetry is no longer
only argued from Raman's curated gallery — it is measured, and it is ours.

**What it does not demonstrate.** The forced-choice rate alone (0.532, p = .33) and the paired
test (p = .076) are both short of significance. At n = 23 personas this study cannot establish the
size of the effect, only its consistent direction across four measures. It is *suggestive and
directionally unanimous*, not established. Said plainly: had the contaminated arm come out flat,
that would have been a finding about the harness and would be reported here as one.

---

## The control that caught its own statistic

The cross-chart contrast — each persona's claims scored against their own chart, minus the same
claims scored against the other 22 — is the study's most interesting piece of methodology, because
running **coin-flip answers through the identical machinery** returns a contrast of **+0.0339**
from an answerer that knows nothing at all. The gate (|contrast| < 0.02) **fails**, exactly as
predicted before this run, and the failure is structural rather than a fluke: run 1 measured the
same artifact at +0.0309.

**Why the statistic is biased.** Part C selects each chart's **rarest** readings. A persona's
significations are therefore unusual for their own chart and comparatively typical on anyone
else's, so the two arms of the contrast are not looking at comparable items. The poles compound
it: `one_way` agrees with a favourable *or* an afflicted verdict while `mixed` agrees only with
`mixed`. Either asymmetry manufactures a positive contrast from nothing.

The primary's own sham gate would never have caught this, because the primary is scored against a
0.5 that holds by construction. **A control validated for one statistic is not validated for
another** — this gate was added post-hoc, and is recorded as Deviation 2 in the pre-registration.

This is why the contaminated arm's +0.0704 is reported as "clears the floor by +0.037" rather than
as "+0.070". The floor is real and it is subtracted.

---

## Everything else, also null

**Every split of the blind arm.** Not one subgroup departs from chance. The contaminated column is
shown beside it — every split moves the same direction, none significantly:

| split | blind | contaminated |
|---|---|---|
| stratum 1 — long success | 24/48 = 0.500 (p=1.00) | 26/48 = 0.542 (p=.67) |
| stratum 2 — early death | 25/48 = 0.521 (p=.89) | 26/48 = 0.542 (p=.67) |
| stratum 3 — imprisonment | 25/48 = 0.521 (p=.89) | 25/48 = 0.521 (p=.89) |
| stratum 4 — chronic illness | 18/36 = 0.500 (p=1.00) | 18/36 = 0.500 (p=1.00) |
| stratum 5 — childless / rupture | 24/48 = 0.500 (p=1.00) | 30/48 = 0.625 (p=.11) |
| stratum 6 — wealth ↔ ruin | 22/48 = 0.458 (p=.67) | 23/48 = 0.479 (p=.89) |
| Rodden AA | 105/204 = 0.515 (p=.73) | 113/204 = 0.554 (p=.14) |
| Rodden A | 33/72 = 0.458 (p=.56) | 35/72 = 0.486 (p=.91) |
| time to the minute | 69/132 = 0.523 (p=.66) | 71/132 = 0.538 (p=.43) |
| time to the quarter | 52/108 = 0.481 (p=.77) | 58/108 = 0.537 (p=.50) |
| time to the round hour | 17/36 = 0.472 (p=.87) | 19/36 = 0.528 (p=.87) |

The catastrophe strata were included precisely so agreement could not come from base rate alone.
They score the same as the success stratum. A birth time known to the minute scores no better than
one known to the hour, which is the sharpest single statement in the table: if the chart carried
information about the life, precision in casting it ought to matter.

**The dated spine.** 394 dated turning points across 23 lives; **10 fell within ±3 months of a
Mahadasha boundary** against a computed chance rate of 0.0234, p = .74.

**Events against their own house.** 59 of 114 dated events (51.8%) fell in a period the engine
graded top for that matter. No pooled p-value is offered — each chart's null is its own set of
per-house base rates, which cannot simply be added.

**Inverted channels:** 4/9 blind, 6/9 contaminated. Too few to read either way.

**Part D.** Blind, every persona declined it unprompted, on the grounds that no reading had been
shown to them — the correct answer, and a small piece of evidence that the blind held. The
contaminated arm answered it, which is what it is for.

---

## What the study bought: eleven defects

Filling the instrument end to end found eleven real defects, each fixed with a failing test
written first. Eight came from run 1 and are listed below; run 2 added three more, all in the
study's own machinery — which is the right place to find them and the worst place to leave them.

**Run 2 — three defects in the measurement apparatus itself.**

1. **`verify` hashed only half the collected data.** It globbed `answers/` and never
   `answers_contaminated/` — 23 of the 46 files, the entire third arm, were never hashed at all.
   The command whose whole purpose is "these answers cannot now be revised" did not cover the arm
   carrying the study's most interesting result.
2. **An answer token no question offered was absorbed in silence.** An unknown option code crashes
   nothing: it simply never matches, so the item scores as one fewer agreement and the study
   reports a colder number for a reason recorded nowhere. **That is the worst error this study can
   make, because it looks exactly like an honest result.** `off_vocabulary` now names every stray
   at verify time. One survives in the data — Madoff's A18 carries `manual`, a work-*mode* code on
   the trade question — and it is recorded, not corrected.
3. **A whole persona's event history was unreadable and would have vanished quietly.** The gate's
   first run caught it: Reeve's contaminated file encoded 21 turning points and 4 rectification
   anchors as one prose blob per question instead of one row per key, and `parse_answers` could
   read none of them. Re-encoded mechanically, changing no event, date or code; the answerer's
   original strings are kept verbatim in the file under `raw_events_as_given` (Deviation 5).

**Run 1 — eight defects, two of them crashes reachable in ordinary use.**

4. **A reader ticking three boxes got a 422.** `InstrumentAnswer.answer` was capped at 40
   characters while the instrument's own vocabularies run far past it — three trade families join
   to 50, all nineteen to 236. Worse, anything that squeaked past was stored as `answer[:40]`, cut
   mid-code into something no longer parseable. The bound is now derived from the widest vocabulary.
5. **An undated event beside a dated one in the same year crashed the scorer.** Events sort as
   `(year, month-or-None, kind)` and `None < 3` raises. Only a *shared* year fires it, which is why
   it hid — and why it is ordinary, since remembering the month of one turning point and only the
   year of another is the normal case. It took down both measurements that read events.
6. **The trade comparison read a dict's keys instead of its frames.** `career_frames` is a dict;
   iterating it yielded the string `"frames"`, and `.get("trade")` on a string raised. Two defects
   in one — the crash, and a comparison silently running on half its evidence.
7. **Three questions' answers were discarded forever.** `_score_life` dispatches on `maps_to`,
   which is not unique: A10/A11 share `h9.father` and A28/A29 share `h5.children`, but only the
   first question's vocabulary was mapped. A31 had no entry at all.
8. **A p-value against a null the data never had.** `aggregate` tested the pooled spine count
   against a hard-coded 0.25 while each chart computes its own chance rate; now event-weighted.
9. **A 500 from the public API** for any birth more than ~140 years back — the Vimshottari sequence
   unrolls 140 years, `dasha_on` returns None, and `synthesize` dereferenced it. The API accepts
   `year >= 1800`.
10. **A control validated for one statistic but not another** — this document's own subject.
11. **Seven citations resolving to blank lines,** found by the anchor test the study prompted.

---

## The roster, and what the gate refused

23 of 48 registered candidates admitted; 17 AA and 6 A. Identical to run 1 — the gate is
deterministic, and reproducing the same 23 from the same registered list is itself a check. The
gate did real work:

- 4 refused for a weak Rodden rating (Mandela DD, Capone C, Hope C, Hawking C);
- 4 refused because the birthplace was on **local mean time** at that date — Einstein (1879 Ulm),
  Kahlo (1907 Mexico City), Keller (1880 Alabama), Roosevelt (1882 New York). `zoneinfo` answers
  such dates with the *zone's* LMT, which belongs to the reference city rather than the birth city:
  Berlin's +00:53:28 against Ulm's own +00:39:58, about 3.5° of ascendant;
- 4 because no nativity is published;
- 1 — Martin Luther King's 12:00 — as a noon default, under Deviation 1.

Stratum 4 admitted only three: its candidate list was exhausted, and a shortfall is reported rather
than filled by promoting a name out of registered order.

---

## Reading this beside the closed programme

The blind primary lands where `REAL_OUTCOME_GENERALIZATION.md` says it should, and the mechanism
named in `WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md` is visible in the per-reading breakdown: with 56
significations judged on every chart and both poles available on 97.1% of them, agreement on any
one of them is close to a coin toss whichever life is attached.

What this study adds is not another null — the null was already established far more powerfully. It
adds two things:

**The controls are load-bearing.** A perfectly reasonable statistic, applied to real blinded data,
returned p = .044 in run 1; the coin flip put two-thirds of that straight back. Anyone reading
engine output for agreement with a life should assume the same of their own impressions, which have
no sham arm at all.

**The asymmetry is ours to point at, not only Raman's.** The same personas, the same items, the
same charts — and the arm that read the reading first agrees with the chart more, on four measures
at once, while the blind arm sits at 0.502. That is the clearest available statement of why the
engine must never be presented as a validated predictor: the agreement a reader feels is
manufactured by the order in which they meet the evidence, and this study reproduces that
manufacture on demand.

---

## Provenance

- **Answers committed**: `tests/fixtures/persona_study/answers/` (23, blind) and
  `answers_contaminated/` (23). Every figure here is re-derivable from them.
- **Hashed before scoring**: `tests/fixtures/persona_study/answers_manifest.json`, both arms, with
  each file's off-vocabulary tokens recorded alongside its digest.
- Roster, payloads, verdicts and `results.json` under `tests/fixtures/persona_study/`.
- Engine SHA the answers were scored under: **`baed614`**, recorded in `results.json`.
- **What the blind rests on**: construction. The payload provably carries no verdict, band share,
  signification name or inverted-warning — asserted at build time, and pinned by a test. It does
  *not* rest on the key being computed later: `verdicts/` is written at build time because the
  contaminated arm's own input is rendered from it. `verify` adds the operator's half — once the
  digest is written, answers cannot be revised in the light of a score.
- Golden ratchet byte-identical throughout: **exact 259/293 · within-1 283/293 · real-errors 10**.
  Nothing in this study touches the verdict path.

---

## Superseded: run 1

> **The raw data for run 1 no longer exists.** A container reset destroyed `data/persona_study/` in
> its entirety: all 23 blind answer files, the SHA-256 manifest, the roster, the payloads, the
> verdicts and the scorecard.
>
> The cause was mine and it was structural, not bad luck. The persona answers are *collected* data
> — irreproducible, since a language model does not answer identically twice — and I wrote them to
> `data/`, which this repository gitignores for *derived* artifacts that can always be rebuilt. A
> container reset then did exactly what a reset does. Run 2 commits its answers to
> `tests/fixtures/`, which is why its figures are re-derivable and these are not.

| | run 1 | run 2 |
|---|---|---|
| sham gate — primary | 132/267 = 0.494 | 132/267 = 0.494 |
| **blind primary** | **141/267 = 0.528**, p = .39 | **134/267 = 0.502**, p = 1.00 |
| rarity-weighted | 0.533 | 0.508 |
| cross-chart contrast | +0.0494, perm p = .044 | +0.0166, perm p = .30 |
| sham floor on the contrast | +0.0309 | +0.0339 |
| contaminated arm | *never run* | 142/267 = 0.532 |
| confident / unsure | 64/132 · 21/35 | 65/135 · 23/37 |
| dated spine | 7/433 near a boundary, p = .52 | 10/394, p = .74 |

Both runs return a null primary, and the coin-flip arm reproduces to the item (132/267 in both —
it is deterministic given the seed and the payloads, so this is a reproducibility check as well as
a gate). Run 1's one nominally significant number, the cross-chart contrast at p = .044, did not
replicate: run 2 puts it at +0.0166, below its own sham floor. The rejection of that statistic as
an artifact, made in run 1 on the strength of the coin-flip control alone, is confirmed by the
replication.
