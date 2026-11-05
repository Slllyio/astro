# Hold-out 2 results (2026-10-24)

Protocol: `FIDELITY_FIXES_PREREG.md` Addenda 5 and 6. Fixture `tests/fixtures/raman_holdout2_sealed.jsonl`
(commit 1c9ae4c), scored once per variant. Per-row output: `holdout2_score_2026-10-24.json`.

## What was built

26 Raman natives the engine had never been scored on: 12 Notable Horoscopes charts (Nos. 1-15,
cast from Raman's printed positions; No. 50 was already a golden chart), plus HTJAH Vol I and Vol II
charts whose birth date is in neither earlier fixture. 134 scored conclusions: 94 favourable,
33 afflicted, 7 mixed. Thirteen cast charts were rejected because the cast disagreed with Raman's
printed dasa balance, one for a Lagna mismatch. Vol II was read by two independent engine-blind
extractors; only the 32 conclusions they gave identically are scored (they contradicted each other
on none).

## Scores

| Variant | Exact | Within one | Real errors | Addendum 5 rule |
|---|---|---|---|---|
| V0 (engine as shipped) | 55/134 = 41.0% | 98/134 = 73.1% | 36 (27%) | baseline |
| R2 re-scope ten rules from their citations | 58 | 98 | 36 | **passes** (exact +3, nothing else moves) |
| R4 stated-chart tie-break | 64 | 94 | 40 | fails (4 new inversions, all NH) |
| R5 general lord-affliction rule | 55 | 100 | 34 | **passes** (real -2, within one +2) |

Per book, real errors never rise for R2 or R5. R5 loses one exact row in HTJAH-II.

## Reading it honestly

1. **The engine is much weaker out of sample than in sample.** In-pool it is 70.7% exact with 9.8%
   real errors; hold-out 1 gave 63.9% and 22%; hold-out 2 gives 41.0% and 27%. The pool figure is
   flattered by years of rule work done on those same charts.
2. **The main failure is over-calling affliction.** Raman calls 94 of the 134 matters favourable;
   the engine says favourable for 48, afflicted for 39, mixed for 38 and abstains on 9. Of the 36
   real errors, 18 are Raman-favourable read as afflicted, 9 the reverse, and 9 are abstentions.
3. **Caveats.** 98 of the 134 rows are NH Nos. 1-15, many of them ancient or speculative charts
   (Raman himself calls Nos. 3, 6 and 11 speculative) cast from printed positions with some
   degrees missing. NH rows score 35% exact; the Vol II rows 61%.
4. **The variant effects are small.** R2 changes three rows, R5 five. Taken together with the pool
   result, R2 is +5 exact and +1 real error; R5 is -4 exact and -1 real error. Neither is a clear
   win on numbers alone.

## Recommendation (the user decides)

Ship **R2**: it makes ten rules say exactly what their cited Raman passage says (engine-blind
review on file), and on unseen charts it only gains. Keep **R5** held: its hold-out gain is two
rows and it lost four exact rows in the pool. Drop **R4**. Hold-out 2 is now spent for these
variants.
