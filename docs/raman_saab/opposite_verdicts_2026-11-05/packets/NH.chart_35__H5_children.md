# NH.chart_35 H5/children

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `NH.chart_35`; name: Rabindranath Tagore; book: NH; case_type: worked_example; confidence: 0.3
- birth: {"dt": "1861-05-07T02:51:00", "tz": 5.9, "lat": 22.67, "lon": 88.5}
- cast: cast from the birth data 1861-05-07 02:51:00 (UTC+5.9)
- lagna_sign: 12
- stated_positions: none
- expected verdict: **afflicted** (children; review CONFIRMED)
- verdict_prose: The position of Jupiter in the 5th or house of intelligence in exaltation made Tagore an intellectual giant.
- citations: NH:7887, NH:7897, NH:7904, NH:7915, NH:7939
- located in the book by the study tool: NH:7887-7889

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 6.12° Pisces | 1 | 1 |  |  |
| Sun | 25.78° Aries | 2 | 3 | Bharani 4 | Scorpio |
| Moon | 21.98° Pisces | 1 | 2 (sandhi) | Revati 2 | Capricorn |
| Mars | 1.59° Gemini | 4 | 4 | Mrigasira 3 | Libra |
| Mercury | 9.28° Aries | 2 | 2 | Aswini 3 | Gemini |
| Jupiter | 27.39° Cancer | 5 | 6 | Aslesha 4 | Pisces |
| Venus | 24.50° Aries | 2 | 3 | Bharani 4 | Scorpio |
| Saturn | 12.19° Leo | 6 | 6 | Makha 4 | Cancer |
| Rahu (R) | 26.29° Sagittarius | 10 | 11 | Poorvashadha 4 | Scorpio |
| Ketu (R) | 26.29° Gemini | 4 | 5 | Punarvasu 2 | Taurus |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 35; heading at line 7818; write-up span lines 7818-7979 (162 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 7818-7979 (full write-up)

## c. The engine's view

Verdict **favourable**; degree strong; lead frame lagna; karaka Jupiter; borderline_shifted False.

Count: Only favourable indications: 4 rules for, none against. On 2,000 random charts, 11% show the same for this matter (typically 2 for and 2 against).

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
| _saptamsa_gate | favourable | 2197 |  |
| _fertility_gate | favourable | 2124 |  |
| _longevity_span | favourable | 2046 |  |
| _marital_bond_gate | favourable | 1897 |  |
| _malefic_occupancy_gate | favourable | 1928 |  |
| _marginal_karaka_gate | favourable | 1974 |  |
| _yogakaraka_lagna_gate | favourable | 2017 |  |
| _powerful_dhana_kendra_floor | favourable | 1775 |  |
| _event_timing | favourable | 1870 |  |

Metadata: saptamsa=neutral; beeja_kshetra=numeric_strong; varga_D7=Moon:neutral|Jupiter:exalt; sav_bindus=20:weak; active_periods=Moon(lord) 1904-1914; Jupiter(karaka) 1939-1955; Ketu(timer) 1871-1878; Rahu(timer) 1921-1939

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Moon |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 557.367 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 4, malefic 0, neutral 2, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Moon |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 557.367 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 4, malefic 0, neutral 2, blemish 0 |

### Fired rules (lead frame)

- **H5.P.Jupiter** (benefic; polarity benefic; evaluable/planet_in_house; signification children; frame LAGNA; branch general) cite `HTJAH-I:5248`
  - reading: learned in logic, law and mantrasastra; highly intelligent; a preceptor or adviser to a king; great discrimination; good friends, vehicles and decorous manners; many children; god-fearing and happy
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EA10650>`
  - cited lines: `HTJAH-I:5245-5251` (±3, Raman, natal); text in the local packet
- **H5.C.1** (benefic; polarity benefic; evaluable/combination; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5183`
  - reading: benefic associations or aspects on the 5th → there will be children
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EA0D040>`
  - cited lines: `HTJAH-I:5180-5186` (±3, Raman, natal); text in the local packet
- **H5.C.2** (benefic; polarity benefic; evaluable/combination; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5184`
  - reading: Lagna-lord in the 5th (with a strong 5th lord), or 1st-5th lord exchange → favours birth of children
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EA0D220>`
  - cited lines: `HTJAH-I:5181-5187` (±3, Raman, natal); text in the local packet
- **H5.C.32** (benefic; polarity benefic; evaluable/combination; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5214`
  - reading: the 5th lord in the Lagna AND the Lagna lord in the 5th → an obedient child
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA0F170>`
  - cited lines: `HTJAH-I:5211-5217` (±3, Raman, natal); text in the local packet
- **H5.L.1** (neutral; polarity neutral; evaluable/lord_in_house; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5112`
  - reading: commands servants; Judge / Magistrate / Minister empowered to punish the evil-minded; earns grace of God; few children; will have foes; gives happiness to others
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038E987800>`
  - cited lines: `HTJAH-I:5109-5115` (±3, Raman, natal); text in the local packet
- **H5.C.21** (neutral; polarity neutral; evaluable/combination; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5206`
  - reading: 5th lord in the 1st, 2nd or 3rd → the first child will be male
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EA0E510>`
  - cited lines: `HTJAH-I:5203-5209` (±3, Raman, natal); text in the local packet
