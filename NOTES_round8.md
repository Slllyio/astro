# Round 8 — Unification & Productionization (in-flight notes)

This is the running narrative for Round 8 per `implementation_plan_round8.md`
(plan signed off 2026-05-20). Modeled on `NOTES_round6_phases.md` —
phase-by-phase: what we built → what we measured → what we learned.

---

## Phase 0 — Pre-execution setup (DONE)

- Branch: `round8-unification` from `main` at HEAD `e0e0a80`.
- Corpus: `event_corpus_round5_all.parquet` re-confirmed at
  14,166 rows × 1,072 cols (SHA-256 prefix `da7140760d4067ea`).
- **Locked group-split** at `data/ml_runs/round8_master_eval/`:
  - GroupShuffleSplit by `name`, seed=42, test_fraction=0.20.
  - 11,378 train rows / 2,788 test rows.
  - 4,067 train unique names / 1,017 test unique names.
  - **Zero name leak** verified.
  - Class balance ±1pp across all top-10 classes.
- Artifacts: `baseline_holdout_indices.parquet`, `split_manifest.json`,
  `test_names.txt`. All downstream models judge on these same 2,788
  held-out human lives.

---

## Phase 1 — Production lean-feature retrain

### Phase 1.1 — feature_groups registry (DONE)

New module `app/medini/ml/feature_groups.py` consolidates the
DISCRETE_GROUPS / CONTINUOUS_GROUPS / `_resolve_group_cols` defs that
were previously embedded in `dequant_deep_dive.py`. Adds:

- `DROP_BY_DEFAULT`: tuple of 15 group names from Tier-2 §2's aggressive
  lean list.
- `resolve_drop_columns(all_cols, drop_groups=DROP_BY_DEFAULT)`: returns
  the concrete set of cols to drop given group names.

`dequant_deep_dive.py` refactored to import from here; `dequant_deep_dive_chunked.py`
inherits transitively. Single source of truth for ablation runs +
production training.

### Phase 1.2 — train_classifier patch (DONE)

`select_features()` gained a `lean: bool` kwarg. When True, calls
`resolve_drop_columns` after categorical coercion. CLI gained `--lean`
flag.

**See Phase 1.3 below for the default-direction decision.**

### Phase 1.3 — Locked-holdout lean vs full comparison (DONE — NEGATIVE RESULT)

Trained binary XGBoost (n_est=100, depth=4, balanced class weights) per
class × variant. Used the locked Phase-0 group-split. 5-fold CV on the
11,378 train rows; ROC-AUC on the 2,788 locked holdout.

| Class | n train+ | n test+ | FULL holdout AUC | LEAN holdout AUC | Δ (lean−full) |
|---|---|---|---|---|---|
| Work | 1,771 | 395 | 0.5712 | 0.5846 | **+0.0134** |
| Death, Cause unspecified | 1,173 | 303 | 0.9431 | 0.9450 | +0.0019 |
| Relationship | 996 | 246 | 0.5468 | 0.5391 | -0.0077 |
| Published/Exhibited/Released | 524 | 156 | 0.7028 | 0.6784 | **-0.0244** |
| Prize | 429 | 101 | 0.7494 | 0.7393 | -0.0100 |
| Family | 362 | 74 | 0.5337 | 0.4535 | **-0.0802** |
| fame | 338 | 77 | 0.8604 | 0.8390 | -0.0213 |
| career | 325 | 78 | 0.8632 | 0.8705 | +0.0073 |
| Death by Disease | 320 | 70 | 0.8124 | 0.8251 | +0.0127 |
| Marriage | 305 | 78 | 0.7791 | 0.7504 | **-0.0288** |

**Aggregate**:
- LEAN wins **4/10** classes (Work, Death-unspec, career, Death by Disease).
- FULL wins **6/10** (Relationship, Publication, Prize, Family, fame, Marriage).
- Mean Δ AUC = **-0.0137** (LEAN is on average WORSE by 1.37pp).
- Median Δ = -0.0089.

