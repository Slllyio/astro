---
date: 2026-05-24
revised: 2026-05-24 (rev 2)
type: design-spec
status: draft (awaiting user review after reviewer-loop fixes)
project: Medini Round 9
parent: implementation_plan_round9.md
supersedes: none
related:
  - data/ml_runs/phase3c_wedge/DECISION.md
  - data/ml_runs/phase3c_wedge/LOOP_ANALYSIS.md
  - data/ml_runs/fork_a_diagnostic/stage_b_corrected.md
  - data/ml_runs/fork_a_3level/diagnostic_3level.md
  - data/ml_runs/fork_a_doctrine/doctrine_score.md
  - data/ml_runs/fork_a_stage_e/stage_e_lord_house_score.md
authors:
  - Akshay
revision_notes:
  - "rev 1 → rev 2: corrected event-class count (14 → 30 after corpus inspection), corrected column prefix `is_event_` → `event_`, applied 5 advisory clarifications from spec-document-reviewer loop."
---

# Fork A · Stage D — Dynamic-DeepHit hazard model design spec

## Context & motivation

Round-9 Phase 3C tested the structural-yoga hypothesis as binary classification across
five substrates (n = 951 → 20,631) and FAILed every gate. The post-mortem
([LOOP_ANALYSIS.md](../../../data/ml_runs/phase3c_wedge/LOOP_ANALYSIS.md)) identified
three forks; the user committed to **Fork A — time-to-event reframing** on 2026-05-24.

Fork A has since produced positive signal at the MD-only level: exposure-adjusted Poisson
hazard ([stage_b_corrected.md](../../../data/ml_runs/fork_a_diagnostic/stage_b_corrected.md))
showed RR ≥ 1.5 with joint p = 1.8e-08 across 14 event classes. Stages B+, doctrine, and
E have all produced artifacts. The originally-planned **Stages C (Cox PH) and D
(Dynamic-DeepHit) have not been built.**

This spec defines Stage D — the survival-model analog of the Phase-3C falsifiable gate —
with full Vedic-feature conditioning.

## Approach summary

Build Stage D on **Astro-Databank primary**; **lunarastro replication is conditional**
on Stage D-AD passing the pre-committed gate. If Stage D-AD fails, do not run
lunarastro — the framing is wrong and lunarastro won't save it. If it passes,
lunarastro replication becomes a separate spec (out of scope here).

## 1. Goal, falsifiable claim, scope

### Goal

