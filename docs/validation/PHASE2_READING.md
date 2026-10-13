# Phase 2: how to read RELIABILITY.md (hand-written; the table itself is generated)

Run 2026-10-13. Frozen Parashara engine on 2,000 hashed tier-A (Rodden AA) charts × 9 conditions,
plus a Raman-vs-Parashara comparison on the full 22,173-chart store. No outcomes read; no holdout spent.

## 1. Birth-time error: how much it scrambles the engine
| birth-time error | house verdict κ | AD timing κ (H7 / maraka) | MD timing κ (H7 / maraka) | ayurdaya shift |
|---|---|---|---|---|
| ±15 min | 0.87 | 0.83 / 0.81 | 0.88 / 0.85 | ±2.6 yrs |
| ±30 min | 0.74 | 0.66 / 0.62 | 0.75 / 0.70 | ±3.9 yrs |
| ±60 min | 0.50 | 0.41 / 0.35 | 0.52 / 0.43 | ±5.6 yrs |

- **Reliability ρ for later tests:** use ρ_AD ≈ 0.82 for Rodden AA (birth-certificate times, typical
  error ≤ 15 min) and ρ_AD ≈ 0.64 for memory-grade A times (~30 min). The plan's threshold ("ρ_AD at
  ±30 min below 0.6 → AD tests structurally blind") is **not crossed**, so AD-level tests on A/B stay
  informative, but attenuated. A true timing effect θ shows up as about 0.64–0.82 · θ.
- Phase 3 power check, disattenuated: the pooled MDE ≈ 0.018 becomes 0.018 / 0.64 ≈ **0.028 true**,
  still below the 0.03 SESOI. The pooled design survives the measurement error.
- **Precision-gradient prediction for Phase 3 (fixed now, before any timing outcome is read):** if
  dasha timing works, the AD-level effect in Rodden AA must exceed the effect in Rodden A by roughly
  0.82 / 0.64 ≈ 1.3×. MD-level effects should depend far less on rating (ρ_MD 0.88 vs 0.75).
- Ayurdaya moves ±2.6 years per 15 minutes of birth time, so a lifespan test cannot resolve finer
  than a few years even with perfect outcomes.

## 2. Ayanamsa: a bigger error source than birth time
| frame (vs Lahiri) | verdict κ | AD timing κ (H7 any / auspicious / maraka) | MD timing κ |
|---|---|---|---|
| Krishnamurti (KP) | 0.98 | 0.95 / 0.94 / 0.95 | 0.99 |
| **Raman** | 0.72 | **0.46 / 0.34 / 0.45** | 0.78 / 0.80 |

- Lahiri vs Raman (~1.4°) changes roughly **half of all AD-level timing calls**. That is worse than a
  30-minute birth-time error (κ 0.62–0.66). KP is practically identical to Lahiri.
- So a timing claim in this tradition is only as definite as the ayanamsa choice behind it. Phase 3
  keeps Lahiri as primary (locked convention) and must report the Raman-ayanamsa instrument as a
  pre-registered sensitivity arm. An AD effect that exists under one frame and vanishes under the
  other is not a robust finding.

## 3. Raman vs Parashara: the two engines barely agree
- House verdicts, 3-pole scale (Parashara mapped with the report card's own `SYNTH_TO_RAMAN`):
  **κ = 0.00–0.05 in all 12 houses**, on 22,173 charts.
- **Ayanamsa-matched** (Parashara re-cast under Raman's ayanamsa): still κ = −0.00–0.05. The
  disagreement is doctrinal, not frame-induced.
- Mapping-free check (Spearman on each engine's full ordinal scale): ρ = 0.01–0.07 per house.
  It is non-zero only because n is 22k; it is negligible in size.
- Join verified: identical person ids, identical house numbering.

**What this means.** Each engine is faithful to its own text: Raman 70.6% exact on Raman's printed
verdicts, Parashara agreeing on the BPHS example horoscopes. Yet on the same real charts they
reach unrelated house judgments. The plan's pre-declared consequence applies:
- **"The doctrine" is not one testable object.** Every outcome test tests an *implementation*: which
  factors a tradition weighs, and how it breaks ties. Write-ups must say "Raman's method" or
  "Parashara synthesis", never "Vedic astrology".
- It fits the measured mechanism (the median chart offers 19 afflicted + 31 favourable
  significations at once). With that many indications available, the verdict is set by the
  weighting rule, and two defensible weighting rules land almost independently.
- Decision-framework item 6 ("where the two engines agree on an instrument, both show the same
  sign") now applies only to the small subset of charts where they agree. Phase 3 should report
  that agreement subset as a pre-registered stratum.

## Caveats
- The constructs are not identical. Raman's rollup summarises several significations per house;
  Parashara's verdict is one promise per house. Part of the disagreement is definitional. Still, a
  shared doctrine should give κ well above 0.05 even across adjacent constructs.
- The sample is tier A only. Jitter κ for lower tiers is implied by the ±30/±60 rows, not measured
  on lower-tier charts directly.
