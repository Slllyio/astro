# HTJAH-II.h10_04 H10/profession_authority

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `HTJAH-II.h10_04`; name: Chart 198 (H10 profession_authority); book: HTJAH-II; case_type: worked_example; confidence: 0.6
- birth: {"dt": "1889-11-14T23:03:00", "tz": 5.4667, "lat": 25.4167, "lon": 82}
- cast: cast from the birth data 1889-11-14 23:03:00 (UTC+5.4667)
- lagna_sign: 4
- stated_positions: none
- expected verdict: **favourable** (profession_authority; review CONFIRMED)
- verdict_prose: Idol of India, Prime Minister — but Moon-dominated: emotional, vacillating; insignificant Mars made him weaker as administrator than as thinker.
- citations: HTJAH-II:13503
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 24.39° Cancer | 1 | 1 |  |  |
| Sun | 1.71° Scorpio | 5 | 4 | Visakha 4 | Cancer |
| Moon | 19.32° Cancer | 1 | 1 | Aslesha 1 | Sagittarius |
| Mars | 11.43° Virgo | 3 | 3 | Hasta 1 | Aries |
| Mercury | 18.58° Libra | 4 | 4 | Swati 4 | Pisces |
| Jupiter | 16.62° Sagittarius | 6 | 6 | Poorvashadha 1 | Leo |
| Venus | 8.80° Libra | 4 | 4 | Swati 1 | Sagittarius |
| Saturn | 12.24° Leo | 2 | 2 | Makha 4 | Cancer |
| Rahu (R) | 14.17° Gemini | 12 | 12 | Aridra 3 | Aquarius |
| Ketu (R) | 14.17° Sagittarius | 6 | 6 | Poorvashadha 1 | Leo |

## b. Raman's write-up

File: `how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md`. Chart number 198; heading at line 13521; write-up span lines 13503-13553 (51 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 13503-13553 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree moderate; lead frame lagna; karaka Sun; borderline_shifted False.

Count: Only favourable indications: 1 rule for, none against. On 2,000 random charts, 51% show the same for this matter (typically 1 for and 0 against).

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
| _saptamsa_gate | afflicted | 2179 |  |
| _fertility_gate | afflicted | 2111 |  |
| _longevity_span | afflicted | 2046 |  |
| _marital_bond_gate | afflicted | 1897 |  |
| _malefic_occupancy_gate | afflicted | 1928 |  |
| _marginal_karaka_gate | afflicted | 1974 |  |
| _yogakaraka_lagna_gate | afflicted | 2017 |  |
| _powerful_dhana_kendra_floor | afflicted | 1775 |  |
| _event_timing | afflicted | 1870 |  |

Metadata: sav_bindus=26:average; active_periods=Mars(lord) 1946-1953; Sun(karaka) 1930-1936; Mercury(timer) 1889-1903; Ketu(timer) 1903-1910; Venus(timer) 1910-1930

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Mars |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | False |
| bhava_bala | 405.11 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 0, neutral 1, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Mars |
| lord_strong | True |
| karaka | Sun |
| karaka_strong | False |
| bhava_bala | 405.11 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 1, malefic 0, neutral 1, blemish 0 |

### Fired rules (lead frame)

- **H10.C.63** (benefic; polarity benefic; evaluable/combination; signification career; frame LAGNA; branch fortified) cite `NH:12473`
  - reading: three or more benefics casting their rays on the 10th → the house of Karma is the centre of beneficial convergence; eminence in career
  - condition: `<app.raman_saab.doctrine.rule_sets.house_10_karma.combinations._BeneficsConvergeOnTenth object at 0x000002038EAADCA0>`
  - cited lines: `NH:12470-12476` (±3, Raman, natal); text in the local packet
- **H10.L.3** (neutral; polarity neutral; evaluable/lord_in_house; signification career; frame LAGNA; branch fortified) cite `HTJAH-II:9474`
  - reading: may have to travel constantly on short journeys; a speaker or writer of celebrity; brothers may be instrumental to some extent in advancing his career
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EAAE210>`
  - cited lines: `HTJAH-II:9471-9477` (±3, Raman, natal); text in the local packet
