# The Failure Atlas — where the engine's readings meet real lives

> Per-case, per-house, per-feature statistics of the raman_saab engine against the AstroDatabank reality corpus (16,450 tier-A/B charts). Descriptive companion to [REAL_OUTCOME_GENERALIZATION.md](REAL_OUTCOME_GENERALIZATION.md) (THAT it fails) and [WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md](WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md) (WHY). Nothing here is a discovery claim; matched AUCs are the pre-registered Stage-7 numbers, never recomputed.

> All named individuals are public figures from the public AstroDatabank corpus; every stated life fact is that database's own published category label. No private (app_user) records appear in any name-bearing artifact.


## 1. The atlas at a glance

| feature | house·sig | n | AUC | J (expected-class excess) | Δstrong | background@expected | failure class |
|---|---|---|---|---|---|---|---|
| bankrupt | H2·wealth | 44 | 0.448 | -0.000 | +0.000 | 29% | SATURATED-FAVOURABLE-AGAINST |
| eyes_problem | H2·vision | 44 | 0.546 | +0.059 | +0.019 | 28% | PURE-NOISE |
| wealthy | H2·wealth | 474 | 0.448 | -0.107 | -0.121 | 63% | PURE-NOISE |
| military | H3·courage | 1192 | 0.480 | -0.038 | -0.013 | 74% | INVERTED |
| mother_died_early | H4·mother | 25 | 0.464 | -0.009 | -0.009 | 33% | UNDER-POWERED |
| creative_vocation | H5·intellect | 8307 | 0.500 | +0.005 | -0.004 | 65% | SATURATED-FAVOURABLE |
| kids_many | H5·children | 1475 | 0.523 | +0.042 | -0.011 | 23% | SATURATED-AFFLICTED-AGAINST |
| kids_none | H5·children | 391 | 0.523 | +0.035 | -0.003 | 76% | SATURATED-AFFLICTED |
| science_vocation | H5·intellect | 643 | 0.502 | +0.006 | -0.002 | 66% | SATURATED-FAVOURABLE |
| legal_trouble | H6·enemies | 18 | — | +0.095 | +0.012 | 79% | UNDER-POWERED |
| major_disease | H6·disease_chronic | 1501 | 0.506 | +0.025 | -0.008 | 80% | SATURATED-AFFLICTED |
| divorced | H7·marital_happiness | 793 | 0.485 | -0.026 | +0.001 | 39% | PURE-NOISE |
| long_marriage | H7·marital_happiness | 1529 | 0.485 | -0.048 | -0.004 | 47% | PURE-NOISE |
| widowed | H7·coverture | 477 | 0.490 | +0.003 | -0.005 | 34% | PURE-NOISE |
| long_life | H8·longevity | 3874 | 0.496 | -0.012 | +0.004 | 75% | SATURATED-FAVOURABLE |
| short_life | H8·longevity | 725 | 0.496 | +0.006 | +0.000 | 1% | SATURATED-FAVOURABLE-AGAINST |
| suicide | H8·death | 372 | 0.534 | +0.044 | +0.018 | 72% | WEAK-SIGNAL |
| father_died_early | H9·father | 26 | 0.450 | -0.081 | -0.003 | 31% | UNDER-POWERED |
| religion_vocation | H9·dharma | 941 | 0.496 | +0.001 | -0.013 | 67% | SATURATED-FAVOURABLE |
| awards_top | H10·status_honour | 2463 | 0.502 | +0.009 | +0.003 | 66% | SATURATED-FAVOURABLE |
| inheritance | H11·gains | 101 | 0.500 | +0.056 | -0.064 | 70% | PURE-NOISE |
| expatriate | H12·foreign_residence | 831 | 0.507 | +0.004 | -0.007 | 30% | PURE-NOISE |
| prison | H12·incarceration | 430 | 0.475 | -0.044 | -0.004 | 65% | INVERTED |

Off-diagonal noise floor (|AUC−.5| across 1209 unmatched cells): median 0.008, p95 0.061. A matched effect below the p95 is indistinguishable from the field's own noise.


