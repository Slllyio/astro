# HTJAH-II.h11_08 H11/gains

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `HTJAH-II.h11_08`; name: Chart 217 (H11 gains); book: HTJAH-II; case_type: worked_example; confidence: 0.6
- birth: {"dt": "1922-10-28T20:40:00", "tz": 5.5, "lat": 9.917, "lon": 78.117}
- cast: cast from the birth data 1922-10-28 20:40:00 (UTC+5.5)
- lagna_sign: 2
- stated_positions: none
- expected verdict: **favourable** (gains; review CONFIRMED)
- verdict_prose: Powerful Dhana Yoga; chart strongly placed for financial gains — gave the native engineering industries worth several crores.
- citations: HTJAH-II:15242
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 25.80° Taurus | 1 | 1 |  |  |
| Sun | 13.09° Libra | 6 | 6 | Swati 2 | Capricorn |
| Moon | 25.18° Capricorn | 9 | 9 | Dhanishta 1 | Leo |
| Mars | 7.17° Capricorn | 9 | 8 (sandhi) | Uttarashadha 4 | Pisces |
| Mercury | 24.90° Virgo | 5 | 5 | Chitta 1 | Leo |
| Jupiter | 9.07° Libra | 6 | 6 | Swati 1 | Sagittarius |
| Venus | 17.57° Scorpio | 7 | 7 | Jyeshta 1 | Sagittarius |
| Saturn | 22.25° Virgo | 5 | 5 | Hasta 4 | Cancer |
| Rahu (R) | 6.42° Virgo | 5 | 5 | Uttara 3 | Aquarius |
| Ketu (R) | 6.42° Pisces | 11 | 11 | Uttarabhadra 1 | Leo |

## b. Raman's write-up

File: `how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md`. Chart number 217; heading at line 15191; write-up span lines 15191-15249 (59 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 15191-15249 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree strong; lead frame lagna; karaka Jupiter; borderline_shifted False.

Count: Only favourable indications: 2 rules for, none against. On 2,000 random charts, 43% show the same for this matter (typically 3 for and 1 against).

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
| _dhana_floor | afflicted | 1729 |  |
| _blemishless_venus_floor | afflicted | 1683 |  |
| _saptamsa_gate | afflicted | 2179 |  |
| _fertility_gate | afflicted | 2111 |  |
| _longevity_span | afflicted | 2046 |  |
| _marital_bond_gate | afflicted | 1897 |  |
| _malefic_occupancy_gate | afflicted | 1928 |  |
| _marginal_karaka_gate | afflicted | 1974 |  |
| _yogakaraka_lagna_gate | afflicted | 2017 |  |
| _powerful_dhana_kendra_floor | afflicted | 1779 |  |
| _event_timing | afflicted | 1870 |  |

Metadata: sav_bindus=30:strong; active_periods=Jupiter(karaka) 1946-1962; Mars(timer) 1922-1928; Rahu(timer) 1928-1946; Saturn(timer) 1962-1981; Mercury(timer) 1981-1998

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Jupiter |
| lord_strong | False |
| karaka | Jupiter |
| karaka_strong | False |
| bhava_bala | 405.76 |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | True |
| lord_hard_afflicted | True |
| flags | LORD_KARAKA_IDENTITY, LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 0, neutral 4, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Mars |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | False |
| bhava_bala | 405.76 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 2, malefic 0, neutral 4, blemish 0 |

### Fired rules (lead frame)

- **H11.C.8** (benefic; polarity benefic; evaluable/combination; signification gains; frame LAGNA; branch fortified) cite `HTJAH-II:14392`
  - reading: the 11th lord well placed in a kendra or trikona from the Ascendant, OR malefics strong in the 11th → the native is immensely wealthy
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EAB15B0>`
  - cited lines: `HTJAH-II:14389-14395` (±3, Raman, natal); text in the local packet
- **H11.C.11** (benefic; polarity benefic; evaluable/combination; signification gains; frame MOON; branch fortified) cite `HTJAH-II:14414`
  - reading: the 2nd, 9th or 11th lord in a kendra from the Moon AND Jupiter owning the 11th → similar (ruler) results
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAB19D0>`
  - cited lines: `HTJAH-II:14411-14417` (±3, Raman, natal); text in the local packet
- **H11.L.6** (neutral; polarity neutral; evaluable/lord_in_house; signification gains; frame LAGNA; branch general) cite `HTJAH-II:14293`
  - reading: gains money through maternal relatives, litigation and running nursing-homes
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EAB4AA0>`
  - cited lines: `HTJAH-II:14290-14296` (±3, Raman, natal); text in the local packet
- **H11.L.6a** (neutral; polarity neutral; evaluable/lord_in_house; signification gains; frame LAGNA; branch general) cite `HTJAH-II:14294`
  - reading: the 11th lord afflicted in the 6th - thrives on setting person against person, involves himself in other people's quarrels and anti-social activity
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAB4C20>`
  - cited lines: `HTJAH-II:14291-14297` (±3, Raman, natal); text in the local packet
- **H11.L.6b** (neutral; polarity neutral; evaluable/lord_in_house; signification gains; frame LAGNA; branch general) cite `HTJAH-II:14297`
  - reading: malefics afflicting the 11th lord - the native may lose through similar sources
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAB4D40>`
  - cited lines: `HTJAH-II:14294-14300` (±3, Raman, natal); text in the local packet
- **H11.P.Ketu** (neutral; polarity neutral; evaluable/planet_in_house; signification gains; frame LAGNA; branch general) cite `HTJAH-II:14486`
  - reading: habit of hoarding; may get a monetary windfall through speculation such as lottery, horse-racing and the stock exchange; noble and possessed of many good qualities of head and heart; succeeds in all his ventures; participates in charitable and similar works of beneficence
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EAB5E20>`
  - cited lines: `HTJAH-II:14483-14489` (±3, Raman, natal); text in the local packet
