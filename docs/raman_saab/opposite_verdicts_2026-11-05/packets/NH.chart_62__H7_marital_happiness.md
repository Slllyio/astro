# NH.chart_62 H7/marital_happiness

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: afflicted.

## a. Golden record

- id: `NH.chart_62`; name: Ramakrishna Dalmia; book: NH; case_type: worked_example; confidence: 0.7
- birth: {"dt": "1893-04-07T09:43:00", "tz": 5.06, "lat": 20.933, "lon": 75.917}
- cast: cast from the birth data 1893-04-07 09:43:00 (UTC+5.06)
- lagna_sign: 3
- stated_positions: none
- expected verdict: **afflicted** (marital_happiness; review CONFIRMED)
- verdict_prose: Mark the affliction of the Kalatra Bhave. 7th lord Jupiter is in the 11th with Rahu
- citations: NH:12913, NH:12915, NH:12925, NH:12941
- located in the book by the study tool: NH:12941-12942

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 0.70° Gemini | 1 | 1 |  |  |
| Sun | 26.67° Pisces | 10 | 11 | Revati 4 | Pisces |
| Moon | 1.33° Sagittarius | 7 | 7 | Moola 1 | Aries |
| Mars | 15.23° Taurus | 12 | 1 | Rohini 2 | Taurus |
| Mercury (R) | 16.02° Pisces | 10 | 11 | Uttarabhadra 4 | Scorpio |
| Jupiter | 12.04° Aries | 11 | 12 | Aswini 4 | Cancer |
| Venus | 20.10° Pisces | 10 | 11 | Revati 2 | Capricorn |
| Saturn (R) | 17.90° Virgo | 4 | 5 | Hasta 3 | Gemini |
| Rahu (R) | 8.49° Aries | 11 | 11 | Aswini 3 | Gemini |
| Ketu (R) | 8.49° Libra | 5 | 5 | Swati 1 | Sagittarius |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 62; heading at line 12826; write-up span lines 12826-12987 (162 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 12826-12987 (full write-up)

## c. The engine's view

Verdict **favourable**; degree moderate; lead frame lagna; karaka Venus; borderline_shifted False.

Count: Both outcomes are indicated: 2 rules of Raman's point for it and 1 against. On 2,000 random charts, 21% show the same for this matter (typically 1 for and 0 against).

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
| _marital_bond_gate | favourable | 1907 |  |
| _malefic_occupancy_gate | favourable | 1928 |  |
| _marginal_karaka_gate | favourable | 1974 |  |
| _yogakaraka_lagna_gate | favourable | 2017 |  |
| _powerful_dhana_kendra_floor | favourable | 1775 |  |
| _event_timing | favourable | 1870 |  |

Metadata: sav_bindus=26:average; active_periods=Jupiter(lord) 1960-1976; Venus(karaka) 1899-1919; Ketu(timer) 1893-1899; Moon(timer) 1925-1935; Mars(timer) 1935-1942

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Jupiter |
| lord_strong | True |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | 482.184 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | MARAKA_NON_DEATH_GUARD, LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 1, neutral 0, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Mercury |
| lord_strong | True |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | 482.184 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | MARAKA_NON_DEATH_GUARD |
| fired counts | benefic 2, malefic 1, neutral 0, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Mercury |
| lord_strong | True |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | 482.184 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | MARAKA_NON_DEATH_GUARD |
| fired counts | benefic 2, malefic 1, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H7.C.1** (benefic; polarity benefic; evaluable/combination; signification marital_happiness; frame LAGNA; branch fortified) cite `HTJAH-II:353`
  - reading: benefics influencing the 7th (from Lagna or Moon) → a happy marriage and a loving, fortunate wife
  - condition: `<app.raman_saab.doctrine.conditions.CountInHouse object at 0x000002038E012F90>`
  - cited lines: `HTJAH-II:350-356` (±3, Raman, natal); text in the local packet
- **H7.C.7** (benefic; polarity benefic; evaluable/combination; signification marital_happiness; frame KARAKA; branch fortified) cite `HTJAH-II:368`
  - reading: Venus exalted or in own sign (or Gopura/Vaiseshikamsa varga) → a good and beautiful wife
  - condition: `<app.raman_saab.doctrine.conditions.HasDignity object at 0x000002038EA18CB0>`
  - cited lines: `HTJAH-II:365-371` (±3, Raman, natal); text in the local packet
- **H7.K.3** (malefic; polarity malefic; evaluable/from_karaka; signification marital_happiness; frame KARAKA; branch afflicted) cite `HTJAH-II:376`
  - reading: unhappy marriage — malefics in the 7th from Venus
  - condition: `<app.raman_saab.doctrine.conditions.ClassInHouseFrom object at 0x000002038EA20E30>`
  - cited lines: `HTJAH-II:373-379` (±3, Raman, natal); text in the local packet
