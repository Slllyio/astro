# HTJAH-I.chart_60 H3/siblings

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: mixed.

## a. Golden record

- id: `HTJAH-I.chart_60`; name: Chart 60 (Sagittarius 3rd, Jupiter lord well-disposed but Karaka+house afflicted, no brothers); book: HTJAH-I; case_type: worked_example; confidence: 0.5
- birth: {"dt": "1896-10-21T06:00:00", "tz": 5.2022, "lat": 9.9667, "lon": 78.0333}
- cast: cast from the birth data 1896-10-21 06:00:00 (UTC+5.2022)
- lagna_sign: 7
- stated_positions: none
- expected verdict: **afflicted** (siblings; review CONFIRMED)
- verdict_prose: Though Jupiter (the third lord) is well-disposed in the horoscope, the Karaka Mars and the third house are subject to affliction; the native has no brothers.
- citations: HTJAH-I:3802-3816
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 9.04° Libra | 1 | 1 |  |  |
| Sun | 7.17° Libra | 1 | 1 | Swati 1 | Sagittarius |
| Moon | 0.15° Aries | 7 | 7 | Aswini 1 | Aries |
| Mars | 7.41° Gemini | 9 | 9 | Aridra 1 | Sagittarius |
| Mercury | 19.51° Virgo | 12 | 12 | Hasta 3 | Gemini |
| Jupiter | 13.18° Leo | 11 | 11 | Makha 4 | Cancer |
| Venus | 4.47° Scorpio | 2 | 2 | Anuradha 1 | Leo |
| Saturn | 28.00° Libra | 1 | 2 | Visakha 3 | Gemini |
| Rahu (R) | 29.98° Capricorn | 4 | 5 | Dhanishta 2 | Virgo |
| Ketu (R) | 29.98° Cancer | 10 | 11 | Aslesha 4 | Pisces |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 60; heading at line 3792; write-up span lines 3792-3817 (26 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 3792-3817 (full write-up)

## c. The engine's view

Verdict **favourable**; degree moderate; lead frame moon; karaka Mars; borderline_shifted False.

Count: Both outcomes are indicated: 4 rules of Raman's point for it and 1 against. On 2,000 random charts, 94% show the same for this matter (typically 4 for and 3 against).

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

Metadata: sav_bindus=26:average; active_periods=Mercury(lord) 1999-2016; Mars(karaka) 1939-1946; Ketu(timer) 1896-1903; Rahu(timer) 1946-1964; Jupiter(timer) 1964-1980

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Mercury |
| lord_strong | True |
| karaka | Mars |
| karaka_strong | True |
| bhava_bala | 570.44 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 4, malefic 1, neutral 0, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Jupiter |
| lord_strong | True |
| karaka | Mars |
| karaka_strong | True |
| bhava_bala | 570.44 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 4, malefic 1, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H3.L.11** (benefic; polarity benefic; evaluable/lord_in_house; signification siblings; frame LAGNA; branch general) cite `HTJAH-I:3351`
  - reading: not a very good combination; earnings with effort; becomes vindictive; the body unattractive and emaciated; subservient to or dependent upon others, and liable to frequent attacks of illness
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038E988AA0>`
  - cited lines: `HTJAH-I:3348-3354` (±3, Raman, natal); text in the local packet
- **H3.C.1** (benefic; polarity benefic; evaluable/combination; signification siblings; frame LAGNA; branch fortified) cite `HTJAH-I:3351`
  - reading: the 3rd lord well-disposed in the 3rd, 6th or 11th -> a number of younger brothers
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038E9852E0>`
  - cited lines: `HTJAH-I:3348-3354` (±3, Raman, natal); text in the local packet
- **H3.C.7** (benefic; polarity benefic; evaluable/combination; signification siblings; frame LAGNA; branch fortified) cite `HTJAH-I:3430`
  - reading: good (benefic) planets residing in or aspecting the 3rd -> he will get many brothers (same when Mars and the 3rd house are similarly well situated)
  - condition: `<app.raman_saab.doctrine.rule_sets.house_03_sahaja.combinations._BeneficOccupiesOrAspects3rd object at 0x000002038E985A60>`
  - cited lines: `HTJAH-I:3427-3433` (±3, Raman, natal); text in the local packet
- **H3.C.8** (benefic; polarity benefic; evaluable/combination; signification siblings; frame LAGNA/KARAKA/D9; branch fortified) cite `HTJAH-I:3432`
  - reading: the 3rd lord or Mars in exaltation, own house, own Navamsha, or the Navamsha of benefics -> an increase in brothers may be expected
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038E985BE0>`
  - cited lines: `HTJAH-I:3429-3435` (±3, Raman, natal); text in the local packet
- **H3.C.35** (malefic; polarity malefic; evaluable/combination; signification siblings; frame LAGNA; branch afflicted) cite `HTJAH-I:3430`
  - reading: natural malefic planets aspecting the 3rd -> few brothers (inverse of #7: benefic aspect/occupation strengthens the 3rd; malefic aspect weakens it)
  - condition: `<app.raman_saab.doctrine.rule_sets.house_03_sahaja.combinations._MaleficAspects3rd object at 0x000002038E9872C0>`
  - cited lines: `HTJAH-I:3427-3433` (±3, Raman, natal); text in the local packet
