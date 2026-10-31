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
