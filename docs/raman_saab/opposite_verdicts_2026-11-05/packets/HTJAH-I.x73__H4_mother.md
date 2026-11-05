# HTJAH-I.x73 H4/mother

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `HTJAH-I.x73`; name: Chart 73 (extracted, DRAFT); book: HTJAH-I; case_type: worked_example; confidence: 0.5
- birth: {"dt": "1891-01-05T12:30:00", "tz": 4.8544, "lat": 18.9, "lon": 72.8167}
- cast: cast from the birth data 1891-01-05 12:30:00 (UTC+4.8544)
- lagna_sign: 1
- stated_positions: none
- expected verdict: **afflicted** (mother; review CONFIRMED)
- verdict_prose: The fourth house is not much afflicted, but the lord and Karaka are moderately blemished. The native lost his mother in Saturn Dasha Venus Bhukti. Saturn is in a Maraka from the fourth and Venus is in a Maraka from the Moon.
- citations: HTJAH-I:4646-4656
- located in the book by the study tool: HTJAH-I:4656-4658

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 6.93° Aries | 1 | 1 |  |  |
| Sun | 23.84° Sagittarius | 9 | 10 | Poorvashadha 4 | Scorpio |
| Moon | 15.47° Libra | 7 | 7 | Swati 3 | Aquarius |
| Mars | 23.54° Aquarius | 11 | 12 | Poorvabhadra 2 | Taurus |
| Mercury (R) | 9.56° Capricorn | 10 | 10 | Uttarashadha 4 | Pisces |
| Jupiter | 24.56° Capricorn | 10 | 11 | Dhanishta 1 | Leo |
| Venus | 16.07° Scorpio | 8 | 8 | Anuradha 4 | Scorpio |
| Saturn (R) | 26.23° Leo | 5 | 6 | Pubba 4 | Scorpio |
| Rahu (R) | 22.10° Taurus | 2 | 3 | Rohini 4 | Cancer |
| Ketu (R) | 22.10° Scorpio | 8 | 9 | Jyeshta 2 | Capricorn |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 73; heading at line 4646; write-up span lines 4646-4659 (14 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 4646-4659 (full write-up)

## c. The engine's view

Verdict **favourable**; degree strong; lead frame lagna; karaka Moon; borderline_shifted False.

Count: No rule of Raman's speaks for or against this matter in this chart. On 2,000 random charts, 9% show the same for this matter (typically 1 for and 1 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 769 | 5. clean strength + supportive bhava + no malefic -> favourable. (`base = "mixed" if (C2_OBSTRUCTED_CARRIER and L.lord_obstructed) else "favourable"`) |
| _decide | favourable | 622 |  |
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

Metadata: sav_bindus=24:weak; active_periods=Rahu(maraka) 1891-1897; Saturn(maraka) 1913-1932; Moon(karaka) 1982-1992; Jupiter(timer) 1897-1913

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Moon |
| lord_strong | True |
| karaka | Moon |
| karaka_strong | True |
| bhava_bala | 429.159 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | False |
| lord_karaka_identical | True |
| lord_hard_afflicted | False |
| flags | LORD_KARAKA_IDENTITY |
| fired counts | benefic 0, malefic 0, neutral 2, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Saturn |
| lord_strong | True |
| karaka | Moon |
| karaka_strong | True |
| bhava_bala | 429.159 |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 0, malefic 0, neutral 2, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Saturn |
| lord_strong | True |
| karaka | Moon |
| karaka_strong | True |
| bhava_bala | 429.159 |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 0, malefic 0, neutral 2, blemish 0 |

### Fired rules (lead frame)

- **H4.L.7** (neutral; polarity neutral; evaluable/lord_in_house; signification mother_home; frame LAGNA; branch fortified) cite `HTJAH-I:4168`
  - reading: generally happy; commands houses and lands
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038E98BF20>`
  - cited lines: `HTJAH-I:4165-4171` (±3, Raman, natal); text in the local packet
- **H4.L.7a** (neutral; polarity neutral; evaluable/lord_in_house; signification mother_home; frame LAGNA; branch general) cite `HTJAH-I:4168`
  - reading: the 4th lord in the 7th in a movable sign - ekes out a livelihood in distant places
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA0C0E0>`
  - cited lines: `HTJAH-I:4165-4171` (±3, Raman, natal); text in the local packet
