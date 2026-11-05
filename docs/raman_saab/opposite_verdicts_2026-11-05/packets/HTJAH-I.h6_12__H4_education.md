# HTJAH-I.h6_12 H4/education

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `HTJAH-I.h6_12`; name: Chart 121 (H6 enemies); book: HTJAH-I; case_type: worked_example; confidence: 0.6
- birth: {"dt": "1908-03-16T10:56:00", "tz": 5.5, "lat": 15.4, "lon": 75.65}
- cast: cast from the birth data 1908-03-16 10:56:00 (UTC+5.5)
- lagna_sign: 2
- stated_positions: none
- expected verdict: **afflicted** (education; review CONFIRMED)
- verdict_prose: It is the Vidya-Karaka that is really strong. The natives’ general education in the sense of school knowledge is poor. His knowledge of English is almost nil. This is indicated by the Sun's (lord of the fourth) conjunction with Saturn. But, however, his grasp of the current political, social and international problems is unique. He is educated in the sense that he has learnt things by self-study and not by going to college or school. Above we have given six charts bearing on education and learning. Each combination is capable of producing a variety of effects consistent with the ownershi
- citations: HTJAH-I:6937
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 17.47° Taurus | 1 | 1 |  |  |
| Sun | 4.11° Pisces | 11 | 11 | Uttarabhadra 1 | Leo |
| Moon | 13.03° Leo | 4 | 4 | Makha 4 | Cancer |
| Mars | 24.04° Aries | 12 | 12 | Bharani 4 | Scorpio |
| Mercury | 9.89° Aquarius | 10 | 10 | Satabhisha 1 | Sagittarius |
| Jupiter (R) | 12.77° Cancer | 3 | 3 | Pushya 3 | Libra |
| Venus | 15.71° Aries | 12 | 12 | Bharani 1 | Leo |
| Saturn | 8.46° Pisces | 11 | 11 | Uttarabhadra 2 | Virgo |
| Rahu (R) | 19.37° Gemini | 2 | 2 | Aridra 4 | Pisces |
| Ketu (R) | 19.37° Sagittarius | 8 | 8 | Poorvashadha 2 | Virgo |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 121; heading at line 6940; write-up span lines 6937-6944 (8 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 6937-6944 (full write-up)

## c. The engine's view

Verdict **favourable**; degree strong; lead frame lagna; karaka Jupiter; borderline_shifted False.

Count: Only favourable indications: 3 rules for, none against. On 2,000 random charts, 41% show the same for this matter (typically 2 for and 1 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 769 | 5. clean strength + supportive bhava + no malefic -> favourable. (`base = "mixed" if (C2_OBSTRUCTED_CARRIER and L.lord_obstructed) else "favourable"`) |
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 769 | 5. clean strength + supportive bhava + no malefic -> favourable. (`base = "mixed" if (C2_OBSTRUCTED_CARRIER and L.lord_obstructed) else "favourable"`) |
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

Metadata: varga_D12=Sun:exalt|Jupiter:own; sav_bindus=22:weak; active_periods=Sun(lord) 1928-1934; Jupiter(karaka) 1969-1985; Ketu(timer) 1908-1908; Moon(timer) 1934-1944; Mars(timer) 1944-1951

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Sun |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 587.409 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 3, malefic 0, neutral 1, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Mars |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 587.409 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 3, malefic 0, neutral 1, blemish 0 |

### Fired rules (lead frame)

- **H4.P.Moon** (benefic; polarity benefic; evaluable/planet_in_house; signification mother_home; frame LAGNA; branch fortified) cite `HTJAH-I:4245`
  - reading: the Moon fortified, that is well aspected or conjoined -> mental peace
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EA0C9E0>`
  - cited lines: `HTJAH-I:4242-4248` (±3, Raman, natal); text in the local packet
- **H4.C.40** (benefic; polarity benefic; evaluable/combination; signification education; frame LAGNA; branch fortified) cite `HTJAH-I:4919`
  - reading: Jupiter exalted, or in the 2nd/9th/5th/10th → great learning in the Vedas and scriptures
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038E98AD50>`
  - cited lines: `HTJAH-I:4916-4922` (±3, Raman, natal); text in the local packet
- **H4.C.50** (benefic; polarity benefic; evaluable/combination; signification education; frame KARAKA; branch fortified) cite `NH:4963`
  - reading: the Gnanakaraka Jupiter aspecting the lord of the 4th → learning is fortified; the mind is not left dull
  - condition: `<app.raman_saab.doctrine.rule_sets.house_04_sukha.combinations._JupiterAspectsFourthLord object at 0x000002038E98B770>`
  - cited lines: `NH:4960-4966` (±3, Raman, natal); text in the local packet
- **H4.L.11** (neutral; polarity neutral; evaluable/lord_in_house; signification mother_home; frame LAGNA; branch fortified) cite `HTJAH-I:4184`
  - reading: self-made, generous, sickly; the mother fortunate, but he may have a step-mother also; favours success in selling and buying cattle and lands
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA0C710>`
  - cited lines: `HTJAH-I:4181-4187` (±3, Raman, natal); text in the local packet
