# HTJAH-I.h5_16 H5/children

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `HTJAH-I.h5_16`; name: Chart 106 (H5 children); book: HTJAH-I; case_type: worked_example; confidence: 0.55
- birth: {"dt": "1902-05-30T03:19:00", "tz": 5.4511, "lat": 17, "lon": 81.7667}
- cast: cast from the birth data 1902-05-30 03:19:00 (UTC+5.4511)
- lagna_sign: 1
- stated_positions: none
- expected verdict: **favourable** (children; review CONFIRMED)
- verdict_prose: 5th house highly significant; trebled count gives 15 — actually 13 children born, of which 3 lost due to affliction of 5th lord and PutraKaraka.
- citations: HTJAH-I:5924
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 11.17° Aries | 1 | 1 |  |  |
| Sun | 16.51° Taurus | 2 | 2 | Rohini 2 | Taurus |
| Moon | 9.50° Aquarius | 11 | 11 | Satabhisha 1 | Sagittarius |
| Mars | 2.81° Taurus | 2 | 2 | Krittika 2 | Capricorn |
| Mercury | 9.46° Gemini | 3 | 3 | Aridra 1 | Sagittarius |
| Jupiter | 26.12° Capricorn | 10 | 11 | Dhanishta 1 | Leo |
| Venus | 3.28° Aries | 1 | 1 | Aswini 1 | Aries |
| Saturn (R) | 6.38° Capricorn | 10 | 10 | Uttarashadha 3 | Aquarius |
| Rahu (R) | 11.57° Libra | 7 | 7 | Swati 2 | Capricorn |
| Ketu (R) | 11.57° Aries | 1 | 1 | Aswini 4 | Cancer |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 106; heading at line 5931; write-up span lines 5924-5939 (16 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 5924-5939 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame moon; karaka Jupiter; borderline_shifted True.

Count: Both outcomes are indicated: 2 rules of Raman's point for it and 1 against. On 2,000 random charts, 69% show the same for this matter (typically 2 for and 2 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | afflicted | 563 |  |
| _decide_clauses | afflicted | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "mixed"`) |
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "favourable"`) |
| _decide | mixed | 626 |  |
| _decisive_affliction | mixed | 1615 |  |
| _catastrophic_severity_gate | mixed | 1647 |  |
| _yoga_modulate | mixed | 1571 |  |
| _dhana_floor | mixed | 1726 |  |
| _blemishless_venus_floor | mixed | 1683 |  |
| _saptamsa_gate | afflicted | 2197 |  |
| _fertility_gate | afflicted | 2122 |  |
| _longevity_span | afflicted | 2046 |  |
| _marital_bond_gate | afflicted | 1897 |  |
| _malefic_occupancy_gate | afflicted | 1928 |  |
| _marginal_karaka_gate | afflicted | 1974 |  |
| _yogakaraka_lagna_gate | afflicted | 2017 |  |
| _powerful_dhana_kendra_floor | afflicted | 1775 |  |
| _event_timing | afflicted | 1870 |  |

Metadata: saptamsa=weakens; beeja_kshetra=weak; varga_D7=Mercury:neutral|Jupiter:debil; sav_bindus=28:average; active_periods=Mercury(lord) 1951-1968; Jupiter(karaka) 1916-1932; Ketu(timer) 1968-1975; Sun(timer) 1995-2001; Moon(timer) 2001-2011

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Mercury |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 402.088 |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN, FERTILITY_GATE |
| fired counts | benefic 2, malefic 1, neutral 1, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Sun |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 402.088 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 1, neutral 1, blemish 0 |

### Fired rules (lead frame)

- **H5.L.2** (benefic; polarity benefic; evaluable/lord_in_house; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5119`
  - reading: beautiful wife and well-behaving children; gains from Government/King; becomes learned and a good astrologer
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA0F950>`
  - cited lines: `HTJAH-I:5116-5122` (±3, Raman, natal); text in the local packet
- **H5.C.1** (benefic; polarity benefic; evaluable/combination; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5183`
  - reading: benefic associations or aspects on the 5th → there will be children
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EA0D040>`
  - cited lines: `HTJAH-I:5180-5186` (±3, Raman, natal); text in the local packet
- **H5.C.10** (malefic; polarity malefic; evaluable/combination; signification children; frame LAGNA; branch afflicted) cite `HTJAH-I:5193`
  - reading: 5th aspected by a malefic AND the 5th lord joining an evil planet → children die early
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EA0D640>`
  - cited lines: `HTJAH-I:5190-5196` (±3, Raman, natal); text in the local packet
- **H5.C.21** (neutral; polarity neutral; evaluable/combination; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5206`
  - reading: 5th lord in the 1st, 2nd or 3rd → the first child will be male
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EA0E510>`
  - cited lines: `HTJAH-I:5203-5209` (±3, Raman, natal); text in the local packet
