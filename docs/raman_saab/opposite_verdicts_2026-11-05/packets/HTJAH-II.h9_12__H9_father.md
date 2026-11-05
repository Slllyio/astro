# HTJAH-II.h9_12 H9/father

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `HTJAH-II.h9_12`; name: 96 (H9 father); book: HTJAH-II; case_type: worked_example; confidence: 0.6
- birth: {"dt": "1958-08-04T06:40:00", "tz": 5.5, "lat": 9.917, "lon": 78.117}
- cast: cast from the birth data 1958-08-04 06:40:00 (UTC+5.5)
- lagna_sign: 4
- stated_positions: none
- expected verdict: **afflicted** (father; review CONFIRMED)
- verdict_prose: 9th house and karaka free of affliction, but 9th lord Jupiter (Vargottama) blemished by Rahu and Mars aspect and placed in a martian (maraka) constellation; father died Apr 1979.
- citations: HTJAH-II:8532
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 26.21° Cancer | 1 | 1 |  |  |
| Sun | 19.33° Cancer | 1 | 1 | Aslesha 1 | Sagittarius |
| Moon | 9.13° Pisces | 9 | 8 | Uttarabhadra 2 | Virgo |
| Mars | 16.57° Aries | 10 | 10 | Bharani 1 | Leo |
| Mercury | 14.49° Leo | 2 | 2 | Pubba 1 | Leo |
| Jupiter | 2.88° Libra | 4 | 3 | Chitta 3 | Libra |
| Venus | 23.59° Gemini | 12 | 12 | Punarvasu 2 | Taurus |
| Saturn (R) | 27.58° Scorpio | 5 | 5 | Jyeshta 4 | Pisces |
| Rahu (R) | 4.16° Libra | 4 | 3 | Chitta 4 | Scorpio |
| Ketu (R) | 4.16° Aries | 10 | 9 | Aswini 2 | Taurus |

## b. Raman's write-up

File: `how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md`. Chart number 96; heading at line 8546; write-up span lines 8532-8579 (48 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 8532-8579 (full write-up)

## c. The engine's view

Verdict **favourable**; degree moderate; lead frame moon; karaka Sun; borderline_shifted False.

Count: Both outcomes are indicated: 2 rules of Raman's point for it and 3 against. On 2,000 random charts, 73% show the same for this matter (typically 1 for and 3 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "favourable"`) |
| _decide | favourable | 622 |  |
| _decisive_affliction | favourable | 1615 |  |
| _catastrophic_severity_gate | favourable | 1647 |  |
| _yoga_modulate | favourable | 1592 |  |
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

Metadata: yoga=Y.RAJA.910A:noted; sav_bindus=22:weak; active_periods=Saturn(maraka) 1958-1969; Mercury(maraka) 1969-1986; Moon(timer) 2019-2029

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Mars |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | True |
| bhava_bala | 448.448 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 3, neutral 3, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Jupiter |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | True |
| bhava_bala | 448.448 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 3, neutral 3, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Jupiter |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | True |
| bhava_bala | 448.448 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 3, neutral 3, blemish 0 |

### Fired rules (lead frame)

- **H9.P.Moon** (benefic; polarity benefic; evaluable/planet_in_house; signification fortune; frame LAGNA; branch general) cite `HTJAH-II:7522`
  - reading: fortunate and prosperous; many sons, friends and kinsmen; principled and generous-minded; may build charitable institutions; acquires good immovable property and visits foreign countries
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EAA78F0>`
  - cited lines: `HTJAH-II:7519-7525` (±3, Raman, natal); text in the local packet
- **H9.B.21** (benefic; polarity benefic; evaluable/combination; signification fortune; frame LAGNA; branch fortified) cite `HTJAH-II:7460`
  - reading: a benefic occupying the 9th → native is lucky
  - condition: `<app.raman_saab.doctrine.conditions.CountInHouse object at 0x000002038EAA1E50>`
  - cited lines: `HTJAH-II:7457-7463` (±3, Raman, natal); text in the local packet
- **H9.A.13** (malefic; polarity malefic; evaluable/combination; signification father; frame KARAKA; branch afflicted) cite `HTJAH-II:7443`
  - reading: the 5th lord OR the Sun afflicted by Saturn / Rahu / Mandi → native a source of misery to the father. The 5th-lord arm is encoded faithfully via the per-chart 5th lord (not a hard-coded planet); the Mandi/Gulika afflictor is deferred. TODO(predicate: Mandi/Gulika)
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EAA13A0>`
  - cited lines: `HTJAH-II:7440-7446` (±3, Raman, natal); text in the local packet
- **H9.A.20** (malefic; polarity malefic; evaluable/combination; signification father; frame KARAKA; branch afflicted) cite `HTJAH-II:7455`
  - reading: the Sun or the Moon in a kendra in a movable sign → native will not perform the father's last rites
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EAA1B80>`
  - cited lines: `HTJAH-II:7452-7458` (±3, Raman, natal); text in the local packet
- **H9.C.35** (malefic; polarity malefic; evaluable/combination; signification fortune; frame LAGNA; branch afflicted) cite `HTJAH-II:7507`
  - reading: planets in the 9th not associated with Mercury and Jupiter → diseased, forlorn, captivity and misery
  - condition: `<app.raman_saab.doctrine.rule_sets.house_09_bhagya.combinations._PlanetInHouseNotWith object at 0x000002038EAA2C00>`
  - cited lines: `HTJAH-II:7504-7510` (±3, Raman, natal); text in the local packet
- **H9.L.4** (neutral; polarity neutral; evaluable/lord_in_house; signification fortune; frame LAGNA; branch general) cite `HTJAH-II:7326`
  - reading: vast landed properties and beautiful bungalows, or the native may earn through estate and land dealings; his mother will be a rich and fortunate woman; he will inherit his father's immovable properties
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EAA5C40>`
  - cited lines: `HTJAH-II:7323-7329` (±3, Raman, natal); text in the local packet
- **H9.L.4a** (neutral; polarity neutral; evaluable/lord_in_house; signification fortune; frame LAGNA; branch general) cite `HTJAH-II:7330`
  - reading: the 9th lord afflicted in the 4th - the native may not have any domestic unhappiness [sic, as printed; almost certainly 'happiness']; his early life will be crossed by miseries due to a hard-hearted father or disharmony between parents
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAA6300>`
  - cited lines: `HTJAH-II:7327-7333` (±3, Raman, natal); text in the local packet
- **H9.L.4b** (neutral; polarity neutral; evaluable/lord_in_house; signification fortune; frame LAGNA; branch general) cite `HTJAH-II:7333`
  - reading: Rahu afflicting - the mother may be a divorcee or living separately from his father
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAA41A0>`
  - cited lines: `HTJAH-II:7330-7336` (±3, Raman, natal); text in the local packet
