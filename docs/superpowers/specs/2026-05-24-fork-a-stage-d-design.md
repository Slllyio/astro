---
date: 2026-05-24
type: design-spec
status: draft (awaiting review)
project: Medini Round 9
parent: implementation_plan_round9.md
supersedes: none
related:
  - data/ml_runs/phase3c_wedge/DECISION.md          # the 5-substrate FAIL that motivated Fork A
  - data/ml_runs/phase3c_wedge/LOOP_ANALYSIS.md     # fork selection rationale
  - data/ml_runs/fork_a_diagnostic/stage_b_corrected.md  # Stage B PASS, RR=1.5, p=1.8e-8
  - data/ml_runs/fork_a_3level/diagnostic_3level.md
  - data/ml_runs/fork_a_doctrine/doctrine_score.md
  - data/ml_runs/fork_a_stage_e/stage_e_lord_house_score.md
authors:
  - Akshay
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
14 event classes the corpus already supports.

### Falsifiable claim (pre-committed; identical wording will go in DECISION.md)

> Conditional on (natal Vedic features + active dasha chain MD/AD/PD + active Phase-3B
> yoga catalog + Stage-E lord-house features), Stage D's per-event-class C-index on a
> held-out test set exceeds a matched Cox-PH baseline's per-event-class C-index by
> ≥ 3 σ_noise on the per-class mean across 14 event classes, AND ≥ 5 of 14 individual
> classes clear baseline + 3 σ_noise individually, AND σ_model ≤ Δ_mean, AND the
> result replicates on a held-back fold.

Failure closes Fork A on the Astro-Databank substrate. PASS triggers the lunarastro
replication step (separate spec).

### Scope IN

- One Dynamic-DeepHit model trained on [dasha_mdadpd_corpus.parquet](../../../app/medini/data/dasha_mdadpd_corpus.parquet).
- One matched Cox-PH baseline (same feature inputs, classical survival model).
- C-index-based noise-floor measurement (sample-variability protocol, 20 seeds per class).
- 10-seed multi-seed evaluation with bootstrap 95% CIs per class.
- Replication-clause held-back fold (single, test_size=0.25).
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
- The 14 event classes are those already labeled in the corpus.
- Lahiri ayanamsa locked (per [CLAUDE.md](../../../CLAUDE.md)); no recomputation of natal positions.
- Python 3.12, PyTorch on the existing `.venv`. CPU-acceptable for n ≈ 10k × 14.

## 2. Data flow & corpus structure

### Input substrate (already built — read-only)

[dasha_mdadpd_corpus.parquet](../../../app/medini/data/dasha_mdadpd_corpus.parquet).
One row per **(person × MD × AD × PD)** leaf window.

Per-row columns:

```
person_id              # stable id, used for GroupShuffleSplit
name_norm              # for joining with natal features
md_seq_idx, ad_seq_idx, pd_seq_idx
md_lord, ad_lord, pd_lord
start_jd, end_jd
duration_days
is_event_career, is_event_fame, is_event_marriage, ...   # 14 binary labels
event_jd_career, ...                                     # NaN if no event
```

Smoke variant: `dasha_mdadpd_smoke.parquet` (~10 % sample, used in tests).

### Feature pipeline

Stage D joins four feature blocks onto the corpus on `person_id`:

| Block | Source ETL | Columns | Notes |
|---|---|---|---|
| Natal Vedic Tensor | [feature_engineering.py](../../../app/medini/etl/feature_engineering.py) `expected_feature_columns` | 193 (Base 70 + Kinematic 63 + Vedic 50 + meta 10) | Per-person; same value across that person's windows. |
| Active dasha encoding | NEW Stage-D helper | ~25 | One-hot MD lord × AD lord × PD lord collapsed to lord-presence one-hots + Stage B+ Cochran-Armitage "n-of-3 relevant lords" rate-ladder features. |
| Active yogas | [add_yoga_features.py](../../../app/medini/etl/add_yoga_features.py) + NEW dasha-gating layer | 32 (16 `<yoga>_natal_strength` + 16 `<yoga>_dasha_active`) | `dasha_active` = at least one of MD/AD/PD lord ∈ yoga's planet set. |
| Stage-E lord-house features | [build_natal_lord_houses.py](../../../app/medini/etl/build_natal_lord_houses.py) + NEW dasha-gated joiner | 27 + per-window aggregation (~50) | "Lord rules X, occupies Y, aspects Z" for the active MD lord at each window. |
| Doctrine score | [dasha_doctrine_score.py](../../../app/medini/ml/dasha_doctrine_score.py) | 1 × 14 = 14 | Optional pre-computed classical prior; included to give the neural net a warm prior. |