## 2. House heat table

| house | features tested | mean |AUC−.5| | over-affliction index | classes |
|---|---|---|---|---|
| H1 | — untested (no pre-registered reality feature) | | | |
| H2 | wealthy, bankrupt, eyes_problem | 0.050 | 28% | PURE-NOISE, SATURATED-FAVOURABLE-AGAINST |
| H3 | military | 0.020 | — | INVERTED |
| H4 | mother_died_early | 0.036 | 33% | UNDER-POWERED |
| H5 | kids_none, kids_many, creative_vocation, science_vocation | 0.012 | 76% | SATURATED-AFFLICTED, SATURATED-AFFLICTED-AGAINST, SATURATED-FAVOURABLE |
| H6 | major_disease, legal_trouble | 0.003 | 80% | SATURATED-AFFLICTED, UNDER-POWERED |
| H7 | divorced, long_marriage, widowed | 0.013 | 36% | PURE-NOISE |
| H8 | long_life, short_life, suicide | 0.014 | 36% | SATURATED-FAVOURABLE, SATURATED-FAVOURABLE-AGAINST, WEAK-SIGNAL |
| H9 | religion_vocation, father_died_early | 0.027 | 31% | SATURATED-FAVOURABLE, UNDER-POWERED |
| H10 | awards_top | 0.002 | — | SATURATED-FAVOURABLE |
| H11 | inheritance | 0.000 | — | PURE-NOISE |
| H12 | expatriate, prison | 0.016 | 65% | INVERTED, PURE-NOISE |

## 3. Feature blocks — confusion, calibration, and named cases


### H2 · wealth ← `bankrupt` (direction: afflicted-expected) — **SATURATED-FAVOURABLE-AGAINST**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 44 | 30% | 2% | 68% | 0% |
| reference (contrast) | 467 | 30% | 8% | 63% | 0% |
| background | 15939 | 29% | 8% | 63% | 0% |

Calibration P(case|reading): afflicted→8.6%, mixed→2.6%, favourable→9.3% (prevalence 8.6%). Tier-A AUC — vs tier-B 0.410 (the birth-time-noise test).

Example cases:
- **Bach, Richard** (b. 1936-06-23, tier A) — engine read H2 wealth **favourable-strong**; reality: bankrupt. [DISAGREE_STRONG]
- **Kreuger, Ivar** (b. 1880-03-02, tier B) — engine read H2 wealth **favourable-strong**; reality: bankrupt. [DISAGREE_STRONG]


### H2 · vision ← `eyes_problem` (direction: afflicted-expected) — **PURE-NOISE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 44 | 34% | 9% | 57% | 0% |
| reference (background) | 16406 | 28% | 8% | 64% | 0% |
| background | 16406 | 28% | 8% | 64% | 0% |

Calibration P(case|reading): afflicted→0.3%, mixed→0.3%, favourable→0.2% (prevalence 0.3%). Tier-A AUC 0.500 vs tier-B 0.588 (the birth-time-noise test).

Example cases:
- **Presley, Elvis** (b. 1935-01-08, tier A) — engine read H2 vision **favourable-strong**; reality: eyes_problem. [DISAGREE_STRONG]
- **Ritter, John** (b. 1948-09-17, tier A) — engine read H2 vision **favourable-strong**; reality: eyes_problem. [DISAGREE_STRONG]
- **Kohli, Rahul** (b. 1985-11-13, tier B) — engine read H2 vision **afflicted-strong**; reality: eyes_problem. [AGREE_STRONG]


### H2 · wealth ← `wealthy` (direction: favourable-expected) — **PURE-NOISE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 474 | 30% | 8% | 62% | 0% |
| reference (contrast) | 37 | 24% | 3% | 73% | 0% |
| background | 15939 | 29% | 8% | 63% | 0% |

Calibration P(case|reading): afflicted→94.0%, mixed→97.4%, favourable→91.6% (prevalence 92.8%). Tier-A AUC — vs tier-B 0.410 (the birth-time-noise test).

