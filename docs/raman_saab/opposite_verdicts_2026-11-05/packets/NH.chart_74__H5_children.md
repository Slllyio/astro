# NH.chart_74 H5/children

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `NH.chart_74`; name: AN   EXAMPLE   FOR  RAJA YOGA; book: NH; case_type: worked_example; confidence: 0.6
- birth: none in the golden (cast from stated positions)
- cast: cast from the positions Raman printed
- lagna_sign: 10
- stated_positions: Sun sign None bhava 10 lon 180.9; Moon sign None bhava 5 lon 34.2833; Mars sign None bhava 11 lon 229.5167; Mercury sign None bhava 10 lon 180.5333; Jupiter sign None bhava 6 lon 84.0167; Venus sign None bhava 9 lon 171.1667; Saturn sign None bhava 8 lon 124.3833; Rahu sign None bhava 11 lon 224.4; Ketu sign None bhava 5 lon 44.4
- expected verdict: **favourable** (children; review CONFIRMED)
- verdict_prose: the number of surviving children are 7.
- citations: NH:14890
- located in the book by the study tool: NH:14980-14981

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 5.00° Capricorn | 1 | 1 |  |  |
| Sun | 0.90° Libra | 10 | 10 | Chitta 3 | Libra |
| Moon | 4.28° Taurus | 5 | 5 | Krittika 3 | Aquarius |
| Mars | 19.52° Scorpio | 11 | 11 | Jyeshta 1 | Sagittarius |
| Mercury | 0.53° Libra | 10 | 10 | Chitta 3 | Libra |
| Jupiter | 24.02° Gemini | 6 | 6 | Punarvasu 2 | Taurus |
| Venus | 21.17° Virgo | 9 | 9 | Hasta 4 | Cancer |
| Saturn | 4.38° Leo | 8 | 8 | Makha 2 | Taurus |
| Rahu | 14.40° Scorpio | 11 | 11 | Anuradha 4 | Scorpio |
| Ketu | 14.40° Taurus | 5 | 5 | Rohini 2 | Taurus |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 74; heading at line 14885; write-up span lines 14885-15090 (206 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 14885-15090 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame lagna; karaka Jupiter; borderline_shifted True.

Count: Both outcomes are indicated: 3 rules of Raman's point for it and 2 against. On 2,000 random charts, 69% show the same for this matter (typically 2 for and 2 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | mixed | 550 |  |
| _decide_clauses | mixed | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "mixed"`) |
| _navamsa_modulate | mixed | 550 |  |
| _decide_clauses | mixed | 722 | 2. contradiction — weigh the PREPONDERANCE when benefic AND malefic both fire. (`base = "mixed"`) |
| _decide | mixed | 627 |  |
| _decisive_affliction | mixed | 1615 |  |
| _catastrophic_severity_gate | mixed | 1647 |  |
| _yoga_modulate | mixed | 1592 |  |
| _dhana_floor | mixed | 1726 |  |
| _blemishless_venus_floor | mixed | 1683 |  |
| _saptamsa_gate | afflicted | 2197 |  |
| _fertility_gate | afflicted | 2144 |  |
| _longevity_span | afflicted | 2046 |  |
| _marital_bond_gate | afflicted | 1897 |  |
| _malefic_occupancy_gate | afflicted | 1928 |  |
| _marginal_karaka_gate | afflicted | 1974 |  |
| _yogakaraka_lagna_gate | afflicted | 2017 |  |
| _powerful_dhana_kendra_floor | afflicted | 1775 |  |
| _event_timing | afflicted | 1831 |  |

Metadata: yoga=Y.KALANIRDESAT_PUTRANASA:noted; saptamsa=weakens; beeja_kshetra=one_weak_denied; sav_bindus=27:average

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Venus |
| lord_strong | None |
| karaka | Jupiter |
| karaka_strong | None |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | FERTILITY_GATE |
| fired counts | benefic 3, malefic 2, neutral 0, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Mercury |
| lord_strong | None |
| karaka | Jupiter |
| karaka_strong | None |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | confirms |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | True |
| flags | none |
| fired counts | benefic 3, malefic 2, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H5.L.9** (benefic; polarity benefic; evaluable/lord_in_house; signification children; frame LAGNA; branch afflicted) cite `HTJAH-I:5156`
  - reading: the 5th lord afflicted - earns divine wrath and consequent destruction of fortune
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EA0FE30>`
  - cited lines: `HTJAH-I:5153-5159` (±3, Raman, natal); text in the local packet
- **H5.P.Moon** (benefic; polarity benefic; evaluable/planet_in_house; signification children; frame LAGNA; branch general) cite `HTJAH-I:5236`
  - reading: clarity of mind; happiness from children; lands, gems and precious stones; a chance to serve the State; straightforward, truthful, learned, god-fearing, with no enemies; gains by speculation; one child becomes famous; gentlemanly
  - condition: `<app.raman_saab.doctrine.conditions.InRashiHouse object at 0x000002038EA10290>`
  - cited lines: `HTJAH-I:5233-5239` (±3, Raman, natal); text in the local packet
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
