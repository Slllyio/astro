# HTJAH-I.x65 H4/mother

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: afflicted.

## a. Golden record

- id: `HTJAH-I.x65`; name: Chart 65 (extracted, DRAFT); book: HTJAH-I; case_type: worked_example; confidence: 0.5
- birth: {"dt": "1914-11-16T16:54:00", "tz": 4.5833, "lat": 27.9167, "lon": 68.75, "rectified": "Raman: 4th Cancer aspected by debilitated Jupiter; 4th lord Moon in the 7th with Mercury lord of the 3rd and 6th; Mars in the 2nd from the Moon with the Sun (HTJAH-I:4465-4475) -> Aries Lagna. The printed 5 p.m. casts Taurus 1.0deg (Swiss Ephemeris, Raman ayanamsa). Re-timed -6 min from the printed 17:00 to the smallest shift that puts the Lagna 0.5deg inside Raman's sign, after the HTJAH-I.chart_35 precedent; the re-timed chart was checked against every feature quoted (2026-10-24)."}
- cast: cast from the birth data 1914-11-16 16:54:00 (UTC+4.5833)
- lagna_sign: 1
- stated_positions: none
- expected verdict: **afflicted** (mother; review CONFIRMED)
- verdict_prose: The fourth house is moderately strong, but the lord and the Karaka are considerably afflicted. Hence the native lost his mother very early. Fourth Bhava-—In
- citations: HTJAH-I:4465-4485
- located in the book by the study tool: HTJAH-I:4485-4488

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 29.29° Aries | 1 | 1 |  |  |
| Sun | 2.08° Scorpio | 8 | 7 | Visakha 4 | Cancer |
| Moon | 15.57° Libra | 7 | 7 | Swati 3 | Aquarius |
| Mars | 12.43° Scorpio | 8 | 8 (sandhi) | Anuradha 3 | Libra |
| Mercury (R) | 15.75° Libra | 7 | 7 | Swati 3 | Aquarius |
| Jupiter | 23.54° Capricorn | 10 | 10 | Dhanishta 1 | Leo |
| Venus (R) | 19.30° Scorpio | 8 | 8 | Jyeshta 1 | Sagittarius |
| Saturn (R) | 10.19° Gemini | 3 | 3 | Aridra 2 | Capricorn |
| Rahu (R) | 10.26° Aquarius | 11 | 11 | Satabhisha 2 | Capricorn |
| Ketu (R) | 10.26° Leo | 5 | 5 | Makha 4 | Cancer |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 65; heading at line 4465; write-up span lines 4465-4487 (23 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 4465-4487 (full write-up)

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

Metadata: sav_bindus=28:average; active_periods=Saturn(maraka) 1936-1955; Mercury(maraka) 1955-1972; Moon(karaka) 2005-2015; Rahu(timer) 1914-1920; Jupiter(timer) 1920-1936

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Moon |
| lord_strong | True |
| karaka | Moon |
| karaka_strong | True |
| bhava_bala | 439.301 |
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
| bhava_bala | 439.301 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
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
| bhava_bala | 439.301 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
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
