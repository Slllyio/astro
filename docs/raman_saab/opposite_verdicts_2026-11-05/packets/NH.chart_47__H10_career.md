# NH.chart_47 H10/career

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `NH.chart_47`; name: Franklin Delano Roosevelt; book: NH; case_type: worked_example; confidence: 0.3
- birth: {"dt": "1882-01-30T20:00:00", "tz": -4.93, "lat": 40.72, "lon": -73.98}
- cast: cast from the birth data 1882-01-30 20:00:00 (UTC-4.93)
- lagna_sign: 5
- stated_positions: none
- expected verdict: **favourable** (career; review CONFIRMED)
- verdict_prose: This combination enabled Roosevelt to reach the highest position in life that is possible in a democratic country
- citations: NH:10131, NH:10148, NH:10155, NH:10164, NH:10221
- located in the book by the study tool: NH:10154-10156

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 23.48° Leo | 1 | 1 |  |  |
| Sun | 20.34° Capricorn | 6 | 6 | Sravana 4 | Cancer |
| Moon | 15.10° Gemini | 11 | 11 | Aridra 3 | Aquarius |
| Mars (R) | 6.24° Gemini | 11 | 10 (sandhi) | Mrigasira 4 | Scorpio |
| Mercury | 6.38° Aquarius | 7 | 6 | Dhanishta 4 | Scorpio |
| Jupiter | 26.17° Aries | 9 | 9 | Bharani 4 | Scorpio |
| Venus | 15.25° Capricorn | 6 | 6 | Sravana 2 | Taurus |
| Saturn | 15.32° Aries | 9 | 9 | Bharani 1 | Leo |
| Rahu (R) | 14.92° Scorpio | 4 | 4 | Anuradha 4 | Scorpio |
| Ketu (R) | 14.92° Taurus | 10 | 10 | Rohini 2 | Taurus |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 47; heading at line 10080; write-up span lines 10080-10231 (152 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 10080-10231 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame moon; karaka Sun; borderline_shifted False.

Count: Only unfavourable indications: 1 rule against, none for. On 2,000 random charts, 14% show the same for this matter (typically 1 for and 0 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | afflicted | 547 |  |
| _decide_clauses | afflicted | 769 | 6. a weak pillar with malefic / weak-bhava / maraka pressure -> afflicted... (`base = "afflicted"`) |
| _decide | afflicted | 622 |  |
| _decisive_affliction | afflicted | 1611 |  |
| _catastrophic_severity_gate | afflicted | 1647 |  |
| _yoga_modulate | afflicted | 1592 |  |
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

Metadata: yoga=Y.RAJA.KT:noted; varga_D10=Jupiter:own|Sun:neutral; sav_bindus=20:weak; active_periods=Ketu(afflictor) 1940-1947; Jupiter(lord) 1888-1904; Sun(karaka) 1967-1973; Rahu(timer) 1882-1888; Saturn(timer) 1904-1923

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Jupiter |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | False |
| bhava_bala | 449.02 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 1, neutral 1, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Venus |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | False |
| bhava_bala | 449.02 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 1, neutral 1, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Venus |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | False |
| bhava_bala | 449.02 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 1, neutral 1, blemish 0 |

### Fired rules (lead frame)

- **H10.P.Ketu** (malefic; polarity malefic; evaluable/planet_in_house; signification career; frame LAGNA; branch general) cite `HTJAH-II:9900`
  - reading: strong, bold and well-known; commits vile deeds and is impure in his resolves; faces many obstacles in all his undertakings; very clever
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EAB0C80>`
  - cited lines: `HTJAH-II:9897-9903` (±3, Raman, natal); text in the local packet
- **H10.L.6a** (neutral; polarity neutral; evaluable/lord_in_house; signification career; frame LAGNA; branch general) cite `HTJAH-II:9509`
  - reading: Saturn aspecting the 10th lord - may have to work all his life in a low-paying job with not much prospects
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAAECC0>`
  - cited lines: `HTJAH-II:9506-9512` (±3, Raman, natal); text in the local packet