Example cases:
- **Presley, Elvis** (b. 1935-01-08, tier A) — engine read H2 wealth **favourable-strong**; reality: wealthy. [AGREE_STRONG]


### H3 · courage ← `military` (direction: favourable-expected) — **INVERTED**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 1192 | 28% | 1% | 70% | 0% |
| reference (background) | 15258 | 24% | 2% | 74% | 0% |
| background | 15258 | 24% | 2% | 74% | 0% |

Calibration P(case|reading): afflicted→8.4%, mixed→6.0%, favourable→6.9% (prevalence 7.2%). Tier-A AUC 0.480 vs tier-B 0.480 (the birth-time-noise test).

Example cases:
- **Pétros, Prince of Greece and Denmark** (b. 1908-12-03, tier A) — engine read H3 courage **afflicted-strong**; reality: military. [DISAGREE_STRONG]
- **Bowser, Alpha L.** (b. 1910-08-21, tier B) — engine read H3 courage **afflicted-strong**; reality: military. [DISAGREE_STRONG]
- **McQueen, Steve** (b. 1930-03-24, tier B) — engine read H3 courage **favourable-strong**; reality: military. [AGREE_STRONG]


### H4 · mother ← `mother_died_early` (direction: afflicted-expected) — **UNDER-POWERED**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 25 | 32% | 8% | 60% | 0% |
| reference (background) | 16425 | 33% | 12% | 55% | 0% |
| background | 16425 | 33% | 12% | 55% | 0% |

Calibration P(case|reading): afflicted→0.1%, mixed→0.1%, favourable→0.2% (prevalence 0.1%). Tier-A AUC — vs tier-B — (the birth-time-noise test).

Example cases:
- **Bergman, Ingrid** (b. 1915-08-29, tier B) — engine read H4 mother **favourable-strong**; reality: mother_died_early. [DISAGREE_STRONG]
- **Anna, Duchess of Mecklenburg** (b. 1865-04-07, tier B) — engine read H4 mother **favourable-strong**; reality: mother_died_early. [DISAGREE_STRONG]


### H5 · intellect ← `creative_vocation` (direction: favourable-expected) — **SATURATED-FAVOURABLE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 8307 | 30% | 1% | 66% | 3% |
| reference (background) | 8143 | 31% | 1% | 65% | 3% |
| background | 8143 | 31% | 1% | 65% | 3% |

Calibration P(case|reading): afflicted→50.3%, mixed→43.2%, favourable→50.7% (prevalence 50.5%). Tier-A AUC 0.501 vs tier-B 0.500 (the birth-time-noise test).

Example cases:
- **Wilson, Flip** (b. 1933-12-08, tier A) — engine read H5 intellect **afflicted-strong**; reality: creative_vocation. [DISAGREE_STRONG]
- **Affleck, Ben** (b. 1972-08-15, tier A) — engine read H5 intellect **afflicted-strong**; reality: creative_vocation. [DISAGREE_STRONG]
- **Berle, Milton** (b. 1908-07-12, tier B) — engine read H5 intellect **favourable-strong**; reality: creative_vocation. [AGREE_STRONG]


### H5 · children ← `kids_many` (direction: favourable-expected) — **SATURATED-AFFLICTED-AGAINST**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 1475 | 76% | 1% | 23% | 0% |
| reference (contrast) | 391 | 79% | 2% | 19% | 0% |
| background | 14584 | 76% | 1% | 23% | 0% |

Calibration P(case|reading): afflicted→78.3%, mixed→69.6%, favourable→82.1% (prevalence 79.0%). Tier-A AUC 0.533 vs tier-B 0.517 (the birth-time-noise test).

Example cases:
- **Allen, Woody** (b. 1935-12-01, tier A) — engine read H5 children **afflicted-strong**; reality: kids_many. [DISAGREE_STRONG]
- **Densen-Gerber, Judianne** (b. 1934-11-13, tier A) — engine read H5 children **afflicted-strong**; reality: kids_many. [DISAGREE_STRONG]
- **Baker, James** (b. 1930-04-28, tier A) — engine read H5 children **favourable-strong**; reality: kids_many. [AGREE_STRONG]


