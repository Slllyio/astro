# Real-outcome generalization — the Prime Directive's second axis, measured at scale (2026-07-24)

> "Measure honestly. Distinguish textbook fidelity from real-outcome generalization; report both;
> overfitting to worked examples is not accuracy." — CLAUDE.md Prime Directive
>
> The golden ratchet measures **textbook fidelity** (does the engine reproduce Raman's printed
> verdicts — currently 261/293 = 89%). It has never measured **real-outcome generalization** (does
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

> **Textbook fidelity: 261/293 = 89.1% (at its proven ceiling).
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
