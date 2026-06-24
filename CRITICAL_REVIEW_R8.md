# Critical Pipeline Review — Why Results Are Not Good

**Date**: 2026-05-20
**Trigger**: Phases 1 and 2 of the Round 8 unification plan both failed
their acceptance criteria. The lean-feature drop list — which Tier-2 §2
"validated" at +0.0065 — landed at −0.0137 mean Δ AUC under a
methodologically-correct holdout. The per-class drop dict from the
10×32 ablation matrix landed at −0.0028.

This is the third consecutive falsification of a "headline win" once
the evaluation protocol is hardened. The pattern is too consistent to
ignore. Before we burn more cycles on Phase 3 (EGNN bridge), Phase 4
(LoRA), and Phase 5 (continuous features), we need to ask whether the
foundation itself is sound.

---

## 1. The pattern of degradation

Every Round-6 / Round-7 / Tier-2 "win" that was re-evaluated under a
stricter protocol either shrank dramatically or reversed direction:

| Headline result | Original | Re-evaluated honestly | Δ |
|---|---|---|---|
| Phase 3 contrastive embeddings: K=5 NN Jaccard | 0.888 in-sample | 0.738 held-out | −0.150 |
| Tier-2 §2 lean-feature lift: top-5 multiclass | +0.0065 | (universal, group-split) **−0.0137** | −0.020 |
| Tier-2 §1 "8 groups actively hurt the model" | 8 groups | (Phase 2 matrix) 5 of 8 are actually load-bearing under group-split per-class | reversed |
| Phase 1 holdout AUC vs CV AUC (e.g. Work) | CV 0.77 | Holdout 0.58 | −0.19 |
| Phase 1 holdout AUC vs CV AUC (e.g. Relationship) | CV 0.70 | Holdout 0.55 | −0.15 |

The methodological fixes have been correct each time. The data are
saying: **most of what we thought we'd discovered was chart-
memorization, era-confounding, or split leakage.**

---

## 2. Root causes — diagnosed with evidence

### 2.1 Massive selection bias in the cohort

The "screening universe" is 91,549 charts in `ml_astro_15k.parquet`.
The "event universe" is 14,166 rows in
`event_corpus_round5_all.parquet`, drawn from only **5,084 unique
people** — every one of them notable enough to be in Astro-Databank.

**85,113 charts (94% of the natal universe) are NEVER used as
negative-class controls.** Every model we've trained has been
multi-class softprob across event types within the event-positive
sub-population. We have never asked the only scientifically
meaningful question: *given a random chart, can the model flag whether
this person is likely to have a notable Marriage event?*

The "Sun-in-10th = career VALIDATED" rule from Phase 7 doesn't say
"having Sun in the 10th increases your real-world probability of a
career event." It says "among the 5,084 notable people in our biased
corpus, those with Sun-in-10th are more likely to have biographies
that include the substring 'career.'" That's not a prediction about
humans; it's a prediction about biographers.

### 2.2 Era-confounding is catastrophic

Birth-decade medians by event class:

| Event class | Median birth decade |
|---|---|
| Death, Cause unspecified | **1900** |
| Death by Disease | 1920 |
| Marriage | 1930 |
| Relationship | 1930 |
| Work | 1940 |
| Family | 1945 |
| career | 1960 |
| fame | **1960** |

A **60-year birth-decade gap** between "Death" classes (median 1900) and
"fame" / "career" (median 1960). These are obviously confounded — most
of the dead people in the corpus are dead BECAUSE THEY WERE BORN
EARLIER. Any natal feature that proxies era (declinations, ayanamsa-
adjusted longitudes, even subtle inclination drifts due to nutation)
will trivially separate the classes via ERA, not via real astrological
signal.

