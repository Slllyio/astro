---
title: "The 30 real errors (distance 2) after the 2026-10-23 audit fixes"
kind: analysis
topic: validation
measured: true
updated: 2026-10-23
tags: [raman-saab, analysis, validation]
---
# The 30 real errors after the 2026-10-23 audit fixes

Supersedes the per-case list in `MISS_TABLE.md` (June 2026, 240-row corpus) for **which** rows are wrong today. The ratchet is 276/396 exact, 366/396 within one step, 30 real errors (distance 2: the engine says the opposite of Raman). The list is pinned in `tests/fixtures/golden_accuracy_baseline.json` `real_errors`; `test_no_new_real_errors` fails on any row outside it.

Mechanism tags are computed, not read: a row can carry several. They say where in the judge the verdict was decided, not why Raman disagrees; that still needs reading each chart against its cited text before any fix is designed (CLAUDE.md: re-derive before designing).

## By mechanism

| Mechanism | Rows |
|---|---|
| benefic and malefic rules both fired; the pillar count decided | 13 |
| the navamsa step moved a near miss to the opposite pole | 7 |
| none of the above; needs a per-case reading | 7 |
| the frame the engine dropped (Lagna vs Moon) gives Raman's verdict | 6 |
| a late gate (saptamsa, fertility, yoga) moved the verdict | 5 |
| book chart with stated positions only, no Shadbala | 5 |
| no rule fired; strength alone decided | 4 |

## By direction

- Raman afflicted, engine favourable: 16
- Raman favourable, engine afflicted: 14

## What the audit fixes changed

- Six rows left the list. HTJAH-II chart_73 H8 death (Lincoln) and NH chart_25 H2 speech were cleared by the navamsa guard. HTJAH-I chart_09 H1 left the scored pool because its label was the engine's abstain category. HTJAH-I chart_44 H2 wealth, NH chart_54 H9 fortune and NH chart_75 H1 self were cleared when the Bhava Bala pillar stopped voting.
- One row is a NEW real error: HTJAH-I h5_15 H5 children (Raman favourable, engine now afflicted). It was favourable while the Bhava Bala pillar voted, and flipped when that vote was withdrawn. It is pinned in the list so it stays visible.

## The rows

| Chart | House / matter | Raman | Engine | Mechanism |
|---|---|---|---|---|
| HTJAH-I.chart_17 | H1 self | favourable | afflicted | the navamsa step moved a near miss to the opposite pole, benefic and malefic rules both fired; the pillar count decided |
| HTJAH-I.chart_31 | H1 self | afflicted | favourable | the frame the engine dropped (Lagna vs Moon) gives Raman's verdict, benefic and malefic rules both fired; the pillar count decided |
| HTJAH-I.chart_60 | H3 siblings | afflicted | favourable | benefic and malefic rules both fired; the pillar count decided |
| HTJAH-I.h5_10 | H5 children | afflicted | favourable | no rule fired; strength alone decided |
| HTJAH-I.h5_15 | H5 children | favourable | afflicted | the frame the engine dropped (Lagna vs Moon) gives Raman's verdict |
| HTJAH-I.h5_16 | H5 children | favourable | afflicted | the navamsa step moved a near miss to the opposite pole, the frame the engine dropped (Lagna vs Moon) gives Raman's verdict, benefic and malefic rules both fired; the pillar count decided |
| HTJAH-I.h6_04 | H6 disease_chronic | afflicted | favourable | the navamsa step moved a near miss to the opposite pole, benefic and malefic rules both fired; the pillar count decided |
| HTJAH-I.x68 | H4 mother | afflicted | favourable | benefic and malefic rules both fired; the pillar count decided |
| HTJAH-I.x73 | H4 mother | afflicted | favourable | no rule fired; strength alone decided |
| HTJAH-I.x75 | H4 mother | favourable | afflicted | none of the above; needs a per-case reading |
| HTJAH-II.h11_01 | H11 elder_siblings | afflicted | favourable | none of the above; needs a per-case reading |
| HTJAH-II.h11_02 | H7 spouse | favourable | afflicted | a late gate (saptamsa, fertility, yoga) moved the verdict |
| HTJAH-II.h9_02 | H9 father | afflicted | favourable | the navamsa step moved a near miss to the opposite pole, benefic and malefic rules both fired; the pillar count decided |
| NH.chart_22 | H7 marital_happiness | afflicted | favourable | none of the above; needs a per-case reading |
| NH.chart_27 | H5 children | favourable | afflicted | a late gate (saptamsa, fertility, yoga) moved the verdict, benefic and malefic rules both fired; the pillar count decided |
| NH.chart_30 | H10 career | afflicted | favourable | book chart with stated positions only, no Shadbala |
| NH.chart_33 | H2 speech | favourable | afflicted | the navamsa step moved a near miss to the opposite pole, benefic and malefic rules both fired; the pillar count decided |
| NH.chart_40 | H7 marital_happiness | afflicted | favourable | none of the above; needs a per-case reading |
| NH.chart_46 | H12 moksha | favourable | afflicted | book chart with stated positions only, no Shadbala |
| NH.chart_47 | H10 career | favourable | afflicted | none of the above; needs a per-case reading |
| NH.chart_48 | H5 children | favourable | afflicted | the frame the engine dropped (Lagna vs Moon) gives Raman's verdict, book chart with stated positions only, no Shadbala, a late gate (saptamsa, fertility, yoga) moved the verdict |
| NH.chart_52 | H5 children | afflicted | favourable | the frame the engine dropped (Lagna vs Moon) gives Raman's verdict, a late gate (saptamsa, fertility, yoga) moved the verdict, benefic and malefic rules both fired; the pillar count decided |
| NH.chart_55 | H1 self | afflicted | favourable | no rule fired; strength alone decided |
| NH.chart_57 | H1 body | favourable | afflicted | the navamsa step moved a near miss to the opposite pole, the frame the engine dropped (Lagna vs Moon) gives Raman's verdict, benefic and malefic rules both fired; the pillar count decided |
| NH.chart_57 | H5 children | afflicted | favourable | no rule fired; strength alone decided |
| NH.chart_64 | H10 career | afflicted | favourable | none of the above; needs a per-case reading |
| NH.chart_65 | H2 wealth | favourable | afflicted | the navamsa step moved a near miss to the opposite pole, benefic and malefic rules both fired; the pillar count decided |
| NH.chart_73 | H2 wealth | afflicted | favourable | book chart with stated positions only, no Shadbala |
| NH.chart_74 | H5 children | favourable | afflicted | book chart with stated positions only, no Shadbala, a late gate (saptamsa, fertility, yoga) moved the verdict, benefic and malefic rules both fired; the pillar count decided |
| NH.chart_74 | H7 marital_happiness | favourable | afflicted | none of the above; needs a per-case reading |

