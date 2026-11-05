# HTJAH-I.x75 H4/mother

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `HTJAH-I.x75`; name: Chart 75 (extracted, DRAFT); book: HTJAH-I; case_type: worked_example; confidence: 0.5
- birth: {"dt": "1895-07-17T11:42:00", "tz": 5.2444, "lat": 11.0, "lon": 78.6667, "rectified": "Raman: 4th Sagittarius unoccupied, aspected by Jupiter (4th lord) and Mercury (Lagna lord); 4th lord in a Kendra with Mercury; Moon in Aries aspected by exalted Saturn; Navamsha 4th lord Mars in Aries (HTJAH-I:4682-4693) -> Virgo Lagna, every stated feature reproduced. The printed 12-30 p.m. casts Libra 11.2deg (wrong chart). Re-timed -48 min from the printed 12:30 to the smallest shift that puts the Lagna 0.5deg inside Raman's sign, after the HTJAH-I.chart_35 precedent; the re-timed chart was checked against every feature quoted (2026-10-24)."}
- cast: cast from the birth data 1895-07-17 11:42:00 (UTC+5.2444)
- lagna_sign: 6
- stated_positions: none
- expected verdict: **favourable** (mother; review CONFIRMED)
- verdict_prose: Consequently the fourth house is quite strong rendering the native enjoy the fortune of possessing his mother till his age of 52. Education and Learning
- citations: HTJAH-I:4680-4695
- located in the book by the study tool: HTJAH-I:4694-4697

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 29.38° Virgo | 1 | 1 |  |  |
| Sun | 3.43° Cancer | 11 | 10 | Pushya 1 | Leo |
| Moon | 28.20° Aries | 8 | 8 | Krittika 1 | Sagittarius |
| Mars | 1.65° Leo | 12 | 11 | Makha 1 | Aries |
| Mercury | 15.13° Gemini | 10 | 10 | Aridra 3 | Aquarius |
| Jupiter | 28.53° Gemini | 10 | 10 | Punarvasu 3 | Gemini |
| Venus | 18.82° Leo | 12 | 12 | Pubba 2 | Virgo |
| Saturn | 9.73° Libra | 2 | 1 | Swati 1 | Sagittarius |
| Rahu (R) | 24.45° Aquarius | 6 | 6 | Poorvabhadra 2 | Taurus |
| Ketu (R) | 24.45° Leo | 12 | 12 | Pubba 4 | Scorpio |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 75; heading at line 4680; write-up span lines 4680-4742 (63 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 4680-4742 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame lagna; karaka Moon; borderline_shifted False.

Count: Only favourable indications: 1 rule for, none against. On 2,000 random charts, 24% show the same for this matter (typically 1 for and 1 against).

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

Metadata: sav_bindus=24:weak; active_periods=Moon(maraka) 1900-1910; Mars(maraka) 1910-1917

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Jupiter |
| lord_strong | True |
| karaka | Moon |
| karaka_strong | False |
| bhava_bala | 500.695 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 0, neutral 0, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Moon |
| lord_strong | False |
| karaka | Moon |
| karaka_strong | False |
| bhava_bala | 500.695 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | True |
| lord_hard_afflicted | False |
| flags | LORD_KARAKA_IDENTITY, LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 0, neutral 0, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Moon |
| lord_strong | False |
| karaka | Moon |
| karaka_strong | False |
| bhava_bala | 500.695 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | True |
| lord_hard_afflicted | False |
| flags | LORD_KARAKA_IDENTITY, LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 0, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H4.L.10** (benefic; polarity benefic; evaluable/lord_in_house; signification mother_home; frame LAGNA; branch fortified) cite `HTJAH-I:4180`
  - reading: political success; an expert chemist; vanquishes his enemies and makes his personality felt by the world
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA0C4A0>`
  - cited lines: `HTJAH-I:4177-4183` (±3, Raman, natal); text in the local packet
