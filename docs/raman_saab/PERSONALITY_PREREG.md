# Track B — Personality (Native Profile) pre-registration

**Status: pre-registered. No results computed at commit time.** This document
fixes every hypothesis, feature definition, null, statistic, and decision
threshold **before** the harness (`app/medini/ml/raman_saab/personality_validate.py`)
touches the feature↔outcome relationship. It is committed as its own commit,
ahead of the results commit, so the git history proves the analysis was not
chosen after seeing the data. It reuses the permutation-null discipline of the
death-timing and vocation work verbatim.

## Motivation

The served reading now emits an 8-style **"Who you are" native profile**
(`app/reading/native_profile.py`) — decision-making, emotional style,
leadership, communication, risk tolerance, learning, financial behaviour,
relationship style. Each style is a deterministic restatement of the condition
of its governing graha. This is *doctrine-faithful* but has never been checked
against real people. Track B's death axis is refuted (N=82,589) and the vocation
axis is null across 19 tests (N=60,540). Two personality claims were **never
tested**: (a) the native_profile predictor itself (the `well_placed` condition of
the governing grahas, not the raw kāraka features), and (b) **relationship style
→ real marital outcome**. This registration tests those.

**Honest scope, stated up front.** There is **no validated psychometric
instrument** (Big Five / MBTI / HEXACO) paired with accurate birth **time** in
any accessible dataset — confirmed by search (the large open Big-Five corpora
carry only country/age, so no ascendant can be cast). So "personality" is
operationalized here as the closest available **real behaviors** with
birth-time-accurate charts: **marriage outcome** and **vocation**. A null does
not disprove "personality" in the psychometric sense (untested); it shows the
engine's personality output does not forecast these real behaviors. The
psychometric arm (F4) is formally dropped for lack of data — itself a reported
finding.

## The predictor (frozen feature): the native_profile `well_placed` condition

For every person, cast once with `chart_bundle.build_bundle(...)` (Lahiri
sidereal, whole-sign houses — the served-engine frame). Compute each graha's
`dignity`, `combust`, and 0–100 `composite` via the **served engine's own**
`app.reading.proforma._planet_strength(wrapper, avasthas=None)`, then apply the
frozen rule `app.reading._planet_lexicon.well_placed(dignity, composite, combust)`:

> `well_placed` = **+1 (well placed)** if dignity ∈ {exalted, own, moolatrikona}
> ∧ not combust; **−1 (under strain)** if debilitated ∨ combust; else **+1** if
> composite ≥ 55, **−1** if composite < 42, else **0 (mixed)**.

Binary feature `PLANET_WELL_PLACED(P) = 1{well_placed(P) == +1}`, frozen per
graha P ∈ {Sun, Moon, Mars, Mercury, Jupiter, Venus}. This is the exact
native_profile signal, with the single documented deviation that the composite
omits the avasthā 5th smoothing term (not carried on the bundle; `avasthas=None`)
— dignity and combustion, the dominant drivers, are exact. A birth-year sanity
filter (1400 ≤ year ≤ 2010) drops corrupt rows before any test.

The continuous companion `COMPOSITE(P) ∈ [0,100]` is recorded for the F1
continuous arm.

## Corpora (frozen)

- **F1 — marriage.** `data/vedastro/marriage_corpus.parquet`, **N = 14,278**, all
  Rodden **AA** (birth-certificate). Built by `app/medini/etl/vedastro_importer.py`
  from HuggingFace `vedastro-org/15000-Famous-People-Birth-Date-Location` ⋈
  `…-Marriage-Divorce-Info` (MIT). Label `marriage_dissolution ∈ {0,1}` =
  ≥1 marriage ended in Dissolution (base rate 0.2395; 3,419 dissolved / 10,859
  intact). sha256 `c6901d501d1949c4a159f36757b5731f5818121e77c1a04c3d295d0f027eecd7`.
- **F3 — vocation.** `data/holos/vocation_corpus.parquet`, **N = 60,547** (the
  frozen vocation-run corpus; birth data + `eminent` + 12 `voc_*` labels; Rodden
  AA/A/B). sha256 `18ff150ac8997282a15bfd2ada26081293b83cbc8a13db73b85afb7f994e867f`.
- Both pinned in `data/ml_runs/raman_saab/personality_corpora_MANIFEST.json`.

**Dropped (no data):** F2 life-valence (`lapaasindia/good-time-finder`
unreachable under this session's network policy); F4 psychometric (no Big-Five/
MBTI + birth-time dataset exists in accessible form). Both reported "not run,"
never faked.

## Null (PRIMARY, for every binary test): birth-decade-stratified label permutation

