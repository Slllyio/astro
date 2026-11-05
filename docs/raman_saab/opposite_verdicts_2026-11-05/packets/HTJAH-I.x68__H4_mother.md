# HTJAH-I.x68 H4/mother

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `HTJAH-I.x68`; name: Chart 68 (extracted, DRAFT); book: HTJAH-I; case_type: worked_example; confidence: 0.5
- birth: {"dt": "1896-10-13T07:56:00", "tz": 5.11, "lat": 8.8833, "lon": 76.65}
- cast: cast from the birth data 1896-10-13 07:56:00 (UTC+5.11)
- lagna_sign: 7
- stated_positions: none
- expected verdict: **afflicted** (mother; review CONFIRMED)
- verdict_prose: The aspect of Saturn, as lord of the fourth, on Matru-Karaka Moon could have been construed as beneficial but for the fact Saturn happens to be a natural malefic. The fourth is moderately strong. Matru-Karaka is feebly strong. The fourth house is considerably afflicted.
- citations: HTJAH-I:4543-4572
- located in the book by the study tool: HTJAH-I:4558-4560

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 29.73° Libra | 1 | 1 |  |  |
| Sun | 29.30° Virgo | 12 | 12 | Chitta 2 | Virgo |
| Moon | 23.24° Sagittarius | 3 | 3 | Poorvashadha 3 | Libra |
| Mars | 5.77° Gemini | 9 | 8 | Mrigasira 4 | Scorpio |
| Mercury (R) | 20.59° Virgo | 12 | 12 | Hasta 4 | Cancer |
| Jupiter | 11.81° Leo | 11 | 10 | Makha 4 | Cancer |
| Venus | 24.72° Libra | 1 | 1 | Visakha 2 | Taurus |
| Saturn | 27.11° Libra | 1 | 1 | Visakha 3 | Gemini |
| Rahu (R) | 0.40° Aquarius | 5 | 4 | Dhanishta 3 | Libra |
| Ketu (R) | 0.40° Leo | 11 | 10 | Makha 1 | Aries |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 68; heading at line 4543; write-up span lines 4543-4561 (19 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 4543-4561 (full write-up)

Cited lines outside the span: 4543-4572

## c. The engine's view

Verdict **favourable**; degree moderate; lead frame moon; karaka Moon; borderline_shifted False.

Count: Both outcomes are indicated: 1 rule of Raman's point for it and 1 against. On 2,000 random charts, 39% show the same for this matter (typically 1 for and 1 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "favourable"`) |
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "favourable"`) |
| _decide | favourable | 627 |  |
| _decisive_affliction | favourable | 1615 |  |
| _catastrophic_severity_gate | favourable | 1647 |  |
| _yoga_modulate | favourable | 1571 |  |
| _dhana_floor | favourable | 1726 |  |
| _blemishless_venus_floor | favourable | 1683 |  |
| _saptamsa_gate | favourable | 2179 |  |
| _fertility_gate | favourable | 2111 |  |
| _longevity_span | favourable | 2046 |  |
| _marital_bond_gate | favourable | 1897 |  |
| _malefic_occupancy_gate | favourable | 1928 |  |
| _marginal_karaka_gate | favourable | 1974 |  |
| _yogakaraka_lagna_gate | favourable | 2017 |  |
| _powerful_dhana_kendra_floor | favourable | 1775 |  |
| _event_timing | favourable | 1870 |  |

Metadata: varga_D12=Jupiter:own|Moon:neutral; sav_bindus=31:strong; active_periods=Venus(maraka) 1896-1901; Sun(maraka) 1901-1907; Rahu(timer) 1924-1942; Ketu(timer) 1994-2001

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Jupiter |
| lord_strong | True |
| karaka | Moon |
| karaka_strong | True |
| bhava_bala | 422.474 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 1, neutral 0, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Saturn |
| lord_strong | True |
| karaka | Moon |
| karaka_strong | True |
| bhava_bala | 422.474 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 1, malefic 1, neutral 0, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Jupiter |
| lord_strong | True |
| karaka | Moon |
| karaka_strong | True |
| bhava_bala | 422.474 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 1, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H4.L.1** (benefic; polarity benefic; evaluable/lord_in_house; signification mother_home; frame LAGNA; branch fortified) cite `HTJAH-I:4149`
  - reading: highly learned, but afraid to speak in public assemblies; likely to lose inherited wealth; born in a rich family
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038E98B9B0>`
  - cited lines: `HTJAH-I:4146-4152` (±3, Raman, natal); text in the local packet
- **H4.C.48** (malefic; polarity malefic; evaluable/combination; signification mother; frame KARAKA; branch afflicted) cite `HTJAH-I:4551`
  - reading: the Matru-Karaka Moon carries the combined contact of two or more first-rate malefics → the mother's significator is considerably afflicted
  - condition: `<app.raman_saab.doctrine.rule_sets.house_04_sukha.combinations._MatruKarakaDoublyAfflicted object at 0x000002038E98B620>`
  - cited lines: `HTJAH-I:4548-4554` (±3, Raman, natal); text in the local packet
