# NH.chart_74 H7/marital_happiness

Engine **insufficient-evidence** vs Raman **favourable**: opposite. House rollup: afflicted.

## a. Golden record

- id: `NH.chart_74`; name: AN   EXAMPLE   FOR  RAJA YOGA; book: NH; case_type: worked_example; confidence: 0.6
- birth: none in the golden (cast from stated positions)
- cast: cast from the positions Raman printed
- lagna_sign: 10
- stated_positions: Sun sign None bhava 10 lon 180.9; Moon sign None bhava 5 lon 34.2833; Mars sign None bhava 11 lon 229.5167; Mercury sign None bhava 10 lon 180.5333; Jupiter sign None bhava 6 lon 84.0167; Venus sign None bhava 9 lon 171.1667; Saturn sign None bhava 8 lon 124.3833; Rahu sign None bhava 11 lon 224.4; Ketu sign None bhava 5 lon 44.4
- expected verdict: **favourable** (marital_happiness; review CONFIRMED)
- verdict_prose: The 7th lord Moon is well placed and Kalatrakaraka is neechabhanga, so that married life would be fairly happy.
- citations: NH:14890
- located in the book by the study tool: NH:14981-14982

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

Verdict **insufficient-evidence**; degree mild; lead frame lagna; karaka Venus; borderline_shifted False.

Count: No rule of Raman's speaks for or against this matter in this chart. On 2,000 random charts, 27% show the same for this matter (typically 1 for and 0 against).

### How the verdict was decided

Pipeline stages as run (judge order, from a tracer; `house_template.py` line of each return):

| stage | result | return line | clause / branch |
|---|---|---|---|
| _navamsa_modulate | insufficient-evidence | 564 |  |
| _decide_clauses | insufficient-evidence | 732 | 3. Track-B fallback — no Shadbala -> decide on rule polarity / maraka alone. (`base = "insufficient-evidence"`) |
| _navamsa_modulate | insufficient-evidence | 564 |  |
| _decide_clauses | insufficient-evidence | 732 | 3. Track-B fallback — no Shadbala -> decide on rule polarity / maraka alone. (`base = "insufficient-evidence"`) |
| _decide | insufficient-evidence | 627 |  |
| _decisive_affliction | insufficient-evidence | 1615 |  |
| _catastrophic_severity_gate | insufficient-evidence | 1647 |  |
| _yoga_modulate | insufficient-evidence | 1571 |  |
| _dhana_floor | insufficient-evidence | 1726 |  |
| _blemishless_venus_floor | insufficient-evidence | 1689 |  |
| _saptamsa_gate | insufficient-evidence | 2179 |  |
| _fertility_gate | insufficient-evidence | 2111 |  |
| _longevity_span | insufficient-evidence | 2046 |  |
| _marital_bond_gate | insufficient-evidence | 1897 |  |
| _malefic_occupancy_gate | insufficient-evidence | 1928 |  |
| _marginal_karaka_gate | insufficient-evidence | 1974 |  |
| _yogakaraka_lagna_gate | insufficient-evidence | 2017 |  |
| _powerful_dhana_kendra_floor | insufficient-evidence | 1775 |  |
| _event_timing | insufficient-evidence | 1831 |  |

Metadata: sav_bindus=28:average

### Pillars

**Lead frame**

| field | value |
|---|---|
| frame | lagna |
| lord | Moon |
| lord_strong | True |
| karaka | Venus |
| karaka_strong | None |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | MARAKA_NON_DEATH_GUARD |
| fired counts | benefic 0, malefic 0, neutral 0, blemish 0 |

**Alternate frame (moon, does not set the verdict)**

| field | value |
|---|---|
| frame | moon |
| lord | Mars |
| lord_strong | True |
| karaka | Venus |
| karaka_strong | None |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | MARAKA_NON_DEATH_GUARD |
| fired counts | benefic 0, malefic 0, neutral 0, blemish 0 |

**Alternate frame (karaka, does not set the verdict)**

| field | value |
|---|---|
| frame | karaka |
| lord | Jupiter |
| lord_strong | None |
| karaka | Venus |
| karaka_strong | None |
| bhava_bala | None |
| bhava_bala_strong | None |
| navamsa_status | weakens |
| karaka_intact | True |
| maraka_active | False |
| parivartana_resilient | True |
| lord_karaka_identical | False |
| lord_hard_afflicted | False |
| flags | MARAKA_NON_DEATH_GUARD |
| fired counts | benefic 0, malefic 0, neutral 0, blemish 0 |

### Fired rules (lead frame)

No rule fired for this matter on the lead frame.
