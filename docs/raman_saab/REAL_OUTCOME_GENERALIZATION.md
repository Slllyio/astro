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
