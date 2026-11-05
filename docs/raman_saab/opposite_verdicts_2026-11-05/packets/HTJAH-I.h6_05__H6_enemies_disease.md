# HTJAH-I.h6_05 H6/enemies_disease

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: afflicted.

## a. Golden record

- id: `HTJAH-I.h6_05`; name: Chart 113 (H6 enemies_disease); book: HTJAH-I; case_type: worked_example; confidence: 0.4
- birth: {"dt": "1893-10-07T08:35:00", "tz": 5.481, "lat": 16.95, "lon": 82.217, "rectified": "Raman: the 6th lord Mars, also RogaKaraka, in the 11th with Saturn, Ketu and the Sun, aspected by Jupiter (HTJAH-I:6667-6670) -> Scorpio Lagna. The printed 8-30 a.m. casts Libra 29.4deg. Re-timed +5 min from the printed 08:30 to the smallest shift that puts the Lagna 0.5deg inside Raman's sign, after the HTJAH-I.chart_35 precedent; the re-timed chart was checked against every feature quoted (2026-10-24)."}
- cast: cast from the birth data 1893-10-07 08:35:00 (UTC+5.481)
- lagna_sign: 8
- stated_positions: none
- expected verdict: **afflicted** (enemies_disease; review CONFIRMED)
- verdict_prose: Serious smallpox in Sun MD/Moon AD. 6th lord Mars (RogaKaraka) in the 11th with malefics Saturn, Ketu and Sun; only slight relief from Jupiter's aspect.
- citations: HTJAH-I:6667
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 0.52° Scorpio | 1 | 1 |  |  |
| Sun | 23.14° Virgo | 11 | 12 | Hasta 4 | Cancer |
| Moon | 20.49° Leo | 10 | 11 | Pubba 3 | Libra |
| Mars | 12.13° Virgo | 11 | 11 | Hasta 1 | Aries |
| Mercury | 5.11° Libra | 12 | 12 | Chitta 4 | Scorpio |
| Jupiter (R) | 10.04° Taurus | 7 | 7 | Rohini 1 | Aries |
| Venus | 3.07° Scorpio | 1 | 1 | Visakha 4 | Cancer |
| Saturn | 24.66° Virgo | 11 | 12 | Chitta 1 | Leo |
| Rahu (R) | 28.80° Pisces | 5 | 6 | Revati 4 | Pisces |
| Ketu (R) | 28.80° Virgo | 11 | 12 | Chitta 2 | Virgo |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 113; heading at line 6671; write-up span lines 6667-6672 (6 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 6667-6672 (full write-up)

## c. The engine's view

Verdict **favourable**; degree strong; lead frame lagna; karaka Mars; borderline_shifted False.

Count: No rule of Raman's speaks for or against this matter in this chart. On 2,000 random charts, 7% show the same for this matter (typically 0 for and 1 against).

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

Metadata: sav_bindus=30:strong; active_periods=Mars(karaka) 1919-1926; Sun(timer) 1903-1909; Rahu(timer) 1926-1944; Jupiter(timer) 1944-1960; Saturn(timer) 1960-1979

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Mars |
| lord_strong | True |
| karaka | Mars |
| karaka_strong | True |
| bhava_bala | 407.348 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | True |
| lord_hard_afflicted | True |
| flags | LORD_KARAKA_IDENTITY, AFFLICTION_MATTER, LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 0, neutral 1, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Saturn |
| lord_strong | True |
| karaka | Mars |
| karaka_strong | True |
| bhava_bala | 407.348 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | AFFLICTION_MATTER, LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 0, neutral 1, blemish 0 |

### Fired rules (lead frame)

- **H6.L.11** (neutral; polarity neutral; evaluable/lord_in_house; signification enemies_disease; frame LAGNA; branch fortified) cite `HTJAH-I:6055`
  - reading: the 6th lord with benefic association - the eldest brother will be a judge
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA13AD0>`
  - cited lines: `HTJAH-I:6052-6058` (±3, Raman, natal); text in the local packet