### H5 · children ← `kids_none` (direction: afflicted-expected) — **SATURATED-AFFLICTED**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 391 | 79% | 2% | 19% | 0% |
| reference (contrast) | 1475 | 76% | 1% | 23% | 0% |
| background | 14584 | 76% | 1% | 23% | 0% |

Calibration P(case|reading): afflicted→21.7%, mixed→30.4%, favourable→17.9% (prevalence 20.9%). Tier-A AUC 0.533 vs tier-B 0.517 (the birth-time-noise test).

Example cases:
- **Liberace** (b. 1919-05-16, tier B) — engine read H5 children **favourable-strong**; reality: kids_none. [DISAGREE_STRONG]
- **McKellen, Ian** (b. 1939-05-25, tier B) — engine read H5 children **favourable-strong**; reality: kids_none. [DISAGREE_STRONG]
- **Dole, Elizabeth** (b. 1936-07-29, tier A) — engine read H5 children **afflicted-strong**; reality: kids_none. [AGREE_STRONG]


### H5 · intellect ← `science_vocation` (direction: favourable-expected) — **SATURATED-FAVOURABLE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 643 | 30% | 1% | 67% | 3% |
| reference (background) | 15807 | 30% | 1% | 66% | 3% |
| background | 15807 | 30% | 1% | 66% | 3% |

Calibration P(case|reading): afflicted→3.8%, mixed→4.0%, favourable→4.0% (prevalence 3.9%). Tier-A AUC 0.498 vs tier-B 0.503 (the birth-time-noise test).

Example cases:
- **Lamarr, Hedy** (b. 1914-11-09, tier B) — engine read H5 intellect **afflicted-strong**; reality: science_vocation. [DISAGREE_STRONG]
- **Wallace, Henry** (b. 1888-10-07, tier B) — engine read H5 intellect **afflicted-strong**; reality: science_vocation. [DISAGREE_STRONG]
- **Keynes, John Maynard** (b. 1883-06-05, tier B) — engine read H5 intellect **favourable-strong**; reality: science_vocation. [AGREE_STRONG]


### H6 · enemies ← `legal_trouble` (direction: afflicted-expected) — **UNDER-POWERED**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 18 | 89% | 0% | 11% | 0% |
| reference (background) | 16432 | 79% | 1% | 20% | 0% |
| background | 16432 | 79% | 1% | 20% | 0% |

Calibration P(case|reading): afflicted→0.1%, mixed→0.0%, favourable→0.1% (prevalence 0.1%). Tier-A AUC — vs tier-B — (the birth-time-noise test).

Example cases:
- **Clinton, Bill** (b. 1946-08-19, tier B) — engine read H6 enemies **afflicted-strong**; reality: legal_trouble. [AGREE_STRONG]


### H6 · disease_chronic ← `major_disease` (direction: afflicted-expected) — **SATURATED-AFFLICTED**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 1501 | 82% | 1% | 17% | 0% |
| reference (background) | 14949 | 80% | 1% | 19% | 0% |
| background | 14949 | 80% | 1% | 19% | 0% |

Calibration P(case|reading): afflicted→9.4%, mixed→10.5%, favourable→8.0% (prevalence 9.1%). Tier-A AUC 0.516 vs tier-B 0.498 (the birth-time-noise test).

Example cases:
- **Hugo, Victor** (b. 1802-02-26, tier B) — engine read H6 disease_chronic **favourable-strong**; reality: major_disease. [DISAGREE_STRONG]
- **Belafonte, Harry** (b. 1927-03-01, tier B) — engine read H6 disease_chronic **favourable-strong**; reality: major_disease. [DISAGREE_STRONG]
- **Wilson, Flip** (b. 1933-12-08, tier A) — engine read H6 disease_chronic **afflicted-strong**; reality: major_disease. [AGREE_STRONG]


