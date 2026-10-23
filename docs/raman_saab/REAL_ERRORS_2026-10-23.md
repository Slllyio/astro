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
