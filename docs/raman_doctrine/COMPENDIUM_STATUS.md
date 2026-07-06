# Raman Doctrine Compendium — Status

**1,349 rule records across 10 of B. V. Raman's books**, every quote verbatim-verified against the pinned OCR (`quote_verified` = true for all), every executable antecedent compiling through the DSL engine.

## By book

| key | title | records |
|---|---|---:|
| `hpa` | Hindu Predictive Astrology | 599 |
| `htjah_vol1` | How to Judge a Horoscope Vol. 1 | 341 |
| `three_hundred` | Three Hundred Important Combinations | 147 |
| `htjah_vol2` | How to Judge a Horoscope Vol. 2 | 185 |
| `jaimini_studies` | Studies in Jaimini Astrology | 24 |
| `graha_bhava_balas` | Graha and Bhava Balas | 12 |
| `manual_hindu_astrology` | A Manual of Hindu Astrology | 12 |
| `prasna_marga_1` | Prasna Marga, Part 1 | 10 |
| `prasna_marga_2` | Prasna Marga, Part 2 | 10 |
| `muhurtha` | Muhurtha (Electional Astrology) | 9 |
| | **total** | **1349** |

## By computability

| class | count | meaning |
|---|---:|---|
| full | 872 | antecedent fully expresses the condition in the DSL |
| partial | 230 | DSL captures the core; a qualifier quoted in ambiguity_notes |
| manual | 139 | arithmetic/mechanism lives in code (cited) — antecedent null |
| unfalsifiable | 108 | a definition/signification with no testable condition |

## By rule type

- graha_effect: 540
- yoga: 177
- bhava_judgment: 192
- definition: 149
- method: 52
- functional_role: 43
- cancellation: 15
- dasha_timing: 144
- prasna: 4
- strength: 3
- transit: 29
- electional: 1

## Phases

- **P0** source fetch + QC gate + mechanical page maps (`SOURCES.md`)
- **P1** rule schema, compendium loader, OCR-tolerant quote-verification honesty gate
- **P2** feature layer: sodhana (HPA Ch. XXVI golden), khara/64th-navamsa, arishta, `RamanChart`
- **P3** DSL engine: 29 frame-aware leaf ops, escape-hatch registry, profile evaluation
- **P4** tranche 1 extraction (Three Hundred, HPA longevity/AV, HTJAH Vol 1)
- **P5** fidelity gate 1 — mechanism precision/recall 1.0 (`FIDELITY_REPORT.md`)
- **P6** tranche 2 — HTJAH Vol 2 + Jaimini, Manual, Graha & Bhava Balas, Muhurtha, Prasna Marga
- **P7** domain engine (`domains/houses.py`) composing compendium rules with `bhava_judge`; specialised-book deepening — Jaimini Karakamsa/education/Arudha-wealth, Muhurtha Tarabala, Shadbala components, Prasna Marga Part 2 (marriage/progeny horary)
- **P8** general-text completion — HPA planets-in-bhavas (XXI) and in-signs (XXII), special yogas (XX), Female Horoscopy (XXX); **transit engine**: `transit_in_house` leaf (Gochara reckoned from the natal Moon/lagna) + HPA Gocharaphala (XXXIV), evaluable only under a supplied transit context
- **P9** exhaustive HTJAH house-by-house methodology (both volumes) — per house: significations + planets-in-house + lord placements + Important Combinations
- **P10** First-House methodology & **timing engine** — Raman's judgment sequence (`method` records), the 36 Signs-Ascending tendencies, and ch. IV's "When Do Indications Fructify?": the `planet_influences_house` leaf (owns/occupies/aspects the house *or its lord* — the five-factor influence test) driving the 9 per-Dasa "Nature of the Results" and the lagna-lord conjunction Dasa combos

Coverage per book/chapter is tracked in `COVERAGE.md`; sources and sha256 pins in `SOURCES.md`.
