# Phase-3 — DRAFT golden validation worksheet

Generated 2026-06-25 (Item 3). The fixture carries **34 DRAFT verdicts** awaiting
user validation. Confirming a DRAFT = set `verdict_review: "CONFIRMED"` in
`tests/fixtures/raman_goldens.jsonl`; it then enters the Track-B ratchet. A DRAFT
the engine already matches becomes a CORRECT verdict (ratchet numerator + denominator
both +1); a DRAFT the engine misses adds to the denominator only.

**Your task per row:** read the cited Raman passage, confirm the recorded verdict is
Raman's actual reading (or correct it), then I flip `verdict_review` for the ones you OK.

## A. Ready to confirm — engine already matches (10 DRAFTs)

Confirming the verdicts you validate here moves the ratchet 90/130 → up to 100/140.

| # | id | house/sig | recorded verdict | engine | held? | Raman's reasoning (verdict_prose) | citations |
|---|----|-----------|------------------|--------|-------|-----------------------------------|-----------|
| 1 | h7_01 | H7/marital_happiness | **favourable** | favourable |  | Happy married life; a reverenced, learned, well-placed husband. | HTJAH-II:1687 |
| 2 | h7_06 | H7/spouse | **mixed** | mixed |  | Two wives, both alive (dwikalatra yoga) via the 7th-11th relationship from Lagna and Moon. | HTJAH-II:1918 |
| 3 | h7_12 | H7/coverture | **afflicted** | afflicted |  | A disgusting, stupid, stubborn husband; widowhood in Saturn Dasa, Saturn Bhukti. | HTJAH-II:2233 |
| 4 | h7_13 | H7/coverture | **afflicted** | afflicted |  | Husband died in Venus Bhukti, Mars Dasa — both period lords in the 12th-from-7th. | HTJAH-II:2280 |
| 5 | h7_14 | H7/spouse | **afflicted** | afflicted |  | Jara Yoga — extra-marital relations with many women, a glutton for sexual experience; the wife too carried on affairs. | HTJAH-II:2446 |
| 6 | h12_13 | H12/left_eye | **afflicted** | afflicted | ⚠️ HELD | First suffered night-blindness, then lost vision completely. | HTJAH-II:17420 |
| 7 | h12_14 | H12/left_eye | **afflicted** | afflicted |  | Totally blind — heavy affliction to Venus in both Rasi and Navamsa. | HTJAH-II:17447 |
| 8 | h9_01 | H9/father | **afflicted** | afflicted |  | Native lost his father, his guardian angel, in the Ketu Bhukti of Saturn Dasa; Kujavad-Ketu in a martian sign was the operative 9th-house period. | HTJAH-II:7638 |
| 9 | h6_02 | H6/disease_chronic | **afflicted** | afflicted |  | Unmarried lady, T.B. suspected 1947 in Rahu MD/Jupiter AD/Sun antara; died in 27th year the moment Saturn (AyushKaraka, 7th from Moon) sub-period began. Rahu with Jupiter (6th lord from Lagna) and Saturn (6th lord from Moon). | HTJAH-I:6634 |
| 10 | h6_05 | H6/enemies_disease | **afflicted** | afflicted |  | Serious smallpox in Sun MD/Moon AD. 6th lord Mars (RogaKaraka) in the 11th with malefics Saturn, Ketu and Sun; only slight relief from Jupiter's aspect. | HTJAH-I:6667 |

## B. H8 death/longevity — no verdict assigned yet (7 placeholders)

These are `verdict="DRAFT"` literals — the death-house has **0 confirmed goldens**.
You need to assign the verdict from Raman's text; the engine's current output is shown
as a starting hypothesis.