Total input vector: ~315 dims raw, ~250 dims effective after categorical-lord embeddings.

### Labels & survival framing

For Dynamic-DeepHit, each leaf window contributes one (or zero) event:

- `time` = `duration_days` (the window's exposure period).
- `event` ∈ 0..14. `0` = censored; `1..14` = the event class that fired.
- Co-occurring events: earliest-JD wins for the discrete-time formulation. Co-occurrence
  rate tracked in a separate `event_co_occurrence_mask` column for diagnostics, not
  used by the model. The pre-flight reports the rate.
- Right-censoring: at `min(birth_jd + 100 yrs, death_jd_if_recorded)`.

### Train/test split

`GroupShuffleSplit(test_size=0.20, random_state=<seed>)` keyed on `person_id` — same
person never appears in both train and test (mirrors Phase 3C's leak-fix). Replication
fold uses `test_size=0.25`.

### Outputs

- `app/medini/data/dasha_stage_d_features.parquet` — materialized joined feature table.
- `app/medini/data/dasha_stage_d_features_smoke.parquet` — smoke variant.

## 3. Model architecture

### Library choice

Use **[pycox](https://github.com/havakv/pycox)** as the DeepHit foundation. Pycox is
the canonical PyTorch implementation, stable, benchmarked on standard survival datasets.
A from-scratch reimplementation would burn ~2 weeks for no scientific payoff.

Requires adding to [requirements.txt](../../../requirements.txt): `pycox>=0.2.3`,
`torch>=2.0`, `lifelines>=0.27`.

### Architecture

```
   Input feature vector (~315 raw, ~250 after embedding)
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
        ┌────────┴────────┬────────┬─── ... (14 heads)
        │                 │        │
   ┌────▼────┐      ┌────▼────┐
   │ Head 1  │      │ Head 2  │       Each head: FC(128) + ReLU + FC(K=50)
   │ career  │      │ fame    │       Output = hazard probability per time bin
   └────┬────┘      └────┬────┘
        │                 │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ Softmax across   │       Total parameters ≈ 1.3M.
        │ (14 × 50 + 1)    │       The +1 is the "no event" mass.
        │ outputs = PMF    │
        └─────────────────┘
```

### Time discretization

K = 50 log-spaced bins from 1 day to 100 years
(`np.logspace(np.log10(1), np.log10(100*365.25), 51)`). Each window's `duration_days`
maps to the bin containing its endpoint.

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
- **14 cause-specific Cox PH models**, one per event class. For class *k*: outcome =
  `is_event_k`, time = `duration_days`, other 13 classes treated as censoring (standard
  cause-specific approach).
- **L1 penalty `penalizer=0.01`** to handle the 250-dim input at n ≈ 10k. Fixed (no tune).
- Categorical lord features → ordinal encoded (lifelines doesn't do embeddings).

### Code organization for baseline

| File | Purpose |
|---|---|
| [app/medini/ml/stage_d_baseline.py](../../../app/medini/ml/stage_d_baseline.py) | Train 14 cause-specific Cox PH models, persist coefficients + per-class C-index. |
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
| **G2** | Per-class breadth | `count{ k : Δ_class_k ≥ 3 × σ_noise_class_k } ≥ 5` |
| **G3** | Model stability | `σ_model_class ≤ Δ_class` for ALL classes that contribute to G2 |
| **G4** | Replication | All of G1, G2, G3 hold on the held-back fold with test_size=0.25 |

Where:

- `Δ_class = mean_over_seeds(C_DeepHit_class) − mean_over_seeds(C_Cox_class)`, averaged across the 10 main seeds.
- `σ_noise_class` — pre-measured on 20 independent seeds (§4), frozen.
- `σ_model_class = std_over_seeds(C_DeepHit_class)` — Stage D seed-to-seed wobble.

### Multi-seed run protocol

```
Pre-flight (done once, before the main run):
  For seed in [101..120]:
    split = GroupShuffleSplit(test_size=0.20, random_state=seed)
    train Stage D, train Cox baseline
    record (C_DeepHit_class_k, C_Cox_class_k) per class
  σ_noise_class_k = std{ C_DeepHit_class_k − C_Cox_class_k : 20 seeds }
  FREEZE σ_noise table → data/ml_runs/fork_a_stage_d/noise_floor.json (git-committed).

Main run:
  For seed in [1..10]:
    split = GroupShuffleSplit(test_size=0.20, random_state=seed)
    train Stage D, train Cox baseline
    record per-class C-index for both
  Compute Δ_class, σ_model_class. Evaluate G1, G2, G3.

Replication (only if G1 ∧ G2 ∧ G3 hold):
  For seed in [201..210]:
    split = GroupShuffleSplit(test_size=0.25, random_state=seed)
    train Stage D, train Cox baseline
    record per-class C-index
  Evaluate G1, G2, G3 again. If all hold → G4 passes → PASS.
```

Total: 20 (noise floor) + 10 (main) + maybe 10 (replication) = up to 40 Stage-D fits + 40 Cox fits. ~2–4 hours on CPU.

### Class qualification floor

A class qualifies for G2 only if it has **≥ 50 positives in the training set of every seed**.
Sub-50 classes still reported in the verdict but excluded from the G2 count. The corpus
has ~12 likely-qualifying classes; the 2–3 borderline ones (death_disease, awards) get
reported as "did not qualify (n < 50)".

### Multiple-comparisons defense

Under independent pure noise at α = 0.0013 (3σ one-sided),
**P(≥ 5 of 14 clear by chance) ≈ 5 × 10⁻⁹**. Effectively zero. **G2's ≥5-of-14 requirement
IS the multiple-comparisons defense**; no Bonferroni layer needed.

Classes aren't independent (shared encoder → correlated residuals). G3 catches the case
where all classes move together due to model overfitting on a lucky seed.

### Decision table

| G1 | G2 | G3 | G4 | Outcome | Action |
|---|---|---|---|---|---|
| ✓ | ✓ | ✓ | ✓ | **PASS strong** | Proceed to lunarastro replication (separate spec) |
| ✓ | ✓ | ✓ | ✗ | PASS weak / replication fail | Treat as FAIL with partial signal — investigate borderline classes |
| ✓ | ✓ | ✗ | — | FAIL: model unstable | Stage D overfits. Consider capacity reduction or larger n. |
| ✓ | ✗ | ✓ | — | FAIL: signal too narrow | Lift driven by 1-2 classes only. Cannot claim general astrology-predicts-events. Class-specific follow-on (Phase 6 territory). |
| ✗ | — | — | — | FAIL: no aggregate signal | Honest null. Trigger pivot decision: Fork B deepen OR Fork C write-up. |

### Artifacts

```
data/ml_runs/fork_a_stage_d/
  noise_floor.json                  # σ_noise per class, frozen pre-flight (git-committed)
  main_run.json                     # all 10×14 C-indices, both models
  main_summary.md                   # per-class table + G1/G2/G3 verdicts
  replication_run.json              # all 10×14 from held-back fold (if triggered)
  replication_summary.md            # G4 verdict
  DECISION.md                       # final PASS/FAIL with next-step
  models/seed_<N>_deephit.pt
  models/seed_<N>_cox.pkl
```

Artifacts are written **incrementally** — a mid-run crash can resume from the next seed.

## 6. Failure modes & instrumentation

| # | Failure mode | Manifestation | Catch |
|---|---|---|---|
| **F1** | Person leakage between train/test | Stage D C-index inflated 0.05-0.10; baseline same | Assertion: `train.person_id.isdisjoint(test.person_id)` per split, every seed. Fail loudly. |
| **F2** | Time-causal feature leakage | Both models trivially predict; C-indices > 0.95 | Unit test: train on shuffled event times, expect C-index ≈ 0.5. Anomalies fail. |
| **F3** | Censoring information bleed (death_jd as feature) | C-index for `death_*` classes anomalously high | Hard-coded deny list in dataset: no column matching `^.*_jd$\|^death.*$\|^observation_horizon`. Audit logged. |
| **F4** | Class co-occurrence collapse | Per-class C-index drops where co-occurrence is high | Pre-flight reports `% windows with > 1 event class`. If > 5 %, flag in DECISION.md. |
| **F5** | Time-bin discretization artifact | C-index sensitivity to K | Sensitivity: re-evaluate one seed at K=30 and K=80. If Δ_class swings by > σ_noise, flag. |
| **F6** | Neural overfit | Train C-index ≈ 0.95, val ≈ 0.55 | Report train/val/test per class per seed. Gap > 0.10 on > half classes → "overfit-suspect" flag for human review. |
| **F7** | Cox baseline convergence failure | Garbage C-index ≈ 0.5; Δ inflated | Trap `lifelines.exceptions.ConvergenceError`; mark seed Cox-FAIL; abort if > 1 of 30. |
| **F8** | Lord-name as trivial predictor | Stage D lift driven entirely by lord features | Mandatory ablation: one-seed run with MD/AD/PD lord features zeroed. If Δ drops to ≤ σ_noise, report "lift is lord-only — Stage D adds nothing beyond Stage B." Not a FAIL but most important disclosure. |
| **F9** | NaN / Inf in DeepHit loss | Training crashes or fits with NaN-masked gradients | `torch.autograd.set_detect_anomaly(True)` in dev; `assert torch.isfinite(loss).all()` per step in prod. |
| **F10** | Reproducibility failure | σ_noise contaminated with non-stochastic variance | `torch.use_deterministic_algorithms(True)` + seed numpy/random/torch + log torch/cuda version. CI test: same seed twice → identical to 4 decimals. |
| **F11** | C-index computation differs across libraries | Per-class numbers don't match audit by hand | Hard-pin one implementation: `lifelines.utils.concordance_index` for BOTH DeepHit risk scores and Cox risk scores. Cross-check with scikit-survival on 1 seed. |
| **F12** | HARKing temptation | Gate becomes meaningless | `noise_floor.json` git-committed BEFORE main run; its SHA-256 logged in `main_run.json`. Adjusting σ_noise post-hoc requires a new commit, which is visible in `git log`. |
| **F13** | Smoke parquet not representative | Tests pass, real run fails | Smoke test asserts ≥ 1 positive per class. If a class becomes vacant after a corpus rebuild, smoke loses test power and pytest reports. |
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
  "noise_floor_sha256": "ab12...",
  "torch_version": "2.4.1+cpu",
  "lifelines_version": "0.28.0",
  "pycox_version": "0.2.3",
  "per_class": {
    "career": {
      "n_train_positives": 142, "n_test_positives": 38,
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
4. Class qualification table (which classes pass `n_train_positives ≥ 50`).
5. Hardware report (torch version, CUDA available, deterministic mode active).

**Hard block**: if any pre-flight check fails, the main run is BLOCKED. No partial results.

## 7. Deliverables, sequencing, sub-gates

### Phases

| Phase | Deliverable | Sub-gate (must pass before next phase) | Effort |
|---|---|---|---|
| **D.0** Feature pipeline materialization | `stage_d_features.py` + `dasha_stage_d_features.parquet` (+ smoke) | All 14 classes present with ≥ 1 positive in smoke. NaN rate < 5 % per column. No `_jd` columns in feature set. Schema documented. | 3-4d |
| **D.1** Cox baseline | `stage_d_baseline.py` + tests | 14 Cox models converge on smoke and full. Per-class C-index ∈ [0.4, 0.7]. L1 penalty = 0.01 fixed. | 3-4d |
| **D.2** DeepHit wrapper + dataset | `stage_d_model.py`, `stage_d_dataset.py` + tests | Forward pass shapes correct. Loss finite on 100 random inputs. Save/load round-trips bit-identically. Person-leak assertion fires on synthetic leaky split. | 4-5d |
| **D.3** Training script + pre-flight | `stage_d_train.py`, `stage_d_preflight.py` | Pre-flight passes all 5 checks. One-seed smoke train converges (val loss decreases). Per-class C-index ∈ [0.4, 0.7] on smoke. | 3-4d |
| **D.4** Noise floor measurement | 20-seed run → `noise_floor.json` (git-committed) | σ_noise per class reported. All 20 seeds complete (no Cox-FAIL > 1). Magnitudes in expected band 0.015-0.04 per class. SHA-256 logged. | 1-2d |
| **D.5** Main 10-seed run | `main_run.json` + `main_summary.md` | All 10 seeds complete. G1/G2/G3 evaluated and reported. No overfit-suspect flags > 50 % of seeds. | 2d |
| **D.6** Conditional replication (triggers only if G1 ∧ G2 ∧ G3 pass) | `replication_run.json` + `replication_summary.md` | All 10 held-back-fold seeds complete. G1/G2/G3 re-evaluated. G4 verdict. | 2-3d |
| **D.7** Verdict synthesis | `DECISION.md` | Per the decision table in §5: PASS / FAIL with explicit next-step recommendation. Same template as [phase3c_wedge/DECISION.md](../../../data/ml_runs/phase3c_wedge/DECISION.md). | 1-2d |

**Total expected effort**: ~3 weeks if FAIL at D.5; ~4 weeks if PASS triggers D.6 + D.7.

### File inventory after Stage D

```
app/medini/ml/
  stage_d_features.py        (NEW, ~120 LOC)
  stage_d_dataset.py         (NEW, ~80 LOC)
  stage_d_model.py           (NEW, ~150 LOC)
  stage_d_baseline.py        (NEW, ~100 LOC)
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

**New code total**: ~1100 LOC source + ~410 LOC tests = ~1500 LOC. Largest file ~150 LOC,
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
3. **The 14 event-class label space inherits the same documentation-bias concerns Round 8 flagged.** Stage D inherits this; the PASS-strong outcome would still need to acknowledge it in DECISION.md before any claim of "astrology predicts life events" is made.
4. **Pycox is a research-grade library, not production-grade.** API surface has shifted across minor versions. Pin exactly via `requirements.txt` and document the pin reason.
