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

### Rule 1: the 389 rows (baseline 152 / 295 / 94)

| Variant | Exact | Within one | Real errors | Rule 1 |
|---|---|---|---|---|
| F1 Lagna lord balanced | 152 | 296 | 93 | **pass** |
| F2 aspect once for a lord in its own house | 153 | 297 | 92 | **pass** |
| F3 node aspect from the Bhava | 146 | 296 | 93 | fail (exact falls 6) |
| F4 Navamsa own-sign malefic spared | 152 | 293 | 96 | fail (real errors rise 2) |
| F5 computed span decides longevity | 153 | 293 | 96 | fail (real errors rise 2) |
| all five | 148 | 295 | 94 | fail |
| **F1 + F2 (shipped)** | **153** | **298** | **91** | **pass** |

Rows F1 changed (3): HTJAH-II.h10_06 H10 afflicted→mixed (Raman mixed, now exact); HTJAH-II.h12_16
H12 afflicted→mixed (Raman afflicted, now one step off); NH.chart_42 H4 afflicted→mixed (Raman
favourable; this row is one of the off-topic labels already noted in PROCEDURE_READER_2026-10-25).
Rows F2 changed (3): HTJAH-I.chart_40 H2 mixed→favourable (Raman favourable); HTJAH-II.h11_06 H11
afflicted→mixed (Raman favourable); NH.chart_58 H3 afflicted→mixed (Raman favourable). Five of the
six move toward Raman, one moves one step away.

### Rule 2: the random sample

`random.Random(20261028).sample` over the 237 records with confirmed verdicts drew HTJAH-I.h6_13,
HTJAH-II.h9_13, NH.chart_55, NH.chart_75, HTJAH-I.h6_03, HTJAH-II.chart_33, HTJAH-I.h6_02,
NH.chart_54, HTJAH-I.h4_01 and HTJAH-I.chart_33.

- **F1 and F2 changed no verdict in the sample**, so rule 2 passes for them without testing
  anything. The two fixes are narrow: F1 only touches a Scorpio Lagna (the one Lagna whose table
  prints its natural-malefic lord neutral), and F2 only a lord sitting in its own house under an
  aspect. That is why the 389-row figures move by one to three.
- F3 changed one sample row, away from Raman: NH.chart_75 (Farouk) H7 mixed→favourable, where Raman
  writes of "the unhappiness in Farouk's domestic life".
- F5 changed one sample row, toward Raman: HTJAH-II.chart_33 H8 afflicted→favourable (Raman's own
  Pindayu 86 years). It still fails rule 1 on the full set.

### What ships

F1 and F2 on; F3, F4 and F5 kept behind their switches, off. T1, T2 and T3 ship (text only).

### What this says about the hand reading

Three of the five verdict fixes came from my reading of the Mainpuri chart and did not survive
Raman's own charts. F3 (moving the node's aspect with the Bhava) and F4 (an own-sign malefic in
the Navamsa not lowering the house) are extensions Raman never prints, and the 389 rows do not
support them. F5 helps some longevity rows and hurts others; Raman's span method and the engine's
Pindayu are not the same thing on every chart. The Mainpuri 10th and 11th therefore still read
afflicted in the procedure reader, and the hand reading's "favourable" for them stays an opinion,
not a measured fix.

---

## Addendum 1 (2026-10-28, written before any number for these two variants exists)

The user looked at the re-built Mainpuri page and objected that the 10th and 11th still read
afflicted. A line-by-line read of those two houses found two testimonies that contradict a rule
the reader already applies elsewhere. Each is pre-registered here as a narrow variant and measured
under the same pass rule (rules 1-4 above), against the shipped state **153 / 298 / 91**.

| Id | Fix | Raman basis |
|---|---|---|
| F4b | In the Navamsa house test, **only the house's own lord** is not counted against his house (F4 without its own-sign and exaltation clauses). On Mainpuri the 10th lord Sun, in his own Leo in the Navamsa, currently lowers the 10th. | "as he happens to be the 7th lord himself" (HTJAH:8594-8595, `own_lord_defused`); the reader already applies it in the Rasi. |
| F6 | A natural malefic that **owns a kendra other than the Lagna** and that Raman's table prints **neutral** counts 0 as an occupant, associate or aspecter ("named both ways"), not -1. On Mainpuri this is Saturn, lord of the 3rd and 4th, whose one aspect lowers the 11th house, the 10th lord and the karaka Jupiter. | Kendra lords that are not natural benefics are among the benefic lords (HTJAH:573-604; procedure spec 2.1); the table's "neutral" (HTJAH-I:552-553) sets the net to nothing, as the reader's `dual_nature_named` does for a functional benefic. |

F4b is the part of F4 with a printed citation; F4 as a whole failed. Choosing it after seeing F4's
six changed rows is a post-hoc narrowing, and is recorded as such: two of those six rows
(NH.chart_25 H7, NH.chart_57 H10) were own-lord cases that moved toward Raman. The variant is
justified by the citation, not by those rows, and is measured on all 389 like any other.

### Addendum 1 results (against 153 / 298 / 91)

| Variant | Exact | Within one | Real errors | Rule 1 | Random sample (rule 2) |
|---|---|---|---|---|---|
| F4b own lord in the Navamsa | 154 | 298 | 91 | pass | no change in the sample: pass |
| F6 kendra-owning neutral malefic | 154 | 298 | 91 | pass | 1 changed, further (NH.chart_55 H1, Raman afflicted, became mixed): **fail** |
| F4b + F6 | 154 | 298 | 91 | pass | as F6: fail |

F4b ships (reader now **154 / 298 / 91**). F6 is held behind its switch. Of its 25 changed rows,
the 10th and 11th rows moved toward Raman (NH.chart_42, 61, 69 H10; HTJAH-II.h11_15, x226 H11),
while 8th, 9th and 12th affliction rows moved away (Gandhi H8, NH.chart_30 H9/H12, NH.chart_58 H12,
NH.chart_52 H5). Restricting it to the 10th and 11th would be choosing the rule by its results, so
it is not done.

On Mainpuri the template tally therefore still reads the 10th and 11th afflicted: Saturn's
aspect (F6, held) and Rahu's sign aspect on the 10th (F3, held) are what remain. The page now leads
each house with the main engine's verdict (the scored judge, 260/389 exact), which reads both
favourable, and shows the template tally beside it.
