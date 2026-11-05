# NH.chart_22 H7/marital_happiness

Engine **favourable** vs Raman **afflicted**: opposite. House rollup: afflicted.

## a. Golden record

- id: `NH.chart_22`; name: MARIE ANTOINETTE; book: NH; case_type: worked_example; confidence: 0.6
- birth: none in the golden (cast from stated positions)
- cast: cast from the positions Raman printed
- lagna_sign: 3
- stated_positions: Sun sign None bhava 5 lon 201.0; Moon sign None bhava 5 lon 182.0; Mars sign None bhava 1 lon 87.0; Mercury sign None bhava 6 lon 224.0; Jupiter sign None bhava 4 lon 169.0; Venus sign None bhava 5 lon 202.0; Saturn sign None bhava 8 lon 274.0; Rahu sign None bhava 4 lon 156.0; Ketu sign None bhava 10 lon 336.0
- expected verdict: **afflicted** (marital_happiness; review CONFIRMED)
- verdict_prose: The 7th lord Jupiter with Rahu evidences that neither domestically nor publicly was the husband able to give Marie any happiness.
- citations: NH:5757
- located in the book by the study tool: NH:5930-5932

Chart as the engine casts it:

| Body | Longitude | Sign from Lagna | Bhava | Nakshatra | Navamsa |
|---|---|---|---|---|---|
| Lagna | 5.00° Gemini | 1 | 1 |  |  |
| Sun | 21.00° Libra | 5 | 5 | Visakha 1 | Aries |
| Moon | 2.00° Libra | 5 | 5 | Chitta 3 | Libra |
| Mars | 27.00° Gemini | 1 | 1 | Punarvasu 3 | Gemini |
| Mercury | 14.00° Scorpio | 6 | 6 | Anuradha 4 | Scorpio |
| Jupiter | 19.00° Virgo | 4 | 4 | Hasta 3 | Gemini |
| Venus | 22.00° Libra | 5 | 5 | Visakha 1 | Aries |
| Saturn | 4.00° Capricorn | 8 | 8 | Uttarashadha 3 | Aquarius |
| Rahu | 6.00° Virgo | 4 | 4 | Uttara 3 | Aquarius |
| Ketu | 6.00° Pisces | 10 | 10 | Uttarabhadra 1 | Leo |

## b. Raman's write-up

File: `notable_horoscopes_raman/chapter_001_full-text-unsplit.md`. Chart number 22; heading at line 5752; write-up span lines 5752-5968 (217 lines).

Book text is not committed (data/knowledge_library is gitignored). The verbatim, line-numbered text is in the local packet of the same name under `data/opposite_verdicts_2026-11-05/packets_with_text/` on the project PC.

Ranges in the local packet: 5752-5968 (full write-up)

## c. The engine's view

Verdict **favourable**; degree mild; lead frame lagna; karaka Venus; borderline_shifted False.

Count: Only favourable indications: 1 rule for, none against. On 2,000 random charts, 32% show the same for this matter (typically 1 for and 0 against).

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
| _marital_bond_gate | favourable | 1907 |  |
| _malefic_occupancy_gate | favourable | 1933 |  |
| _marginal_karaka_gate | favourable | 1974 |  |
| _yogakaraka_lagna_gate | favourable | 2017 |  |
| _powerful_dhana_kendra_floor | favourable | 1775 |  |
| _event_timing | favourable | 1831 |  |

Metadata: sav_bindus=20:weak

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Jupiter |
| lord_strong | None |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | False |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | MARAKA_NON_DEATH_GUARD |
| fired counts | benefic 1, malefic 0, neutral 0, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Mars |
| lord_strong | None |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | MARAKA_NON_DEATH_GUARD |
| fired counts | benefic 1, malefic 0, neutral 0, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Mars |
| lord_strong | None |
| karaka | Venus |
| karaka_strong | True |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | neutral |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | MARAKA_NON_DEATH_GUARD |
| fired counts | benefic 1, malefic 0, neutral 0, blemish 0 |

### Fired rules (lead frame)

- **H7.C.7** (benefic; polarity benefic; evaluable/combination; signification marital_happiness; frame KARAKA; branch fortified) cite `HTJAH-II:368`
  - reading: Venus exalted or in own sign (or Gopura/Vaiseshikamsa varga) → a good and beautiful wife
  - condition: `<app.raman_saab.doctrine.conditions.HasDignity object at 0x000002038EA18CB0>`
  - cited lines: `HTJAH-II:365-371` (±3, Raman, natal); text in the local packet