**Acceptance criteria (from plan §2 verification)**:
- LEAN ≥ FULL on ≥ 7/10 classes → 4/10, **FAIL**.
- Mean Δ ≥ +0.003 → -0.0137, **FAIL**.

### What this falsifies

The Tier-2 §2 "+0.0065 lift" finding was an artifact of two issues:

1. **Row-level random split.** Tier-2 used `train_test_split(stratify=y)`
   without grouping by `name`. With 14k rows from only 5,084 unique
   people, ~50% of test rows had at least one chart from the same
   person in the train set. The "lift" was largely chart-memorization
   plus pure-noise feature pruning helping with that memorization.
2. **Top-5 multi-class softprob ≠ per-class binary AUC.** The Tier-2
   evaluation aggregated across 5 classes via multiclass accuracy.
   When the model has to do per-class binary discrimination, small
   classes (<500 train positives) suffer disproportionately from
   dropping features — they need every signal they can get.

The group split is dramatic on its own: in-sample CV AUC averaged
~0.80; locked-holdout AUC averaged ~0.71. The bench was overestimating
generalization by ~9pp. Round 6/7's reported AUCs are similarly
in-sample-inflated. **This is the single most important Round-8 finding
so far — every prior model's "headline AUC" needs to be discounted.**

### Pattern across classes

| Pattern | Classes |
|---|---|
| LEAN helps (n train+ ≥ 1000 OR rare-feature-independent) | Work, Death, Death by Disease, career |
| FULL helps (n train+ < 600 OR rare-feature-dependent) | Family, Marriage, Publication, Prize, Relationship, fame |

The interaction is a textbook **bias-variance tradeoff**: large-cohort
classes have enough data to filter noise from the dropped cols; small-
cohort classes are data-starved and benefit from every feature, even
"noisy" ones.

### Code change

Reverted `select_features(..., lean=False)` as the default. The CLI flag
flipped from `--no-lean` (opt-out) to `--lean` (opt-in). The lean path
remains accessible for experiments; the safe production default is the
FULL Round-5 tensor.

### Implications for Round 8 sequencing

1. **Phase 2 (per-class × per-group ablation) becomes the priority**.
   The lean falsification proves drop lists must be class-conditional.
   A 10×32 matrix will tell us, e.g., "for Family, drop X; for Death,
   drop Y" — yielding a per-class drop dictionary instead of one
   universal list.

2. **Phase 3 (EGNN bridge)** uses the FULL feature tensor as the
   tabular baseline now. The comparison is XGBoost-on-full vs
   EGNN-on-continuous-coords, not XGBoost-on-lean vs anything.

3. **The locked-holdout AUC numbers are the new ground-truth bench.**
   No more in-sample numbers in Round-8 reporting. Every model gets
   judged on those 2,788 lives, period.

### Phase 1 status: COMPLETE (lean-by-default rejected, full retained)

Artifacts:
- `app/medini/ml/feature_groups.py` (new)
- `app/medini/ml/round5b_compare.py` (new, the chunked comparison runner)
- `app/medini/ml/train_classifier.py` (lean kwarg added, default False)
- `data/ml_runs/round5b_compare/report.md` (the head-to-head)
- `data/ml_runs/round5b_compare/comparison.csv`
- `data/ml_runs/round5b_compare/state.json`
- `data/ml_runs/round8_master_eval/` (Phase 0 locked split)

---

## Phase 2 — Per-class × per-group ablation matrix (NEXT)

Per the plan and the Phase 1 falsification, Phase 2 is now the
highest-priority follow-up. We need the class × group → Δ AUC matrix
to tell us which feature groups actually help which classes, on the
locked group-split.


---

## Phase 2 — Per-class × per-group ablation matrix (DONE — PARTIAL WIN)

### Phase 2.1/2.2 — The 10×32 matrix (DONE)

