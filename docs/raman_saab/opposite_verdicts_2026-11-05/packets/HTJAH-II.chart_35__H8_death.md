# HTJAH-II.chart_35 H8/death

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `HTJAH-II.chart_35`; name: Chart 35 ayur (Poornayu; died 7-2-1966 Rahu Dasa Sun Bhukti; Sagittarius Lagna); book: HTJAH-II; case_type: worked_example; confidence: 0.6
- birth: {"dt": "1896-01-31T04:30:00", "tz": 4.8844, "lat": 22.0, "lon": 73.2667}
- cast: cast from the birth data 1896-01-31 04:30:00 (UTC+4.8844)
- lagna_sign: 9
- stated_positions: none
- expected verdict: **favourable** (death; review CONFIRMED)
- verdict_prose: Poornayu. Died 7-2-1966 in Rahu Dasa, Sun Bhukti (Saturn delegates killing to Sanivad Rahu; Sun empowered owning 2nd and 7th from Moon-Amsa; Saturn transit to Aquarius/Gemini-Navamsa Feb-Mar 1966 the final signal).
- citations: HTJAH-II:4661, HTJAH-II:4844-4855
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 15.64° Sagittarius | 1 | 1 |  |  |
| Sun | 19.68° Capricorn | 2 | 2 | Sravana 3 | Gemini |
| Moon | 28.10° Cancer | 8 | 8 | Aslesha 4 | Pisces |
| Mars | 14.87° Sagittarius | 1 | 1 | Poorvashadha 1 | Leo |
| Mercury (R) | 5.01° Aquarius | 3 | 2 | Dhanishta 4 | Scorpio |
| Jupiter (R) | 12.31° Cancer | 8 | 8 | Pushya 3 | Libra |
| Venus | 10.42° Sagittarius | 1 | 1 | Moola 4 | Cancer |
| Saturn | 27.53° Libra | 11 | 11 | Visakha 3 | Gemini |
| Rahu (R) | 13.97° Aquarius | 3 | 3 | Satabhisha 3 | Aquarius |
| Ketu (R) | 13.97° Leo | 9 | 9 | Pubba 1 | Leo |

## b. Raman's write-up