### H7 · marital_happiness ← `divorced` (direction: afflicted-expected) — **PURE-NOISE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 793 | 39% | 11% | 49% | 0% |
| reference (contrast) | 1443 | 41% | 13% | 46% | 0% |
| background | 14214 | 39% | 13% | 47% | 0% |

Calibration P(case|reading): afflicted→34.0%, mixed→33.2%, favourable→37.3% (prevalence 35.5%). Tier-A AUC 0.484 vs tier-B 0.487 (the birth-time-noise test).

Example cases:
- **Caan, James** (b. 1940-03-26, tier A) — engine read H7 marital_happiness **favourable-strong**; reality: divorced. [DISAGREE_STRONG]
- **Koestler, Arthur** (b. 1905-09-05, tier B) — engine read H7 marital_happiness **favourable-strong**; reality: divorced. [DISAGREE_STRONG]
- **Deschanel, Zooey** (b. 1980-01-17, tier A) — engine read H7 marital_happiness **afflicted-strong**; reality: divorced. [AGREE_STRONG]


### H7 · marital_happiness ← `long_marriage` (direction: favourable-expected) — **PURE-NOISE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 1529 | 42% | 13% | 46% | 0% |
| reference (contrast) | 707 | 38% | 11% | 50% | 0% |
| background | 14214 | 39% | 13% | 47% | 0% |

Calibration P(case|reading): afflicted→70.3%, mixed→70.4%, favourable→66.2% (prevalence 68.4%). Tier-A AUC 0.484 vs tier-B 0.487 (the birth-time-noise test).

Example cases:
- **Hackman, Gene** (b. 1930-01-30, tier B) — engine read H7 marital_happiness **afflicted-strong**; reality: long_marriage. [DISAGREE_STRONG]
- **Ailes, Roger** (b. 1940-05-15, tier A) — engine read H7 marital_happiness **afflicted-strong**; reality: long_marriage. [DISAGREE_STRONG]
- **Koestler, Arthur** (b. 1905-09-05, tier B) — engine read H7 marital_happiness **favourable-strong**; reality: long_marriage. [AGREE_STRONG]


### H7 · coverture ← `widowed` (direction: afflicted-expected) — **PURE-NOISE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 477 | 34% | 27% | 38% | 0% |
| reference (background) | 15973 | 34% | 31% | 35% | 0% |
| background | 15973 | 34% | 31% | 35% | 0% |

Calibration P(case|reading): afflicted→2.9%, mixed→2.6%, favourable→3.2% (prevalence 2.9%). Tier-A AUC 0.475 vs tier-B 0.500 (the birth-time-noise test).

Example cases:
- **Cartland, Barbara** (b. 1901-07-09, tier A) — engine read H7 coverture **favourable-strong**; reality: widowed. [DISAGREE_STRONG]
- **Coppola, Francis Ford** (b. 1939-04-07, tier A) — engine read H7 coverture **favourable-strong**; reality: widowed. [DISAGREE_STRONG]
- **Boonstra-van der Bijl, Cornelia** (b. 1910-10-06, tier B) — engine read H7 coverture **afflicted-strong**; reality: widowed. [AGREE_STRONG]


### H8 · longevity ← `long_life` (direction: favourable-expected) — **SATURATED-FAVOURABLE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 3874 | 1% | 24% | 75% | 0% |
| reference (contrast) | 725 | 1% | 22% | 76% | 0% |
| background | 11851 | 1% | 24% | 75% | 0% |

Calibration P(case|reading): afflicted→73.5%, mixed→85.2%, favourable→84.0% (prevalence 84.2%). Tier-A AUC 0.492 vs tier-B 0.500 (the birth-time-noise test).

Example cases:
- **Kristofferson, Kris** (b. 1936-06-22, tier B) — engine read H8 longevity **favourable-strong**; reality: long_life. [AGREE_STRONG]


