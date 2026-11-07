# Pre-registration: the new weighing, tested once on the fresh-41 (2026-11-07)

Committed before any engine run on the sealed set. User decision 2026-11-07: "Use the 41".

## Why this test

The opposite-verdict study (2026-11-05) and its follow-up found that the misses that remain come
from how the judge weighs evidence, not from missing rules. On every unseen Raman set so far, the
clause cascade (`house_template._decide_clauses`) lost to a plain count of the rules that fired:

| Set | n | Engine exact | Plain count (B3) | Always favourable |
|---|---|---|---|---|
| Hold-outs 1-3 | 198 | 87 | 131 | 126 |
| Hold-outs 4-5 | 64 | 29 | 40 | 38 |

The cascade gains 9 exact on the pool it was tuned on (231 → 240) and loses 55 on unseen
charts. The reason-coding study (2026-10-31) found Raman's own verdict is close to an
equal-weight signed tally of the reasons he states (84% leave-one-chart-out). So the redesign
candidate is that tally, applied to the reasons the engine encodes. Every hold-out is now
development data; the fresh-41 is the only unseen set left.

## Candidate R1 (frozen here)

For each matter, count the benefic and the malefic rules that fired **for that matter's own
signification** (`rule.signification == matter`). Rules for a sibling matter in the same house do
not count; the study found they cause contradictions such as h6_04, x68 and h9_12. The decision:

- more benefic than malefic → favourable
- more malefic than benefic → afflicted
- a tie, or nothing fired → favourable

There are no fitted parameters. The tie rule follows Raman's own base rate: he concludes
favourable in most matters, and "mixed" in 7 of 198 unseen rows.

**How R1 was chosen, disclosed.** Seven tally variants were compared on development data
(the pool plus hold-outs 1-5) on 2026-11-07, before this file:

| Variant | Pool exact | H1-5 exact | H1-5 real errors |
|---|---|---|---|
| E (shipped engine) | 240/365 | 116/262 | 62 |
| B3, all fired rules, ties favourable | 231 | 171 | 79 |
| **R1, own-signification rules, ties favourable** | 224 | **175** | 75 |
| R1, ties go to E | 223 | 165 | 70 |
| B3, ties mixed | 216 | 163 | 70 |
| B3, ties go to E | 232 | 168 | 72 |
| B3, nothing fired go to E | 234 | 158 | 92 |
| always favourable | 163 | 164 | 86 |

R1 was picked for the best exact score on H1-5. That is a selection on development data, so its
H1-5 figure is optimistic; only the fresh-41 is a clean test. Also note that R1 makes more
outright reversals than E (75 against 62), because it never answers "mixed".

## The sealed set

There are 41 conclusions from 29 natives, kept unread at the owner's PC in
`C:\Users\S.C.C\Documents\astro-fresh-sealed\fresh_sealed_agreed.jsonl`. Two engine-blind readers
read each chart, and both had to agree. Sources: HTJAH leftover charts (12), Planetary
Influences (6), Astrology for Beginners (4), HPA outside hold-out 3 (2), and Raman's
Astrological Magazine memoir series of 1986-91 (17). Seventeen rows have printed birth data. The
cloud thread has seen counts only.

**Conversion to the golden shape.** This is done on the PC before scoring, without running the
engine:

- `birth` holds printed date, time, tz, lat and lon, with the printed values used as they are.
- `lagna_sign` comes from the printed chart, or from Raman's prose where the record notes it.
- `stated_positions` holds the planets by printed degree. Where only the sign is printed, the
  harness uses its mid-sign convention, and the bhava is the whole-sign house from the Lagna.
- `expected_verdicts` holds the signification key from the engine's list for that house. Map it
  by the matter Raman names, with the map written down before scoring.

**Exclusions**, fixed now:

1. No birth data, and no Lagna with all nine positions: not castable, so excluded.
2. A reader-flagged date that contradicts Raman's own printed position (HTJAH-II 205's Sun), or
   one that is OCR-garbled with no printed positions to fall back on: excluded. The cast uses
   the positions where they exist.
3. A matter with no engine signification key: excluded.

Every exclusion is listed in the output. The medium- and low-confidence rows are not scored.

## Measures and the decision rule

Script: `tools/raman_saab/fresh41_score.py`, frozen in this commit. Self-check on development
data: on hold-outs 4-5 it reproduces E 29 exact with 14 real errors, and B3 40 with 19.

It reports the following for E, R1, B3 and always-favourable:

- exact
- within one step
- real errors (distance 2 or more; a non-graded answer counts 2)
- macro recall
- class split
- the same figures on the birth-data rows alone
- the chart-clustered 95% interval of R1 minus E, for exact and for real errors (seed 20261107)

**Primary.** D = exact(R1) − exact(E) on the scored rows.

- **R1 BETTER**: D ≥ 10% of n, and the interval excludes 0. The result is then put to the owner as
  a candidate to replace the clause cascade. Shipping is the owner's decision. The trade in real
  errors must be shown beside it, because an inversion is the worse failure (CLAUDE.md B1).
- **R1 WORSE**: D ≤ −10% of n, and the interval excludes 0. R1 is dropped.
- **Anything else: UNDERPOWERED.** With about 40 rows this is the likely outcome, and it is
  reported as such. It is not to be read as a tie or as a win.

Secondary, reported only: real errors R1 − E, B3 against E, and the birth-data rows alone.

## Rules for the run

- The script runs once, on the PC. Per-row results stay in the sealed folder. Only the
  aggregates leave it.
- No change to R1, the script, the exclusions or the decision rule after this commit. Any
  deviation goes in a dated addendum before the run.
- No book text enters the repo.
