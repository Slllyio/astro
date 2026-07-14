# raman_saab Vocation & Eminence — VERDICT

**Date**: 2026-07-14
**Module**: `app/medini/ml/raman_saab/vocation_validate.py`
**Corpus**: ASTROCRM timed corpus, **N = 60,540** Rodden AA/A/B charts with
real birth times → real lagna/houses/yogas (`data/holos/vocation_corpus.parquet`;
source sha256-pinned in `data/holos/MANIFEST.json`).
**Pre-registration**: `docs/raman_saab/VOCATION_PREREG.md` (committed *before*
results — see git history: prereg commit precedes this one).
**Results JSON**: `data/ml_runs/raman_saab/vocation_validation.json`.

## Headline

> **NULL — all three families.** Across 19 pre-registered tests, none of the
> engine's house / kāraka / **yoga** signals predicts real vocation or eminence
> at population scale. Every relative risk lands in **RR ∈ [0.956, 1.026]**;
> the pre-registered effect gate is **RR ≥ 1.20**. The nulls are **powered**,
> not blind: null calibration is exact (**z ~ N(0.015, 0.976)** over 300
> shuffles) and a planted G1-sized effect is recovered cleanly
> (**target RR 1.20 → recovered 1.199, z = 19.0**). This is the first
> population-scale test of the *house/yoga* doctrine (the death axis could only
> reach dāśā timing) — and of the increments 34–38 yoga library — against an
> independent biographical outcome. It refutes at high power.

## Question

Do the engine's outputs — classical significators (kārakas), the
Pañca-Mahāpuruṣa / Rāja yogas surfaced by `app/core/yoga_library`, 10th-house
strength, and the Gauquelin Mars-angularity claim — enrich real biographical
vocation and eminence beyond what birth-epoch sampling already explains?

## Method (per `VOCATION_PREREG.md`)

Each chart cast Lahiri sidereal / whole-sign (Vedic frame) plus a tropical
Placidus cusp set for the Gauquelin mundane position. **PRIMARY null =
birth-decade-stratified label permutation** — the outcome label is shuffled
within birth-decade strata, breaking only the feature↔label pairing while
preserving the feature rate, the label rate, and the era confound (ADB samples
skew by epoch). Exact hypergeometric z / RR (Poisson-binomial normal, no
Monte-Carlo). Gate: RR ≥ 1.20 **and** one-sided p < α = 0.05/19 = 0.00263, at
power (E ≥ 10).

## Results

### Family 1 — kāraka → vocation (12 tests) — all null

| vocation | kāraka | N | RR | z | p₁ | verdict |
|---|---|---:|---:|---:|---:|---|
| sports | Mars | 8,703 | 1.001 | 0.19 | 0.42 | refuted |
| military | Mars | 3,770 | 1.018 | 1.64 | 0.050 | refuted |
| medical | Mars | 2,090 | 0.997 | −0.21 | 0.58 | refuted |
| writers | Mercury | 13,191 | 1.003 | 0.49 | 0.31 | refuted |
| science | Mercury | 2,901 | 1.017 | 1.29 | 0.099 | refuted |
| business | Mercury | 4,605 | 1.008 | 0.80 | 0.21 | refuted |
| education | Jupiter | 5,209 | 0.989 | −1.32 | 0.91 | refuted |
| law | Jupiter | 2,098 | 0.993 | −0.55 | 0.71 | refuted |
| religion | Jupiter | 1,337 | 0.976 | −1.41 | 0.92 | refuted |
| entertainment | Venus | 18,775 | 1.004 | 0.98 | 0.17 | refuted |
| art | Venus | 3,667 | 0.985 | −1.27 | 0.90 | refuted |
| politics | Sun | 7,798 | 0.988 | −1.42 | 0.92 | refuted |

### Family 2 — eminence → yogas (4 tests) — all null

| signal | N eminent | RR | z | p₁ | verdict |
|---|---:|---:|---:|---:|---|
| Pañca-Mahāpuruṣa active | 4,214 | 1.026 | 1.27 | 0.10 | refuted |
| Rāja-yoga active | 4,214 | 0.999 | −0.07 | 0.53 | refuted |
| 10th lord strong | 4,214 | 1.006 | 0.32 | 0.37 | refuted |
| union of the three | 4,214 | 1.008 | 1.44 | 0.074 | refuted |

The engine's own eminence signatures — including the Pañca-Mahāpuruṣa and Rāja
yogas — are **not** enriched among people the world actually rated in the top
5 % of their profession.

### Family 3 — Gauquelin Mars-effect (3 tests) — all null (wrong direction)

Mars plus-zone base rate = 0.171. Among eminent athletes/soldiers Mars is if
anything *less* likely to occupy the diurnal plus-zones:

| population | N | RR | z | p₁ | verdict |
|---|---:|---:|---:|---:|---|
| eminent ∧ sports | 2,084 | 0.964 | −0.77 | 0.78 | refuted |
| eminent ∧ military | 225 | 0.974 | −0.18 | 0.57 | refuted |
| eminent ∧ (sports∨military) | 2,257 | 0.956 | −0.97 | 0.84 | refuted |

A null Mars-effect on an independently-collected sample — consistent with the
large body of failed replications outside Gauquelin's own data.

## Validity (the null is powered, not blind)

- **Null calibration** (300 shuffled labels, `k_Venus` feature): z_mean =
  0.015, z_sd = 0.976 → the stratified test is exactly N(0,1) under the null.
- **Planted recovery**: a synthetic label engineered to a true **RR = 1.20** at
  the eminence label size is recovered at **RR = 1.199, z = 19.0** — a real
  G1-sized effect would be caught overwhelmingly. The observed RR ≤ 1.026
  everywhere is therefore a genuine absence of signal, not underpower.

## Interpretation & ratchet

Combined with the death axis (dāśā rules refuted at N=82,589; house-maraka null
at N=4,586), Track B now has **two independent, powered, non-circular refutations
on real population outcomes** — death timing/longevity **and** vocation/eminence.
The vocation family enters `RATCHET_LEDGER.json` as **refuted** (G1 failed at
high power; kārakas, the increments-34–38 eminence yogas, and the Gauquelin
claim all null). Per the ratchet's kill criterion this closes the population
"reality axis" for the doctrine's *descriptive* (chart-shape → life) claims.

This does **not** touch the reading engine's value as a faithful *encoder* of
Raman's doctrine (the ~53–58 % within-one-grade fidelity ceiling, the 90 %
yoga-coverage) — it says only that the doctrine, faithfully encoded, does not
predict these real outcomes at population scale. Both facts are reported
together; neither is buried.
