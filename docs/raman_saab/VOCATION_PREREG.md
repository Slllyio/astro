# Track B — Vocation & Eminence pre-registration

**Status: pre-registered. No results computed at commit time.** This document
fixes every hypothesis, feature definition, null, statistic, and decision
threshold **before** the harness touches the chart↔outcome relationship. It is
committed as its own commit, ahead of the results commit, so the git history
proves the analysis was not chosen after seeing the data. This is the vocation
analog of the death-timing work (`docs/ml_runs/raman_saab_death_timing_VERDICT.md`)
and reuses its permutation-null discipline.

## Motivation

The Track-B death axis is closed: B. V. Raman's dāśā death-timing rules are
**refuted** at N=82,589 and the house-based maraka rules are null at N=4,586,
under confound-controlled permutation nulls (powered — planted effects
recovered). The one axis never tested is a **non-death outcome** that exercises
the house / kāraka / **yoga** engine (increments 34–38). Astro-Databank supplies
it: real people with Rodden-rated **birth times** (→ real lagna, houses, yogas)
and an independent biographical **vocation + eminence** taxonomy.

## Corpus (frozen)

`data/holos/vocation_corpus.parquet`, **N = 60,547** persons. Built by
`app/medini/etl/astrocrm_vocation_corpus.py` from the sha256-pinned ASTROCRM
mirror (`data/holos/MANIFEST.json`): `holos_clean.csv` (Rodden AA/A/B timed
births + coords + tz) ⋈ `astro_analytics_quality.csv` (categories), on a
normalised name key. Charts are cast **Lahiri sidereal, whole-sign houses**, via
the production `calculate_all_charts` / `cast_kundali`, identical to the served
engine. Group Ns (frozen): eminent 4,215; sports 8,703; military 3,770; writers
13,192; entertainment 18,776; art 3,668; politics 7,799; education 5,209; law
2,098; religion 1,337; science 2,901; business 4,605; medical 2,090.

## Null (PRIMARY, for every test): birth-decade-stratified label permutation

For a feature indicator `f_i ∈ {0,1}` (a chart property) and an outcome label
`L_i ∈ {0,1}` (vocation membership or eminence), the observed count is
`O = Σ_i L_i f_i`. Under the null, **the label is permuted within birth-decade
strata** — breaking only the feature↔label pairing while preserving (a) the
feature's base rate, (b) the label's base rate, and (c) any secular
(birth-epoch) confound shared by both. This is the vocation analog of the death
harness's age-distribution-preserving shuffle, and it neutralises the dominant
artifact here: Astro-Databank's sampling skews by era (more recent entertainers,
older military) while astronomical feature rates also drift with epoch.

Per stratum `s`, null hit-probability `p_s = (Σ_{i∈s} f_i) / n_s`. Then
`E = Σ_s n_{L,s} · p_s` and, since each labelled person is an independent
Bernoulli(`p_{s(i)}`), `O` is Poisson-binomial → `O ≈ Normal(E, Σ p(1−p))`,
giving an **exact one-sided z and p** with no Monte-Carlo on the test itself.
`RR = O / E`. Strata = birth decade (`floor(birth_year/10)`); strata with
`n_s < 20` are pooled into an adjacent decade.

## Decision gates (same bar as the death harness)

- **G1 (effect size):** `RR ≥ 1.20` in the hypothesised (enrichment) direction.
- **Significance:** one-sided `p < α_Bonferroni`, `α = 0.05 / K`, `K` = total
  pre-registered tests below = **12 + 4 + 3 = 19** → `α = 0.00263`.
- **Powered-null check:** the harness must (i) show null calibration `z ~ N(0,1)`
  on shuffled labels, and (ii) recover a planted 5 % enrichment at true size.
  A hypothesis is **refuted** only if it fails G1 at adequate power
  (`E ≥ 10` expected hits); otherwise `underpowered`.
- A hypothesis is **supported** iff G1 **and** `p < α` **and** powered.

