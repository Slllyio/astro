# Round 8 Master Plan — Unification & Productionization

**Status**: PROPOSAL — awaiting user review before execution.
**Date**: 2026-05-20
**Author**: Claude (analysis based on full re-read of NOTES_round6_phases.md,
implementation_plan.md, dequantization_mindmap.md, review_round6_phases.md,
astrov2/PROJECT_STATUS.md, and the latest code in app/medini/ml/ + astrov2/src/).

---

## 0. Executive thesis

Round 7 closed with three substantive deliverables: a methodologically-defensible
audit of 154 classical Vedic rules (11 validated, 12 reversed); a continuous-DML
sweep that surfaced 9 new causal findings binary DML missed; and an empirical
deep-dive showing 313 of 1,064 feature columns are net-negative (Tier-2 §1/§2).
All three converge on the same architectural truth: **the model is held back
more by feature redundancy and tabular flatness than by sample size.**

Round 6's negative results (Phase 5 GNN, Phase 8 MoE) failed because they were
under-specified. Meanwhile, in parallel, the `astrov2/` codebase has been
quietly building exactly the right thing — a torch_geometric EGNN over
continuous 3D planetary coordinates, with bipartite natal-transit and
tripartite synastry graphs — but on a 558-event subset, miles away from the
91,549-row `ml_astro_15k.parquet` that powers app/medini/ml.

**Round 8 is the unification round.** The point is not to invent new
architectures; we have all the pieces. The point is to bridge the two
codebases, ship the lean-feature lift to production, validate the LoRA fine-
tune end-to-end, and start replacing the redundant feature groups with the
continuous-space-time encodings dequantization_mindmap.md prescribes.

If we run Round 8 well, by the end we should have:
1. **A production Round-5b model** with the 15-group drop list applied,
   measured lift on full 27-class 5-fold CV.
2. **astrov2 EGNN trained on the 91k corpus**, not the 558-event subset.
   Bipartite natal-transit Module 8.7 architecture, full event taxonomy.
3. **A trained LoRA adapter** on the 5,664-record QA dataset, deployed as
   the `/interpret/chart` endpoint backend (replacing or supplementing the
   Claude API path in `chart_chatbot.py`).
4. **Continuous-spacetime feature ablation** — replace the worst-offending
   discrete groups with the Gaussian aspect fields / harmonic Varga
   encodings / fractal Dasha vectors from the mindmap, measure the lift.
5. **A unified evaluation harness** so future rounds can compare tabular
   XGBoost, astrov2 EGNN, and LoRA-LLM on the same held-out cohort.