## Addendum 2026-10-24: eight charts were not Raman's charts

The list is now **33 rows; the ratchet is 273/396 exact, 363/396 within one step.** No judge or
doctrine code changed. The drop comes from fixing the charts themselves.

**What was wrong.** 42 scored records carry a birth time but no `lagna_sign`, so the Track A
casting check never ran on them. Reading Raman's own description of each chart (which house is
which sign, who lords what, where the lords sit) gave his Lagna for 24 of them. 16 matched the
cast. **8 did not**: the engine had been judging a chart Raman never judged.

| Record | Raman's Lagna | Cast Lagna | Re-timed | Scored row before -> after |
|---|---|---|---|---|
| x65 | Aries | Taurus 1.0 | -6 min | H4 mother: matched -> **inversion** |
| x79 | Libra | Scorpio 1.8 | -13 min | H4 education: matched -> matched |
| chart_42 | Capricorn | Aquarius 2.9 | -13 min | H2 wealth: matched -> **inversion** |
| chart_46 | Cancer | Leo 4.4 | -21 min | H2 wealth: one step out -> one step out |
| h6_02 | Cancer | Gemini 28.4 | +10 min | H6 disease: matched -> matched |
| h6_05 | Scorpio | Libra 29.4 | +5 min | H6 enemies/disease: matched -> **inversion** |
| x75 | Virgo | Libra 11.2 | -48 min | H4 mother: inversion -> inversion |
| x93 | Sagittarius | Libra 29.7 | +135 min | H5 children: matched -> matched |

**The fix.** Each was re-timed to the smallest shift that puts the Lagna 0.5 degrees inside
Raman's sign, following the HTJAH-I.chart_35 precedent, and the re-timed chart was then checked
against every feature Raman quotes for it. All eight reproduce his description in full,
including x75 and x93 where the printed time is far off (most likely misprinted or misread
times). `birth.rectified` on each record holds the evidence and line citations. `lagna_sign` is
now set on all 24, so Track A guards them from here on.

**Why the score fell, and why that is right.** On Raman's own charts, three rows the engine used
to match (x65 H4, chart_42 H2, h6_05 H6) become inversions. Those matches were produced by the
wrong chart. Keeping them would be the overfitting the Prime Directive forbids.

**Also fixed.** x93's verdict prose quoted Chart 94's conclusion. It now quotes Chart 93's own
(HTJAH-I:5669-5670). The verdict is unchanged, since both say no children.

**Still unchecked.** 18 of the 42 have no Lagna that can be read off the text (OCR-garbled chart
diagrams or no house named). They are listed by the 2026-10-24 checker run and stay as they are.

**Also measured the same day, nothing shipped:** letting Raman's influence axis (who joins and
aspects a planet) vote in the verdict. Pre-registered in DISPOSITION_PILLAR_PREREG.md; it raised
real errors 30 -> 38, so it does not bring the engine closer to Raman.
