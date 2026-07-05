# Raman Doctrine Compendium — Status

**769 rule records across 10 of B. V. Raman's books**, every quote verbatim-verified against the pinned OCR (`quote_verified` = true for all), every executable antecedent compiling through the DSL engine.

## By book

| key | title | records |
|---|---|---:|
| `hpa` | Hindu Predictive Astrology | 262 |
| `htjah_vol1` | How to Judge a Horoscope Vol. 1 | 198 |
| `three_hundred` | Three Hundred Important Combinations | 147 |
| `htjah_vol2` | How to Judge a Horoscope Vol. 2 | 85 |
| `jaimini_studies` | Studies in Jaimini Astrology | 24 |
| `graha_bhava_balas` | Graha and Bhava Balas | 12 |
| `manual_hindu_astrology` | A Manual of Hindu Astrology | 12 |
| `prasna_marga_1` | Prasna Marga, Part 1 | 10 |
| `prasna_marga_2` | Prasna Marga, Part 2 | 10 |
| `muhurtha` | Muhurtha (Electional Astrology) | 9 |
| | **total** | **769** |

## By computability

| class | count | meaning |
|---|---:|---|
| full | 365 | antecedent fully expresses the condition in the DSL |
| partial | 176 | DSL captures the core; a qualifier quoted in ambiguity_notes |
| manual | 131 | arithmetic/mechanism lives in code (cited) — antecedent null |
| unfalsifiable | 97 | a definition/signification with no testable condition |

## By rule type

- graha_effect: 205
- yoga: 153
- bhava_judgment: 151
- definition: 138
- method: 46
- functional_role: 43
- cancellation: 15
- dasha_timing: 8
- prasna: 4
- strength: 3
- transit: 2
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

Coverage per book/chapter is tracked in `COVERAGE.md`; sources and sha256 pins in `SOURCES.md`.
