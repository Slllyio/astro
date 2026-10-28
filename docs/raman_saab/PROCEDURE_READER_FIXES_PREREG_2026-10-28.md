# Procedure reader fixes from the Mainpuri hand reading — pre-registration

Date: 2026-10-28. Written and committed **before** any of the fixes below is coded or measured.
Source of the fixes: the hand reading of the Mainpuri chart (12 Oct 1989, 10:02 IST), copied in
the project files as `MAINPURI_CRITICAL_READING_2026-10-28.md`, section 7. User instruction:
"fix now since u know problems and before check on random samples".

Scope: the procedure reader (`app/raman_saab/procedure/`) only. It is a separate instrument; it
does not feed the scored judge, the golden ratchet or the report sections. **The judge is not
touched.** Its two Mainpuri errors (H7.K.2 "wife dies soon" firing on Rahu 4th from Venus, and the
4th read as mixed through Rahu with the Moon) follow the rule's printed wording (HTJAH-II:374 counts
malefics by sign from Venus); freeing them by the bhava would extend Raman's bhava device to a
from-karaka count he never applies it to, so it is left alone and recorded here.

Hold-out 3 (`HOLDOUT_BRIEF3_ADDENDUM.md`) is **not** read or scored by this work. Spending it is
the user's call.

## Baseline (measured 2026-10-28 on base `83d85f73`, before any change)

`python -m tools.raman_saab.procedure_reader_measure`: reader **152 / 389 exact, 295 within one,
94 real errors**. The judge, for reference: 260 / 349 / 40 (unchanged by this work).

## The verdict-changing fixes (each behind a switch, measured alone and together)

| Id | Fix | Raman basis | Status of the basis |
|---|---|---|---|
| F1 | A natural-malefic **Lagna lord** acting as an occupant, associate or aspecter counts 0 (named both ways), not -1. | Benefic lords include the Lagna lord (HTJAH:575-578; procedure spec 2.1). | doctrine; the 0 weight is the reader's existing "dual nature" convention |
| F2 | When a lord **occupies its own house**, an aspect already counted on the house is shown on the lord at weight 0 ("already weighed on the house"), not charged a second time. | Raman's sentences name an aspect once for a lord in its own house (procedure spec 3.3 sub-order). | convention |
| F3 | A node moved to another **Bhava** casts its 7th aspect from that Bhava: the aspect on the sign-7th house is dropped and the Bhava-7th house receives it. | "Ketu is actually in the 12th Bhava. Thus Lagna is free" (HTJAH:1945-1946), extended from occupancy to the node's 7th aspect, which is Raman's only nodal aspect (CLAUDE.md lock 2026-10-13). | convention extending doctrine |
| F4 | In the **Navamsa house test**, a natural malefic in its own or exaltation sign in the Navamsa, or the house's own lord, does not lower the grade. | Own sign cancels a malefic occupant's blemish (the reader's `own_sign_cancels`), applied the same way in the Navamsa. | convention extending doctrine |
| F5 | For **longevity**, when the engine has computed the span (birth data present), the span class decides the verdict (Purnayu favourable, Madhyayu mixed, Alpayu afflicted); the Lagna-lord/8th-lord comparison and Saturn are shown as sub-answers. Charts without birth data keep the current rule. | "The span of life comes first" (procedure spec 2.2; HTJAH:763-765, 1578-1580). | doctrine for the order; the span is the engine's `ayurdaya` |

## Text-only fixes (no verdict can change; checked by test, not by score)

- **T1** "children denied" is printed only when no factor of the four (house, lord, karaka, the view
  from the Moon) carries a redeeming benefic testimony; otherwise "few or delayed" (the floor rule,
  HTJAH:8669-8670, spec 4.4).
- **T2** The longevity sub-answers name the computed span beside the lords' band, and say so when
  they disagree.
- **T3** A "Special features" list in stage zero, Raman's opening paragraph: vargottama Lagna and
  planets, planets exalted in the Rasi but debilitated in the Navamsa (and the reverse), planets in
  their own Navamsa, Kemadruma with its cancellation, Kuja dosha from the Lagna, the Moon and Venus,
  and planets within one degree of a Bhava-sandhi with the margin in degrees. Descriptive only.

## The pass rule (fixed now)

Measured with `tools/raman_saab/procedure_reader_measure.py` on the 389 rows, against the baseline
152 / 295 / 94:

1. A fix **passes** if real errors do not rise **and** exact matches do not fall.
2. A fix that passes rule 1 must also pass the **random-sample check**: ten Track-B golden charts
   drawn with `random.Random(20261028).sample` from the records that carry confirmed verdicts. On
   every row of those charts whose verdict the fix changes, I read Raman's printed prose
   (`verdict_prose`) and record whether the new verdict is closer to it, the same distance, or
   further. A fix fails if more of its changed rows move further from Raman than closer.
3. The combined set is measured once more after the individual runs, and ships only if it also
   passes rules 1 and 2.
4. A fix that fails is kept in the code behind its switch set to off, with its numbers recorded
   here, the way the judge's held variants are.

This is an **in-sample** measurement: the 389 rows are the same goldens that earlier reader rounds
were reviewed on. A pass shows the fix does not hurt fidelity on Raman's charts; it is not an
out-of-sample improvement.

## Results

(Filled in after the runs; nothing below this line existed when the rule above was committed.)
