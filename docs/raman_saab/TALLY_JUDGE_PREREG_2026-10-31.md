# Tally judge T1: pre-registration (2026-10-31)

Follows `REASON_CODING_RESULTS_2026-10-31.md`: Raman's verdict is close to a signed tally of the
reasons he states (84% recovered on unseen charts, near-equal weights), and the engine sees only
29% of those reasons. T1 computes, from the chart alone, the factor types Raman checks, signs
each by his general bhava-judging principles (HTJAH-I:474-497 lists the factors: the house, its
lord, the karaka, their dispositions, aspects and associations), and adds them up with one
shared weight. A **parallel** judge: the shipped engine is unchanged unless the user ships T1.
The user was asked to choose this (decision card 2026-10-31); this is built on the recommended
option while that is open, and nothing irreversible is done (hold-outs stay sealed).

Fixed before any T1 number exists.

## Factors (each instance counts +1 or -1)

Frames: Lagna, the Moon as Lagna, and the matter's karaka as Lagna (the karaka the engine
already assigns to the signification). For each frame, T = the matter's house counted from the
frame, located by whole sign. L = lord of T.
1. **Lord placement:** L in a kendra or trikona from the frame +1; L in the 6th, 8th or 12th from
   the frame -1.
2. **Lord dignity:** exalted, moolatrikona or own sign +1; debilitated or in an enemy's sign -1.
3. **Lord associations:** each natural benefic (Jupiter, Venus, Mercury) joining or aspecting L
   +1; each natural malefic (Sun, Mars, Saturn, Rahu, Ketu) joining or aspecting L -1; L combust -1.
4. **Occupants of T** (other than L): natural benefic +1, natural malefic -1.
5. **Aspects on T:** natural benefic +1, natural malefic -1; L aspecting T +1.
6. **Hemming of T:** between malefics -1, between benefics +1.
7. **6th/8th/12th lords** (from the frame, unless also L) occupying T: -1 each.
Once per matter, not per frame:
8. **Karaka:** dignity as in 2; in the 6th, 8th or 12th from Lagna -1; associations as in 3.
9. **Navamsa:** L and the karaka each: in its exaltation or own sign in the Navamsa +1, in its
   debilitation sign in the Navamsa -1.
10. **Named yogas:** each yoga the engine detects that its existing route table sends to this
    matter: +1, or -1 for arishta yogas and the progeny curses.

Aspects use the engine's whole-sign drishti (nodes 7th only). Mercury and the Moon count as
benefic in 3-5 only as listed (the Moon is left out of the benefic list, as its benefic status
depends on its phase, which T1 does not judge).

## Model

S = sum of all factor instances. Ordinal logistic on S with three fitted numbers (scale and two
cut points). Verdict = most probable of afflicted / mixed / favourable.

## Stages and pass rule

1. **Development check:** fit on the pool; score on hold-outs 1-3 (198). **Stop rule:** if T1's
   exact count there is not above B3's 131, T1 is reported as failed and hold-outs 4 and 5 are not
   proposed.
2. Otherwise refit on pool + hold-outs 1-3 and freeze (fitted numbers, code commit, SHA-256 of
   the 587 development verdicts).
3. **Final test**, once, only with the user's say-so: hold-outs 4 and 5 (64 rows). T1 passes if its
   exact count is >= B3's and > E's, its real errors are <= B3's, and its log-loss beats the class
   frequencies; reported with chart-clustered bootstrap intervals; "PASS, UNDERPOWERED" if the
   interval on T1 minus B3 includes 0.

Only bug fixes may follow the development check, each recorded here before re-running.

## Addendum 1 (2026-10-31): development check, T1 FAILS the stop rule

Fit on the pool, scored on hold-outs 1-3 (198): T1 124 exact, 67 real errors, log-loss 0.831
(class frequencies 0.838); B3 131 / 60; E 87 / 48. On the pool itself T1's log-loss is 0.940
against 0.945 for class frequencies, and it never predicts "mixed". T1 is below B3's 131, so by
the stop rule it is reported as failed, not frozen, and hold-outs 4 and 5 are not proposed.

**Exploratory, not pre-registered (pool, 389 rows): rank correlation of each T1 factor with
Raman's verdict.** Lord placement +0.01, lord dignity -0.00, Navamsa +0.03, hemming +0.02,
occupants +0.07, karaka +0.08, aspects -0.08, lord associations +0.12, 6/8/12 lords -0.11,
routed yogas +0.21. The engine's own benefic-minus-malefic rule count: +0.46 (in-sample; those
rules were built on this pool).

Reading: the general bhava factors, applied mechanically, carry almost no information about
Raman's verdicts on his worked charts, although his *stated* reasons recover 84% of them. He
picks, from many possible factors, the ones that agree with the conclusion, and on these
charts (mostly famous lives) the conclusion often rests on what is known to have happened
(13% of his stated factors are dasa or life facts). This is consistent with the 47k-chart
real-outcome null. Caveat: T1's signing is the general rule only (no functional
benefic/malefic by Lagna, no upachaya exception), so a finer signing could do somewhat better.

## Addendum 2 (2026-10-31): variant T2, fixed before any T2 number exists

User decision 2026-10-31 ("Refine factor signing once more"). T2 = T1 with two changes, nothing
else:
1. **Functional nature.** Wherever T1 signs an influencing planet by natural nature (factors 3,
   4, 5, and the karaka's associations in 8), T2 signs it by its functional nature for the frame's
   sign as Lagna, from Raman's printed table (HTJAH-I:523-566, `compute_functional_nature`):
   benefic or yogakaraka +1, malefic -1, neutral 0. Rahu and Ketu keep -1 (they have no lordship).
   For the karaka block the frame is the Lagna.
2. **Upachaya exception.** When the matter's house is the 3rd, 6th or 11th, a malefic occupying T
   counts +1 instead of -1 (Raman: malefics in the 3rd, 6th and 11th do good).
Same model, same stages, same stop rule (development check exact must be above B3's 131), and
the same one-time final test on hold-outs 4 and 5 only with the user's say-so.

## Addendum 3 (2026-10-31): T2 development check, FAILS the stop rule

| | Pool exact (in-sample) | Pool log-loss | H1-3 exact | H1-3 real errors | H1-3 log-loss |
|---|---|---|---|---|---|
| T1 | 193 | 0.940 | 124 | 67 | 0.831 |
| **T2** | 210 | 0.933 | **118** | 73 | 0.819 |
| B3 (simple rule count) | 253 | - | **131** | 60 | - |
| class frequencies | - | 0.945 | - | - | 0.838 |

Functional nature and the upachaya exception make the tally slightly more informative (log-loss
0.819 vs 0.831 on hold-outs 1-3; +17 exact on the pool), but on the hold-outs it gets fewer exact
matches (118), still never predicts "mixed", and stays well below B3. Not frozen; hold-outs 4 and
5 not proposed. (The runner's output labels the column "T1"; with `--T2` it is T2.)
