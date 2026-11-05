# HTJAH-II.h11_02 H7/spouse

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `HTJAH-II.h11_02`; name: Chart 211 (H11 elder_siblings); book: HTJAH-II; case_type: worked_example; confidence: 0.6
- birth: {"dt": "1940-05-21T07:50:00", "tz": 5.5, "lat": 13, "lon": 77.583}
- cast: cast from the birth data 1940-05-21 07:50:00 (UTC+5.5)
- lagna_sign: 3
- stated_positions: none
- expected verdict: **favourable** (spouse; review CONFIRMED)
- verdict_prose: There is a preponderance of benefice influences on the 7th house due to the aspect of two benefices, Jupiter and Venus, on it. Venus is not only a benefice lord but also the KalatraKaraka and so his aspect on the 7th house becomes quite desirable. The aspect of Mars on the 7th is not so welcome since he happens to be the ruler of malefic Bhr vas, but his maleficence is kept in check by the aspect of 9th lord neechabhanga Saturn. The native has a happy married life. The aspect of 7th lord Jupiter on the 7th and of Karaka Venus also on it have given the native a devoted wife. The Seventh
- citations: HTJAH-II:14835, HTJAH-II:1638-1680
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 5.58° Gemini | 1 | 1 |  |  |
| Sun | 8.30° Taurus | 12 | 12 | Krittika 4 | Pisces |
| Moon | 2.05° Scorpio | 6 | 6 | Visakha 4 | Cancer |
| Mars | 10.67° Gemini | 1 | 1 | Aridra 2 | Capricorn |
| Mercury | 7.36° Taurus | 12 | 12 | Krittika 4 | Pisces |
| Jupiter | 9.50° Aries | 11 | 11 | Aswini 3 | Gemini |
| Venus | 17.66° Gemini | 1 | 1 | Aridra 4 | Pisces |
| Saturn | 16.11° Aries | 11 | 11 | Bharani 1 | Leo |
| Rahu (R) | 26.50° Virgo | 4 | 5 | Chitta 1 | Leo |
| Ketu (R) | 26.50° Pisces | 10 | 11 | Revati 3 | Aquarius |

## b. Raman's write-up

File: `how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md`. Chart number 211; heading at line 14841; write-up span lines 14816-14915 (100 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 14816-14915 (full write-up)

Cited lines outside the span: 1638-1680

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame moon; karaka Venus; borderline_shifted True.

Count: Only unfavourable indications: 1 rule against, none for. On 2,000 random charts, 17% show the same for this matter (typically 1 for and 1 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | mixed | 564 |  |
| _decide_clauses | mixed | 769 | 8. everything else is a genuine borderline -> mixed. (`base = "mixed"`) |
| _navamsa_modulate | mixed | 564 |  |
| _decide_clauses | mixed | 769 | 8. everything else is a genuine borderline -> mixed. (`base = "mixed"`) |
| _decide | mixed | 627 |  |
| _decisive_affliction | afflicted | 1615 |  |
| _catastrophic_severity_gate | afflicted | 1647 |  |
| _yoga_modulate | afflicted | 1571 |  |
| _dhana_floor | afflicted | 1726 |  |
| _blemishless_venus_floor | afflicted | 1683 |  |
| _saptamsa_gate | afflicted | 2179 |  |
| _fertility_gate | afflicted | 2111 |  |
| _longevity_span | afflicted | 2046 |  |
| _marital_bond_gate | afflicted | 1897 |  |
| _malefic_occupancy_gate | afflicted | 1928 |  |
| _marginal_karaka_gate | afflicted | 1978 |  |
| _yogakaraka_lagna_gate | afflicted | 2017 |  |
| _powerful_dhana_kendra_floor | afflicted | 1775 |  |
| _event_timing | afflicted | 1870 |  |

Metadata: sav_bindus=23:weak; active_periods=Jupiter(maraka) 1940-1941; Saturn(maraka) 1941-1960; Ketu(timer) 1977-1984; Rahu(timer) 2027-2045

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Venus |
| lord_strong | True |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | 506.065 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | True |
| lord_hard_afflicted | False |
| flags | LORD_KARAKA_IDENTITY |
| fired counts | benefic 0, malefic 1, neutral 3, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Jupiter |
| lord_strong | True |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | 506.065 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 1, neutral 3, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Jupiter |
| lord_strong | True |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | 506.065 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 1, neutral 3, blemish 0 |

### Fired rules (lead frame)

- **H7.C.86** (malefic; polarity malefic; evaluable/combination; signification spouse; frame LAGNA; branch afflicted) cite `HTJAH-II:1773`
  - reading: the 7th lord heavily afflicted (conjunct a node and malefic-aspected, or hemmed by papakartari) → a vitiated spouse / disharmonious marriage
  - condition: `<app.raman_saab.doctrine.rule_sets.house_07_kalatra.combinations._SeventhLordAfflictedVitiatesSpouse object at 0x000002038EA201D0>`
  - cited lines: `HTJAH-II:1770-1776` (±3, Raman, natal); text in the local packet
- **H7.L.11** (neutral; polarity neutral; evaluable/lord_in_house; signification spouse; frame LAGNA; branch fortified) cite `HTJAH-II:323`
  - reading: there may be more than one marriage or the native may associate with many women
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA22FC0>`
  - cited lines: `HTJAH-II:320-326` (±3, Raman, natal); text in the local packet
- **H7.L.11b** (neutral; polarity neutral; evaluable/lord_in_house; signification spouse; frame LAGNA; branch general) cite `HTJAH-II:326`
  - reading: the 7th lord afflicted - the native may marry more than once, but one wife may outlive him
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA23350>`
  - cited lines: `HTJAH-II:323-329` (±3, Raman, natal); text in the local packet
- **H7.C.38** (neutral; polarity neutral; evaluable/combination; signification spouse; frame LAGNA; branch afflicted) cite `HTJAH-II:484`
  - reading: the 7th sign (and Venus) in common (dual) signs → marries at least twice (the strongest dual-sign remarriage signature; the 7th-lord-in-dual-Navamsa refinement is kept in text)
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA1A0F0>`
  - cited lines: `HTJAH-II:481-487` (±3, Raman, natal); text in the local packet
