# NH.chart_46 H12/moksha

Engine **afflicted** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `NH.chart_46`; name: SRI RAMANA MAHARSHI; book: NH; case_type: worked_example; confidence: 0.6
- birth: none in the golden (cast from stated positions)
- cast: cast from the positions Raman printed
- lagna_sign: 7
- stated_positions: Sun sign None bhava 3 lon 257.0667; Moon sign None bhava 9 lon 89.9667; Mars sign None bhava 7 lon 23.4333; Mercury sign None bhava 2 lon 234.6; Jupiter sign None bhava 5 lon 317.95; Venus sign None bhava 2 lon 211.95; Saturn sign None bhava 6 lon 348.5333; Rahu sign None bhava 3 lon 265.3833; Ketu sign None bhava 9 lon 85.3833
- expected verdict: **favourable** (moksha; review CONFIRMED)
- verdict_prose: Jaimini's dictum that Ketu in the 12th from Karakamsa gives one Kaivalya or final emancipation is literally applicable in this case.
- citations: NH:9901
- located in the book by the study tool: NH:10040-10042

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 5.00° Libra | 1 | 1 |  |  |
| Sun | 17.07° Sagittarius | 3 | 3 | Poorvashadha 2 | Virgo |
| Moon | 29.97° Gemini | 9 | 9 | Punarvasu 3 | Gemini |
| Mars | 23.43° Aries | 7 | 7 | Bharani 4 | Scorpio |
| Mercury | 24.60° Scorpio | 2 | 2 | Jyeshta 3 | Aquarius |
| Jupiter | 17.95° Aquarius | 5 | 5 | Satabhisha 4 | Pisces |
| Venus | 1.95° Scorpio | 2 | 2 | Visakha 4 | Cancer |
| Saturn | 18.53° Pisces | 6 | 6 | Revati 1 | Sagittarius |
| Rahu | 25.38° Sagittarius | 3 | 3 | Poorvashadha 4 | Scorpio |
| Ketu | 25.38° Gemini | 9 | 9 | Punarvasu 2 | Taurus |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 46; heading at line 9896; write-up span lines 9896-10079 (184 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 9896-10079 (full write-up)

## c. The engine's view

Verdict **afflicted**; degree mild; lead frame lagna; karaka Saturn; borderline_shifted False.

Count: Only unfavourable indications: 3 rules against, none for. On 2,000 random charts, 57% show the same for this matter (typically 0 for and 3 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | afflicted | 547 |  |
| _decide_clauses | afflicted | 732 | 3. Track-B fallback — no Shadbala -> decide on rule polarity / maraka alone. (`return _clamp_longevity(v, guarded), shifted`) |
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
| _event_timing | afflicted | 1831 |  |

Metadata: sav_bindus=31:strong

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Mercury |
| lord_strong | None |
| karaka | Saturn |
| karaka_strong | None |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 0, malefic 3, neutral 0, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Venus |
| lord_strong | None |
| karaka | Saturn |
| karaka_strong | None |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | none |
| fired counts | benefic 0, malefic 3, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H12.L.2** (malefic; polarity malefic; evaluable/lord_in_house; signification loss_moksha; frame LAGNA; branch general) cite `HTJAH-II:16138`
  - reading: financial losses, debts, nefarious activity, untimely meals, poor eyesight, disharmonious family
  - condition: `<app.raman_saab.doctrine.conditions.LordIn object at 0x000002038EABC260>`
  - cited lines: `HTJAH-II:16135-16141` (±3, Raman, natal); text in the local packet
- **H12.C.C5** (malefic; polarity malefic; evaluable/combination; signification loss_moksha; frame KARAKA; branch afflicted) cite `HTJAH-II:16410`
  - reading: a malefic in the 2nd/4th/5th FROM Jupiter → the native will be poor
  - condition: `<app.raman_saab.doctrine.conditions.ClassInHouseFrom object at 0x000002038EAB7CE0>`
  - cited lines: `HTJAH-II:16407-16413` (±3, Raman, natal); text in the local packet
- **H12.C.F1** (malefic; polarity malefic; evaluable/combination; signification moksha; frame LAGNA; branch afflicted) cite `HTJAH-II:16491`
  - reading: the 12th aspected/occupied by Saturn or Mandi AND the 12th lord in a Vipat (3rd)/Pratyak (5th)/Naidhana (7th) constellation from Janma Nakshatra → calamities, vicious conduct, goes to hell after death (Mandi leg absent on stated-position charts, which carry no upagrahas)
  - condition: `<app.raman_saab.doctrine.conditions.And object at 0x000002038EAB9BE0>`
  - cited lines: `HTJAH-II:16488-16494` (±3, Raman, natal); text in the local packet