Everything else — corpus scaling past 91k, synastry couple data, the 4D
ST-GNN with 180-day windows — stays deferred per Round 7's reasoning
(blocked on external resources or GPU time we don't yet have).

---

## 1. Current state inventory

### 1.1 Codebases

| Codebase | Purpose | Scale | Architecture |
|---|---|---|---|
| `app/medini/ml/` | Tabular ML on Round-5 feature tensor | 14,166 events × 1,072 cols × 27 classes | XGBoost, DML, contrastive embeddings, Cox PH, RuleFit, MoE |
| `app/medini/etl/` | Data pipeline + event extraction | 91,549 natal charts; 47,466 events | LLM + regex event extractors, ephemeris features |
| `astrov2/src/` | PyTorch EGNN spatiotemporal | 558 marriage events (subset) | torch_geometric EGNN, bipartite/tripartite graphs |
| `portal/` | Flask probability-report web UI | n/a | astro-web-portal probability engine, mostly stable |

### 1.2 Trained model artifacts

- `app/medini/ml/` outputs in `data/ml_runs/`: 28 experiment directories, all
  Round-5 / Round-6 / Round-7 artifacts.
- `astrov2/`: 3 PyTorch checkpoints (bipartite, discovery, synastry).
- No production-served model. `portal/` uses classical rule-based scoring,
  not the ML pipeline.

### 1.3 Where the corpus stands

- **91,549** chart records with full Round-5 physics features in
  `ml_astro_15k.parquet`. (Naming misleading; the "15k" was the original
  scope before scraper-expansion.)
- **47,466** event records across **15,610** unique profiles
  (`events_all.csv`).
- **14,166** rows in `event_corpus_round5_all.parquet` after natal-event
  joining and de-duplication. This is the cohort every Round-5/6 model
  trained on.
- The 77,383-chart gap between natal corpus and event corpus (14k) is the
  unlabelled mass the regex+LLM extractors were built to mine. Walkthrough.md
  reports this expanded the marriage cohort to 12,457 — but that hasn't been
  pushed into `event_corpus_round5_all.parquet` yet.

### 1.4 The major deferred Round-7 items

| Item | Why deferred | Round-8 readiness |
|---|---|---|
| §2.1 4D ST-GNN | GPU + 80GB intermediate storage | astrov2 covers this in a leaner form |
| §2.2 LoRA training | GPU | Cloud-deployable; ~$3-10 on Modal |
| §3.1 spatial dequant | Done as a probe | Production drop-list ready (Tier-2) |
| §3.2 fractal Dasha vector | Design drafted only | Implementable, 2-hour effort |
| §4.1 corpus scaling | External (rate limits) | Walkthrough claims done to 91k — not verified |
| §4.2 synastry data | External (no labelled couples) | Deferred again; astrov2 has 17 pairs |

---

## 2. Phase-by-phase plan

Each phase has: **Goal → 2-3 alternatives with tradeoffs → Recommendation →
File-level work breakdown → Verification → Effort estimate → Risk flags**.

---

### Phase 1 — Production lean-feature retrain (the quick win)

**Goal**: Apply the 15-group drop list from Tier-2 §2 to the full 27-class
Round-5 training. Measure the actual lift on 5-fold CV. Ship a Round-5b
parquet/model that subsequent phases build on.

**Why this first**: Tier-2 §2 measured +0.0065 on a top-5 single-split eval.
Production-grade 5-fold × 27-class is a different beast. We need to verify
the lift survives that step up before committing to the lean tensor as the
new default. If it survives, every downstream phase trains faster and
better; if it doesn't, we learned the deep dive overfit to the top-5 setup.

#### Alternative 1A — Hard drop in `train_classifier.py`'s feature selection
Modify `select_features()` (currently `app/medini/ml/train_classifier.py:81`)
to drop columns whose prefixes match the 15 group prefixes. Retrain Round-5
end-to-end. Pro: minimal code change, immediate; Con: hard-codes the drop
list into the training entry point; future feature additions can collide
with the drop prefixes.

#### Alternative 1B — Configurable feature-group registry [RECOMMENDED]
Introduce `app/medini/ml/feature_groups.py` that owns the
`DISCRETE_GROUPS` / `CONTINUOUS_GROUPS` / `_resolve_group_cols` definitions
currently embedded in `dequant_deep_dive.py`. Add `DROP_BY_DEFAULT: set[str]`.
Update both `train_classifier.py` and the deep-dive scripts to import from
this shared module. Pro: single source of truth; future ablations can re-use;
makes the "lean by default" decision explicit and auditable. Con: ~30 mins
of refactor before any retrain.

#### Alternative 1C — Two-model A/B
Keep the full feature tensor; train BOTH the full Round-5 model AND a lean
variant; ship both as `round5b_full.json` and `round5b_lean.json`. Let
downstream consumers pick. Pro: zero-risk; Con: doubles training compute,
ambiguous downstream story.

**Recommendation: 1B**. The deep dive already factored out the group registry;
elevating it to a first-class module pays for itself the second time we
ablate (Phase 2 will).

**File-level work**:
1. `[NEW] app/medini/ml/feature_groups.py` — move `DISCRETE_GROUPS`,
   `CONTINUOUS_GROUPS`, `_resolve_group_cols` here; add `DROP_BY_DEFAULT`
   tuple constant with the 15 Tier-2 §2 groups.
2. `[MODIFY] app/medini/ml/dequant_deep_dive.py` — import from feature_groups.
3. `[MODIFY] app/medini/ml/dequant_deep_dive_chunked.py` — same.
4. `[MODIFY] app/medini/ml/train_classifier.py:select_features` — after the
   existing categorical-coercion loop, drop columns matching DROP_BY_DEFAULT
   prefixes. Add a `--no-lean` CLI flag to override (preserves the old
   behaviour for ablation comparisons).
5. Run: `python -m app.medini.ml.train_classifier --target-token "Marriage"
   --n-splits 5` for marriage; then for each top-10 event class.
6. Output: `data/ml_runs/round5b_lean_<target>_*/` per class.

**Verification**:
- Lean ROC-AUC ≥ baseline ROC-AUC on at least 7 of 10 classes, OR
- Aggregate multi-class 5-fold CV accuracy improves by ≥ +0.003 absolute.
- If neither, the deep dive overfit; document as Phase-1 negative result
  and revert to full tensor for Phase 2-5.

**Effort**: 1 day code + 6-8 hours total compute (10 classes × 30-50 min
each, runnable in background per class).

**Risks**:
- The +0.0065 might shrink at 27-class scale because XGBoost has more
  classes to fit per round → marginal noise gets averaged differently.
- A "hurting" group at 5 classes may not hurt at 27 classes (some features
  only matter for the rarer classes).
- Mitigation: ship the registry approach (1B) regardless; even a partial-
  validation outcome leaves the codebase cleaner for Phase 2.

---

### Phase 2 — Per-class × per-group ablation matrix

**Goal**: For each of the top-10 event classes, run the full per-group
ablation. Build a `class × group → Δ` matrix. Phase 1's lean drop is uniform
across classes; this phase tells us if a different drop list per class
would yield more lift.

**Why second**: Phase 1 is the cheap aggregate win. Phase 2 is the
diagnostic that tells us whether per-class feature engineering can push
us further. If the matrix shows strong class-specific patterns
(e.g., "drishti hurts work but helps death"), Phase 3+ can do class-
conditional feature selection. If the matrix is flat (uniform Δ across
classes), we know the lean drop list is optimal and we focus on the GNN
side.

#### Alternative 2A — Same chunked-runner pattern, 10x scale
Iterate the Tier-2 §1 chunked runner across 10 classes × 32 groups = 320
evals × ~20s = ~110 minutes total compute. Sandbox-friendly (≤45s per
process). Pro: re-uses existing code; Con: 110 minutes of sequential
single-cell evals on small data.

#### Alternative 2B — Single-shot multi-class with class-conditional XGB [RECOMMENDED]
Train ONE multi-class XGBoost per ablation cell (instead of per class).
For each of the 32 ablations, fit a 27-class softprob model and extract the
per-class one-vs-rest AUC. 32 evals × ~30s = ~16 minutes. Pro: 7× faster;
Con: per-class AUCs come from the multi-class model's calibration, which
is slightly different from per-class binary classifiers.

#### Alternative 2C — Stratified ablation with bootstrap CI
For each (class, group) cell, do K=5 bootstrap resamples to get a Δ
confidence interval. Pro: tells us which Δs are statistically real vs noise;
Con: 5× compute; could be done lazily later on the cells flagged by 2B.

**Recommendation: 2B as primary, 2C lazily on borderline cells**. The
chunked runner is already proven; this scales it cleanly.

**File-level work**:
1. `[NEW] app/medini/ml/dequant_class_matrix.py` — based on
   `dequant_deep_dive_chunked.py`. Outer loop: ablation groups. Inner: one
   27-class XGBoost. Persist per-class AUC vector per ablation cell.
2. Re-use `feature_groups.py` from Phase 1.
3. Output: `data/ml_runs/dequant_class_matrix/`:
   - `matrix.csv` — rows=groups, cols=class names, values=Δ AUC.
   - `report.md` — heatmap-shaped markdown with sortable columns.
   - `state.json` — resume state.

**Verification**:
- Look for cells where Δ ≷ ±0.01. Those are class-specific signals.
- Compare row-mean to Tier-2 §1's headline Δ — should reproduce within ±0.001.

**Effort**: 1 day code + ~30 min compute.

**Risks**:
- Multi-class probabilistic outputs are calibrated jointly; per-class AUC
  could behave differently than the per-class binary classifier ablations
  from Tier-2 §1. Document the discrepancy if present.

---

### Phase 3 — astrov2 ↔ app/medini bridge (the codebase unification)

**Goal**: Train the astrov2 EGNN on the same 14k-event corpus that
app/medini/ml uses. Build the data adapter, run the bipartite (Module 8.7)
architecture, evaluate against the Round-5 XGBoost baseline.

**Why third**: this is the single biggest open architectural question.
astrov2 has all the de-quantization machinery (continuous coords, EGNN,
fractal time) but trained on 558 events with random control sampling. Until
we train it on the same cohort as our XGBoost baseline, we don't actually
know if continuous-space-time outperforms the discrete-binned tabular
approach on a fair head-to-head.

#### Alternative 3A — Port astrov2 model into app/medini/ml/, retrain
Copy `astrov2/src/predictive_architecture.py` (EGNNConv + CelestialEGNN) into
`app/medini/ml/spatiotemporal_egnn.py`. Build a `CelestialDataset` adapter
that reads `event_corpus_round5_all.parquet`, reconstructs (X,Y,Z, t) per
event using `app/core/ephemeris.py` (or astrov2/src/ephemeris_engine.py).
Train. Pro: clean integration into the main ML stack; Con: two ephemeris
engines to maintain unless we deprecate one.

#### Alternative 3B — Keep codebases separate, build data adapter only [RECOMMENDED]
Add `astrov2/src/cohort_loader.py` that reads the parquet from
`../app/medini/data/event_corpus_round5_all.parquet`, converts each row to a
(natal_state, transit_state, label) tuple via astrov2's existing
`InteractionTensorBuilder`. Train using `astrov2/src/train.py` with the
new dataset. Pro: respects the two-codebase separation; minimal cross-deps;
Con: requires us to commit to keeping astrov2/ as a sister project, not
merge it.

#### Alternative 3C — Full merge: deprecate one ephemeris engine
Delete `astrov2/src/ephemeris_engine.py`; route everything through
`app/core/ephemeris.py`. Move `astrov2/src/*` into `app/medini/ml/gnn/`.
Pro: one codebase forever; Con: 2-3 day refactor; risks breaking astrov2's
existing 3 trained model checkpoints.

**Recommendation: 3B for Round 8, 3C as Round-9 cleanup**. The bridge
data-adapter is the minimal step to answer the scientific question
(EGNN vs XGBoost on the same cohort). Codebase consolidation is a separate,
deferrable problem.

**File-level work**:
1. `[NEW] astrov2/src/cohort_loader.py` — reads
   `../app/medini/data/event_corpus_round5_all.parquet`; for each row,
   computes natal coords via `EphemerisEngine`; supports `--task` for
   {marriage, death, work, ...} → binary outcome subsetting.
2. `[NEW] astrov2/src/train_cohort.py` — wraps `train.py` with
   the cohort_loader; uses `CelestialSpatiotemporalNet` (bipartite, Module
   8.7) as the model; emits training curves + held-out AUC.
3. `[NEW] astrov2/eval_vs_xgb.py` — runs the same 80/20 hold-out used by
   Tier-2; prints head-to-head AUC for XGBoost and EGNN on the held-out
   set. Persist comparison to
   `data/ml_runs/round8_phase3_xgb_vs_egnn/comparison.csv`.

**Verification**:
- EGNN converges (loss curve descending; not NaN).
- EGNN AUC on held-out within ±0.05 of XGBoost AUC for at least 5 of 10
  classes. (We're not expecting it to dominate yet; we're checking it
  performs at all on the larger cohort.)
- Compare against the `astrov2` 55.36% marriage accuracy baseline; new
  scale should at least match or beat it.

**Effort**: 2-3 days. Coder time dominated by writing the adapter +
ensuring ephemeris consistency.

**Risks**:
- Two ephemeris engines might give slightly different coordinates for the
  same chart due to different ayanamsa / topocentric handling. Add a
  unit-test that cross-checks 100 random charts and asserts |Δ longitude|
  < 0.1°.
- EGNN training time scales with sample count; 14k events × 4 GNN layers
  on CPU could take 6-12 hours per epoch. Budget for GPU rental (~$5).
- The bipartite architecture's 558-event signal may not survive class
  imbalance and noise at 14k scale. If AUC degrades vs the small-cohort
  result, that itself is a finding (current scale exceeds the architecture's
  effective sample efficiency).

---

### Phase 4 — LoRA fine-tune end-to-end (close the §2.2 deferral)

**Goal**: Run the LoRA training script `train_llm.py` on the 5,664-record
QA dataset, end-to-end, on a cloud GPU. Produce a merged Qwen2.5-1.5B
adapter. Stand up the `/interpret/chart` endpoint that routes to it.
Compare its output quality to the Claude API path in `chart_chatbot.py`.

**Why fourth**: it's GPU-bound but standalone; can run in parallel with
Phase 3. The infrastructure (script, deployment guide, dataset, eval
harness) is already 80% built. We're spending money (~$5) and time
(~2-3 hours of cloud compute), not engineering effort.

#### Alternative 4A — Modal A10G, 3 epochs Qwen2.5-1.5B
Per `LORA_DEPLOYMENT.md`'s Option B. Pro: cheap, fast, reproducible; Con:
~$3.30 spend; need a Modal account.

#### Alternative 4B — Colab Free T4, 2 epochs [RECOMMENDED IF NO BILLING]
Per `LORA_DEPLOYMENT.md`'s Option A. Pro: $0; Con: 6-hour session limit,
needs manual notebook runs; less reproducible.

#### Alternative 4C — Local Apple Silicon (M-series) via MLX
If user has an M-series Mac: convert the training loop to MLX-LM, run on
local GPU. Pro: $0, no session limits; Con: requires writing an MLX
adapter to the existing peft/trl pipeline.

#### Alternative 4D — Skip LoRA, double down on Claude API chatbot
The user has already shipped `chart_chatbot.py` which routes to Claude
Opus 4.7 with prompt caching. If LoRA's quality doesn't measurably beat
Claude-API output on the eval set, the LoRA path is research, not
production. Pro: nothing to do; Con: never closes §2.2.

**Recommendation: 4A if billing available, 4B otherwise**. Either way,
**run the eval (4D's premise needs an empirical test)**. The eval can use
the existing 5,664-record dataset's 10% hold-out, scoring on event_root
match rate; if Qwen-LoRA matches or beats Claude-API on this synthetic
test, the deployment story changes.

**File-level work**:
1. `[NEW] app/medini/ml/eval_llm_chart_predictions.py` — wrapper around the
   dataset; for the held-out 10%, computes (model_pred_event_root,
   gold_event_root) accuracy. Supports both Claude API and local LoRA
   backends behind a `--backend` flag.
2. `[Cloud run]` Modal or Colab — execute `train_llm.py` per the deployment
   guide. Save the merged adapter as `data/ml_models/astro_qwen2.5_lora/`.
3. `[NEW] app/llm/lora_interpreter.py` — wraps the merged adapter as a
   FastAPI dependency. Routes from `/interpret/chart`.
4. `[MODIFY] app/main.py` — register the new `/interpret/chart` route, or
   if already registered, swap backend per env var
   `INTERPRETER_BACKEND={claude_api,lora,both}`.

**Verification**:
- Eval script runs on 566 held-out records (10% × 5664). Reports:
  - LoRA: event_root accuracy
  - Claude API: event_root accuracy
  - Δ between them
- Manual inspection of 20 randomly-sampled chart readings from each.

**Effort**: 2 days (script ready; cloud run + eval + deploy).

**Risks**:
- LoRA may underperform Claude API on a synthetic gold dataset that was
  itself generated from the same chart-verbalizer Claude was prompted with.
  Document and pivot to 4D if so.
- Modal billing / Colab session expiration during training; mitigate with
  checkpoint-resume in the train_llm script (already exists).

---

### Phase 5 — Continuous-spacetime feature engineering (§3.2 + §3.3 deferred items)

**Goal**: Implement three of the dequantization_mindmap.md's most testable
continuous encodings as additional feature groups in `feature_engineering.py`,
add them to a new Round-5c variant, ablate to measure marginal lift.

The three:
1. **Gaussian aspect fields** (mindmap §1.3): replace binary
   drishti_<a>_<b> with continuous I(Δθ) = exp(-(Δθ - μ)² / 2σ²). One
   feature per (planet pair, classical aspect type). ~63 new columns.
2. **Harmonic Varga encoding** (mindmap §1.2.2): for each planet, add
   sin(kθ), cos(kθ) for k ∈ {2, 3, 9, 10, 12} (the classical varga
   multipliers). 90 new columns. Replaces dXX_sign / dXX_deg discretes.
3. **Fractal Dasha vector** (mindmap §2.1): replace `active_md_lord` /
   `active_ad_lord` / `active_pd_lord` with a 9-dim continuous vector,
   weights summing to 1, per the formula in §3.2 of implementation_plan.md.

**Why fifth**: Tier-2 §1 identified divisional_signs, divisional_degrees,
and drishti as net-zero or net-negative. The mindmap claims continuous
encodings beat the discrete bins. This phase tests that claim head-to-head
within the XGBoost framework before we commit to it in the EGNN side
(which already uses continuous coords natively).

#### Alternative 5A — Implement all three simultaneously
Ship as one Round-5c variant; ablate jointly. Pro: fast; Con: can't tell
which individual encoding drove any lift.

#### Alternative 5B — Implement individually, ablate sequentially [RECOMMENDED]
Three separate parquet variants (Round-5c-gauss, Round-5c-harmonic,
Round-5c-fractal). Each gets a full 5-fold CV eval vs Round-5b lean
baseline. Pro: identifies which encoding matters; Con: 3× compute.

#### Alternative 5C — Defer Fractal Dasha, ship Gaussian + Harmonic only
Fractal Dasha is the most speculative (the §3.1 result suggests discrete
dasha is already good). Ship the two encodings most-likely to lift. Pro:
2/3 the effort; Con: leaves a deferred item open.

**Recommendation: 5B**. Each encoding takes ~half a day to implement; the
sequential ablation gives us the clean per-encoding lift data we'll need
to decide which to keep for Round-9.

**File-level work**:
1. `[MODIFY] app/medini/etl/feature_engineering.py` — add three new functions:
   - `add_gaussian_aspect_fields(df)` → adds `gauss_drishti_<a>_<b>_<orb>`
     columns.
   - `add_harmonic_vargas(df)` → adds `harm_<planet>_sin<k>` /
     `harm_<planet>_cos<k>` columns for k ∈ {2,3,9,10,12}.
   - `add_fractal_dasha_vector(df)` → adds `frac_dasha_<planet>` columns
     summing to 1.0 per row.
2. `[NEW] scripts/build_round5c_variants.py` — orchestrates parquet rebuilds.
3. `[NEW] app/medini/ml/round5c_ablation.py` — runs the 3 variants through
   5-fold CV, compares to Round-5b lean baseline.
4. Outputs:
   - `app/medini/data/event_corpus_round5c_gauss.parquet`
   - `app/medini/data/event_corpus_round5c_harmonic.parquet`
   - `app/medini/data/event_corpus_round5c_fractal.parquet`
   - `data/ml_runs/round5c_ablation/{report.md, results.csv}`

**Verification**:
- For each variant: aggregate 5-fold CV accuracy compared to Round-5b lean.
- Acceptance: ≥ +0.003 absolute lift on at least one variant. If all three
  fail, document the de-quantization paradigm as empirically-falsified at
  this scale (a publishable negative result).

**Effort**: 3-4 days code + 2-3 hours compute.

**Risks**:
- The Gaussian aspect fields with learnable σ should ideally be co-trained
  with the model (XGBoost can't backprop into the feature transform). At
  XGBoost-level, σ is hand-chosen — limit one source of the theoretical
  lift. Document this; the proper σ-learning version lives in the EGNN
  side (Phase 3).
- Harmonic encodings add 90 cols; could exacerbate overfitting if the
  Round-5b baseline is already near-saturated.

---

### Phase 6 — Unified eval harness + Round-8 master summary

**Goal**: Single script that takes a chart cohort + target event class and
runs all 3 model families (XGBoost lean, astrov2 EGNN, LoRA-LLM) against
the same held-out split. Output: a comparison table that lets us cite
"on cohort X, model Y outperforms Z by Δ" with one command.

**Why last**: synthesizes everything. Becomes the standing harness for
Round-9 future model comparisons.

#### Alternative 6A — Wrapper script over the existing 3 model APIs
`scripts/round8_compare_all.py` instantiates: Round-5b XGBoost (via
`train_classifier.py` API), astrov2 EGNN (via `astrov2/src/` API),
LoRA-LLM (via `app/llm/lora_interpreter.py`). For a given cohort + target,
runs all three on the held-out set; prints comparison table.

#### Alternative 6B — Live web dashboard
A Flask/Streamlit page that lets you pick a chart from a dropdown, runs all
three models, shows their predictions side-by-side. Pro: useful for demos;
Con: 1-2 days of UI work that doesn't move the science forward.

**Recommendation: 6A**. Ship the CLI harness. Dashboard can be Round-9.

**File-level work**:
1. `[NEW] scripts/round8_compare_all.py` — ~150 lines.
2. `[NEW] NOTES_round8.md` — the Round-8 narrative summary, modeled on
   NOTES_round6_phases.md.

**Effort**: 1-2 days.

---

## 3. Strategic discussion

### 3.1 What this round bets on

The thesis behind picking these 5 phases is that **the next 0.05 AUC of
accuracy isn't hiding in some unknown architecture; it's in cleaning up
what we already built and bridging the two codebases**. Three independent
findings converge on this:

- Tier-2 §1 found ~150 cols of pure noise in the tabular tensor.
- Round 6 Phase 5 GNN failed because nodes were starved of features the
  tabular set had — astrov2 doesn't have that problem (it has full
  continuous coords).
- Round 6 Phase 11 showed transit trajectories add +0.085 AUC — exactly
  what astrov2's bipartite natal-transit architecture models natively.

### 3.2 What this round does NOT bet on

- **Corpus scaling**. Walkthrough.md claims 91k. Notes show 14k as the
  modeling cohort. The gap is the unlabelled mass; mining it requires
  another LLM-extraction round we haven't budgeted for. Round 9 territory.
- **Full 180-day ST-GNN**. The implementation_plan.md §2.1 calls for 180-day
  rolling windows; storage estimate was ~80GB. astrov2 currently uses
  point-in-time bipartite, not rolling. Worth scoping for Round 9, not 8.
- **Synastry**. 17 pairs is not a viable training set. Defer indefinitely
  until couple data is sourced.
- **MoE redesign**. karaka_moe_v2 (May 19 16:44) already attempted top-K
  + load-balance + classical-prior init and only got 9/26 class-karaka
  matches with val_acc 0.234. The MoE story is closed unless someone
  funds a true class-conditional-gating redesign — Round 10 candidate.

### 3.3 Sequencing rationale

```
Phase 1 ────► Phase 2 ────┐
                          ├──► Phase 6 (eval harness)
Phase 3 ──────────────────┤
                          │
Phase 4 ──────────────────┤
                          │
Phase 5 ──────────────────┘
```

- Phase 1 is the prerequisite for everything (every later phase wants the
  lean Round-5b parquet as input).
- Phase 2 produces the diagnostic that may reshape Phase 5 (class-specific
  drop list).
- Phases 3, 4, 5 are independent and parallelizable.
- Phase 6 synthesizes.

### 3.4 Risk-adjusted expected outcomes

| Phase | Best case | Expected case | Worst case |
|---|---|---|---|
| 1 lean retrain | +0.010 AUC, lean tensor adopted | +0.003-0.005, partial adoption | No lift; revert to full tensor |
| 2 class matrix | Strong class-specific patterns, redesigned drop list | Some patterns, minor refinement | Flat matrix, P1 list confirmed optimal |
| 3 EGNN bridge | EGNN matches or beats XGBoost on ≥5 classes | EGNN within ±0.03 on most classes | EGNN catastrophically underperforms at scale |
| 4 LoRA fine-tune | LoRA beats Claude API on eval; cheaper serving | Roughly equal; nice deployment option | LoRA loses; pivot to Claude-only |
| 5 continuous features | All 3 encodings lift; paradigm validated | 1 lifts (likely harmonic), 2 flat | All 3 flat; de-quantization falsified |

### 3.5 Decision points for user input

1. **Phase 1 — drop list scope**: ship the 15-group aggressive list, or
   start with the 3-group conservative list and add groups incrementally?
2. **Phase 3 — codebase consolidation**: respect the two-codebase
   separation for Round 8 (Alt 3B) or commit to consolidation now (Alt 3C)?
3. **Phase 4 — GPU spend authority**: OK to spend ~$5 on Modal? Or
   Colab-free path?
4. **Phase 5 — encoding priority**: All three, or skip Fractal Dasha?
5. **Schedule preference**: phases serial (lowest risk, ~3 weeks) or
   phases 3/4/5 parallel (higher peak load, ~2 weeks)?

---

## 4. Open questions / unknowns

- **Are the 91,549 charts in `ml_astro_15k.parquet` event-labelled enough to
  power the bigger cohort the walkthrough claims?** Need to spot-check the
  natal ↔ events join. If the 14k is a proper subset and the rest is
  unlabelled, Phase 1's "27-class 5-fold CV" still has 14k rows of data;
  bigger only matters once we mine more labels.
- **Is `event_corpus_round5_all.parquet` really the canonical training
  parquet, or has someone shipped a v2/v3 since?** The latest tracked
  artifacts in `data/ml_runs/` show consistent use of the same parquet,
  so the assumption holds — but Phase 1 should re-confirm.
- **Does astrov2's ephemeris produce identical coords to app/core's?**
  Cross-check in Phase 3.
- **What's the user's actual goal for the deployed product?**
  - Research artifact only (publish the findings)?
  - Deployed prediction service?
  - Both?
  The answer materially changes Phase 4's priority (LoRA vs Claude API)
  and Phase 6's scope.

---

## 5. Estimated total effort

- Engineering: ~12-15 working days, sequential.
- Compute: ~30 hours CPU (5-fold CV runs) + 3-6 hours GPU (LoRA + EGNN).
- Spend: ~$5-15 cloud (Modal + maybe RunPod for EGNN).

If phases 3-5 run in parallel, calendar time compresses to ~2 weeks with
2-3 parallel work streams.

---

## 6. Pre-execution checklist

Before kicking off Phase 1, verify:
- [ ] `event_corpus_round5_all.parquet` is still the canonical training
      input (no v2 from someone's WIP branch).
- [ ] User signs off on the 15-group aggressive drop list (or selects the
      conservative variant).
- [ ] Decision on GPU budget for Phase 4.
- [ ] Decision on Phase 3's codebase-consolidation scope.
- [ ] Round 8 branch name in git: suggest `round8-unification`.

---

**End of plan.** Ready for review. Once approved, execution starts with
Phase 1 (lean-feature productionization) — that's the prerequisite for
everything else and gives us a measurable win in ≤2 days.
