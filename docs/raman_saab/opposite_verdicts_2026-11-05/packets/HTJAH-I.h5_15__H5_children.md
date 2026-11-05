# HTJAH-I.h5_15 H5/children

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `HTJAH-I.h5_15`; name: Chart 105 (H5 children); book: HTJAH-I; case_type: worked_example; confidence: 0.55
- birth: {"dt": "1906-01-06T17:24:00", "tz": 5.5, "lat": 30.0, "lon": 78.0}
- cast: cast from the birth data 1906-01-06 17:24:00 (UTC+5.5)
- lagna_sign: 3
- stated_positions: none
- expected verdict: **favourable** (children; review CONFIRMED)
- verdict_prose: 5th house fairly well disposed; counting gives about 9 children — the native had 8 issues, out of which one died.
- citations: HTJAH-I:5906
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 23.28° Gemini | 1 | 1 |  |  |
| Sun | 24.19° Sagittarius | 7 | 7 | Poorvashadha 4 | Scorpio |
| Moon | 6.36° Taurus | 12 | 12 | Krittika 3 | Aquarius |
| Mars | 16.50° Aquarius | 9 | 9 | Satabhisha 3 | Aquarius |
| Mercury | 1.28° Sagittarius | 7 | 6 | Moola 1 | Aries |
| Jupiter (R) | 5.76° Taurus | 12 | 12 | Krittika 3 | Aquarius |
| Venus | 14.85° Sagittarius | 7 | 7 | Poorvashadha 1 | Leo |
| Saturn | 8.70° Aquarius | 9 | 9 | Satabhisha 1 | Sagittarius |
| Rahu (R) | 1.75° Leo | 3 | 2 (sandhi) | Makha 1 | Aries |
| Ketu (R) | 1.75° Aquarius | 9 | 8 (sandhi) | Dhanishta 3 | Libra |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 105; heading at line 5912; write-up span lines 5906-5923 (18 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 5906-5923 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame moon; karaka Jupiter; borderline_shifted False.

Count: Only favourable indications: 1 rule for, none against. On 2,000 random charts, 11% show the same for this matter (typically 2 for and 2 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | afflicted | 547 |  |
| _decide_clauses | afflicted | 769 | 6. a weak pillar with malefic / weak-bhava / maraka pressure -> afflicted... (`base = "afflicted"`) |
| _decide | afflicted | 622 |  |
| _decisive_affliction | afflicted | 1611 |  |
| _catastrophic_severity_gate | afflicted | 1647 |  |
| _yoga_modulate | afflicted | 1571 |  |
| _dhana_floor | afflicted | 1726 |  |
| _blemishless_venus_floor | afflicted | 1683 |  |
| _saptamsa_gate | afflicted | 2197 |  |
| _fertility_gate | afflicted | 2122 |  |
| _longevity_span | afflicted | 2046 |  |
| _marital_bond_gate | afflicted | 1897 |  |
| _malefic_occupancy_gate | afflicted | 1928 |  |
| _marginal_karaka_gate | afflicted | 1974 |  |
| _yogakaraka_lagna_gate | afflicted | 2017 |  |
| _powerful_dhana_kendra_floor | afflicted | 1775 |  |
| _event_timing | afflicted | 1870 |  |

Metadata: saptamsa=confirms; beeja_kshetra=weak; varga_D7=Mercury:neutral|Jupiter:own; sav_bindus=39:strong; active_periods=Mercury(lord) 1977-1994; Jupiter(karaka) 1942-1958; Sun(timer) 1906-1907; Rahu(timer) 1924-1942; Venus(timer) 2001-2021

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | moon |
| lord | Mercury |
| lord_strong | False |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 402.004 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN, FERTILITY_GATE |
| fired counts | benefic 1, malefic 0, neutral 0, blemish 0 |

**Alternate frame (lagna, does not set the verdict)**

| field | value |
|---|---|
| frame | lagna |
| lord | Venus |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 402.004 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 0, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H5.L.7** (benefic; polarity benefic; evaluable/lord_in_house; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5147`
  - reading: son lives abroad and attains distinction, wealth and fame; or many issues; renowned, learned, prosperous, devoted to master, charming personality
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA0FD10>`
  - cited lines: `HTJAH-I:5144-5150` (±3, Raman, natal); text in the local packet
