# HTJAH-II.h11_01 H11/elder_siblings

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `HTJAH-II.h11_01`; name: Chart 210 (H11 elder_siblings); book: HTJAH-II; case_type: worked_example; confidence: 0.6
- birth: {"dt": "1937-08-16T08:31:00", "tz": 5.5, "lat": 13, "lon": 77.583}
- cast: cast from the birth data 1937-08-16 08:31:00 (UTC+5.5)
- lagna_sign: 6
- stated_positions: none
- expected verdict: **afflicted** (elder_siblings; review CONFIRMED)
- verdict_prose: The native has no surviving elder brother; karaka-Moon association gave one but severe afflictions to the 11th house and lord killed him young.
- citations: HTJAH-II:14804
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 5.41° Virgo | 1 | 1 |  |  |
| Sun | 1.28° Leo | 12 | 12 | Makha 1 | Aries |
| Moon | 23.24° Scorpio | 3 | 4 | Jyeshta 2 | Capricorn |
| Mars | 11.80° Scorpio | 3 | 3 | Anuradha 3 | Libra |
| Mercury | 28.55° Leo | 12 | 1 | Uttara 1 | Sagittarius |
| Jupiter (R) | 27.23° Sagittarius | 4 | 5 | Uttarashadha 1 | Sagittarius |
| Venus | 21.22° Gemini | 10 | 11 (sandhi) | Punarvasu 1 | Aries |
| Saturn (R) | 12.86° Pisces | 7 | 7 | Uttarabhadra 3 | Libra |
| Rahu (R) | 19.97° Scorpio | 3 | 3 (sandhi) | Jyeshta 1 | Sagittarius |
| Ketu (R) | 19.97° Taurus | 9 | 9 (sandhi) | Rohini 3 | Gemini |

## b. Raman's write-up

File: `how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md`. Chart number 210; heading at line 14761; write-up span lines 14761-14815 (55 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 14761-14815 (full write-up)

## c. The engine's view

Verdict **favourable**; degree moderate; lead frame moon; karaka Jupiter; borderline_shifted False.

Count: Only favourable indications: 2 rules for, none against. On 2,000 random charts, 26% show the same for this matter (typically 4 for and 1 against).

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

Metadata: sav_bindus=29:average; active_periods=Mercury(lord) 1937-1946; Jupiter(karaka) 2014-2030; Ketu(timer) 1946-1953; Venus(timer) 1953-1973; Moon(timer) 1979-1989

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Mercury |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 478.423 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 0, neutral 2, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Moon |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 478.423 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 0, neutral 2, blemish 0 |

### Fired rules (lead frame)

- **H11.C.31** (benefic; polarity benefic; evaluable/combination; signification elder_siblings; frame LAGNA; branch fortified) cite `HTJAH-II:14348`
  - reading: the 11th flanked on both sides by benefics, or otherwise favourably disposed → a powerful elder brother; fabulous wealth through the mother
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EAB2A20>`
  - cited lines: `HTJAH-II:14345-14351` (±3, Raman, natal); text in the local packet
- **H11.C.45** (benefic; polarity benefic; evaluable/combination; signification elder_siblings; frame LAGNA; branch fortified) cite `HTJAH-II:14631`
  - reading: the 11th lord in the 3rd with the 3rd lord → both elder & younger co-borns; brothers taken as business partners → much wealth; writing ability
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAB3590>`
  - cited lines: `HTJAH-II:14628-14634` (±3, Raman, natal); text in the local packet
- **H11.L.3** (neutral; polarity neutral; evaluable/lord_in_house; signification gains; frame LAGNA; branch fortified) cite `HTJAH-II:14274`
  - reading: a concert-singer or musician and earns thereby; gain through brothers; many friends and helpful neighbours
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EAB44D0>`
  - cited lines: `HTJAH-II:14271-14277` (±3, Raman, natal); text in the local packet
- **H11.L.3a** (neutral; polarity neutral; evaluable/lord_in_house; signification gains; frame LAGNA; branch general) cite `HTJAH-II:14277`
  - reading: the 11th lord in the 3rd afflicted - afflictions give contrary results
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAB4620>`
  - cited lines: `HTJAH-II:14274-14280` (±3, Raman, natal); text in the local packet