### H8 · longevity ← `short_life` (direction: afflicted-expected) — **SATURATED-FAVOURABLE-AGAINST**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 725 | 1% | 22% | 76% | 0% |
| reference (contrast) | 3874 | 1% | 24% | 75% | 0% |
| background | 11851 | 1% | 24% | 75% | 0% |

Calibration P(case|reading): afflicted→26.5%, mixed→14.8%, favourable→16.0% (prevalence 15.8%). Tier-A AUC 0.492 vs tier-B 0.500 (the birth-time-noise test).

Example cases:
- **Brown, Bobbi Kristina** (b. 1993-03-04, tier A) — engine read H8 longevity **favourable-strong**; reality: short_life. [DISAGREE_STRONG]
- **Audouit, Maryse** (b. 1961-07-11, tier A) — engine read H8 longevity **favourable-strong**; reality: short_life. [DISAGREE_STRONG]


### H8 · death ← `suicide` (direction: afflicted-expected) — **WEAK-SIGNAL**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 372 | 77% | 1% | 22% | 0% |
| reference (background) | 16078 | 72% | 1% | 27% | 0% |
| background | 16078 | 72% | 1% | 27% | 0% |

Calibration P(case|reading): afflicted→2.4%, mixed→3.3%, favourable→1.9% (prevalence 2.3%). Tier-A AUC 0.540 vs tier-B 0.531 (the birth-time-noise test).

Example cases:
- **Jackson, Arthur** (b. 1935-08-28, tier A) — engine read H8 death **favourable-strong**; reality: suicide. [DISAGREE_STRONG]
- **Boyer, Charles** (b. 1899-08-28, tier B) — engine read H8 death **favourable-strong**; reality: suicide. [DISAGREE_STRONG]
- **Hemingway, Margaux** (b. 1954-02-16, tier B) — engine read H8 death **afflicted-strong**; reality: suicide. [AGREE_STRONG]


### H9 · father ← `father_died_early` (direction: afflicted-expected) — **UNDER-POWERED**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 26 | 23% | 8% | 69% | 0% |
| reference (background) | 16424 | 31% | 11% | 58% | 0% |
| background | 16424 | 31% | 11% | 58% | 0% |

Calibration P(case|reading): afflicted→0.1%, mixed→0.1%, favourable→0.2% (prevalence 0.2%). Tier-A AUC — vs tier-B — (the birth-time-noise test).

Example cases:
- **Adams, Patch** (b. 1945-05-28, tier B) — engine read H9 father **favourable-strong**; reality: father_died_early. [DISAGREE_STRONG]
- **Heche, Anne** (b. 1969-05-25, tier A) — engine read H9 father **favourable-strong**; reality: father_died_early. [DISAGREE_STRONG]


### H9 · dharma ← `religion_vocation` (direction: favourable-expected) — **SATURATED-FAVOURABLE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 941 | 27% | 5% | 67% | 0% |
| reference (background) | 15509 | 27% | 5% | 67% | 0% |
| background | 15509 | 27% | 5% | 67% | 0% |

Calibration P(case|reading): afflicted→5.8%, mixed→5.5%, favourable→5.7% (prevalence 5.7%). Tier-A AUC 0.498 vs tier-B 0.495 (the birth-time-noise test).

Example cases:
- **Burgess, Belva** (b. 1890-03-21, tier A) — engine read H9 dharma **afflicted-strong**; reality: religion_vocation. [DISAGREE_STRONG]
- **Kreskin** (b. 1935-01-12, tier A) — engine read H9 dharma **afflicted-strong**; reality: religion_vocation. [DISAGREE_STRONG]
- **Moyers, Bill** (b. 1934-06-05, tier B) — engine read H9 dharma **favourable-strong**; reality: religion_vocation. [AGREE_STRONG]


### H10 · status_honour ← `awards_top` (direction: favourable-expected) — **SATURATED-FAVOURABLE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 2463 | 23% | 10% | 67% | 0% |
| reference (background) | 13987 | 24% | 10% | 66% | 0% |
| background | 13987 | 24% | 10% | 66% | 0% |