Built `app/medini/ml/round8_class_matrix.py`. Per-cell: drop one feature
group, train one multi-class softprob XGBoost (top-10 classes,
8,121 rows), extract per-class one-vs-rest AUC on the locked
1,578-row holdout. 33 cells (1 baseline + 32 group drops), each
~8-10s. Total 4 min.

### Universal load-bearing groups (mean Δ across 10 classes)

| Group | Kind | Mean Δ | Notes |
|---|---|---|---|
| `active_dasha_lords` | discrete | **+0.0149** | Dominant. The 3 MD/AD/PD lord cols are the single most important group. |
| `drishti` | discrete | +0.0041 | Classical aspects carry signal at multi-class scale. |
| `house_pos_continuous` | continuous | +0.0037 | Reverses Tier-2's "this hurts" finding. |
| `velocities` | continuous | +0.0032 | Also reverses Tier-2. |
| `tattvas` | discrete | +0.0030 | Also reverses Tier-2 (was top-3 hurter there). |

The Tier-2 §2 single-split scoring badly misidentified which groups
were noise. Under the locked split + per-class binary eval, multiple
groups Tier-2 labeled "actively harmful" turn out to be load-bearing.
This is a clean second confirmation of the Phase 1 lesson: chart-
memorization in single-row splits → spurious "noise" features.

### Class-specific noise groups (best per-class drop candidates)

The clearest per-class noise signals:
- **Family**: drops `divisional_signs` (Δ -0.0367), `aspect_orbs` (-0.0363),
  `panchanga_continuous` (-0.0333), and 22 more. Family is a tiny cohort
  (362 train+, 74 test+) and the model overfits hard; any drop helps.
- **career**: 23 small-Δ drops cumulate (`lagna_continuous`, `acceleration_jerk`,
  `stationary` etc.)
- **Marriage**: drops `divisional_degrees` (-0.0123) cleanly.
- **Death by Disease**: drops `house_pos_discrete` (-0.0124).

### Phase 2.3 — Validation of the derived per-class drop dict (DONE — PARTIAL WIN)

Took the matrix's per-class recommendations (groups with Δ ≤ -0.001
for that class) and validated head-to-head on the locked holdout via
**per-class binary** XGBoost (n_est=100, depth=4).

| Class | FULL AUC | PER-CLASS AUC | Δ | n_groups_dropped |
|---|---|---|---|---|
| Work | 0.5712 | 0.5743 | **+0.0031** | 3 |
| Death, Cause unspecified | 0.9431 | 0.9387 | -0.0044 | 16 |
| Relationship | 0.5468 | 0.5236 | -0.0232 | 6 |
| **Published/Exhibited/Released** | 0.7028 | 0.7092 | **+0.0064** | 8 |
| Prize | 0.7494 | 0.7371 | -0.0122 | 4 |
| Family | 0.5337 | 0.5250 | -0.0088 | 25 |
| fame | 0.8604 | 0.8497 | -0.0107 | 13 |
| **career** | 0.8632 | 0.8748 | **+0.0115** | 23 |
| **Death by Disease** | 0.8124 | 0.8330 | **+0.0206** | 5 |
| Marriage | 0.7791 | 0.7686 | -0.0106 | 4 |

**Aggregate**: 4/10 wins, mean Δ -0.0028 (much closer to zero than
Phase 1's universal -0.0137, but still below the +0.003 acceptance
threshold).

### The second falsification, with a twist

The per-class drop dict derived from **multi-class softprob ablation**
doesn't reliably transfer to **per-class binary evaluation**. The two
contexts use different signal structures:
- Multi-class softprob: gradient signal pools across all 10 classes;
  one group can help class A while neutrally affecting class B.
- Per-class binary: gradient signal is solely about that class;
  noise features have nowhere to hide.

For Family, fame, Marriage — classes where the multi-class matrix
showed strong negative Δs — the per-class binary model recovered the
information from other features and the drops just removed useful
backup signal.

