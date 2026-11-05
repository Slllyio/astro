# HTJAH-I.chart_31 H1/self

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `HTJAH-I.chart_31`; name: Chart 31 (Sagittarius, career strides yet lacks happiness); book: HTJAH-I; case_type: worked_example; confidence: 0.4
- birth: {"dt": "1903-10-21T10:43:00", "tz": 5.1722, "lat": 13.0, "lon": 77.5833}
- cast: cast from the birth data 1903-10-21 10:43:00 (UTC+5.1722)
- lagna_sign: 9
- stated_positions: none
- expected verdict: **afflicted** (self; review CONFIRMED)
- verdict_prose: Strides in career and lack of happiness; long thin good-looking face, well-proportioned; God-fearing, honest; clear quick mind; lacks happiness.
- citations: HTJAH-I:2209-2232
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 12.15° Sagittarius | 1 | 1 |  |  |
| Sun | 5.58° Libra | 11 | 11 | Chitta 4 | Scorpio |
| Moon | 13.01° Libra | 11 | 11 | Swati 2 | Capricorn |
| Mars | 29.31° Scorpio | 12 | 1 | Jyeshta 4 | Pisces |
| Mercury | 17.69° Virgo | 10 | 10 | Hasta 3 | Gemini |
| Jupiter (R) | 22.99° Aquarius | 3 | 3 | Poorvabhadra 1 | Aries |
| Venus | 27.26° Leo | 9 | 9 | Uttara 1 | Sagittarius |
| Saturn | 11.76° Capricorn | 2 | 2 | Sravana 1 | Aries |
| Rahu (R) | 14.58° Virgo | 10 | 10 | Hasta 2 | Taurus |
| Ketu (R) | 14.58° Pisces | 4 | 4 | Uttarabhadra 4 | Scorpio |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 31; heading at line 2212; write-up span lines 2209-2239 (31 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 2209-2239 (full write-up)

## c. The engine's view

Verdict **favourable**; degree moderate; lead frame lagna; karaka Sun; borderline_shifted False.

Count: Both outcomes are indicated: 2 rules of Raman's point for it and 2 against. On 2,000 random charts, 82% show the same for this matter (typically 3 for and 2 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "favourable"`) |
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

Metadata: sav_bindus=32:strong; active_periods=Jupiter(lord) 1913-1929; Sun(karaka) 1992-1998; Ketu(timer) 1965-1972; Venus(timer) 1972-1992; Mars(timer) 2008-2015

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Jupiter |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | True |
| bhava_bala | 475.136 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 2, malefic 2, neutral 2, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Venus |
| lord_strong | False |
| karaka | Sun |
| karaka_strong | True |
| bhava_bala | 475.136 |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 2, neutral 2, blemish 0 |

### Fired rules (lead frame)

- **H1.L.3** (benefic; polarity benefic; evaluable/lord_in_house; signification self; frame LAGNA; branch general) cite `HTJAH-I:1015`
  - reading: highly courageous, fortunate, respectable, two wives, intelligent, happy
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038E134A70>`
  - cited lines: `HTJAH-I:1012-1018` (±3, Raman, natal); text in the local packet
- **H1.C.33** (benefic; polarity benefic; evaluable/combination; signification self; frame LAGNA; branch fortified) cite `HTJAH-I:1138`
  - reading: the presence of any planet or planets in the 10th adds greater vigour (on top of a decently placed Lagna lord)
  - condition: `<app.raman_saab.doctrine.conditions.CountInHouse object at 0x000002038E132C00>`
  - cited lines: `HTJAH-I:1135-1141` (±3, Raman, natal); text in the local packet
- **H1.C.26a** (malefic; polarity malefic; evaluable/combination; signification self; frame LAGNA; branch afflicted) cite `HTJAH-I:1127`
  - reading: Lagna hemmed in between two malefics (Papakartari) — the native will encounter thieves and suffer on their account; worst when the hemming pair is Saturn and Rahu
  - condition: `<app.raman_saab.doctrine.rule_sets.house_01_lagna.combinations_core._LagnaHemmedBy object at 0x000002038E132780>`
  - cited lines: `HTJAH-I:1124-1130` (±3, Raman, natal); text in the local packet
- **H1.C.26b** (malefic; polarity malefic; evaluable/combination; signification self; frame LAGNA; branch afflicted) cite `HTJAH-I:1127`
  - reading: lord of the Lagna hemmed in between two malefics — the native will encounter thieves and suffer on their account; worst when the hemming pair is Saturn and Rahu
  - condition: `<app.raman_saab.doctrine.rule_sets.house_01_lagna.combinations_core._LagnaLordHemmedBy object at 0x000002038E130A10>`
  - cited lines: `HTJAH-I:1124-1130` (±3, Raman, natal); text in the local packet
- **H1.B.18** (neutral; polarity neutral; evaluable/constitution; signification self; frame LAGNA; branch fortified) cite `HTJAH-I:1110`
  - reading: corpulence — Lagna owned by a natural benefic AND the D9-sign lord of the Lagna-lord occupies a watery sign
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038E1344D0>`
  - cited lines: `HTJAH-I:1107-1113` (±3, Raman, natal); text in the local packet
- **H1.M.S07** (neutral; polarity neutral; evaluable/moon_mind; signification self; frame MOON; branch fortified) cite `HTJAH-I:1347`
  - reading: idealistic, quick-witted, vindictive, forceful and positive
  - condition: `<app.raman_saab.doctrine.conditions.InSign object at 0x000002038E136570>`
  - cited lines: `HTJAH-I:1344-1350` (±3, Raman, natal); text in the local packet