Build a multi-class competing-risks Dynamic-DeepHit hazard model that takes the full
Vedic Tensor as conditioning features and predicts per-event-class hazard across the
**K event classes** that pass the qualification floor (`n_train_positives ≥ 50` in every
seed). On the current corpus this resolves to **K = 30** classes; see [Appendix A](#appendix-a--the-30-qualifying-event-classes)
for the explicit list.

### Falsifiable claim (pre-committed; identical wording will go in DECISION.md)

> Conditional on (natal Vedic features + active dasha chain MD/AD/PD + active Phase-3B
> yoga catalog + Stage-E lord-house features), Stage D's per-event-class C-index on a
> held-out test set exceeds a matched Cox-PH baseline's per-event-class C-index by
> ≥ 3 σ_noise on the per-class mean across the K qualifying classes, AND ≥ ⌈K · 5/14⌉
> individual classes clear baseline + 3 σ_noise individually (= **≥ 11 of 30** at K = 30),
> AND σ_model ≤ Δ_mean, AND the result replicates on a held-back-fold protocol with
> test_size = 0.25.

The `5/14` ratio preserves the breadth requirement originally chosen during brainstorming
(≈ 36 %), now expressed as a ratio so the threshold scales with the actual K rather
than a hardcoded number. Failure closes Fork A on the Astro-Databank substrate. PASS
triggers the lunarastro replication step (separate spec).

### Scope IN

- One Dynamic-DeepHit model trained on [dasha_mdadpd_corpus.parquet](../../../app/medini/data/dasha_mdadpd_corpus.parquet).
- One matched Cox-PH baseline (same feature inputs, classical survival model).
- C-index-based noise-floor measurement (sample-variability protocol, 20 seeds per class).
- 10-seed multi-seed evaluation with bootstrap 95 % CIs per class.
- Replication-clause held-back fold protocol (10 seeds, test_size = 0.25, distinct from
  the main 10 seeds — single fold *protocol*, not single fold *run*).
- Per-class verdict report + aggregate `data/ml_runs/fork_a_stage_d/DECISION.md`.

### Scope OUT (explicit)

- Lunarastro substrate (conditional follow-on; separate spec).
- Hyperparameter tuning beyond a single declared default.
- Per-class architectural specialization (one shared encoder + per-class heads).
- Interpretability / SHAP-on-the-neural-net (deferred to a Stage-D-interpret follow-on).
- Productionizing the model behind an API (Phase 8 territory).

### Constraints & assumptions

- Existing [build_dasha_event_corpus.py](../../../app/medini/etl/build_dasha_event_corpus.py)
  output is the authoritative input. No re-ETL in this spec.
- The 30 qualifying event classes are the ones already labeled in the corpus that pass
  the qualification floor; see [Appendix A](#appendix-a--the-30-qualifying-event-classes).
- Lahiri ayanamsa locked (per [CLAUDE.md](../../../CLAUDE.md)); no recomputation of natal positions.
- Python 3.12, PyTorch on the existing `.venv`. CPU-acceptable for the Stage D fit;
  Cox baseline is the compute bottleneck and is also CPU-bound.

## 2. Data flow & corpus structure

### Input substrate (already built — read-only)

[dasha_mdadpd_corpus.parquet](../../../app/medini/data/dasha_mdadpd_corpus.parquet).
One row per **(person × MD × AD × PD)** leaf window.

Per-row columns (verified against the parquet schema as of 2026-05-24):

```
name, name_norm, birth_jd, moon_longitude
md_seq_idx, ad_seq_idx, pd_seq_idx
md_lord, ad_lord, pd_lord
window_start_jd, window_end_jd
window_duration_days, window_duration_years
n_events_in_window
event_career, event_fame, event_marriage, event_health, ...   # 56 columns total
```

**Naming convention**: event labels use the `event_<class>` prefix (NOT `is_event_*`).
56 raw event columns exist; the K=30 qualifying subset is enumerated in [Appendix A](#appendix-a--the-30-qualifying-event-classes).

Smoke variant: `dasha_mdadpd_smoke.parquet` (~10 % sample, used in tests).

### Feature pipeline

Stage D joins four feature blocks onto the corpus on `name_norm` (the join key — `person_id` is the conceptual term, `name_norm` the column name):

| Block | Source ETL | Columns | Notes |
|---|---|---|---|
| Natal Vedic Tensor | [feature_engineering.py](../../../app/medini/etl/feature_engineering.py) `expected_feature_columns` | 193 (Base 70 + Kinematic 63 + Vedic 50 + meta 10) | Per-person; same value across that person's windows. |
| Active dasha encoding | NEW Stage-D helper | ~25 | One-hot MD lord × AD lord × PD lord collapsed to lord-presence one-hots + Stage B+ Cochran-Armitage "n-of-3 relevant lords" rate-ladder features. |
| Active yogas | [add_yoga_features.py](../../../app/medini/etl/add_yoga_features.py) + NEW dasha-gating layer | 32 (16 `<yoga>_natal_strength` + 16 `<yoga>_dasha_active`) | `dasha_active` = at least one of MD/AD/PD lord ∈ yoga's planet set. |
| Stage-E lord-house features | [build_natal_lord_houses.py](../../../app/medini/etl/build_natal_lord_houses.py) + NEW dasha-gated joiner | 27 + per-window aggregation (~50) | "Lord rules X, occupies Y, aspects Z" for the active MD lord at each window. |
| Doctrine score | [dasha_doctrine_score.py](../../../app/medini/ml/dasha_doctrine_score.py) | 30 (1 per qualifying class) | Optional pre-computed classical prior; included to give the neural net a warm prior. |

Total input vector: **193 + 25 + 32 + 50 + 30 = 330 dims** raw, ~265 effective dims
after categorical-lord embeddings (~25 categorical levels → 8-dim → ~−65 net).

### Labels & survival framing

For Dynamic-DeepHit, each leaf window contributes one (or zero) event:

- `time` = `window_duration_days` (the window's exposure period).
- `event` ∈ {0, 1, ..., K} where K = number of qualifying classes (= 30 on current corpus).
  `0` = censored; `1..K` = the event class that fired, in the canonical order from
  [Appendix A](#appendix-a--the-30-qualifying-event-classes).
- Co-occurring events: earliest-JD wins for the discrete-time formulation. Co-occurrence
  rate tracked in a separate `event_co_occurrence_mask` column for diagnostics, not
  used by the model. The pre-flight reports the rate.
- **Right-censoring time** is computed by the dataset layer (`stage_d_dataset.py`) as
  `min(birth_jd + 100 yrs, death_jd_if_recorded)` and consumed as the `duration` field
  of each row's survival tuple. The death JD itself is **NOT** included in the feature
  matrix — F3 in §6 hard-denies any `_jd` or `death*` column as a feature input. The
  censoring derivation lives upstream of the feature matrix.

### Train/test split

`GroupShuffleSplit(test_size=0.20, random_state=<seed>)` keyed on `name_norm` — same
person never appears in both train and test (mirrors Phase 3C's leak-fix). Replication
protocol uses `test_size=0.25` for all 10 of its seeds (distinct from the main 10).

### Outputs

- `app/medini/data/dasha_stage_d_features.parquet` — materialized joined feature table.
- `app/medini/data/dasha_stage_d_features_smoke.parquet` — smoke variant.

## 3. Model architecture

### Library choice

Use **[pycox](https://github.com/havakv/pycox)** as the DeepHit foundation. Pycox is
the canonical PyTorch implementation, stable, benchmarked on standard survival datasets.
A from-scratch reimplementation would burn ~2 weeks for no scientific payoff.

Requires adding to [requirements.txt](../../../requirements.txt): `pycox>=0.2.3`,
`torch>=2.0`, `lifelines>=0.27`. Pin pycox exactly (research-grade library, API surface
has shifted across minor versions).

### Architecture

```
   Input feature vector (~330 raw, ~265 after embedding)
                 │
   ┌─────────────▼─────────────┐
   │  Embedding layer           │   md_lord, ad_lord, pd_lord, asc_sign,
   │  - categorical lords       │     planet signs → 8-dim embeddings
   │    → 8-dim each            │
   │  - continuous: pass-through│
   └─────────────┬─────────────┘
                 │
   ┌─────────────▼─────────────┐
   │  Shared encoder            │   MLP: [FC(256) + BN + ReLU + Dropout(0.3)] × 3
   │   ~200k params             │
   └─────────────┬─────────────┘
                 │
        ┌────────┴────────┬────────┬─── ... (30 heads)
        │                 │        │
   ┌────▼────┐      ┌────▼────┐
   │ Head 1  │      │ Head 2  │       Each head: FC(128) + ReLU + FC(K=50)
   │ career  │      │ fame    │       Output = hazard probability per time bin
   └────┬────┘      └────┬────┘
        │                 │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ Softmax across   │       Total parameters ≈ 2.0M
        │ (30 × 50 + 1)    │       (more heads than rev 1 due to K = 30 vs 14).
        │ outputs = PMF    │       The +1 is the "no event" mass.
        └─────────────────┘
```

### Time discretization

K_bins = 50 log-spaced time bins from 1 day to 100 years
(`np.logspace(np.log10(1), np.log10(100*365.25), 51)`). Each window's
`window_duration_days` maps to the bin containing its endpoint.

(`K` is overloaded — the spec uses `K` for class count and `K_bins` for time bins. The
training code should follow the same naming.)

### Loss function

pycox's `DeepHitLoss` = α · NLL + (1 − α) · ranking_loss, α = 0.5.

### Training protocol

- Optimizer: AdamW, lr = 1e-3, weight_decay = 1e-4.
- Scheduler: ReduceLROnPlateau on val loss, patience = 10.
- Batch size: 256.
- Max epochs: 200, early-stop on val loss, patience = 20.
- **Fixed hyperparameters across all seeds — no HP search**, by design.
- Validation slice: 20 % of TRAIN (so train/val/test = 64 / 16 / 20 of corpus).

### Explicit non-features

- No transformer encoder (Grinsztajn et al. — MLP empirically optimal at n ≈ 10k).
- No per-class encoder specialization (defeats the shared-representation hypothesis).
- No mixup / SMOTE / class reweighting (biases per-class C-index and breaks the gate).
- No pretraining from astrov2 EGNN (separate hypothesis).

### Code organization

| File | Purpose | Approx. LOC |
|---|---|---|
| [app/medini/ml/stage_d_model.py](../../../app/medini/ml/stage_d_model.py) | DeepHit wrapper class | ~150 |
| [app/medini/ml/stage_d_dataset.py](../../../app/medini/ml/stage_d_dataset.py) | PyTorch Dataset | ~80 |
| [app/medini/ml/stage_d_train.py](../../../app/medini/ml/stage_d_train.py) | CLI training script | ~120 |
| [tests/test_stage_d_model.py](../../../tests/test_stage_d_model.py) | Forward / loss / round-trip | ~60 |
| [tests/test_stage_d_dataset.py](../../../tests/test_stage_d_dataset.py) | Time-bin + leak tests | ~80 |

## 4. Baseline & noise floor

### Baseline: cause-specific Cox PH on the SAME feature set

The claim being tested is precise: *the neural model finds non-linear feature interactions
that the linear-proportional-hazards model cannot, on the same Vedic feature set.* That
requires a matched-features baseline, not a stripped-down one.

- **Library**: `lifelines.CoxPHFitter`.
- **K = 30 cause-specific Cox PH models**, one per qualifying event class. For class *k*:
  outcome = `event_<k>`, time = `window_duration_days`, other K − 1 classes treated as
  censoring (standard cause-specific approach).
- **L1 penalty `penalizer=0.01`** to handle the 250-dim input at n ≈ 10k. Fixed (no tune).
- Categorical lord features → ordinal encoded (lifelines doesn't do embeddings).
- **Parallelization**: each (seed, class) Cox fit is independent. The training script
  fits in a `concurrent.futures.ProcessPoolExecutor` to amortize the 30× class multiplier
  across CPU cores (`os.cpu_count()`).

### Code organization for baseline

| File | Purpose |
|---|---|
| [app/medini/ml/stage_d_baseline.py](../../../app/medini/ml/stage_d_baseline.py) | Train 30 cause-specific Cox PH models, persist coefficients + per-class C-index. |
| [tests/test_stage_d_baseline.py](../../../tests/test_stage_d_baseline.py) | Convergence + C-index range smoke test. |

### Noise floor — sample-variability protocol

```
σ_noise_class_k = std{ C_DeepHit_class_k − C_Cox_class_k : 20 independent seeds }
where each seed defines a fresh GroupShuffleSplit(test_size=0.20, random_state=seed)
```

This mirrors Phase 3C's σ_Δ_holdout_AUC across 20 seeds — just C-index instead of AUC.
It captures *how much the lift wobbles purely from which 20 % of people end up in test*.

**Pre-committed**: σ_noise is measured BEFORE the main 10-seed evaluation on a separate
set of 20 seeds. Once measured, frozen. Re-measuring after seeing the main result is
HARKing.

### Expected magnitudes

| Quantity | Expected range | Why |
|---|---|---|
| Cox baseline C-index per class | 0.55 – 0.62 | Survival baseline C-index is typically below 0.65 even with strong features. |
| Stage D C-index per class (if signal exists) | 0.58 – 0.66 | DeepHit ranking loss buys ~2-3 pts over Cox on most benchmarks. |
| σ_noise per class | 0.015 – 0.025 | Lifelines + DeepHit at n ≈ 8k train ≈ Phase 3C's 0.016. |
| **3 σ_noise threshold per class** | **0.045 – 0.075** | The bar Stage D must clear. |

If measured σ_noise > 0.04 per class, the 3σ threshold becomes 0.12 — implausibly hard.
That is itself a falsification signal: the corpus is too small for survival modeling at
this depth.

## 5. Gate evaluation protocol

### The four criteria

For PASS, all of the following must hold:

| ID | Criterion | Formula |
|---|---|---|
| **G1** | Aggregate lift | `mean_over_classes(Δ_class) ≥ mean_over_classes(3 × σ_noise_class)` |
| **G2** | Per-class breadth | `count{ k : Δ_class_k ≥ 3 × σ_noise_class_k } ≥ ⌈K · 5/14⌉` (= **≥ 11 at K = 30**) |
| **G3** | Model stability | `σ_model_class ≤ Δ_class` for ALL classes that contribute to G2 |
| **G4** | Replication | All of G1, G2, G3 hold on the held-back-fold protocol (10 seeds, test_size=0.25) |

Where:

- `Δ_class = mean_over_seeds(C_DeepHit_class) − mean_over_seeds(C_Cox_class)`, averaged across the 10 main seeds.
- `σ_noise_class` — pre-measured on 20 independent seeds (§4), frozen.
- `σ_model_class = std_over_seeds(C_DeepHit_class)` — Stage D seed-to-seed wobble.

### C-index computation — exact protocol

**One implementation pinned: `lifelines.utils.concordance_index`** for both DeepHit and
Cox risk scores. The DeepHit model produces a discrete-time PMF over (class, bin); for
the per-class C-index we reduce to a single risk score per (sample, class) as the
**cumulative incidence at the right edge of the time horizon** (sum of the per-bin
hazards across all bins ≤ 100 years). This single scalar per (sample, class) is fed to
`lifelines.utils.concordance_index(durations, -risk_scores, event_observed)` exactly as
for Cox.

Cross-checked on one seed using `scikit-survival.metrics.concordance_index_censored`;
disagreement > 0.005 fails the run (F11 in §6).

### Multi-seed run protocol

```
Pre-flight (done once, before the main run):
  For seed in [101..120]:
    split = GroupShuffleSplit(test_size=0.20, random_state=seed)
    train Stage D, train Cox baseline (30 per-class fits, parallelized)
    record (C_DeepHit_class_k, C_Cox_class_k) per class
  σ_noise_class_k = std{ C_DeepHit_class_k − C_Cox_class_k : 20 seeds }
  FREEZE σ_noise table → data/ml_runs/fork_a_stage_d/noise_floor.json (git-committed).

Main run:
  For seed in [1..10]:
    split = GroupShuffleSplit(test_size=0.20, random_state=seed)
    train Stage D, train Cox baseline (30 per-class fits)
    record per-class C-index for both
  Compute Δ_class, σ_model_class. Evaluate G1, G2, G3.

Replication (only if G1 ∧ G2 ∧ G3 hold):
  For seed in [201..210]:
    split = GroupShuffleSplit(test_size=0.25, random_state=seed)
    train Stage D, train Cox baseline (30 per-class fits)
    record per-class C-index
  Evaluate G1, G2, G3 again. If all hold → G4 passes → PASS.
```

**Total fits**: 40 Stage D fits (each is one multi-head training run) + 40 × 30 = 1200
cause-specific Cox fits. Stage D dominates total wall-clock only if the Cox parallelism
is broken; with `ProcessPoolExecutor` on an 8-core CPU, each seed's Cox baseline is
~8–15 min and Stage D is ~5–10 min. **Expected wall-clock: 6–12 hours** depending on
CPU count.

### Class qualification floor

A class qualifies for G2 only if it has **`n_train_positives ≥ 50` in EVERY seed**.
The "K = 30" count in this spec is the upper bound: classes that fall below 50 in some
seeds get dropped from G2 in those seeds and reported in the diagnostic but not counted
toward the threshold. The pre-flight (§6) prints the per-class table and confirms K
before the main run starts. If pre-flight K < 25 (i.e., > 5 classes drop), the spec
threshold is regenerated as `⌈K · 5/14⌉` and logged in `noise_floor.json` alongside the
σ table.

### Multiple-comparisons defense

Under independent pure noise at α = 0.0013 (3σ one-sided),
**P(≥ 11 of 30 clear by chance) ≈ 7 × 10⁻²⁶**
(Binomial(30, 0.0013) tail; even more conservative than the rev-1 K=14 case's 5 × 10⁻⁹).
**G2's ratio-based threshold IS the multiple-comparisons defense**; no Bonferroni layer needed.

Classes aren't independent (shared encoder → correlated residuals). G3 catches the case
where all classes move together due to model overfitting on a lucky seed.

### Decision table

| G1 | G2 | G3 | G4 | Outcome | Action |
|---|---|---|---|---|---|
| ✓ | ✓ | ✓ | ✓ | **PASS strong** | Proceed to lunarastro replication (separate spec) |
| ✓ | ✓ | ✓ | ✗ | PASS weak / replication fail | Treat as FAIL with partial signal — investigate borderline classes |
| ✓ | ✓ | ✗ | — | FAIL: model unstable | Stage D overfits. Consider capacity reduction or larger n. |
| ✓ | ✗ | ✓ | — | FAIL: signal too narrow | Lift driven by < 11 classes. Cannot claim general astrology-predicts-events. Class-specific follow-on (Phase 6 territory). |
| ✗ | — | — | — | FAIL: no aggregate signal | Honest null. Trigger pivot decision: Fork B deepen OR Fork C write-up. |

### Artifacts

```
data/ml_runs/fork_a_stage_d/
  noise_floor.json                  # σ_noise per class + K + threshold, frozen pre-flight (git-committed)
  main_run.json                     # all 10 × K C-indices, both models
  main_summary.md                   # per-class table + G1/G2/G3 verdicts
  replication_run.json              # all 10 × K from held-back fold (if triggered)
  replication_summary.md            # G4 verdict
  DECISION.md                       # final PASS/FAIL with next-step
  models/seed_<N>_deephit.pt
  models/seed_<N>_cox.pkl
```

Artifacts are written **incrementally** — a mid-run crash can resume from the next seed.

## 6. Failure modes & instrumentation

| # | Failure mode | Manifestation | Catch |
|---|---|---|---|
| **F1** | Person leakage between train/test | Stage D C-index inflated 0.05-0.10; baseline same | Assertion: `train.name_norm.isdisjoint(test.name_norm)` per split, every seed. Fail loudly. |
| **F2** | Time-causal feature leakage | Both models trivially predict; C-indices > 0.95 | Unit test: train on shuffled event times, expect C-index ≈ 0.5. Anomalies fail. |
| **F3** | Censoring information bleed (death_jd as feature) | C-index for `death_*` classes anomalously high | Hard-coded deny list in dataset: no column matching `^.*_jd$\|^death.*$\|^observation_horizon`. Censoring time computed inside `stage_d_dataset.py` from `birth_jd + 100yr` and (where recorded) the person's death JD — but the death JD itself is never written into the feature matrix. Audit logged. |
| **F4** | Class co-occurrence collapse | Per-class C-index drops where co-occurrence is high | Pre-flight reports `% windows with > 1 event class`. If > 5 %, flag in DECISION.md. |
| **F5** | Time-bin discretization artifact | C-index sensitivity to K_bins | Sensitivity: re-evaluate one seed at K_bins=30 and K_bins=80. If Δ_class swings by > σ_noise, flag. |
| **F6** | Neural overfit | Train C-index ≈ 0.95, val ≈ 0.55 | Report train/val/test per class per seed. Gap > 0.10 on > half classes → "overfit-suspect" flag for human review. |
| **F7** | Cox baseline convergence failure | Garbage C-index ≈ 0.5; Δ inflated | Trap `lifelines.exceptions.ConvergenceError`; mark seed Cox-FAIL; abort if > 1 of 30 Cox fits in any seed. |
| **F8** | Lord-name as trivial predictor | Stage D lift driven entirely by lord features | Mandatory ablation: one-seed run with MD/AD/PD lord features zeroed. If Δ drops to ≤ σ_noise, report "lift is lord-only — Stage D adds nothing beyond Stage B." Not a FAIL but most important disclosure. |
| **F9** | NaN / Inf in DeepHit loss | Training crashes or fits with NaN-masked gradients | `torch.autograd.set_detect_anomaly(True)` in dev; `assert torch.isfinite(loss).all()` per step in prod. |
| **F10** | Reproducibility failure | σ_noise contaminated with non-stochastic variance | `torch.use_deterministic_algorithms(True)` + seed numpy/random/torch + log torch/cuda version. CI test: same seed twice → identical to 4 decimals. |
| **F11** | C-index computation differs across libraries | Per-class numbers don't match audit by hand | Hard-pin `lifelines.utils.concordance_index` for BOTH DeepHit risk scores (reduced via cumulative incidence at right edge; see §5) and Cox risk scores. Cross-check with scikit-survival on 1 seed; disagreement > 0.005 fails the run. |
| **F12** | HARKing temptation | Gate becomes meaningless | `noise_floor.json` git-committed BEFORE main run; its SHA-256 logged in `main_run.json`. Adjusting σ_noise post-hoc requires a new commit, which is visible in `git log`. |
| **F13** | Smoke parquet not representative | Tests pass, real run fails | Smoke test asserts ≥ 1 positive per class in the qualifying-class list. If a class becomes vacant after a corpus rebuild, smoke loses test power and pytest reports. |
| **F14** | Hardware nondeterminism (CPU/GPU mismatch) | Results differ between dev and CI | Pin to CPU for gate runs. GPU allowed for dev iteration only. Documented in DECISION.md. |

### Per-seed logging schema

Every seed writes a structured record to `main_run.json` / `replication_run.json`:

```json
{
  "seed": 1,
  "split": "main",
  "test_size": 0.20,
  "n_train_persons": 645,
  "n_test_persons": 161,
  "K_qualifying": 30,
  "g2_threshold": 11,
  "noise_floor_sha256": "ab12...",
  "torch_version": "2.4.1+cpu",
  "lifelines_version": "0.28.0",
  "pycox_version": "0.2.3",
  "per_class": {
    "career": {
      "n_train_positives": 1794, "n_test_positives": 449,
      "qualifies": true,
      "c_index_train_stage_d": 0.71, "c_index_val_stage_d": 0.62, "c_index_test_stage_d": 0.61,
      "c_index_train_cox":      0.66, "c_index_val_cox":      0.58, "c_index_test_cox":      0.57,
      "delta_test": 0.04,
      "cox_converged": true
    },
    "fame": { "...": "..." }
  },
  "overfit_suspect": false,
  "co_occurrence_rate": 0.027,
  "duration_seconds": 318
}
```

The `DECISION.md` generator reads these records to compute the gate verdict — never
hand-edited.

### Mandatory pre-flight

[app/medini/ml/stage_d_preflight.py](../../../app/medini/ml/stage_d_preflight.py) runs once before the main pipeline and writes `preflight.md`:

1. Person-leak smoke test (synthetic 100-person corpus, assertion fires correctly).
2. Time-causal smoke test (event_jd accidentally included → C-index = 1.0 → script aborts).
3. Class co-occurrence rate report.
4. Class qualification table — confirm the K=30 list against the live parquet, flag any change.
5. Hardware report (torch version, CUDA available, deterministic mode active).

**Hard block**: if any pre-flight check fails, the main run is BLOCKED. No partial results.

## 7. Deliverables, sequencing, sub-gates

### Phases

| Phase | Deliverable | Sub-gate (must pass before next phase) | Effort |
|---|---|---|---|
| **D.0** Feature pipeline materialization | `stage_d_features.py` + `dasha_stage_d_features.parquet` (+ smoke) | All K=30 classes present with ≥ 1 positive in smoke. NaN rate < 5 % per column. No `_jd` columns in feature set. Schema documented. | 3-4d |
| **D.1** Cox baseline | `stage_d_baseline.py` + tests | 30 Cox models converge on smoke and full per seed (parallel). Per-class C-index ∈ [0.4, 0.7]. L1 penalty = 0.01 fixed. ProcessPool parallelization verified. | 4-5d (slightly higher than rev 1 due to 30× class count + parallelization scaffolding) |
| **D.2** DeepHit wrapper + dataset | `stage_d_model.py`, `stage_d_dataset.py` + tests | Forward pass shapes correct (output PMF over 30 × 50 + 1). Loss finite on 100 random inputs. Save/load round-trips bit-identically. Person-leak assertion fires on synthetic leaky split. | 4-5d |
| **D.3** Training script + pre-flight | `stage_d_train.py`, `stage_d_preflight.py` | Pre-flight passes all 5 checks. One-seed smoke train converges (val loss decreases). Per-class C-index ∈ [0.4, 0.7] on smoke. K confirmed = 30 (or adjusted with logged rationale). | 3-4d |
| **D.4** Noise floor measurement | 20-seed run → `noise_floor.json` (git-committed, with K + threshold) | σ_noise per class reported. All 20 seeds complete (no Cox-FAIL > 1 per seed). Magnitudes in expected band 0.015-0.04 per class. SHA-256 logged. | 2-3d (slightly higher due to 30× Cox fits) |
| **D.5** Main 10-seed run | `main_run.json` + `main_summary.md` | All 10 seeds complete. G1/G2/G3 evaluated and reported. No overfit-suspect flags > 50 % of seeds. | 2-3d |
| **D.6** Conditional replication (triggers only if G1 ∧ G2 ∧ G3 pass) | `replication_run.json` + `replication_summary.md` | All 10 held-back-fold seeds complete. G1/G2/G3 re-evaluated. G4 verdict. | 2-3d |
| **D.7** Verdict synthesis | `DECISION.md` | Per the decision table in §5: PASS / FAIL with explicit next-step recommendation. Same template as [phase3c_wedge/DECISION.md](../../../data/ml_runs/phase3c_wedge/DECISION.md). | 1-2d |

**Total expected effort**: ~3-4 weeks if FAIL at D.5; ~4-5 weeks if PASS triggers D.6 + D.7.

### File inventory after Stage D

```
app/medini/ml/
  stage_d_features.py        (NEW, ~120 LOC)
  stage_d_dataset.py         (NEW, ~80 LOC)
  stage_d_model.py           (NEW, ~150 LOC)
  stage_d_baseline.py        (NEW, ~120 LOC — includes ProcessPool parallelization)
  stage_d_train.py           (NEW, ~120 LOC)
  stage_d_preflight.py       (NEW, ~100 LOC)
  stage_d_evaluate.py        (NEW, ~100 LOC — DECISION.md generator from JSONs)

app/medini/data/
  dasha_stage_d_features.parquet         (NEW, materialized)
  dasha_stage_d_features_smoke.parquet   (NEW)

tests/
  test_stage_d_features.py    (NEW, ~80 LOC)
  test_stage_d_baseline.py    (NEW, ~60 LOC)
  test_stage_d_model.py       (NEW, ~80 LOC)
  test_stage_d_dataset.py     (NEW, ~80 LOC)
  test_stage_d_preflight.py   (NEW, ~50 LOC)
  test_stage_d_evaluate.py    (NEW, ~60 LOC)

data/ml_runs/fork_a_stage_d/
  preflight.md
  noise_floor.json (git-committed)
  main_run.json
  main_summary.md
  replication_run.json     (conditional)
  replication_summary.md   (conditional)
  DECISION.md
  models/seed_*_deephit.pt
  models/seed_*_cox.pkl

requirements.txt — add: pycox>=0.2.3, lifelines>=0.27, torch>=2.0
```

**New code total**: ~1120 LOC source + ~410 LOC tests = ~1530 LOC. Largest file ~150 LOC,
well under the 800-LOC project ceiling.

### Explicitly NOT in any of these phases

- Lunarastro substrate work (separate spec, triggered only by PASS on D.7).
- SHAP / integrated gradients on the neural net (deferred to Stage D-interpret if PASS).
- Web UI / API endpoint for the trained model.
- Per-class architectural specialization (separate spec).
- Hyperparameter search.
- Multi-task or transfer-learning experiments.

### Dependencies on existing project work

- ✅ [dasha_mdadpd_corpus.parquet](../../../app/medini/data/dasha_mdadpd_corpus.parquet) already built (Stage B+ ETL).
- ✅ [ephemeris_engine.py](../../../app/core/ephemeris_engine.py) for any natal recomputation.
- ✅ [add_yoga_features.py](../../../app/medini/etl/add_yoga_features.py) for Phase-3B yoga features.
- ✅ [build_natal_lord_houses.py](../../../app/medini/etl/build_natal_lord_houses.py) for Stage-E lord-house features.
- ✅ [dasha_doctrine_score.py](../../../app/medini/ml/dasha_doctrine_score.py) for optional doctrine prior.
- ⚠️ [requirements.txt](../../../requirements.txt) — 3 new packages.

## Open risks acknowledged in the design

1. **F8 (lord-as-trivial-predictor) is the highest-probability silent failure mode.** The mandatory ablation in §6 catches it but does not prevent it. If Stage D passes only because of MD/AD/PD lord one-hots, the verdict must be restated as "Stage D = Stage B with extra noise" — not as evidence that the full Vedic feature set carries hazard signal.
2. **n ≈ 950 per class is at the lower edge of where DeepHit holds up.** Pycox's benchmarks typically use n ≥ 5k. If σ_model exceeds 0.04 per class, the gate becomes mechanically unclearable, and we should consider whether a simpler architecture (e.g., DeepSurv) was the right baseline instead.
3. **The K=30 event-class label space inherits the same documentation-bias concerns Round 8 flagged.** Stage D inherits this; the PASS-strong outcome would still need to acknowledge it in DECISION.md before any claim of "astrology predicts life events" is made.
4. **Pycox is a research-grade library, not production-grade.** API surface has shifted across minor versions. Pin exactly via `requirements.txt` and document the pin reason.
5. **K=30 inflates Cox baseline compute by ~2× over rev 1.** Each main seed runs 30 cause-specific Cox fits (vs 14 in rev 1). Mitigated by `ProcessPoolExecutor` parallelism, but the total wall-clock is now expected at 6-12 hours rather than 2-4. Plan compute scheduling accordingly.

---

## Appendix A — The 30 qualifying event classes

Verified against [dasha_mdadpd_corpus.parquet](../../../app/medini/data/dasha_mdadpd_corpus.parquet) on 2026-05-24. A class qualifies if its **total positives in the full corpus ≥ 50** (the n_train_positives ≥ 50 constraint is per-seed and may drop borderline classes; pre-flight reports the per-seed K).

Sorted by descending positive count:

| # | Column | Class name | Total positives |
|--:|---|---|--:|
| 1 | `event_fame` | fame | 2297 |
| 2 | `event_career` | career | 2243 |
| 3 | `event_death_cause_unspecified` | death_cause_unspecified | 1428 |
| 4 | `event_health` | health | 775 |
| 5 | `event_relationships` | relationships | 770 |
| 6 | `event_personal` | personal | 719 |
| 7 | `event_education` | education | 687 |
| 8 | `event_legal` | legal | 681 |
| 9 | `event_finance` | finance | 665 |
| 10 | `event_marriage` | marriage | 654 |
| 11 | `event_relationship` | relationship | 635 |
| 12 | `event_work` | work | 613 |
| 13 | `event_agriculture` | agriculture | 503 |
| 14 | `event_business` | business | 498 |
| 15 | `event_medical` | medical | 448 |
| 16 | `event_property` | property | 430 |
| 17 | `event_death_by_disease` | death_by_disease | 399 |
| 18 | `event_general` | general | 384 |
| 19 | `event_travel` | travel | 292 |
| 20 | `event_family` | family | 276 |
| 21 | `event_children` | children | 284 |
| 22 | `event_spirituality` | spirituality | 274 |
| 23 | `event_accidents` | accidents | 250 |
| 24 | `event_crime` | crime | 151 |
| 25 | `event_death_by_heart_attack` | death_by_heart_attack | 99 |
| 26 | `event_social` | social | 96 |
| 27 | `event_death_of_mate` | death_of_mate | 93 |
| 28 | `event_death_by_accident` | death_by_accident | 75 |
| 29 | `event_death_of_father` | death_of_father | 69 |
| 30 | `event_other_death` | other_death | 52 |

Excluded classes (below the n=50 floor): `death`, `death_by_execution`, `death_by_homicide`, `death_by_suicide`, `death_by_war_or_terrorism`, `death_mysterious`, `death_of_child`, `death_of_mother`, `death_of_sibling`, `death_of_significant_person`, `family_trauma`, `financial`, `financial_crime_perpetration`, `financial_crime_victimization`, `mental_health`, `misc.`, `mundane`, `other_crime`, `other_family`, `other_financial`, `other_misc.`, `other_relationship`, `other_social`, `other_work`, `social_crime_perpetration`, `social_crime_victimization`.

**Notes on the list**:
- `relationship` (n=635) and `relationships` (n=770) are both present — they're separate columns in the corpus, likely from differing label-source conventions. The pre-flight will flag the redundancy; merging them is out of scope for Stage D (would require re-ETL).
- The `death_*` family is heavily fragmented; many subtypes fall below the floor. The 6 qualifying death classes (`death_cause_unspecified`, `death_by_disease`, `death_by_heart_attack`, `death_of_mate`, `death_by_accident`, `death_of_father`, `other_death`) give meaningful coverage of the death event space.
- Highest-n classes (career, fame, death_cause_unspecified) will dominate the aggregate G1 lift; G2's per-class breadth requirement (≥ 11 of 30) ensures the verdict isn't a 2-3-class story.
