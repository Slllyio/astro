# HTJAH-I.h6_04 H6/disease_chronic

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: mixed.

## a. Golden record

- id: `HTJAH-I.h6_04`; name: Chart 112 (H6 disease_chronic); book: HTJAH-I; case_type: worked_example; confidence: 0.65
- birth: {"dt": "1912-06-15T05:23:00", "tz": 5.5, "lat": 25.383, "lon": 86.517}
- cast: cast from the birth data 1912-06-15 05:23:00 (UTC+5.5)
- lagna_sign: 3
- stated_positions: none
- expected verdict: **afflicted** (disease_chronic; review CONFIRMED)
- verdict_prose: Myopia. 6th lord Mars in the 2nd (vision); 2nd lord Moon (ruler of the eyes) in the 12th with Saturn (8th lord).
- citations: HTJAH-I:6664
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 8.40° Gemini | 1 | 1 |  |  |
| Sun | 2.31° Gemini | 1 | 1 | Mrigasira 3 | Libra |
| Moon | 28.54° Taurus | 12 | 1 | Mrigasira 2 | Virgo |
| Mars | 19.29° Cancer | 2 | 3 | Aslesha 1 | Sagittarius |
| Mercury | 29.20° Taurus | 12 | 1 | Mrigasira 2 | Virgo |
| Jupiter (R) | 17.65° Scorpio | 6 | 6 | Jyeshta 1 | Sagittarius |
| Venus | 26.52° Taurus | 12 | 1 | Mrigasira 1 | Leo |
| Saturn | 6.29° Taurus | 12 | 12 | Krittika 3 | Aquarius |
| Rahu (R) | 27.13° Pisces | 10 | 11 | Revati 4 | Pisces |
| Ketu (R) | 27.13° Virgo | 4 | 5 | Chitta 2 | Virgo |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 112; heading at line 6658; write-up span lines 6658-6666 (9 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 6658-6666 (full write-up)

## c. The engine's view

Verdict **favourable**; degree mild; lead frame moon; karaka Saturn; borderline_shifted True.

Count: Both outcomes are indicated: 1 rule of Raman's point for it and 1 against. On 2,000 random charts, 19% show the same for this matter (typically 0 for and 1 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | favourable | 561 |  |
| _decide_clauses | favourable | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "mixed"`) |
| _navamsa_modulate | mixed | 564 |  |
| _decide_clauses | mixed | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "mixed"`) |
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

Metadata: sav_bindus=22:weak; active_periods=Venus(lord) 1993-2013; Saturn(karaka) 1950-1969; Mars(timer) 1912-1916; Rahu(timer) 1916-1934; Jupiter(timer) 1934-1950

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Venus |
| lord_strong | True |
| karaka | Saturn |
| karaka_strong | False |
| bhava_bala | 405.509 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | AFFLICTION_MATTER, LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 1, neutral 1, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Mars |
| lord_strong | True |
| karaka | Saturn |
| karaka_strong | False |
| bhava_bala | 405.509 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | AFFLICTION_MATTER, LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 1, neutral 1, blemish 0 |

### Fired rules (lead frame)

- **H6.P.Jupiter** (benefic; polarity benefic; evaluable/planet_in_house; signification enemies_disease; frame LAGNA; branch general) cite `HTJAH-I:6138`
  - reading: inactive, suffers disrespect, indulges in black magic, feared by enemies, unlucky, dyspeptic, health generally good
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EA18590>`
  - cited lines: `HTJAH-I:6135-6141` (±3, Raman, natal); text in the local packet
- **H6.L.2** (malefic; polarity malefic; evaluable/lord_in_house; signification enemies_disease; frame LAGNA; branch afflicted) cite `HTJAH-I:6007`
  - reading: the 6th lord weak and otherwise ill-disposed in the 2nd - loss of wife in the Dasha or Bhukti of the malefic lord
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA13530>`
  - cited lines: `HTJAH-I:6004-6010` (±3, Raman, natal); text in the local packet
- **H6.L.2b** (neutral; polarity neutral; evaluable/lord_in_house; signification enemies_disease; frame KARAKA; branch general) cite `HTJAH-I:6010`
  - reading: Venus weak - the native will be a celibate and poverty stricken, just able to get a morsel of food when hungry
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA13CE0>`
  - cited lines: `HTJAH-I:6007-6013` (±3, Raman, natal); text in the local packet
