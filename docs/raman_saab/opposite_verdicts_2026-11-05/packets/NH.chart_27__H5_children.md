# NH.chart_27 H5/children

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `NH.chart_27`; name: QUEEN VICTORIA; book: NH; case_type: worked_example; confidence: 0.6
- birth: none in the golden (cast from stated positions)
- cast: cast from the positions Raman printed
- lagna_sign: 2
- stated_positions: Sun sign None bhava 1 lon 42.2167; Moon sign None bhava 1 lon 43.6667; Mars sign None bhava 11 lon 357.7; Mercury sign None bhava 12 lon 19.0333; Jupiter sign None bhava 9 lon 297.0667; Venus sign None bhava 12 lon 6.75; Saturn sign None bhava 11 lon 338.8833; Rahu sign None bhava 11 lon 358.2833; Ketu sign None bhava 5 lon 168.2833
- expected verdict: **favourable** (children; review CONFIRMED)
- verdict_prose: All these factors account for the queen's prolific motherhood. It will be seen that she gave birth to nine children.
- citations: NH:6692
- located in the book by the study tool: NH:6769-6770

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 5.00° Taurus | 1 | 1 |  |  |
| Sun | 12.22° Taurus | 1 | 1 | Rohini 1 | Aries |
| Moon | 13.67° Taurus | 1 | 1 | Rohini 2 | Taurus |
| Mars | 27.70° Pisces | 11 | 11 | Revati 4 | Pisces |
| Mercury | 19.03° Aries | 12 | 12 | Bharani 2 | Virgo |
| Jupiter | 27.07° Capricorn | 9 | 9 | Dhanishta 2 | Virgo |
| Venus | 6.75° Aries | 12 | 12 | Aswini 3 | Gemini |
| Saturn | 8.88° Pisces | 11 | 11 | Uttarabhadra 2 | Virgo |
| Rahu | 28.28° Pisces | 11 | 11 | Revati 4 | Pisces |
| Ketu | 18.28° Virgo | 5 | 5 | Hasta 3 | Gemini |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 27; heading at line 6687; write-up span lines 6687-6836 (150 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 6687-6836 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame lagna; karaka Jupiter; borderline_shifted True.

Count: Both outcomes are indicated: 1 rule of Raman's point for it and 3 against. On 2,000 random charts, 69% show the same for this matter (typically 2 for and 2 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | mixed | 564 |  |
| _decide_clauses | mixed | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "mixed"`) |
| _decide | mixed | 622 |  |
| _decisive_affliction | mixed | 1615 |  |
| _catastrophic_severity_gate | mixed | 1647 |  |
| _yoga_modulate | mixed | 1592 |  |
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
| _event_timing | afflicted | 1831 |  |

Metadata: yoga=Y.KALANIRDESAT_PUTRANASA:noted; saptamsa=weakens; beeja_kshetra=weak; varga_D7=Mercury:neutral|Jupiter:debil; sav_bindus=25:weak

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Mercury |
| lord_strong | None |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | FERTILITY_GATE |
| fired counts | benefic 1, malefic 3, neutral 1, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Mercury |
| lord_strong | None |
| karaka | Jupiter |
| karaka_strong | True |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 1, malefic 3, neutral 1, blemish 0 |

### Fired rules (lead frame)

- **H5.C.1** (benefic; polarity benefic; evaluable/combination; signification children; frame LAGNA; branch fortified) cite `HTJAH-I:5183`
  - reading: benefic associations or aspects on the 5th → there will be children
  - condition: `<app.raman_saab.doctrine.conditions.Or object at 0x000002038EA0D040>`
  - cited lines: `HTJAH-I:5180-5186` (±3, Raman, natal); text in the local packet
- **H5.P.Ketu** (malefic; polarity malefic; evaluable/planet_in_house; signification children; frame LAGNA; branch general) cite `HTJAH-I:5265`
  - reading: loss of children; stomach trouble; strange experiences in emotions and feelings; later inclination to spirituality; afflicted → criminal tendencies, lacks shame, vindictive; lacks the human touch toward one or two of the issues; with Venus → platonic love; Mars the afflicter → many dangers, family extinguished
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EA10950>`
  - cited lines: `HTJAH-I:5262-5268` (±3, Raman, natal); text in the local packet
- **H5.C.9** (malefic; polarity malefic; evaluable/combination; signification children; frame LAGNA; branch afflicted) cite `HTJAH-I:5193`
  - reading: 5th lord hemmed between malefics (papakartari) → children die early
  - condition: `<app.raman_saab.doctrine.rule_sets.house_05_putra.combinations._LordHemmedBy object at 0x000002038EA0D520>`
  - cited lines: `HTJAH-I:5190-5196` (±3, Raman, natal); text in the local packet
- **H5.C.39** (malefic; polarity malefic; evaluable/combination; signification children; frame CHANDRA; branch afflicted) cite `HTJAH-I:5826`
  - reading: two or more natural malefics occupy or aspect the 5th from Chandra Lagna → the house of children is strongly blemished from the Moon
  - condition: `<app.raman_saab.doctrine.rule_sets.house_05_putra.combinations._FifthFromMoonMaleficConvergence object at 0x000002038EA0F5F0>`
  - cited lines: `HTJAH-I:5823-5829` (±3, Raman, natal); text in the local packet
- **H5.L.12** (neutral; polarity neutral; evaluable/lord_in_house; signification children; frame LAGNA; branch general) cite `HTJAH-I:5169`
  - reading: quest for the Ultimate Reality; non-attachment; spiritual; wanders; ultimately attains Moksha
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA10200>`
  - cited lines: `HTJAH-I:5166-5172` (±3, Raman, natal); text in the local packet
