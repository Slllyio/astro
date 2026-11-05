# NH.chart_42 H10/career

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `NH.chart_42`; name: Chittaranjan Das; book: NH; case_type: worked_example; confidence: 0.3
- birth: {"dt": "1870-11-05T06:49:00", "tz": 5.9, "lat": 22.67, "lon": 88.5}
- cast: cast from the birth data 1870-11-05 06:49:00 (UTC+5.9)
- lagna_sign: 8
- stated_positions: none
- expected verdict: **favourable** (career; review CONFIRMED)
- verdict_prose: The subject's remarkable organising capacity and powers of leadership are due to the disposition of the Sun in Lagna Bhava
- citations: NH:9325, NH:9331, NH:9337, NH:9340
- located in the book by the study tool: NH:9331-9332

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 0.34° Scorpio | 1 | 1 |  |  |
| Sun | 21.83° Libra | 12 | 1 | Visakha 1 | Aries |
| Moon | 16.00° Pisces | 5 | 5 (sandhi) | Uttarabhadra 4 | Scorpio |
| Mars | 13.25° Leo | 10 | 10 | Makha 4 | Cancer |
| Mercury | 11.18° Libra | 12 | 12 | Swati 2 | Capricorn |
| Jupiter (R) | 5.13° Gemini | 8 | 8 | Mrigasira 4 | Scorpio |
| Venus | 13.62° Libra | 12 | 12 | Swati 3 | Aquarius |
| Saturn | 5.02° Sagittarius | 2 | 2 | Moola 2 | Taurus |
| Rahu (R) | 22.45° Gemini | 8 | 9 | Punarvasu 1 | Aries |
| Ketu (R) | 22.45° Sagittarius | 2 | 3 | Poorvashadha 3 | Libra |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 42; heading at line 9263; write-up span lines 9263-9416 (154 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 9263-9416 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame moon; karaka Sun; borderline_shifted False.

Count: Only unfavourable indications: 1 rule against, none for. On 2,000 random charts, 14% show the same for this matter (typically 1 for and 0 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | afflicted | 547 |  |
| _decide_clauses | afflicted | 769 | 6. a weak pillar with malefic / weak-bhava / maraka pressure -> afflicted... (`base = "afflicted"`) |
| _navamsa_modulate | afflicted | 547 |  |
| _decide_clauses | afflicted | 769 | 6. a weak pillar with malefic / weak-bhava / maraka pressure -> afflicted... (`base = "afflicted"`) |
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

Metadata: yoga=Y.VIPAREETA:noted; varga_D10=Jupiter:exalt|Sun:neutral; sav_bindus=40:strong; active_periods=Jupiter(lord) 1956-1972; Sun(karaka) 1915-1921; Mercury(timer) 1871-1888; Ketu(timer) 1888-1895; Venus(timer) 1895-1915

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Jupiter |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | False |
| bhava_bala | 338.385 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 1, neutral 2, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Sun |
| lord_strong | False |
| karaka | Sun |
| karaka_strong | False |
| bhava_bala | 338.385 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | True |
| lord_hard_afflicted | False |
| flags | LORD_KARAKA_IDENTITY, LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 1, neutral 2, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Moon |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | False |
| bhava_bala | 338.385 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 0, malefic 1, neutral 2, blemish 0 |

### Fired rules (lead frame)

- **H10.L.12** (malefic; polarity malefic; evaluable/lord_in_house; signification career; frame LAGNA; branch general) cite `HTJAH-II:9564`
  - reading: works in a far-off place, lacking comforts and facing many difficulties in life
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EAB0200>`
  - cited lines: `HTJAH-II:9561-9567` (±3, Raman, natal); text in the local packet
- **H10.L.12a** (neutral; polarity neutral; evaluable/lord_in_house; signification career; frame LAGNA; branch general) cite `HTJAH-II:9569`
  - reading: the 10th lord beneficially disposed - becomes a spiritual seeker
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAB0380>`
  - cited lines: `HTJAH-II:9566-9572` (±3, Raman, natal); text in the local packet
- **H10.P.Mars** (neutral; polarity neutral; evaluable/planet_in_house; signification career; frame LAGNA; branch general) cite `HTJAH-II:9841`
  - reading: other combinations favouring - the native may become a cruel ruler; fond of praise and may take bold steps in governing; rash; earns much money
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EAB0860>`
  - cited lines: `HTJAH-II:9838-9844` (±3, Raman, natal); text in the local packet
