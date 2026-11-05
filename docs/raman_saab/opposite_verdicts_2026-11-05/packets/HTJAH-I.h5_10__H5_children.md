# HTJAH-I.h5_10 H5/children

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `HTJAH-I.h5_10`; name: Chart 100 (H5 children); book: HTJAH-I; case_type: worked_example; confidence: 0.5
- birth: {"dt": "1897-06-03T05:30:00", "tz": 5.3789, "lat": 16.1333, "lon": 80.6833}
- cast: cast from the birth data 1897-06-03 05:30:00 (UTC+5.3789)
- lagna_sign: 2
- stated_positions: none
- expected verdict: **afflicted** (children; review CONFIRMED)
- verdict_prose: House feebly strong, lord weak, Karaka powerless; one male issue born in 1922 died immediately, subsequently two abortions.
- citations: HTJAH-I:5804
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 21.51° Taurus | 1 | 1 |  |  |
| Sun | 21.65° Taurus | 1 | 1 | Rohini 4 | Cancer |
| Moon | 19.24° Gemini | 2 | 2 | Aridra 4 | Pisces |
| Mars | 17.89° Cancer | 3 | 3 | Aslesha 1 | Sagittarius |
| Mercury | 4.90° Taurus | 1 | 1 (sandhi) | Krittika 3 | Aquarius |
| Jupiter | 11.30° Leo | 4 | 4 | Makha 4 | Cancer |
| Venus | 12.90° Aries | 12 | 12 | Aswini 4 | Cancer |
| Saturn (R) | 5.34° Scorpio | 7 | 7 (sandhi) | Anuradha 1 | Leo |
| Rahu (R) | 18.06° Capricorn | 9 | 9 | Sravana 3 | Gemini |
| Ketu (R) | 18.06° Cancer | 3 | 3 | Aslesha 1 | Sagittarius |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 100; heading at line 5801; write-up span lines 5801-5823 (23 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 5801-5823 (full write-up)

## c. The engine's view

Verdict **favourable**; degree moderate; lead frame lagna; karaka Jupiter; borderline_shifted False.

Count: No rule of Raman's speaks for or against this matter in this chart. On 2,000 random charts, 2% show the same for this matter (typically 2 for and 2 against).

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
| _fertility_gate | favourable | 2145 |  |
| _longevity_span | favourable | 2046 |  |
| _marital_bond_gate | favourable | 1897 |  |
| _malefic_occupancy_gate | favourable | 1928 |  |
| _marginal_karaka_gate | favourable | 1974 |  |
| _yogakaraka_lagna_gate | favourable | 2017 |  |
| _powerful_dhana_kendra_floor | favourable | 1775 |  |
| _event_timing | favourable | 1870 |  |

Metadata: saptamsa=weakens; beeja_kshetra=numeric_partial; sav_bindus=26:average; active_periods=Mercury(lord) 1933-1950; Jupiter(karaka) 1898-1914; Rahu(timer) 1897-1898; Saturn(timer) 1914-1933; Ketu(timer) 1950-1957

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Mercury |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 541.954 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 0, neutral 2, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Venus |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 541.954 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 0, neutral 2, blemish 0 |

### Fired rules (lead frame)

- **H5.L.1** (neutral; polarity neutral; evaluable/lord_in_house; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5112`
  - reading: commands servants; Judge / Magistrate / Minister empowered to punish the evil-minded; earns grace of God; few children; will have foes; gives happiness to others
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038E987800>`
  - cited lines: `HTJAH-I:5109-5115` (±3, Raman, natal); text in the local packet
- **H5.C.21** (neutral; polarity neutral; evaluable/combination; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5206`
  - reading: 5th lord in the 1st, 2nd or 3rd → the first child will be male
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EA0E510>`
  - cited lines: `HTJAH-I:5203-5209` (±3, Raman, natal); text in the local packet