Round 6 Phase 1 caught this at the macro level ("Seasonality
dominates rules") and stripped the most obvious solar features. The
deeper era-confounding through decade-scale precession effects on
non-solar features was never controlled. **The 0.94 holdout AUC on
"Death, Cause unspecified" is almost certainly era-confounded
trivially.**

### 2.3 Non-independent rows inflate sample size

7,683 of 14,166 rows (54%) are duplicates of (name, event_date)
pairs. 1,664 distinct (name, event_date) pairs carry multiple
event_root labels (e.g. "Aadland, Beverly" on 1960-04-09: "Crime/
Arrest" AND "Crime/Sex Victimization/Rape" — one event, two labels).
Average duplication factor for these pairs is 4.6.

XGBoost treats these as independent samples. The model sees roughly
the same chart 4.6 times with different labels, learns the
person-specific feature vector, then "memorizes" that the chart maps
to all of those labels. Once we group-split by name, the memorization
fails. The Phase 1 collapse (CV 0.77 → holdout 0.58 on Work) is
exactly this.

### 2.4 Event-positive-only training breaks the meaning of AUC

Every row in the training corpus has `is_event=1`. The "binary
classifier" for "Marriage" actually means "given that this person had
ANY notable biographical event, is THAT event a Marriage?" — not
"will this person have a marriage." When we report a 0.78 AUC on
Marriage, that's about distinguishing marriages from
non-marriage-event-types WITHIN the corpus — it tells us nothing
about whether the chart predicts marriages in the population.

### 2.5 The astrov2 fallback isn't a fallback

Round 8 Phase 3 was planned to "bridge" the astrov2 EGNN onto the
14k cohort. But astrov2's headline number is **55.36% accuracy on
marriage** (PROJECT_STATUS.md v11.0) — barely above the 50% random
baseline for its balanced jittered-control setup. We were planning
to "compare" XGBoost (which we now know is mostly memorizing) against
an EGNN that's effectively random.

If we run that comparison on the same broken cohort, we'd get back
two equally broken numbers and call it a "head-to-head." This is not
informative.

---

## 3. What does this mean for the planned Phases 3-6?

### Phase 3 — astrov2 ↔ app/medini bridge: **don't ship**

As scoped, it would just run another noisy comparison on the same
biased cohort. The architectural lever (continuous coords + EGNN
message-passing) is real, but it can't fix selection bias / era
leakage / duplicates. Defer until §4 below is addressed.

### Phase 4 — LoRA fine-tune: **don't ship**

A 1.5B-parameter LLM on (chart_text → event_text) tuples is just a
fancier function approximator on the same broken substrate. It will
learn the same population biases in text form, and may make them
worse by "smoothing" them under language priors. We'd spend ~$5 and a
day to verify what we already know: the LLM produces plausible text
about charts in our biased cohort.

### Phase 5 — Continuous spacetime feature engineering: **defer**

Gaussian aspect fields and harmonic Vargas are interesting *features*,
but they encode the same underlying era-confounding (planetary
longitudes via sin/cos of θ still drift over decades) and won't help
generalization. They're worth implementing AFTER we've controlled
era and built a proper negative class. Not before.

### Phase 6 — Unified eval harness: **proceed**

The one thing worth building from the old plan. Without the harness,
we can't cleanly measure whether the Phase-7 fixes (below) actually
worked. Useful regardless.

---

## 4. What needs to happen for results to be "good"

Three foundational repairs, in order. Each gates the next.

### Repair 1 — Build the proper screening cohort (CRITICAL)

Construct a training tensor that combines:
- The 14,166 event-positive rows (is_event=1) we have today.
- A **negative-control pool** sampled from the 85,113 unused natal
  charts in `ml_astro_15k.parquet`, with `is_event=0` set explicitly.
- Stratify the negative sample by birth decade to match the
  positive-class era distribution per class — this neutralizes the
  era-confounding shown above.

For each event class, build a **binary** target: "did this chart's
person have a biographical event of type X (yes/no), drawn from the
era-matched joint cohort?"

This converts "predict among notable people which event-type they got"
into "screen any chart for likelihood of event-type X" — the only
question with predictive meaning.

Effort: 2-3 days code (`app/medini/etl/build_screening_cohort.py`),
big effort with no immediate model code change.

### Repair 2 — Deduplicate by (name, event_date)

Collapse the 1,664 duplicate-date rows into single records carrying a
list of co-occurring labels. The XGBoost gets one row per (chart, date)
with a multi-label outcome vector. Removes the 54%-non-independence
problem.

Effort: half a day.

### Repair 3 — Era-stratified evaluation, not just splits

Re-run every Round-6/7/8 model with:
- Group split by name (done — Phase 0 ✓)
- AND stratify CV folds by birth decade
- AND report per-era AUC (does the model work in 1900-1950 charts only,
  or also in post-1980 charts?)

Most Round-7 BPHS rule validations probably collapse under era
stratification. That's information; we should know which ones survive.

Effort: 2-3 days to retrofit the eval harness across all phases.

### Repair 4 — Re-run the locked-holdout benchmarks on the repaired cohort

Once Repairs 1-3 land, re-run Phase 1.3 (lean vs full) on the
era-stratified, deduped, screening cohort. THEN run Phase 3 (EGNN)
honestly. THEN Phase 4 (LoRA).

If the lean lift comes back at +0.005 with all three repairs in place,
it's a real finding. If it doesn't, lean is dead and we know it.

---

## 5. The harder question: is there any signal here?

Honest answer: probably yes, but a much smaller fraction than the
Round-6/7 headline numbers suggested.

The classes with the largest holdout AUC on Phase 1 (Death, Cause
unspec at 0.94; fame at 0.86; career at 0.86) are exactly the classes
with the strongest era confounding. Era controls will probably bring
those down to 0.55-0.65.

The classes where the holdout AUC is already near random (Work 0.57,
Relationship 0.55, Family 0.53) — these are the ACTUAL ASTROLOGICAL
SIGNALS, if any. They're weak because era doesn't help discriminate
them. The repaired cohort will tell us whether they have any non-zero
lift over base rate.

A realistic Round-8 target after the repairs: holdout AUC of 0.55-0.62
on multiple event classes, with confidence intervals that exclude 0.50.
That would be a publishable, defensible result. The current Round-7
numbers of 0.86-0.94 are not real.

---

## 6. Recommended path forward

1. **Pause Phases 3, 4, 5** — they don't fix the foundation.
2. **Execute Repairs 1-3** (~1-2 weeks of data-layer work). Yes, this
   feels like going backwards. It's not.
3. **Re-run Phase 1.3** (lean vs full) on the repaired cohort as the
   first validation that the new substrate is honest.
4. **Re-run the Round-7 BPHS audit** with era stratification. Most
   findings will collapse; the survivors are real.
5. **THEN** decide whether EGNN / LoRA / continuous features are worth
   building. With a clean substrate, those comparisons mean something.

---

## 7. Summary

Phases 1 and 2 of Round 8 weren't failures of the plan. They were
the plan working — we built a methodologically-honest holdout and it
exposed how much of our prior work was inflated. The Round-8 plan
itself was the right plan for *fixing the architecture*; but the
problem isn't architectural. It's foundational. **Selection bias +
era confounding + non-independent rows + event-positive-only training
= near-noise generalization, no matter what model we put on top.**

The next ~3 weeks of work shouldn't be EGNN / LoRA / continuous
features. It should be the four repairs in §4.

We should be honest about this with ourselves and stop the
forward-march to chase better numbers on a broken substrate.
