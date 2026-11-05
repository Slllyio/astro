# NH.chart_73 H2/wealth

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: favourable.

## a. Golden record

- id: `NH.chart_73`; name: AN EXAMPLE FOR POVERTY; book: NH; case_type: worked_example; confidence: 0.25
- birth: none in the golden (cast from stated positions)
- cast: cast from the positions Raman printed
- lagna_sign: 10
- stated_positions: Sun sign None bhava 10 lon 196.0333; Moon sign None bhava 9 lon 175.5167; Mars sign None bhava 10 lon 184.8; Mercury sign None bhava 10 lon 186.4333; Jupiter sign None bhava 10 lon 186.7; Venus sign None bhava 10 lon 189.55; Saturn sign None bhava 4 lon 9.9167; Rahu sign None bhava 4 lon 28.55; Ketu sign None bhava 10 lon 208.55
- expected verdict: **afflicted** (wealth; review CONFIRMED)
- verdict_prose: whilst it should have made the subject a millionaire it has been so spoiled by the evil combinations that the person was a common man, hardly getting 100 chips a month.
- citations: NH:14754
- located in the book by the study tool: NH:14872-14873

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 5.00° Capricorn | 1 | 1 |  |  |
| Sun | 16.03° Libra | 10 | 10 | Swati 3 | Aquarius |
| Moon | 25.52° Virgo | 9 | 9 | Chitta 1 | Leo |
| Mars | 4.80° Libra | 10 | 10 | Chitta 4 | Scorpio |
| Mercury | 6.43° Libra | 10 | 10 | Chitta 4 | Scorpio |
| Jupiter | 6.70° Libra | 10 | 10 | Swati 1 | Sagittarius |
| Venus | 9.55° Libra | 10 | 10 | Swati 1 | Sagittarius |
| Saturn | 9.92° Aries | 4 | 4 | Aswini 3 | Gemini |
| Rahu | 28.55° Aries | 4 | 4 | Krittika 1 | Sagittarius |
| Ketu | 28.55° Libra | 10 | 10 | Visakha 3 | Gemini |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 73; heading at line 14749; write-up span lines 14749-14884 (136 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 14749-14884 (full write-up)

## c. The engine's view

Verdict **favourable**; degree mild; lead frame lagna; karaka Jupiter; borderline_shifted False.

Count: Only favourable indications: 2 rules for, none against. On 2,000 random charts, 10% show the same for this matter (typically 2 for and 2 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 732 | 3. Track-B fallback — no Shadbala -> decide on rule polarity / maraka alone. (`base = "favourable"`) |
| _navamsa_modulate | favourable | 547 |  |
| _decide_clauses | favourable | 732 | 3. Track-B fallback — no Shadbala -> decide on rule polarity / maraka alone. (`base = "favourable"`) |
| _decide | favourable | 627 |  |
| _decisive_affliction | favourable | 1615 |  |
| _catastrophic_severity_gate | favourable | 1647 |  |
| _yoga_modulate | favourable | 1571 |  |
| _dhana_floor | favourable | 1726 |  |
| _blemishless_venus_floor | favourable | 1683 |  |
| _saptamsa_gate | favourable | 2179 |  |
| _fertility_gate | favourable | 2111 |  |
| _longevity_span | favourable | 2046 |  |
| _marital_bond_gate | favourable | 1897 |  |
| _malefic_occupancy_gate | favourable | 1933 |  |
| _marginal_karaka_gate | favourable | 1974 |  |
| _yogakaraka_lagna_gate | favourable | 2017 |  |
| _powerful_dhana_kendra_floor | favourable | 1775 |  |
| _event_timing | favourable | 1831 |  |

Metadata: sav_bindus=32:strong

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Saturn |
| lord_strong | None |
| karaka | Jupiter |
| karaka_strong | None |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 2, malefic 0, neutral 0, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Venus |
| lord_strong | True |
| karaka | Jupiter |
| karaka_strong | None |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | none |
| fired counts | benefic 2, malefic 0, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H2.L.4** (benefic; polarity benefic; evaluable/lord_in_house; signification wealth; frame LAGNA; branch general) cite `HTJAH-I:2355`
  - reading: the results of the lord in the 3rd apply in addition; spends money for his own happiness; highly frugal in dealing with money
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038E983E90>`
  - cited lines: `HTJAH-I:2352-2358` (±3, Raman, natal); text in the local packet
- **H2.C.40** (benefic; polarity benefic; evaluable/combination; signification wealth; frame ARUDHA; branch fortified) cite `HTJAH-I:2498`
  - reading: Arudha Lagna in 11th, 4th, 5th or 7th from Lagna → becomes rich
  - condition: `<app.raman_saab.doctrine.rule_sets.house_02_dhana.combinations._ArudhaLagnaInHousesFromLagna object at 0x000002038E980A70>`
  - cited lines: `HTJAH-I:2495-2501` (±3, Raman, natal); text in the local packet
