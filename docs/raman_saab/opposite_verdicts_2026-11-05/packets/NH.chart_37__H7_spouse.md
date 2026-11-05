# NH.chart_37 H7/spouse

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: mixed.

## a. Golden record

- id: `NH.chart_37`; name: Sayaji Rao III, Gaekwar of Baroda; book: NH; case_type: worked_example; confidence: 0.3
- birth: {"dt": "1863-03-12T02:03:00", "tz": 4.88, "lat": 22.333, "lon": 73.25}
- cast: cast from the birth data 1863-03-12 02:03:00 (UTC+4.88)
- lagna_sign: 9
- stated_positions: none
- expected verdict: **afflicted** (spouse; review CONFIRMED)
- verdict_prose: he lost his first wife and had to marry a second one
- citations: NH:8342, NH:8351, NH:8359, NH:8445, NH:8449
- located in the book by the study tool: NH:8359-8360

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 18.42° Sagittarius | 1 | 1 |  |  |
| Sun | 0.32° Pisces | 4 | 3 | Poorvabhadra 4 | Cancer |
| Moon | 18.53° Scorpio | 12 | 12 | Jyeshta 1 | Sagittarius |
| Mars | 10.97° Taurus | 6 | 6 | Rohini 1 | Aries |
| Mercury | 3.15° Aquarius | 3 | 2 | Dhanishta 3 | Libra |
| Jupiter (R) | 5.60° Libra | 11 | 10 | Chitta 4 | Scorpio |
| Venus | 22.01° Pisces | 4 | 4 | Revati 2 | Capricorn |
| Saturn (R) | 12.56° Virgo | 10 | 9 | Hasta 1 | Aries |
| Rahu (R) | 20.57° Scorpio | 12 | 12 | Jyeshta 2 | Capricorn |
| Ketu (R) | 20.57° Taurus | 6 | 6 | Rohini 4 | Cancer |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 37; heading at line 8243; write-up span lines 8243-8474 (232 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 8243-8474 (full write-up)

## c. The engine's view

Verdict **favourable**; degree moderate; lead frame moon; karaka Venus; borderline_shifted False.

Count: Both outcomes are indicated: 1 rule of Raman's point for it and 1 against. On 2,000 random charts, 55% show the same for this matter (typically 1 for and 1 against).

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
| _marital_bond_gate | favourable | 1907 |  |
| _malefic_occupancy_gate | favourable | 1928 |  |
| _marginal_karaka_gate | favourable | 1974 |  |
| _yogakaraka_lagna_gate | favourable | 2017 |  |
| _powerful_dhana_kendra_floor | favourable | 1775 |  |
| _event_timing | favourable | 1870 |  |

Metadata: sav_bindus=26:average; active_periods=Mercury(maraka) 1863-1877; Ketu(maraka) 1877-1884; Rahu(timer) 1927-1945

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Venus |
| lord_strong | True |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | 417.378 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | True |
| lord_hard_afflicted | False |
| flags | LORD_KARAKA_IDENTITY, LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 1, neutral 2, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Mercury |
| lord_strong | False |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | 417.378 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 1, neutral 2, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Mercury |
| lord_strong | False |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | 417.378 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 1, neutral 2, blemish 0 |

### Fired rules (lead frame)

- **H7.C.7** (benefic; polarity benefic; evaluable/combination; signification marital_happiness; frame KARAKA; branch fortified) cite `HTJAH-II:368`
  - reading: Venus exalted or in own sign (or Gopura/Vaiseshikamsa varga) → a good and beautiful wife
  - condition: `<app.raman_saab.doctrine.conditions.HasDignity object at 0x000002038EA18CB0>`
  - cited lines: `HTJAH-II:365-371` (±3, Raman, natal); text in the local packet
- **H7.K.3** (malefic; polarity malefic; evaluable/from_karaka; signification marital_happiness; frame KARAKA; branch afflicted) cite `HTJAH-II:376`
  - reading: unhappy marriage — malefics in the 7th from Venus
  - condition: `<app.raman_saab.doctrine.conditions.ClassInHouseFrom object at 0x000002038EA20E30>`
  - cited lines: `HTJAH-II:373-379` (±3, Raman, natal); text in the local packet
- **H7.L.3** (neutral; polarity neutral; evaluable/lord_in_house; signification spouse; frame LAGNA; branch general) cite `HTJAH-II:254`
  - reading: lucky brothers who may live abroad; female issues survive
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA21880>`
  - cited lines: `HTJAH-II:251-257` (±3, Raman, natal); text in the local packet
- **H7.C.38** (neutral; polarity neutral; evaluable/combination; signification spouse; frame LAGNA; branch afflicted) cite `HTJAH-II:484`
  - reading: the 7th sign (and Venus) in common (dual) signs → marries at least twice (the strongest dual-sign remarriage signature; the 7th-lord-in-dual-Navamsa refinement is kept in text)
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA1A0F0>`
  - cited lines: `HTJAH-II:481-487` (±3, Raman, natal); text in the local packet