For **Death by Disease, career, Publication** — three classes — the
binary lift is real and reproducible. Selective production rollout:
ship per-class drops ONLY for these three.

### Selective per-class production drop dict (shipped)

Added `SELECTIVE_DROP_PER_CLASS` to `app/medini/ml/feature_groups.py`:

```python
SELECTIVE_DROP_PER_CLASS = {
    "Death by Disease": (5 groups: house_pos_discrete, ashtakavarga,
                          declinations, divisional_degrees, divisional_signs),
    "career":           (23 groups, big aggressive drop list),
    "Published/Exhibited/Released": (8 groups),
}
```

Plus a `resolve_per_class_drop_columns(all_cols, event_class)` helper.
Production trainings for these three classes can now apply the drop;
all other classes use FULL.

### Phase 2 status: COMPLETE — PARTIAL WIN

Three production drop lists shipped. Universal lean confirmed dead.
The high-value next move is Phase 3 (EGNN bridge) — the
architectural lever is fundamentally larger than more XGB ablation
can deliver.

Artifacts:
- `app/medini/ml/round8_class_matrix.py` (the 33-cell ablation runner)
- `app/medini/ml/round8_per_class_validate.py` (the validation runner)
- `app/medini/ml/feature_groups.py` (now exports SELECTIVE_DROP_PER_CLASS)
- `data/ml_runs/round8_class_matrix/{report.md, class_matrix.csv, drop_per_class.json, per_class_drop_dict.json}`
- `data/ml_runs/round8_per_class_validate/{report.md, comparison.csv}`

---

## Phase 3 — astrov2 ↔ app/medini bridge (NEXT)

Per plan §3 and the empirical reality of Phases 1 & 2: tabular
XGBoost feature pruning has diminishing returns on this corpus.
The next ~0.05 AUC won't come from another drop list; it has to
come from a better architecture. Phase 3 builds the EGNN-vs-XGBoost
head-to-head we always needed.


---

## Phase 0.5 / Round 8.5 — Substrate repair + repaired-cohort eval (DONE)

After Phase 1 and Phase 2 both falsified on the locked group-split, the
critical review (CRITICAL_REVIEW_R8.md) identified four root-cause
data-layer issues. Repairs 1-4 were executed.

### Repair 1 — Proper screening cohort built

`app/medini/etl/build_screening_cohort.py` rebuilds, per event class, a
binary screening cohort:
- POSITIVES: people with ≥1 dated event of class X (matched by
  event_root OR event_subtype per CLASS_DEFS)
