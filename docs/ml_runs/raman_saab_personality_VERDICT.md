# raman_saab Personality (Native Profile) — VERDICT

**Date**: 2026-08-19
**Module**: `app/medini/ml/raman_saab/personality_validate.py`
**Corpora**:
- F1 marriage — `data/vedastro/marriage_corpus.parquet`, **N = 14,278** Rodden
  **AA** (birth-certificate) timed charts, from HuggingFace
  `vedastro-org/15000-Famous-People-{Birth-Date-Location, Marriage-Divorce-Info}`
  (MIT); sha256 `c6901d501d1949c4a159f36757b5731f5818121e77c1a04c3d295d0f027eecd7`.
- F3 vocation — `data/holos/vocation_corpus.parquet`, **N = 60,547** (59,983 after
  the 1400–2010 birth-year sanity filter); sha256
  `18ff150ac8997282a15bfd2ada26081293b83cbc8a13db73b85afb7f994e867f`.
- Both pinned in `data/ml_runs/raman_saab/personality_corpora_MANIFEST.json`.

**Pre-registration**: `docs/raman_saab/PERSONALITY_PREREG.md` (committed *before*
results — git history: prereg commit `18ab4dd` precedes this results commit).
**Results JSON**: `data/ml_runs/raman_saab/personality_validation.json`.

## Headline

> **NULL — powered.** The engine's served **"Who you are" personality signal**
> (the `native_profile` `well_placed` condition of the governing grahas) does
> **not** predict real biography. The flagship never-before-tested claim —
> **relationship style (a well-placed Venus) → marital stability** — is refuted
> on high-purity AA data: **RR = 0.997** (z = −0.61, p = 0.73), and the
> continuous arm is flat (Venus composite: intact 55.73 vs dissolved 55.59,
> **Cohen's d = 0.012**, permutation p = 0.51). The 12 personality→vocation
> construct-validity tests are all refuted (**RR ∈ [0.950, 1.012]** vs the
> G1 gate of 1.20). The null is **not blind**: null calibration is exact
> (**z ~ N(0.05, 1.03)**) and a planted G1-sized effect is recovered cleanly
> (**target RR 1.20 → recovered 1.1985, z = 12.8**) at the real label size.
> This is the first population test of the reading's *personality* output — and
> the first test of the relationship/marriage claim — and it refutes at power.

## Question

Does the engine's personality output — the `native_profile` styles, each a
deterministic function of its governing graha's dignity/combustion/strength —
predict the closest available real behaviors (marital stability, vocation) beyond
what birth-epoch sampling already explains? (There is no validated psychometric
instrument paired with birth times in any accessible dataset, so "personality" is
operationalized as behavior; see PREREG.)

## Method (per PREREG)

Predictor = the frozen `_planet_lexicon.well_placed(dignity, composite, combust)`
condition per governing graha, computed from the production
`chart_bundle.build_bundle` cast + the reading's own strength composite
(`avasthas=None`; dignity + combustion — the dominant drivers — are exact). Null
= birth-decade-stratified label permutation (analytic hypergeometric z/RR, no
Monte-Carlo on the test). Gate = **RR ≥ 1.20 AND one-sided p < α (0.05/13 =
0.00385) AND E ≥ 10**. Continuous arm = Welch + Mann-Whitney on Venus composite
with a within-decade permutation null.

## Results

### Family 1 — Relationship style → marital outcome (flagship, N = 14,278 AA)

| test | n | RR | z | p₁ | verdict |
|---|---|---|---|---|---|
| Venus well-placed → intact | 10,859 | **0.997** | −0.607 | 0.728 | **refuted** |
| Venus under-strain → dissolved *(mirror, not K-counted)* | 3,419 | ~1.00 | — | — | null |

Continuous arm: mean Venus composite **55.73 (intact) vs 55.59 (dissolved)**,
Δ = 0.145 on 0–100, **Cohen's d = 0.012**, permutation p = 0.505, Mann-Whitney
consistent. No relationship.

### Family 3 — Personality predictor → vocation (construct validity, N = 59,983)

| vocation | graha | n | RR | z | p₁ | verdict |
|---|---|---|---|---|---|---|
| sports | Mars | 8,702 | 1.009 | 0.82 | 0.205 | refuted |
| military | Mars | 3,770 | 0.983 | −0.98 | 0.836 | refuted |
| medical | Mars | 2,090 | 1.008 | 0.35 | 0.363 | refuted |
| writers | Mercury | 13,189 | 0.997 | −0.25 | 0.598 | refuted |
| science | Mercury | 2,899 | 0.950 | −1.62 | 0.948 | refuted |
| business | Mercury | 4,605 | 1.012 | 0.47 | 0.320 | refuted |
| education | Jupiter | 5,209 | 0.997 | −0.22 | 0.585 | refuted |
| law | Jupiter | 2,098 | 0.973 | −1.18 | 0.882 | refuted |
| religion | Jupiter | 1,337 | 1.004 | 0.13 | 0.450 | refuted |
| entertainment | Venus | 18,766 | 0.992 | −1.35 | 0.911 | refuted |
| art | Venus | 3,668 | 1.004 | 0.23 | 0.409 | refuted |
| politics | Sun | 7,798 | 0.995 | −0.40 | 0.655 | refuted |

(Descriptive extra, not K-counted: Sun well-placed → `eminent` is likewise null.)

### Dropped families (no data — reported, not faked)

- **F2 life-valence** — `lapaasindia/good-time-finder` unreachable under this
  session's network policy.
- **F4 psychometric** — no dataset pairs a validated instrument (Big Five/MBTI)
  with accurate birth **time**; the open Big-Five corpora carry only country/age,
  so no chart can be cast. The "true" psychometric test is **not runnable** for
  lack of public data — an honest limit, not a null.

## Validity

- **Null calibration** (300 shuffled labels): z_mean = 0.053, z_sd = 1.028 →
  the stratified test is exact-N(0,1) as designed.
- **Planted-effect recovery**: a G1-sized RR = 1.20 label planted at the
  dissolved-group size is recovered at **RR = 1.1985, z = 12.8** — the test
  detects a real effect of the pre-registered magnitude. The nulls above are
  therefore genuine absences, not underpower.

## Interpretation & ratchet

The engine's personality output is **doctrine-faithful but not predictive** of
these real behaviors. The relationship-style → marriage claim — the one
personality dimension with a clean behavioral ground truth and never previously
tested — is refuted at power on birth-certificate-grade data. This joins the
death (N=82,589) and vocation (N=60,540) refutations: across every axis with a
real-outcome ground truth, the doctrine's *predictive* claims do not survive a
confound-controlled, powered test. It does **not** speak to psychometric
personality (Big Five/MBTI), which remains untested for lack of data. The served
reading's personality section is honest as *interpretation in Raman's method*,
and its disclosure is updated to state this result (M4). Ledger: F1
`personality.relationship.venus_wellplaced` and the 12 F3 rows → **refuted** at
the recorded RRs; kill criterion met (powered G1 failure).