## Family 1 — Kāraka → vocation (12 tests)

Classical significators (Raman, *How to Judge a Horoscope*; BPHS kāraka scheme).
Feature `f = KĀRAKA_STRONG(K)` for the vocation's kāraka `K`, defined once and
frozen:

> `KĀRAKA_STRONG(K)` = K is in own-sign / exaltation / mūlatrikoṇa **OR** K is
> in a kendra (house 1/4/7/10) **OR** K occupies or aspects (whole-sign graha
> dṛṣṭi) the 10th house **OR** K conjoins the 10th lord.

| # | vocation group | kāraka K | rationale |
|---|---|---|---|
| 1 | sports | Mars | physical prowess, competition |
| 2 | military | Mars | war, weapons |
| 3 | medical | Mars | surgery, cutting |
| 4 | writers | Mercury | writing, intellect |
| 5 | science | Mercury | analysis, computation |
| 6 | business | Mercury | commerce, trade |
| 7 | education | Jupiter | teaching, wisdom |
| 8 | law | Jupiter | justice, dharma |
| 9 | religion | Jupiter | priesthood, dharma |
| 10 | entertainment | Venus | performance, arts |
| 11 | art | Venus | fine art, beauty |
| 12 | politics | Sun | authority, government |

H1_v: `P(KĀRAKA_STRONG(K_v) | in group v)` is enriched vs the stratified null.

## Family 2 — Eminence → yogas (4 tests)

Outcome label = `eminent` (Astro-Databank "notable : famous : top 5% of
profession", N=4,215). Features from the increments-34–38 engine
(`app/core/yoga_library.active_yogas`, `dignity`):

| # | signal `f` |
|---|---|
| E1 | any Pañca-Mahāpuruṣa yoga active (Ruchaka/Bhadra/Haṃsa/Mālavya/Śaśa) |
| E2 | any Rāja-yoga active (Raja / Neecha-Bhaṅga-Raja / Dharma-Karma-Adhipati) |
| E3 | 10th lord strong (own/exalt/mūlatrikoṇa **or** in a kendra) |
| E4 | union of E1–E3 |

H2_e: `P(signal | eminent)` is enriched vs the stratified null.

## Family 3 — Gauquelin Mars-effect (3 tests)

The single most-replicated/most-contested testable astrology claim: among
eminent athletes and soldiers, Mars falls disproportionately in the diurnal
**"plus zones"** — just after the Ascendant and just after the Mid-heaven.
Operationalised on our cast (mundane / Placidus diurnal frame, computed from the
birth time + place via Swiss Ephemeris): **Mars in the plus zone** = Mars within
the 30° sector immediately following the Ascendant (rising) **or** the 30° sector
immediately following the Mid-heaven (culminating) — i.e. Placidus mundane houses
12 or 9. Outcome labels (each its own test, restricted to the Gauquelin
professions, and to `eminent` per the classical finding):

| # | population |
|---|---|
| G_sport | eminent ∧ sports |
| G_mil | eminent ∧ military |
| G_pool | eminent ∧ (sports ∨ military) |

H3: `P(Mars in plus zone | eminent Gauquelin professional)` is enriched vs the
stratified null (the population's own Mars-plus-zone base rate, decade-stratified).

**Pre-registered artifact caveat:** Gauquelin's own effect survived a
birth-hour-rounding artifact check; we log the fraction of births rounded to
`:00` and report the plus-zone rate separately for rounded vs unrounded births,
but the primary test is on all timed births. No effect is claimed from an
artifact-contaminated cell.

## What would count as a positive

Any hypothesis clearing G1 + significance at power is a **genuine, non-circular
signal** — the engine's output predicting real biography. Given the death axis
and the ~53–58 % strength ceiling, the pre-registered expectation is **broad
null**; a stratified-permutation positive on any family would be the first
population-scale support for the doctrine and would be reported as such, not
buried. All 19 outcomes — positive, null, or underpowered — are recorded in the
VERDICT and the ratchet ledger.
