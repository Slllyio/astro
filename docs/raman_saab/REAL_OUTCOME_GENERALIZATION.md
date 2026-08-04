---
title: "Real-outcome generalization — the Prime Directive's second axis, measured at scale"
kind: analysis
topic: validation
measured: true
updated: 2026-07-24
words: 3782
tags: [raman-saab, analysis, validation]
---
# Real-outcome generalization — the Prime Directive's second axis, measured at scale (2026-07-24)

> "Measure honestly. Distinguish textbook fidelity from real-outcome generalization; report both;
> overfitting to worked examples is not accuracy." — CLAUDE.md Prime Directive
>
> The golden ratchet measures **textbook fidelity** (does the engine reproduce Raman's printed
> verdicts — currently 259/293 = 88.4% exact, 283/293 = 96.6% within one ordinal step). It has
> never measured **real-outcome generalization** (does
> the engine predict *actual lives*). Using the AstroDatabank AA-rated corpus (20,218 charts with
> clean birth times + 47k dated life events, under `data/astro_databank/`, local/gitignored), this is
> the first at-scale measurement of that second axis. Harness: `tools/raman_saab/real_outcome_test.py`.

## Test 1 — LONGEVITY: Ayurdaya predicted span vs ACTUAL death age

Own, natural deaths only (relatives' deaths and violent/maraka-cut deaths — Accident/Suicide/Homicide
— excluded, since Ayurdaya predicts *capacity*, which a violent maraka cuts short). n=40 AA charts.

- **Pearson r (predicted span vs actual age): +0.14** — weak positive.
- **Longevity-CLASS match (alpa/madhya/purna): 58%** vs 33% random — **~1.7x chance, a real signal.**
- **Mean predicted 75.6 vs actual 69.3** — the engine OVER-predicts by ~6 years, which is
  *doctrinally correct*: Ayurdaya is a capacity, and people die before their capacity via maraka /
  disease / accident. The over-prediction is the expected capacity-vs-realized gap, not an error.

## Test 2 — TIMING: does `active_houses` fire on the event's house when the event happened?

n=360 dated events (Marriage/Divorce/Death/Career/education/health -> house).

- **hit-rate 0.83 vs base-rate 0.88 -> lift -0.06** — **no timing signal.** The cause is the metric,
  not the engine: `active_houses` is "broad-recall / low-precision by design" (its own docstring) — a
  slow-lord Mahadasha lights up ~10.5 of 12 houses, so "the event's house is active" is nearly always
  true AND so is any random house. The measure is saturated; it cannot resolve event timing.

## The honest headline

**High textbook fidelity (89%) does NOT translate into strong real-outcome prediction.** The engine
reproduces Raman's *books* very well, but on *real lives* it shows only a modest, class-level
longevity signal (~1.7x chance, correctly biased toward capacity) and no event-timing signal from the
broad `active_houses` tool. This is exactly the distinction the Prime Directive demands be reported —
and it is the first time it has been quantified for this engine. It re-frames the ~89% ceiling: that
number is *textbook fidelity at its ceiling*, and it is not the same thing as real-world accuracy.

## Caveats (this is a baseline, not a verdict on the doctrine)

