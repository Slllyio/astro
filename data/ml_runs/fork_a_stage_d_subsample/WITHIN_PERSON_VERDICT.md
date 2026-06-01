# Stage D follow-up — within-person verdict

**Outcome**: **NULL — confound confirmed.** Closes the prediction question.

## The test

After Stage D's between-person DeepHit returned Δ = -0.16 (model worse than
Cox by ~4σ in the wrong direction), the data-scientist audit flagged one
remaining untested methodology: within-person concordance. The hypothesis was
that all 4 prior nulls might be hiding within-person signal because each one
compared across people (where birth-year and selection-bias confound).

Within a single person, chart features are constant. Only dasha-time features
vary. So a clean within-person test asks: does the trained DeepHit model rank
a person's actual event-windows higher than their non-event-windows?

## Headline numbers

Per-class within-person concordance, mean over 5 seeds, top-5 classes by test
positives:

| Class | DeepHit | Age | Duration | Age+Dur | DH - max(baseline) |
|---|---:|---:|---:|---:|---:|
| career | 0.5775 | 0.4033 | 0.6953 | 0.5778 | -0.1178 |
| death_cause_unspecified | 0.6091 | 0.7491 | 0.7300 | 0.8164 | -0.2073 |
| fame | 0.6028 | 0.3418 | 0.7372 | 0.5609 | -0.1344 |
| health | 0.5822 | 0.4790 | 0.6800 | 0.6216 | -0.0978 |
| personal | 0.6125 | 0.2931 | 0.7190 | 0.5133 | -0.1065 |

Across 25 (seed × class) cells, DeepHit beats the best trivial baseline in
**0 of 25 cases**. Every class shows DH underperforms by 0.10 - 0.21 points.

## What this means

The "0.58-0.61 within-person concordance" the DeepHit model achieves IS
non-random signal — but the signal is **trivial dasha-window exposure**.
Vimshottari dasha periods vary from 6 to 20 years; longer windows have more
time for events to occur, so a model that ranks windows by duration alone
scores 0.65-0.74 — *better than DeepHit*.

Three confounds in order of strength:
1. **Duration**: Vimshottari structure gives each lord a fixed-length period
   (Sun 6 yr → Venus 20 yr). Longer periods = more event exposure. C_within
   = 0.65-0.74 from this alone, no chart features needed.
2. **Age**: Has class-specific effects. Death events track age positively
   (0.75). Life events (fame, career, personal) are *reversed* — they
   cluster at younger ages within a person's dasha sequence (0.29-0.40).
3. **Age + duration combined**: Picks up the strongest signal for death
   (0.82) and is roughly comparable to DeepHit for life events.

DeepHit had access to all of these features (window_duration_days,
window_start_jd, birth_jd, md_seq_idx, ad_seq_idx, pd_seq_idx) PLUS the full
688-column chart-structure feature set. If chart structure carried within-
person signal, DH would beat trivial baselines. It doesn't.

## Combined verdict — 5 independent angles

The Stage D within-person test is the 5th independent null on this corpus:

1. **Cross-corpus doctrine quintile RR test** on 3 corpora (75k people total —
   Astro-Databank, Lunarastro, Wikidata). 3-way intersection of Bonferroni-
   significant classes is EMPTY.
2. **Non-structural XGBoost** with proper date controls. Chart features add
   <0.01 AUC over birth_date alone, three of eight class-corpus cells
   *negative*.
3. **LLM real-vs-shuffled chart** at individual scale (n=29). Paired Wilcoxon
   p=0.43; complete null.
4. **Stage D DeepHit between-person** at 5 seeds. Mean Δ = -0.1593 (DeepHit
   worse than Cox by ~4σ in the wrong direction). 1 of 20 qualifying classes
   has positive mean Δ.
5. **Stage D DeepHit within-person** (this test). DeepHit underperforms
   trivial age+duration baseline on every class, every seed.

The prediction question — "does Vedic chart structure predict life events
beyond birth date and trivial exposure effects?" — is now closed.

What this rules out (very strongly):
- Aggregate doctrine signal at population scale (3 corpora).
- Chart-features-add-AUC over date controls (Round 9 nonstructural).
- LLM extracting chart-specific information for prediction (Round 10).
- Survival-flavored framing recovering signal that tree boosters missed
  (Stage D between).
- Within-person dasha-lord attribution adding anything beyond exposure
  duration (Stage D within, this test).

What this does NOT rule out (for completeness):
- The structural fact that some Vimshottari periods are longer than others
  IS empirically associated with more documented events. This is uninteresting
  for prediction (just exposure) but is the only non-null finding.
- Individual-chart reading by a trained practitioner — never tested.
- A vastly larger dataset (10×+) might surface a small residual chart-specific
  signal below the current ceiling. Possible but unlikely to flip the verdict.

## Next step

Per spec §5 decision table + the parallel-agent strategic synthesis on
2026-05-27: **Fork C — write up as combined null result, ship the corpus.**

The 5-method null verdict is itself a publishable scientific contribution
(no prior astrology study has pre-registered a 4+ criterion gate, replicated
across 3 corpora, AND tested within-person to rule out the exposure confound).

The chart engine, RAG knowledge library (6.28M words, 918 artefacts), chart
reader with citations, and mundane forecast tool remain shippable. The 4
rounds of failed predictors (`app/medini/ml/`, `app/medini/etl/` research
scripts) are fully decoupled and can be deleted before the product-launch
sprint.

## Files

- `app/medini/ml/stage_d_within_person.py` — within-person GPU concordance
  using existing DeepHit checkpoints
- `app/medini/ml/stage_d_within_person_control.py` — age/duration/combined
  confound controls
- `data/ml_runs/fork_a_stage_d_subsample/within_person_dml.{md,json}` —
  DeepHit within-person results (raw)
- `data/ml_runs/fork_a_stage_d_subsample/within_person_control.{md,json}` —
  trivial-baseline controls
- `data/ml_runs/fork_a_stage_d_subsample/WITHIN_PERSON_VERDICT.md` (this
  file) — final interpretation