| id | name | sig | engine says | citations |
|----|------|-----|-------------|-----------|
| chart_33 | Chart 33 ayur (Pindayu = 86y 2m 20d; Aquarius Lagna 9d42') | H8/longevity | mixed | HTJAH-II:4105, HTJAH-II:4249-4260 |
| chart_34 | Chart 34 ayur (Amsayu 68y 10m 5d; actual death 15-4-1950 at 70y 3m 15d) | H8/longevity | mixed | HTJAH-II:4332, HTJAH-II:4435-4441 |
| chart_35 | Chart 35 ayur (Poornayu; died 7-2-1966 Rahu Dasa Sun Bhukti; Sagittarius Lagna) | H8/death | afflicted | HTJAH-II:4661, HTJAH-II:4844-4855 |
| chart_74 | Chart 74 (Gandhi - assassinated by a fanatic) | H8/death | mixed | HTJAH-II:6777-6819 |
| chart_73 | Chart 73 (Lincoln - assassinated, shot) | H8/death | favourable | HTJAH-II:6711-6775 |
| chart_75 | Chart 75 (Kennedy/JFK - US President shot dead) | H8/death | afflicted | HTJAH-II:6821-6869 |
| chart_78 | Chart 78 (Hitler - believed suicide) | H8/death | favourable | HTJAH-II:6959-6993 |

## C. Engine mismatch — needs engine work or verdict correction (17 DRAFTs)

The recorded DRAFT verdict differs from the engine. Mostly the over-harsh H7
marriage tail (B2/B3/B4) + H5. Listed for awareness; not ready to confirm.

| id | house/sig | recorded | engine | Raman's reasoning |
|----|-----------|----------|--------|-------------------|
| h5_13 | H5/children | mixed | afflicted | Birth of children not denied (5th lord aspected by Jupiter, PutraKaraka free of affliction); only one daughter born at the start of Ketu Dasha, living, no ot... |
| h5_14 | H5/children | mixed | afflicted | 5th house fairly well disposed but 5th lord and PutraKaraka both considerably afflicted; the native has only one daughter (miscarriages/premature births sugg... |
| h5_15 | H5/children | favourable | mixed | 5th house fairly well disposed; counting gives about 9 children — the native had 8 issues, out of which one died. |
| h5_18 | H5/children | mixed | favourable | Birth of a number of children and loss of all but one; about 10 children born, out of which only one daughter survives. |
| h7_02 | H7/spouse | afflicted | favourable | Husband was already married to another at the time; Rahu with 7th lord made him immoral. |
| h7_03 | H7/marital_happiness | mixed | afflicted | Rigid, headstrong partner; tensions and quarrels but no separation or divorce. |
| h7_04 | H7/marital_happiness | mixed | favourable | Generally happy marriage with domestic bickerings. |
| h7_05 | H7/spouse | afflicted | favourable | Two wives; a clandestine marriage before the regular one, the wife leaving on learning of the secret. |
| h7_07 | H7/coverture | mixed | afflicted | Two marriages, the second after the death of the first husband. |
| h7_09 | H7/coverture | afflicted | favourable | Early widowhood — husband drowned ten months after marriage, in Venus Bhukti of Rahu Dasa. |
| h7_10 | H7/coverture | afflicted | favourable | Death of the wife — debilitated/eclipsed 7th lord with Mars in the 8th. |
| h7_11 | H7/coverture | afflicted | mixed | A good husband, then widowed exactly a year after marriage (Ketu Bhukti, Rahu Dasa). |
| h7_15 | H7/spouse | afflicted | favourable | Disliked his wife; a profligate who contracted venereal disease — both 7th lord and Venus heavily afflicted. |
| h7_16 | H7/spouse | mixed | favourable | A duke of British royalty married a commoner divorcee, abdicating the throne — 8th (marital bond) afflicted in Rasi and Navamsa. |
| h7_17 | H7/spouse | mixed | afflicted | A Hindu married a Christian colleague — Ketu in 7th, Rahu afflicting Venus, papakartari to 8th-from-Moon. |
| h7_18 | H7/spouse | mixed | afflicted | Married a foreigner — Jupiter (9th lord) influence on karaka/7th lord Venus, with 8th afflicted in Rasi and Navamsa. |
| h7_19 | H7/spouse | mixed | favourable | A Brahmin married a Christian youth — all malefics in the 8th plus Saturn's aspect on the 7th-from-Moon. |