The signal is weak partly for reasons that a rigorous study would address, NOT necessarily because the
doctrine fails:
- **Small clean n** (40 natural deaths, 360 timed events) — no significance testing yet.
- **Data noise** — AstroDatabank event attribution is imperfect (namesakes; "College Girl"/"Billy the
  Kid" type mis-datings survive even after own-natural-death filtering); birth-time uncertainty even in
  AA rows shifts the ascendant/dasha.
- **Metric looseness** — Ayurdaya *capacity* != realized death age (needs the maraka-dasha layer for
  the realized span); `active_houses` is too broad (a real timing test needs significator-window or
  antar/pratyantar-level resolution, or a within-chart control-date design).

## What a rigorous version needs (a research program, not a clause)

1. **Curate** a clean death/event subset (dedupe namesakes; verify own-death; keep minute-precision AA
   times) with significance tests and a control-date null.
2. **Realized-death metric**: Ayurdaya span + the maraka-dasha death window (already in the engine:
   `vimshottari.death_window`) vs actual age — capacity alone under-tests the doctrine.
3. **Tighter timing**: `significator_dasha_windows` / antar-pratyantar, or a within-chart control, to
   escape the `active_houses` saturation.
4. **Static trait tests**: multiple-marriage -> H7, childless -> H5, etc., with matched controls.

The harness + the honest baseline are shipped; the rigorous study is the next real-outcome frontier.

---

# THE RIGOROUS STUDY (2026-07-24) — the astrobank program results

The rigorous version was built and run: `tools/raman_saab/astrobank/` — a pre-registered,
doctrine-reviewed, negative-controlled validation over **22,177 charts** (64,644-person celebrity
master, quality-tiered, noon-births excluded) with **18,169 house-specific outcome labels** across
12 cohorts and **31,557 dated events**. Full protocol in `tools/raman_saab/astrobank/METHODOLOGY.md`;
per-mapping doctrine citations verified by bphs-doctrine-reviewer (notably: **HTJAH-II:3937-3943 has
Raman personally mandating exactly this thousands-of-horoscopes test** — the program is doctrinally
self-licensed).

## Results (pre-registered, sham-gated, BH-corrected)

| test | tier | AUC / lift | 95% CI | n | verdict |
|---|---|---|---|---|---|
| **SHAM (expatriate→H5)** | gate | 0.500 | (0.473, 0.525) | 293 | **exact null — pipeline valid** |
| H5 childless-vs-prolific | core | 0.523 | (0.496, 0.549) | 391 | weak direction, sub-threshold (<0.55), BH-fail |
| H8 ayurdaya short-vs-long | core | 0.502 | (0.478, 0.524) | 685 | **null** — capacity does not separate realized spans |
| H12 prison | core | 0.475 | (0.450, 0.503) | 430 | **null, wrong direction**; specificity rank 7/12 |
| H7 divorced-vs-long-marriage | supporting | 0.485 | (0.460, 0.509) | 790 | null |
| H7 widowed (coverture) | supporting | 0.492 | (0.466, 0.517) | 476 | null |
| H2 bankrupt-vs-wealthy | supporting | 0.412 | (0.317, 0.506) | 37 | null (wide CI) |
| H8 suicide (death-manner) | exploratory | **0.535** | (0.505, 0.565), perm p=.005 | 341 | the one above-chance signal (descriptive only) |
| H8 accident (death-manner) | exploratory | 0.511 | (0.483, 0.537) | 394 | weak |
| timing: death vs primary-maraka AD | timing (valid, coverage 0.34) | lift −0.007 | (−0.029, +0.012) | 2,377 | **null** — deaths land in maraka windows no more than control dates |
| timing: marriage/divorce/death-any-maraka | timing | — | — | — | WITHHELD (instrument saturated, coverage 0.63–0.79) |

## The honest headline

**With a validated pipeline (sham exactly 0.500) and Raman's own mandated experimental design, the
engine shows no real-outcome generalization signal on any pre-registered core test.** The 89%
textbook-fidelity number measures how well the engine reproduces *Raman's books*; on 22k *real
lives* the house verdicts, the numeric ayurdaya, and the maraka death-timing all test statistically
null. The single positive is exploratory (suicide → afflicted 8th death-manner, AUC 0.535,
perm p=.005) and per protocol is descriptive, not a claim — a candidate for a future confirmatory
pre-registration on an independent corpus slice.

Three honest qualifications, all pre-registered before results were read:
1. **Doctrine-anticipated miss channels** exist (a strong 5th can still deny children via weak
   Beeja/Kshetra — HTJAH-I:5496-5527) and depress achievable AUC; they cannot explain full nulls.
2. **The corpus is celebrity-selected** with era/geography structure; stratification + the sham
   control address this (and the sham WAS null), but base-rate subtleties remain.
3. **Bhava-verdict binaries are coarse instruments** for graded doctrines; the `degree` secondary
   metric did not change any conclusion.

## The generalization ratchet (committed)

`tools/raman_saab/astrobank/real_outcome_baseline.json` records the 4 valid metrics with floors;
`tests/raman_saab/test_astrobank_ratchet.py` guards them locally (CI-skip-safe, hash-guarded).
Governance stands: these results are a monitoring axis only — the golden (textbook) ratchet remains
the engine's development gate, and the two axes are reported side by side, never averaged:

> **Textbook fidelity: 259/293 = 88.4% exact / 283/293 = 96.6% within-1 (at its proven ceiling).
> Real-outcome generalization: statistically null on all pre-registered core tests (n=22,177).**

That pair of numbers, stated together, is the Prime Directive's "measure honestly" fulfilled.

---

# STAGE 6 (2026-07-24) — the "wrong question" challenge, and the corrected tests

A fair methodological challenge was raised: *the cohort tests may ask the engine the wrong
question.* The diagnostic proved the challenge substantially RIGHT, in three ways:

1. **Instrument skew (proven):** on the ordinary-chart control population the verdict rollup is
   near-constant for the null-testing significations — children **76% afflicted**, incarceration
   65%, death 72%. An engine calibrated on Raman's curated affliction-showcase charts over-afflicts
   ordinary charts, leaving cohort tests almost nothing to discriminate with. (This is also a real
   finding about the ENGINE: its verdicts are book-regime-calibrated, not population-calibrated.)
2. **Question-form mismatch (mathematical):** the doctrine asserts rare conditionals; a rule firing
   on ~4% of charts cannot move cohort AUC visibly even at high precision. The pre-registered AUC
   test could not have detected doctrine-consistent effects of the doctrine's own form.
3. **Wrong timing instrument:** Stage 4 used lifetime maraka windows; the doctrinal instrument is
   the span-anchored `death_window`.

## The corrected tests (pre-registered as v3 BEFORE computation)

**A. Rule-level enrichment** — every evaluable rule on the outcome significations, tested as the
conditional claim Raman made: P(outcome | combination fires) vs base rate, binomial, BH q=0.10,
min 30 fires. Result: **91 rule-outcome tests, 0 survive BH.** Top hits are weak and directionally
scattered (e.g. Saturn-in-5th trends LESS childless, 0.69x). The classical combinations, tested in
their own native conditional form on real lives, do not validate.

**B. Death-window containment** — 2,164 real deaths vs the engine's span-anchored maraka windows:
observed 32.3% in-window vs 11.6% naive expectation — an apparently massive lift (+0.208, CI
+0.189..+0.227). **The falsification control killed it:** testing each death against OTHER
people's windows (age-aligned) gives 32.4% — chart-specific excess = **−0.001**. The entire
"signal" is age structure (windows sit at typical death ages for everyone); the windows carry zero
chart-specific timing information. The controls work in both directions: the sham caught no fake
negatives; the cross-chart null caught this fake positive.

## Final verdict of the program (strengthened by the challenge)

The corrected questions make the null far stronger, because it now survives the question-form
critique: **tested as population classifiers, as rare conditionals (the doctrine's own form), and
with the doctrine's own timing instrument — all with validated controls — the engine's predictions
carry no detectable chart-specific information about real-life outcomes.** The lone residual is the
exploratory suicide/afflicted-8th association (AUC 0.535, perm p=.005), which awaits an independent
confirmatory slice.

Secondary finding for the engine's own roadmap (monitoring-axis only, golden sovereignty holds):
the verdict layer OVER-AFFLICTS ordinary charts (children 76%/incarceration 65%/death 72%
afflicted on random controls) — a population-calibration property invisible to the golden corpus,
now quantified.


> Per-case atlas — WHERE it fails, house by house, with named lives: [FAILURE_ATLAS.md](FAILURE_ATLAS.md)

---

# STAGE 10 (2026-07-24) — the pre-registered confirmatory study (the program's last word)

Pre-registration committed BEFORE computation (`tools/raman_saab/astrobank/CONFIRMATORY_PREREG.md`,
commit 27a9f61): three one-sided primaries, α=.05 each, BH q=.10 family. Results verbatim:

| study | sample | result | verdict |
|---|---|---|---|
| **S1 CONFIRMATORY — suicide → afflicted H8** | 218 HELD-OUT tier-C suicide cases (zero overlap with the 341 exploratory) vs 4,898 controls | **AUC 0.528, CI (0.493, 0.564), p=.062** — the point estimate landed on the pre-registered prediction (0.53), direction right, sham companion null (0.493) | **NOT confirmed** at α=.05 |
| **S2 NEW DOCTRINE — Kuja dosha → divorce** (direct chart test, Mars in 2/4/7/8/12, HTJAH-II:2579) | 793 divorced vs 1,529 long-married | dosha rate **41.9% vs 39.8%**, OR 1.09 (0.91–1.30), p=.18; from-Moon secondary OR 0.92 | **null** |
| **S3 NEW DOCTRINE — Saturn-afflicted Moon → suicide** (direct chart test) | 341 suicide vs 8,000+ controls | **35.8% vs 33.0%**, OR 1.13 (0.90–1.42), p=.16. Secondaries: waning+Saturn OR 1.23 (p=.08, trend); Mars comparator OR 1.00 exactly | **null** (with a doctrinally-shaped, non-significant pattern: Saturn>Mars, dark-Moon amplifying) |

Family BH q=.10: **all three fail.**

## Honest reading

- **The suicide thread is not dead — and not confirmed.** The effect size REPLICATED almost exactly
  (exploratory 0.535 → held-out 0.528, no regression to null), which is what a real-but-small
  effect looks like at n=218 (post-hoc: ~50% power for AUC 0.53 at this n; confirmation would need
  ~500 held-out cases, which the corpus does not contain). Status: *suggestive, twice-observed,
  never confirmed* — permanently recorded as such, claimable by nobody.
- **Kuja dosha — the most famous marriage claim in Vedic astrology — tested directly on raw chart
  geometry (immune to every engine-layer critique) does not distinguish divorced from long-married
  on 2,322 real lives.** Both reckonings (Lagna, Moon) null.
- **The Moon-Saturn suicide doctrine**: null at threshold, though the *shape* of the secondaries
  (Saturn carries what little there is; Mars exactly nothing; waning amplifies) is the one place
  the classical structure echoes faintly. Descriptive only.

This closes the astrobank program's question list. Fidelity proven (89%); generalization null
across engine verdicts, raw evidence, rule conditionals, timing, and now the doctrine's own
primitives tested directly; one small twice-seen thread left honestly unresolved for want of data.


---

# STAGE 11 (2026-07-24) — the Survivors' Gauntlet, lane G3 (addendum result)

Per GAUNTLET_PREREG.md (committed before computation): the 52 medini-sourced new suicide cases
resolved to 50 master persons, of whom **29 were strictly never-tested** (never in the exploratory
matrix, never in the store). Cast fresh, added to the 218 held-out tier-C cases:

> **G3 addendum: n=247 never-tested suicide cases vs 4,898 controls — AUC 0.515, CI (0.479, 0.548),
> p=.198 — not confirmed.**

The honest trajectory of the thread across three looks: exploratory 0.535 → held-out 0.528 →
enlarged 0.515. The effect is FADING with each fresh sample, not strengthening — the signature of
an effect that is either smaller than first estimated or not there at all. The suicide/8th thread
remains unconfirmed and now carries a weakening trend; its definitive resolution still requires a
genuinely large independent sample. Lanes G1 (framework career→10H under person-id joins +
censored windows) and G2 (WD marriage under the clean template + era/source arms) remain open, as
pre-registered.

---

# STAGE 11 (2026-07-24) — the Survivors' Gauntlet, lane G2 (WD marriage)

Per GAUNTLET_PREREG.md. The Round-11 medini result (`disambiguation_v1.json`) reported chart
features adding **+0.043 AUC** over an explicit cyclic-date baseline on Wikidata marriage
(n=32,932) and declared "REAL SIGNAL". Pre-run diagnostics changed the question: **every chart in
this corpus is `time_precision='day'` / `birth_time_confidence=0.0`** — all charts were cast at a
default clock time, so the ascendant and all house columns are deterministic functions of
(birth_date, birth_place); the corpus contains no birth-time information at all. And condition B
controlled date but never place — while Wikidata marriage documentation varies strongly by country.

Four arms under the clean template (`app/medini/ml/gauntlet_g2_marriage.py`; one-row-per-person
asserted; 5 seeds × 5 person-disjoint folds; 2,000-resample person bootstrap on paired OOF AUCs):

| arm | features | mean AUC |
|---|---|---|
| B (original baseline) | birth_jd + cyclic date | 0.6367 |
| D (original chart arm) | B + 28 chart cols | 0.6771 |
| G (geography baseline, NEW) | B + birth_lat + birth_lon | 0.7440 |
| DG (decisive) | G + 28 chart cols | 0.7410 |

| lift | value | 95% CI | reading |
|---|---|---|---|
| D − B (replication) | **+0.0404** | (+0.0352, +0.0453) | the original +0.043 replicates exactly |
| G − B (geography alone) | **+0.1069** | (+0.1005, +0.1132) | lat/lon adds 2.6× what charts ever did |
| **DG − G (decisive)** | **−0.0026** | (−0.0037, −0.0015) | charts add *negative* value once place is known |

> **G2 FALLS.** The +0.043 was birth-place information leaking through default-time chart columns.
> With geography in the baseline, the 28 chart features are pure noise drag (CI excludes zero on
> the negative side). Interpretation lock from the prereg holds: even had it survived, a corpus
> with zero real birth times cannot testify about birth-time astrology.

---

# STAGE 11 (2026-07-24) — the Survivors' Gauntlet, lane G1 (framework career→10H)

Per GAUNTLET_PREREG.md. The 2026-05-29 result (`framework_validation_v1_VERDICT.md`) reported the
10H "strong" verdict at **lift 1.37** on 11,753 career events — "the first project-wide positive
doctrinal signal across 12 rounds." The re-run (`app/medini/ml/gauntlet_g1_career.py`) replaced the
apples-to-oranges comparison at its root: the original pitted a **dynamic** event-time reading
(transit + dasha overlay) against a **static** natal baseline pooled over all 75,149 persons. The
clean design composes the *same* machinery on both arms and compares each event only against the
**same person** at year-shifted, age-near control dates (±2..7 yr, JD arithmetic; windows capped at
`min(death−1yr, scrape)`; ≥3 controls; 2,000 person-clustered bootstrap).

Result on 11,626 career events (7,674 persons):

| quantity | value | reading |
|---|---|---|
| within-person paired lift | **1.000**, CI (1.000, 1.000) | zero timing effect |
| paired excess (event − control strong-rate) | **0.000**, CI (0.000, 0.000) | zero |
| events whose 10H label changed at ANY control date | **0 of 11,626** | the label is date-invariant |
| replication vs the original static baseline | **1.366** | reproduces the reported 1.37 exactly |
| cohort selection lift (stored labels, career cohort vs all, *no composition*) | **1.412** | the whole effect |

> **G1 FALLS — and the mechanism is now proven, not inferred.** `reading_composer` computes
> `verdict_label` from the **natal** bhava alone; the gochara/dasha context only sets a *separate*
> `gochara_triggered` flag and never moves the label (`reading_composer.py:142`). So the reading is
> identical for a person on every date — the "event arm" and any "control arm" return the same
> label by construction, and the paired lift is exactly 1.0. The original 1.37 measured **who has
> documented career events**, not **when** they happen: career-cohort persons carry a natal 10H
> strong-rate 1.41× the population (77% Wikidata, whose natal strong-rate is itself the highest of
> the three corpora). Coarse era×geography standardization within Wikidata already collapses the
> residual toward ~1.13. No timing signal exists; the number was a cohort-composition artifact.

## The Gauntlet's verdict — all three survivors fell

| lane | exploratory claim | clean result | status |
|---|---|---|---|
| G3 | suicide → afflicted H8 (0.535, p=.062) | 0.515, CI (0.479, 0.548), p=.198 — fading across 3 looks | unconfirmed |
| G2 | WD marriage chart-lift +0.043 | −0.0026 vs geography baseline, CI excludes 0 | **falls** |
| G1 | framework career→10H lift 1.37 | 1.000, CI (1.000, 1.000); artifact proven | **falls** |

Twelve-plus rounds across both programs (raman_saab doctrine-encoding + medini ML) produced exactly
three positives that outlived their first tests. Under maximum rigor — geography controls,
same-machinery within-person controls, enlarged never-tested samples — **none survived.** The
real-outcome generalization axis is null without exception; the one remaining thread (suicide/8th)
is not merely unconfirmed but weakening with each fresh sample. This closes the Survivors' Gauntlet.

---

# STAGE 12 (2026-07-24) — the Certified Cohort's first result (matched pairs on the certified slice)

`CERTIFIED_COHORT_DESIGN.md` specifies a fresh, consented, birth-certificate-collected laboratory
whose primary analysis is the **matched-discordant-pair** design (§5). Fresh human collection is a
governance-gated program that cannot be launched from a code session — but its *analysis engine*
was built now (`tools/raman_saab/astrobank/certified_matched_pairs.py`) and run against the
**certified slice of the existing corpus**: quality-tier A only — AA Rodden rating AND minute time
precision, i.e. **birth-certificate-sourced charts**. This is the cleanest cut the current data
allows and a design we had never run: era + geography held constant by 1:1 matching, the chart free
to vary, testing the *relative* affliction rank rather than an absolute threshold.

**Flagship domain — divorce vs long-marriage → 7th-house marital-happiness affliction:**

| arm | n (certified, tier-A) | matched pairs | paired AUC | 95% CI | signed-rank p |
|---|---|---|---|---|---|
| **Sham** (off-target 10th/career) | 341 / 612 | 296 | 0.508 | (0.463, 0.556) | 0.60 |
| **Primary** (7th/marital_happiness, afflicted) | 341 / 612 | 296 | **0.495** | (0.443, 0.546) | 0.67 |

> **NULL, sham-gated.** On birth-certificate-certified charts, matched on era and geography, divorced
> and long-married people are indistinguishable by 7th-house affliction — the point estimate sits
> dead-centre on 0.5 (case mean marital-happiness score 1.156 vs control 1.131), not a suppressed
> positive. This is the same convergent null the whole program has found, now reproduced on the
> **certified minute-precision slice** under the design's **own fairest test** (relative rank within
> matched pairs). It narrows the "bad birth times" escape hatch further: the null holds even when the
> times are certificate-grade.

**What this does and does not close.** The matched design controls era + geography + population and
the AA tier controls birth-time quality — so two of the program's escape hatches are shut on this
result. The remaining hatch is **celebrity selection** (the corpus is still notable people; sex is
also unavailable as a matching key). That hatch closes only with the fresh cohort — which is exactly
why the Certified Cohort program exists. Power note: 296 pairs powers ~AUC 0.57 at 80%; a
suicide-thread-sized effect (~0.53) would be under-powered here and needs the fresh, larger sample.

## STAGE 12b — the full certified matched-pair sweep (every domain on the tier-A slice)

The flagship divorce test was then extended to **every** outcome domain with a certified (tier-A =
AA + minute) cohort, directions and sham (off-target 10th/career) frozen before the sweep
(`tools/raman_saab/astrobank/certified_sweep.py`). Two design flavours: **labelled contrasts** (case
vs a labelled opposite — cleanest) and **pooled controls** (case vs all certified non-cases — used
where no labelled opposite exists; weaker).

| domain | design | pairs | paired AUC | 95% CI | signed-rank p | sham | verdict |
|---|---|---|---|---|---|---|---|
| H5 childless vs prolific | labelled | 120 | 0.533 | (0.471, 0.596) | .159 | 0.504 ok | null |
| H7 divorced vs long-married | labelled | 332 | 0.500 | (0.449, 0.550) | .840 | 0.532 ok | null |
| H7 widowed vs long-married | labelled | 171 | 0.471 | (0.404, 0.538) | .474 | 0.520 ok | null |
| H8 short- vs long-life | labelled | 81 | 0.537 | (0.457, 0.617) | .165 | 0.574 ok | null |
| H2 bankrupt vs wealthy | labelled | 9 | — | — | — | — | insufficient N |
| H12 prison vs pool | pooled | 216 | 0.509 | (0.454, 0.565) | .226 | 0.507 ok | null |
| H8 suicide vs pool | pooled | 126 | 0.504 | (0.436, 0.571) | .110 | **0.587 FAIL** | sham-invalid |
| H8 accident vs pool | pooled | 223 | 0.491 | (0.437, 0.547) | .713 | 0.509 ok | null |

> **0 of 7 interpretable certified domains show signal after BH q=0.10.** Every clean
> labelled-contrast domain — children, marriage, widowhood, longevity — is null with its sham gate
> open, on birth-certificate-grade charts, under the design's fairest within-pair test.

**Two honest caveats, both informative.** (1) `H2_wealth` has only 9 certified bankrupts — not a
test. (2) The `H8_suicide` **pooled-control sham failed** (career-house affliction *also* separates
suicide cases from the pool, 0.587): suicide cases differ from the general certified pool in a
*non-specific* way, across houses unrelated to the hypothesis. That is exactly the confound the
pre-registration warned pooled controls carry, and it is why labelled contrasts are the trustworthy
arm — the suicide thread's real evidence remains the dedicated tier-C confirmatory (Stage 10) and
the G3 addendum, not this pooled sham-invalid cell. Net: the convergent null now spans the full
certified slice; the only surviving thread stays exactly where it was — twice-seen, fading,
unconfirmed — awaiting the fresh cohort the design exists to build.