Identical to the vocation harness. For a feature indicator `f_i ∈ {0,1}` and an
outcome label `L_i ∈ {0,1}`, the observed count is `O = Σ_i L_i f_i`. Under the
null the label is permuted **within birth-decade strata**, breaking only the
feature↔label pairing while preserving (a) the feature base rate, (b) the label
base rate, and (c) the shared birth-epoch confound. Per stratum `s`,
`p_s = (Σ_{i∈s} f_i)/n_s`; `E = Σ_s n_{L,s}·p_s`; each labelled person is an
independent Bernoulli(`p_{s(i)}`) so `O` is Poisson-binomial →
`O ≈ Normal(E, Σ p(1−p))`, giving an exact one-sided z and p (no Monte-Carlo on
the test). `RR = O/E`. Strata = `floor(birth_year/10)`; strata with `n_s < 20`
pooled into the nearest larger decade (`_pool_small_strata`).

## Decision gates (same bar as the death + vocation harnesses)

- **G1 (effect size):** `RR ≥ 1.20` in the hypothesised direction.
- **Significance:** one-sided `p < α_Bonferroni`, `α = 0.05 / K`, **K = 13**
  (F1 = 1 test + F3 = 12 tests) → **α = 0.003846**. The F1 continuous
  Welch/Mann-Whitney arm is reported alongside but is **not** counted in the
  Bonferroni family.
- **Powered-null check:** the harness must (i) show null calibration `z ~ N(0,1)`
  on shuffled labels, and (ii) recover a planted RR=1.20 label at true size. A
  hypothesis is **refuted** only if it fails G1 at adequate power (`E ≥ 10`);
  otherwise `underpowered`.
- **Supported** iff G1 **and** `p < α` **and** powered.

## Family 1 — Relationship style → marital outcome (1 test; the flagship)

Personality claim (native_profile): *"You bring warmth and harmony to close ties"*
when **Venus is well placed** (relationship style). Directional hypothesis:

> **H1:** `PLANET_WELL_PLACED(Venus)` is **enriched among the marriage-intact**
> (label = `1 − marriage_dissolution`) vs the birth-decade-stratified null —
> equivalently, a well-placed Venus is depleted among the dissolved.

Reported alongside (not in the Bonferroni K):
- **Mirror:** `1{well_placed(Venus) == −1}` (Venus under strain) enriched among
  the **dissolved**.
- **Continuous arm:** `COMPOSITE(Venus)` compared between intact and dissolved
  groups — Welch two-sample z and Mann-Whitney U, each with a within-decade
  shuffled-label permutation null (per `maraka_validate.natal_8h_longevity`).

## Family 3 — Personality predictor → vocation, construct validity (12 tests)

The refuted vocation map, re-tested with the **native_profile predictor**
(`PLANET_WELL_PLACED`) swapped in for the raw `KĀRAKA_STRONG` feature. Same 12
vocation groups, same governing graha. **Pre-registered expectation: null**
(the vocation run already refuted the stronger kāraka feature); F3 measures
whether the personality-styled predictor does any better — construct validity,
not a fresh discovery.

| # | vocation group | graha P | style |
|---|---|---|---|
| 1 | sports | Mars | risk tolerance |
| 2 | military | Mars | risk tolerance |
| 3 | medical | Mars | risk tolerance |
| 4 | writers | Mercury | communication / learning |
| 5 | science | Mercury | communication / learning |
| 6 | business | Mercury | communication / learning |
| 7 | education | Jupiter | financial / wisdom |
| 8 | law | Jupiter | financial / wisdom |
| 9 | religion | Jupiter | financial / wisdom |
| 10 | entertainment | Venus | relationship / arts |
| 11 | art | Venus | relationship / arts |
| 12 | politics | Sun | leadership |

> **H3_v:** `PLANET_WELL_PLACED(P_v)` is enriched among vocation group `v` vs the
> stratified null.

(Eminence — Sun well-placed among `eminent` — is reported as a labelled extra in
F3's output but, to keep K exactly at the pre-registered 13, is **not** a
Bonferroni-counted test; it is descriptive.)

## What would count as a positive

Any hypothesis clearing **G1 (RR ≥ 1.20) + significance at power** is a genuine,
non-circular signal — the engine's personality output predicting real biography.
Given the death and vocation nulls and the ~53–58% strength ceiling, the
pre-registered expectation is **broad null**, with F1 (the never-tested
relationship→marriage claim) as the one place a fresh positive could appear. A
stratified-permutation positive on F1 would be the first population-scale support
for the personality doctrine and would be reported as such, not buried. Every
outcome — positive, null, or underpowered — is recorded in the VERDICT
(`docs/ml_runs/raman_saab_personality_VERDICT.md`) and the ratchet ledger.