File: `how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md`. Chart number 35; heading at line 4661; write-up span lines 4661-4864 (204 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 4661-4864 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame lagna; karaka Saturn; borderline_shifted False.

Count: Both outcomes are indicated: 1 rule of Raman's point for it and 4 against. On 2,000 random charts, 29% show the same for this matter (typically 0 for and 2 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | afflicted | 547 |  |
| _decide_clauses | afflicted | 676 | 1.5 DUSTHANA-AFFLICTION CONFIRMATION (Stage-3, user-signed-off "B"). For an inherently (`return _navamsa_modulate("afflicted", L)`) |
| _navamsa_modulate | afflicted | 547 |  |
| _decide_clauses | afflicted | 676 | 1.5 DUSTHANA-AFFLICTION CONFIRMATION (Stage-3, user-signed-off "B"). For an inherently (`return _navamsa_modulate("afflicted", L)`) |
| _decide | afflicted | 627 |  |
| _decisive_affliction | afflicted | 1611 |  |
| _catastrophic_severity_gate | afflicted | 1647 |  |
| _yoga_modulate | afflicted | 1571 |  |
| _dhana_floor | afflicted | 1726 |  |
| _blemishless_venus_floor | afflicted | 1683 |  |
| _saptamsa_gate | afflicted | 2179 |  |
| _fertility_gate | afflicted | 2111 |  |
| _longevity_span | afflicted | 2046 |  |
| _marital_bond_gate | afflicted | 1897 |  |
| _malefic_occupancy_gate | afflicted | 1928 |  |
| _marginal_karaka_gate | afflicted | 1974 |  |
| _yogakaraka_lagna_gate | afflicted | 2017 |  |
| _powerful_dhana_kendra_floor | afflicted | 1775 |  |
| _event_timing | afflicted | 1870 |  |

Metadata: sav_bindus=27:average; death_window=Jupiter/Saturn 1968-08..1971-03; Jupiter/Mercury 1971-03..1973-06; Jupiter/Ketu 1973-06..1974-05; active_periods=Mercury(maraka) 1896-1898; Ketu(maraka) 1898-1905; Mars(timer) 1941-1948; Jupiter(timer) 1966-1982; drekkana22_lord=Jupiter; decanate_cause=Cancer 3: tumour, hallucinations, syncope

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Moon |
| lord_strong | True |
| karaka | Saturn |
| karaka_strong | True |
| bhava_bala | 427.498 |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | AFFLICTION_MATTER, AFFLICTION_OWN_EVIDENCE, LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 4, neutral 2, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Saturn |
| lord_strong | True |
| karaka | Saturn |
| karaka_strong | True |
| bhava_bala | 427.498 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | True |
| lord_hard_afflicted | False |
| flags | LORD_KARAKA_IDENTITY, AFFLICTION_MATTER, AFFLICTION_OWN_EVIDENCE, LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 4, neutral 2, blemish 0 |

### Fired rules (lead frame)

- **H8.L.8** (benefic; polarity benefic; evaluable/lord_in_house; signification longevity; frame LAGNA; branch fortified) cite `HTJAH-II:3001`
  - reading: long life, happiness; lands, conveyance, power and position by past-life merit
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038E12A630>`
  - cited lines: `HTJAH-II:2998-3004` (±3, Raman, natal); text in the local packet
- **H8.C.13** (malefic; polarity malefic; evaluable/combination; signification death; frame LAGNA; branch afflicted) cite `HTJAH-II:3616`
  - reading: Moon in the 8th aspected by (strong) Saturn → surgery, or an anus / eye ailment
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA24AA0>`
  - cited lines: `HTJAH-II:3613-3619` (±3, Raman, natal); text in the local packet
- **H8.K.22** (malefic; polarity malefic; evaluable/combination; signification death; frame LAGNA; branch afflicted) cite `HTJAH-II:3712`
  - reading: Moon in the 8th in a watery sign → consumption leads to death
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA26C60>`
  - cited lines: `HTJAH-II:3709-3715` (±3, Raman, natal); text in the local packet
- **H8.K.25** (malefic; polarity malefic; evaluable/combination; signification death; frame LAGNA; branch afflicted) cite `HTJAH-II:3719`
  - reading: Jupiter in the 8th in a watery sign → affection of the lungs
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA26FC0>`
  - cited lines: `HTJAH-II:3716-3722` (±3, Raman, natal); text in the local packet
- **H8.D.6** (malefic; polarity malefic; evaluable/combination; signification death; frame LAGNA; branch afflicted) cite `NH:9186`
  - reading: a benefic in the 8th aspected by Mars → the natural-death protection fails; the end is violent
  - condition: `<app.raman_saab.doctrine.rule_sets.house_08_ayur.combinations._VitiatedBeneficInEighth object at 0x000002038E129730>`
  - cited lines: `NH:9183-9189` (±3, Raman, natal); text in the local packet
- **H8.P.Jupiter** (neutral; polarity neutral; evaluable/planet_in_house; signification longevity; frame LAGNA; branch general) cite `HTJAH-II:3531`
  - reading: unhappy but generous-hearted; lives long; difficulty in speech; may do ignoble deeds but pretend to be noble; may have liaisons with widows; dirty habits and colitis; a painless death
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EAA0140>`
  - cited lines: `HTJAH-II:3528-3534` (±3, Raman, natal); text in the local packet
- **H8.C.24** (neutral; polarity neutral; evaluable/combination; signification death; frame LAGNA; branch afflicted) cite `HTJAH-II:3900`
  - reading: the 8th is a movable sign → dies in a foreign country / far from birthplace
  - condition: `<app.raman_saab.doctrine.rule_sets.house_08_ayur.combinations._EighthSignModality object at 0x000002038EA27FE0>`
  - cited lines: `HTJAH-II:3897-3903` (±3, Raman, natal); text in the local packet