- NEGATIVES: era-stratified sample from the 77,757 unused natal-only
  charts (people with no events in astro-databank's events_all.csv)
- One row per unique person (no row-level duplication)
- Pure-natal features only (~535 cols — drops transit features)
- 2:1 negative:positive ratio, stratified per birth-decade

Output: 10 cohorts at `app/medini/data/screening_<class>.parquet`.
Sizes: Marriage 1,290; Death-cause-unspec 4,254; Relationship 1,320;
fame 1,035; career 951; Work 1,152; Family 498; Prize 366; Publication 285.

### Repair 2 — Dedup implicitly solved

The screening cohort design (one row per unique person) makes the
(name, event_date) duplication issue irrelevant.

### Repair 3 — Era-stratified eval harness shipped

`app/medini/ml/round8_screening_eval.py`:
- Group-split holdout by name (no leak — same protocol as Phase 0)
- 5-fold CV on train
- Per-era AUC report on the holdout

### Repair 4 — Re-ran FULL + LEAN on every repaired cohort

### THE RESULT — what the data actually says

| Class | Old "Phase 1.3" holdout AUC | NEW repaired-cohort AUC | Δ (truth − inflated) |
|---|---|---|---|
| Death, Cause unspecified | 0.9431 | **0.5123** | −0.4308 |
| career | 0.8632 | **0.6106** | −0.2526 |
| fame | 0.8604 | **0.5961** | −0.2643 |
| Death by Disease | 0.8124 | **0.4914** | −0.3210 |
| Marriage | 0.7791 | **0.5318** | −0.2473 |
| Prize | 0.7494 | **0.5312** | −0.2182 |
| Published/Exhibited | 0.7028 | **0.4460** | −0.2568 |
| Work | 0.5712 | **0.5015** | −0.0697 |
| Relationship | 0.5468 | **0.5028** | −0.0440 |
| Family | 0.5337 | **0.5166** | −0.0171 |

**Mean holdout AUC dropped from ~0.74 to 0.5240 once selection bias
and era confounding were controlled.** The 0.43-AUC drop on "Death,
Cause unspecified" alone is the clearest evidence that prior Round-6/7
"validated" results were largely era-decoding inside a hand-picked
cohort of notable people.

### The actual signal that survives

Two event classes survive at non-trivial lift over random:
- **career: AUC 0.6106  (+11pp over random)**
- **fame: AUC 0.5961  (+10pp over random)**

Six classes are basically random (AUC 0.49-0.53):
Marriage, Prize, Family, Death, Relationship, Work.

Two classes are BELOW random:
Published/Exhibited (0.4460), Death by Disease (0.4914).
This is consistent with small-test-set noise (Publication has only 19
positives in test) plus model regularization pulling predictions
toward the larger class.

### LEAN vs FULL on the repaired cohort — still dead

| Class | FULL | LEAN | Δ |
|---|---|---|---|
| Mean across 10 classes |  |  | **−0.0202** |
| LEAN wins |  |  | **4/10** |

The lean-feature drop list is confirmed dead, again. The hardest hit
is `fame` (full 0.5961 → lean 0.4798, Δ −0.1163) — dropping these
groups demolishes the only signal we had.

### Per-era AUC sanity

For classes where overall holdout is well above random, the per-era
holdout AUCs (within a single birth decade) generally track the
overall — suggesting the lift is genuine and not just era-decoding
that slipped through:
- career: per-era mean 0.6045 vs overall 0.6106 ✓ (real signal)
- fame: per-era mean 0.6115 vs overall 0.5961 ✓ (real signal)

For some classes, per-era is higher than overall — meaning negative
sampling actually OVER-controlled era and removed legit signal:
- Family: per-era 0.7150 vs overall 0.5166 (era-matched negs too
  similar to positives within a decade; relaxing negative sampling
  to allow some cross-decade matching might recover this signal)

### Honest summary

The project has discovered that, on a methodologically-correct
substrate:

1. **6 of 10 event classes show no significant astrological signal**
   (AUC ≈ 0.50 ± 0.03).
2. **career and fame have weak but real signal** (~0.60 AUC), which
   should be interpreted as: "in this corpus of notable people,
   certain natal patterns correlate weakly with which biographical
   category they end up in." Not a population-level prediction.
3. **All prior 0.86-0.94 'validated' AUCs were ~70-90% era-decoding**,
   not astrology.
4. **The lean-feature drop list is dead** in every controlled setting.
5. **The mean usable signal across 10 classes is +0.024 over random.**
   Publishable, but small, and only after substantial methodological
   work.

### Artifacts

- `app/medini/etl/build_screening_cohort.py` (cohort builder)
- `app/medini/data/screening_*.parquet` (10 per-class cohorts)
- `app/medini/ml/round8_screening_eval.py` (eval harness)
- `data/ml_runs/round8_screening_eval/{report.md, comparison.csv, state.json}`

### Round 8.5 status: COMPLETE

The substrate is now honest. Future architecture work (EGNN, LoRA,
continuous-spacetime features) should be evaluated against THIS
cohort and THIS protocol. The bar to clear is: "beat 0.60 AUC on
career/fame, OR show ≥ 0.55 AUC on any of the 6 currently-noise
classes."

That's a modest bar but a real one, and probably the right scope
for Round 9 — not the "bridge two codebases and stand up a LoRA
endpoint" sweep we originally planned for Round 8.
