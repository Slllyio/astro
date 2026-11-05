# HTJAH-I.chart_42 H2/wealth

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `HTJAH-I.chart_42`; name: Chart 42 (Ordinary man Rs. 50-60/month, Dwirdwadasa); book: HTJAH-I; case_type: worked_example; confidence: 0.5
- birth: {"dt": "1909-07-03T21:01:00", "tz": 5.1722, "lat": 13.0, "lon": 77.5833, "rectified": "Raman: Jupiter lord of the 3rd and 12th, in the 8th from Lagna; 2nd lord in the 3rd; Mars in the 2nd (bhava) (HTJAH-I:2790-2798) -> Capricorn Lagna (end of sign; Mars early Pisces and Saturn early Aries fall in bhavas 2 and 3). The printed 9-14 p.m. casts Aquarius 2.9deg. Re-timed -13 min from the printed 21:14 to the smallest shift that puts the Lagna 0.5deg inside Raman's sign, after the HTJAH-I.chart_35 precedent; the re-timed chart was checked against every feature quoted (2026-10-24)."}
- cast: cast from the birth data 1909-07-03 21:01:00 (UTC+5.1722)
- lagna_sign: 10
- stated_positions: none
- expected verdict: **afflicted** (wealth; review CONFIRMED)
- verdict_prose: Mars in 2nd; Jupiter (3L+12L) aspects the 2nd -- both bad; 2nd lord Saturn in 3rd (bad for finance); Dwirdwadasa positions throughout; ordinary man drawing Rs. 50-60/month.
- citations: HTJAH-I:2788-2805
- located in the book by the study tool: not located (prose is a summary or the words are not near the cited lines)

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 29.26° Capricorn | 1 | 1 |  |  |
| Sun | 19.89° Gemini | 6 | 6 | Aridra 4 | Pisces |
| Moon | 21.79° Sagittarius | 12 | 12 | Poorvashadha 3 | Libra |
| Mars | 1.00° Pisces | 3 | 2 | Poorvabhadra 4 | Cancer |
| Mercury | 29.83° Taurus | 5 | 5 | Mrigasira 2 | Virgo |
| Jupiter | 18.76° Leo | 8 | 8 | Pubba 2 | Virgo |
| Venus | 7.60° Cancer | 7 | 6 | Pushya 2 | Virgo |
| Saturn | 1.18° Aries | 4 | 3 | Aswini 1 | Aries |
| Rahu (R) | 24.22° Taurus | 5 | 5 | Mrigasira 1 | Leo |
| Ketu (R) | 24.22° Scorpio | 11 | 11 | Jyeshta 3 | Aquarius |

## b. Raman's write-up

File: `how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`. Chart number 42; heading at line 2788; write-up span lines 2788-2806 (19 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 2788-2806 (full write-up)

## c. The engine's view

Verdict **favourable**; degree strong; lead frame lagna; karaka Jupiter; borderline_shifted False.

Count: Both outcomes are indicated: 3 rules of Raman's point for it and 1 against. On 2,000 random charts, 82% show the same for this matter (typically 2 for and 2 against).

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

Metadata: sav_bindus=29:average; active_periods=Saturn(lord) 1973-1992; Jupiter(karaka) 1957-1973; Venus(timer) 1909-1916; Mars(timer) 1932-1939; Rahu(timer) 1939-1957

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Saturn |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 439.029 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 3, malefic 1, neutral 0, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Saturn |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | 439.029 |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | True |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | LONGEVITY_UNKNOWN |
| fired counts | benefic 3, malefic 1, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H2.L.4** (benefic; polarity benefic; evaluable/lord_in_house; signification wealth; frame LAGNA; branch fortified) cite `HTJAH-I:2355`
  - reading: earns as automobile dealer/agent, agriculturist, landlord or commission agent; benefited by maternal relations
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038E983E90>`
  - cited lines: `HTJAH-I:2352-2358` (±3, Raman, natal); text in the local packet
- **H2.C.40** (benefic; polarity benefic; evaluable/combination; signification wealth; frame ARUDHA; branch fortified) cite `HTJAH-I:2498`
  - reading: Arudha Lagna in 11th, 4th, 5th or 7th from Lagna → becomes rich
  - condition: `<app.raman_saab.doctrine.rule_sets.house_02_dhana.combinations._ArudhaLagnaInHousesFromLagna object at 0x000002038E980A70>`
  - cited lines: `HTJAH-I:2495-2501` (±3, Raman, natal); text in the local packet
- **H2.C.65a** (benefic; polarity benefic; evaluable/combination; signification wealth; frame LAGNA; branch fortified) cite `HTJAH-I:2945`
  - reading: Mars and Moon in mutual Kendra → gives rise to something like Chandramangala Yoga (a Chandramangala-grade wealth yoga from angular disposition)
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038E982870>`
  - cited lines: `HTJAH-I:2942-2948` (±3, Raman, natal); text in the local packet
- **H2.C.69** (malefic; polarity malefic; evaluable/combination; signification wealth; frame LAGNA; branch afflicted) cite `HTJAH-I:2802`
  - reading: Planets bound in Dwirdwadasha (2nd/12th) web throughout → wealth severely curtailed (chart 42: 'ordinary man drawing Rs. 50-60/month'; chart 44: 'lost all fortune, Rs. 50000 debt')
  - condition: `<app.raman_saab.doctrine.conditions.AllPlanetsInDwirdwadasha object at 0x000002038E982BA0>`
  - cited lines: `HTJAH-I:2799-2805` (±3, Raman, natal); text in the local packet
