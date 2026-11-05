# NH.chart_36 H10/profession_learned

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `NH.chart_36`; name: Sri Swami Vivekananda; book: NH; case_type: worked_example; confidence: 0.7
- birth: {"dt": "1863-01-12T06:33:00", "tz": 5.9, "lat": 22.667, "lon": 88.5}
- cast: cast from the birth data 1863-01-12 06:33:00 (UTC+5.9)
- lagna_sign: 9
- stated_positions: none
- expected verdict: **favourable** (profession_learned; review CONFIRMED)
- verdict_prose: As Jupiter is in Karmasthana, Vivekananda became a great exponent of Advaita Vedanta
- citations: NH:8084, NH:8097, NH:8117, NH:8195, NH:8197
- located in the book by the study tool: NH:8197-8198

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 27.43° Sagittarius | 1 | 1 |  |  |
| Sun | 0.87° Capricorn | 2 | 1 | Uttarashadha 2 | Capricorn |
| Moon | 18.89° Virgo | 10 | 9 | Hasta 3 | Gemini |
| Mars | 7.77° Aries | 5 | 4 | Aswini 3 | Gemini |
| Mercury | 13.22° Capricorn | 2 | 1 | Sravana 1 | Aries |
| Jupiter | 5.46° Libra | 11 | 10 | Chitta 4 | Scorpio |
| Venus | 8.55° Capricorn | 2 | 1 | Uttarashadha 4 | Pisces |
| Saturn | 15.02° Virgo | 10 | 9 | Hasta 2 | Taurus |
| Rahu (R) | 23.69° Scorpio | 12 | 12 | Jyeshta 3 | Aquarius |
| Ketu (R) | 23.69° Taurus | 6 | 6 | Mrigasira 1 | Leo |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 36; heading at line 7980; write-up span lines 7980-8242 (263 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 7993-8242 (lines around the citations)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame lagna; karaka Jupiter; borderline_shifted True.

Count: Both outcomes are indicated: 1 rule of Raman's point for it and 1 against. On 2,000 random charts, 22% show the same for this matter (typically 1 for and 0 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | afflicted | 563 |  |
| _decide_clauses | afflicted | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "mixed"`) |
| _navamsa_modulate | mixed | 564 |  |
| _decide_clauses | mixed | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "mixed"`) |
| _decide | afflicted | 627 |  |
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

Metadata: yoga=Y.RAJA.KT:noted; sav_bindus=30:strong; active_periods=Saturn(afflictor) 1907-1926; Mercury(lord) 1926-1943; Jupiter(karaka) 1891-1907; Moon(timer) 1863-1866; Rahu(timer) 1873-1891

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Mercury |
| lord_strong | False |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 437.866 |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 1, neutral 2, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Mercury |
| lord_strong | False |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 437.866 |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 1, neutral 2, blemish 0 |

### Fired rules (lead frame)

- **H10.P.Moon** (benefic; polarity benefic; evaluable/planet_in_house; signification career; frame LAGNA; branch general) cite `HTJAH-II:9828`
  - reading: religious, wealthy, intelligent, bold; succeeds; corn, ornaments, women; skilled in arts; helpful, virtuous; Jupiter conjunct → learned in ancient subjects and astrology; Saturn aspect → dispassionate thinker, earns via printing/selling books, trustee of religious institutions
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EAB07A0>`
  - cited lines: `HTJAH-II:9825-9831` (±3, Raman, natal); text in the local packet
- **H10.P.Saturn** (malefic; polarity neutral; evaluable/planet_in_house; signification career; frame LAGNA; branch general) cite `HTJAH-II:9881`
  - reading: his career will be marked by sudden elevations and depressions
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EAB0B00>`
  - cited lines: `HTJAH-II:9878-9884` (±3, Raman, natal); text in the local packet
- **H10.L.2** (neutral; polarity neutral; evaluable/lord_in_house; signification career; frame LAGNA; branch general) cite `HTJAH-II:9467`
  - reading: fortunate; rises well in life and makes a lot of money; may engage in the family trade and develop it; prospers in catering and restaurant businesses
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EAAE030>`
  - cited lines: `HTJAH-II:9464-9470` (±3, Raman, natal); text in the local packet
- **H10.L.2a** (neutral; polarity neutral; evaluable/lord_in_house; signification career; frame LAGNA; branch general) cite `HTJAH-II:9470`
  - reading: malefics afflicting the 10th house - suffers losses and is responsible for winding up the family business
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAAE180>`
  - cited lines: `HTJAH-II:9467-9473` (±3, Raman, natal); text in the local packet
