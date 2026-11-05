# The house audit: the Mainpuri 10th/11th audit, made standard for every chart

Date: 2026-10-28. User request: "I want this level of analysis. Fix this type now", after the
rule-by-rule audit of the Mainpuri 10th and 11th (`MAINPURI_H10_H11_AUDIT_2026-10-28.md`).

## What it is

`app/raman_saab/house_audit.py` audits each house of any chart. It never changes a verdict. The
verdict is always the scored judge's (`house_template.judge_house`, 260/389 on Raman's conclusions).
For each house the audit gives:

1. **The rules.** Every rule that fired, with its polarity, citation and text, and the matters it
   was weighed for.
2. **The condition check.** A rule is *doubtful* when its condition no longer holds once a planet
   is treated as absent from a sign whose Bhava it does not occupy (HTJAH-I:1945-1946), or which
   it occupies only in a Bhava-sandhi (HPA-24:98-100). `Or` arms and occupant counts are
   re-evaluated, so a rule another arm still satisfies is not flagged.
3. **The weighing.** The clause of `_decide_clauses` that decided each matter, with the pillars,
   the B1 and Navamsa guards, and the Bhava rescue or karaka salvage. A test re-derives each named
   clause's verdict on every golden ledger and checks it against the judge; all agree.
4. **Robustness.** The house judged again without the doubtful rules, using a new
   `house_template.EXCLUDED_RULES` context variable. It is empty by default, and the ratchet is
   unchanged: 260/389, 349 within one, 40 real errors.
5. **Raman's precedents.** His CONFIRMED conclusions on the same house, in the goldens, for charts
   sharing each feature: the lord's placement, dignity and combustion; the lord with other lords;
   the occupants; and Saturn, Mars, Sun, the nodes and Jupiter aspecting the house or its lord.
   It also lists the three most similar charts, with his words. A golden chart is never its own
   precedent.
6. **Birth-time stability.** The house re-judged at -20, -10, -5, +5, +10 and +20 minutes.

Usage: `python -m app.raman_saab.house_audit --date 1989-10-12 --time 10:02 --tz 5.5 --lat 27.23
--lon 79.03`, or `--golden NH.chart_47` to audit one of Raman's charts with his verdict printed
beside each house. All twelve houses take about one second.

## A measurement that sets how robustness is read (in-sample, descriptive)

On all 389 scored conclusions, 77 house-rows carry at least one doubtful rule. Dropping those
rules changes 14 verdicts: **4 move closer to Raman and 10 move further away.** Raman's printed
verdicts on his own charts often still count a planet by its sign. Freeing a house by the Bhava,
applied as a blanket exclusion, is therefore *not* his practice. So the robust verdict is shown
as a sensitivity flag, never as a correction, and the page and markdown say so. This also answers
follow-up (a) of the Mainpuri audit. No change to rule firing is proposed.

Rows that change: HTJAH-I.chart_12 H1, HTJAH-I.chart_61 H3, HTJAH-I.h4_04 H4, HTJAH-II.h7_01 H7,
HTJAH-II.h7_03 H7, HTJAH-II.h11_12 H11, HTJAH-II.h11_14 H11, HTJAH-II.h12_06 H12,
HTJAH-II.h9_11 H9, HTJAH-II.h9_12 H9, HTJAH-II.h9_14 H9, HTJAH-I.h6_09 H6, NH.chart_35 H1 and H10.

## Mainpuri

The 10th and 11th read favourable. Both are robust (the doubtful Ketu and sandhi-Mercury rules do
not carry them) and stable over ±20 minutes. One house is not robust: the 4th reads mixed, and
afflicted without the Rahu rules, because Rahu sits in Aquarius but in the 3rd Bhava.
