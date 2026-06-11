# Pre-registration — external replication of the benefic-AD strength effect

**Status: frozen 2026-06-11, before any external data is acquired.** This is the
single confirmatory test to run on the next independent corpus. Everything below
is fixed; running anything else first, or modifying anything after seeing the
data, voids the confirmation.

## The claim under test

Auspicious life events (marriage, career, education) occur at an elevated rate
during Vimshottari periods whose **antardasha lord is a natural benefic
(Jupiter/Venus/Mercury/Moon) that is (a) well-dignified (exalted/own/friendly by
natal sign), (b) in a kendra/trikona from the Lagna, and (c) in a kendra/trikona/
11th counted from the mahadasha lord** — the full conjunction, spec
`S4_full_strength_benefic_AD` in `dasha_strength_confirm.py`.

Current evidence (LunarAstro corpus, n=3,530 person-events): IRR **1.13**
(95% CI 0.998–1.29, p=0.054); replicated in direction across two internal halves
(1.14 / 1.08); **zero discrimination** (C-index 0.503) and **zero forecast skill**
(log-skill −0.0005). The open question is only whether the marginal *rate*
elevation is real.

## Primary endpoint (one test, one-sided)

Single-exposure **SCCS / conditional-Poisson incidence-rate ratio** for S4 on
pooled auspicious first events, age-banded (marriage 16–55, career 18–72,
education 8–40), each native their own control — `dasha_timing_metrics.sccs_irr`.
**H1: IRR > 1. α = 0.05 one-sided.** Exact within-person permutation
(`dasha_strength_confirm._perm_p`, K=10,000) as the confirmatory p.

## Secondary endpoints (reported, not gated)

1. Within-person C-index on the graded 0–4 score (`discrimination`).
2. Out-of-sample log-skill vs age base-rate (`dasha_forecast_skill`).
3. Per-domain IRRs incl. **death** as a specificity control (the claim predicts
   death should NOT lift; on LunarAstro it lifted 1.11 — if the new corpus also
   lifts death, the "effect" is a non-specific artifact, e.g. data-recording
   structure, not benefic timing).

## Power / sample-size requirement

At base exposure ~7% of in-band person-time, one-sided α=0.05, power 0.80
(z₀.₉₅+z₀.₈₀ = 2.486; lift detectable ≈ 1 + 2.486/√(0.07·n·0.93)):

| true IRR | person-events needed |
|---|---|
| 1.10 | ~9,200 |
| 1.13 | ~5,400 |
| 1.15 | ~4,100 |

So the new corpus must contribute **≥ ~9,000 auspicious first events with
birth-time-quality charts** to resolve an IRR of 1.10. Candidate sources:
full Astro-Databank (Rodden-rated AA/A), larger LunarAstro exports, Kota/ADB
merged corpora — deduplicated against the LunarAstro persons (`resolve_persons_dedup`).

## Fixed analysis details

- Charts: sidereal Lahiri, whole-sign houses, same pipeline
  (`lunarastro_kundli_pipeline` / `build_charts_table` + `build_d9_charts` +
  `build_longitudes`); Vimshottari from the same Moon-longitude code.
- First event per person per domain; events joined to MD/AD by date.
- No exclusions beyond: missing birth JD, no in-band windows, event outside band.
- Dignity = `app.core.dignity.dignity_state`; benefics = {Jup, Ven, Mer, Moon}.
- Code is frozen at the commit introducing this document; rerun exactly
  `python -m app.medini.ml.dasha_timing_metrics --data-dir <new_run>`.

## Interpretation rules (pre-committed)

- **Confirm** (p₁ < 0.05, IRR > 1, death not lifting): the strength effect is
  real-but-small; report it as the single surviving classical timing signal, with
  the Layer B/C caveat that it confers no ranking or forecasting skill.
- **Fail** (p₁ ≥ 0.05): the whisper was noise; classical dasha timing is fully
  null on ~30k events across two corpora. Close the question.
- **Non-specific** (death lifts comparably): reclassify as artifact regardless of p.