Calibration P(case|reading): afflicted→14.8%, mixed→14.2%, favourable→15.2% (prevalence 15.0%). Tier-A AUC 0.505 vs tier-B 0.500 (the birth-time-noise test).

Example cases:
- **Bosley, Tom** (b. 1927-10-01, tier A) — engine read H10 status_honour **afflicted-strong**; reality: awards_top. [DISAGREE_STRONG]
- **Fonda, Bridget** (b. 1964-01-27, tier B) — engine read H10 status_honour **afflicted-strong**; reality: awards_top. [DISAGREE_STRONG]
- **Cher** (b. 1946-05-20, tier A) — engine read H10 status_honour **favourable-strong**; reality: awards_top. [AGREE_STRONG]


### H11 · gains ← `inheritance` (direction: favourable-expected) — **PURE-NOISE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 101 | 12% | 13% | 75% | 0% |
| reference (background) | 16349 | 21% | 9% | 70% | 0% |
| background | 16349 | 21% | 9% | 70% | 0% |

Calibration P(case|reading): afflicted→0.3%, mixed→0.8%, favourable→0.7% (prevalence 0.6%). Tier-A AUC 0.482 vs tier-B 0.512 (the birth-time-noise test).

Example cases:
- **Vanderbilt, Gloria** (b. 1924-02-20, tier B) — engine read H11 gains **favourable-strong**; reality: inheritance. [AGREE_STRONG]


### H12 · foreign_residence ← `expatriate` (direction: favourable-expected) — **PURE-NOISE**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 831 | 37% | 33% | 30% | 0% |
| reference (background) | 15619 | 38% | 32% | 30% | 0% |
| background | 15619 | 38% | 32% | 30% | 0% |

Calibration P(case|reading): afflicted→4.9%, mixed→5.2%, favourable→5.1% (prevalence 5.1%). Tier-A AUC 0.491 vs tier-B 0.513 (the birth-time-noise test).

Example cases:
- **Starr, Ringo** (b. 1940-07-07, tier B) — engine read H12 foreign_residence **afflicted-strong**; reality: expatriate. [DISAGREE_STRONG]
- **DePeyster, Anna** (b. 1944-06-30, tier A) — engine read H12 foreign_residence **afflicted-strong**; reality: expatriate. [DISAGREE_STRONG]
- **Moore, Dudley** (b. 1935-04-19, tier B) — engine read H12 foreign_residence **favourable-strong**; reality: expatriate. [AGREE_STRONG]


### H12 · incarceration ← `prison` (direction: afflicted-expected) — **INVERTED**

| group | n | afflicted | mixed | favourable | abstain |
|---|---|---|---|---|---|
| cases | 430 | 61% | 33% | 7% | 0% |
| reference (background) | 16020 | 65% | 28% | 6% | 0% |
| background | 16020 | 65% | 28% | 6% | 0% |

Calibration P(case|reading): afflicted→2.4%, mixed→3.0%, favourable→2.7% (prevalence 2.6%). Tier-A AUC 0.491 vs tier-B 0.461 (the birth-time-noise test).

Example cases:
- **D'Adelswärd-Fersen, Jacques** (b. 1880-02-20, tier B) — engine read H12 incarceration **favourable-strong**; reality: prison. [DISAGREE_STRONG]
- **Snoop Dogg** (b. 1971-10-20, tier A) — engine read H12 incarceration **favourable-strong**; reality: prison. [DISAGREE_STRONG]
- **Welty, Judias** (b. 1943-04-04, tier A) — engine read H12 incarceration **afflicted-strong**; reality: prison. [AGREE_STRONG]


## 4. Caveats

- Reality labels are AstroDatabank's own category tags (coarse, era-dependent); the corpus is celebrity-selected.
- The tier-A-vs-B columns test the birth-time-noise excuse: if time error blurred a real signal, minute-precision tier-A must out-perform tier-B.
- Lagna slice uses AstroDatabank's published ascendants (tropical→sidereal, cusp rows flagged) — see atlas_results.json.
- Governance: per METHODOLOGY.md, nothing here tunes the engine.
