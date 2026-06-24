# Session Summary — Round 8 Unification & Substrate Repair

**Session date**: 2026-05-19 → 2026-05-20
**Branch**: `round8-unification` (uncommitted; git index.lock blocked commits)
**All artifacts persisted to disk in `E:\astro`.**

---

## TL;DR — The headline result

After a methodologically-honest substrate repair, the mean holdout AUC
across 10 event classes **dropped from ~0.74 (inflated, era-confounded,
selection-biased) to 0.5240 (honest, era-controlled, group-split).**

| Survives at non-trivial signal | AUC | Lift over random |
|---|---|---|
| career  | 0.6106 | +11pp |
| fame    | 0.5961 | +10pp |
| Marriage | 0.5318 | +3pp |
| Prize   | 0.5312 | +3pp |
| Family  | 0.5166 | +2pp |
| Death, Cause unspec | 0.5123 | +1pp |
| Relationship | 0.5028 | 0pp |
| Work    | 0.5015 | 0pp |
| Death by Disease | 0.4914 | −1pp |
| Published/Exhibited | 0.4460 | −5pp |

**Two real signals**: career and fame. Six classes are noise. Two
classes are below random (likely small-test-set artifact for
Publication, n=19 positives).

The Round-7 "Sun-in-10th = career +7.74pp VALIDATED" rule is real but
weaker than reported; the actual lift on a properly-controlled cohort
is ~0.6 AUC, not the 0.86 we'd been quoting.

---

## Workflow this session (chronological)

### 1. Resumed Tier-2 §1 dequant deep dive
- Built [`dequant_deep_dive_chunked.py`](computer://E:\astro\app\medini\ml\dequant_deep_dive_chunked.py) — sandbox-friendly checkpointed runner
- 33-cell ablation matrix at [`data/ml_runs/dequant_deep_dive/report.md`](computer://E:\astro\data\ml_runs\dequant_deep_dive\report.md)
- Tier-2 §2 lean-eval at [`lean_eval.json`](computer://E:\astro\data\ml_runs\dequant_deep_dive\lean_eval.json) — claimed +0.0065 lift (later falsified)
- Findings appended to [NOTES_round6_phases.md](computer://E:\astro\NOTES_round6_phases.md) (Tier-2 §1 + §2)

### 2. Wrote Round 8 master plan
- [implementation_plan_round8.md](computer://E:\astro\implementation_plan_round8.md) — 615 lines, 6 phases, alternatives + risks per phase
- User signed off with structural corrections (ephemeris alignment, Modal A10G, sequential dequant, full lean drop)

### 3. Phase 0 — Locked the proper holdout
- [`data/ml_runs/round8_master_eval/baseline_holdout_indices.parquet`](computer://E:\astro\data\ml_runs\round8_master_eval\baseline_holdout_indices.parquet) — GroupShuffleSplit by name, seed=42
- 11,378 train rows / 2,788 test rows / **zero name leak**
- [`split_manifest.json`](computer://E:\astro\data\ml_runs\round8_master_eval\split_manifest.json) — full provenance + class balance

### 4. Phase 1 — Lean retrain (FALSIFIED)
- Created [`feature_groups.py`](computer://E:\astro\app\medini\ml\feature_groups.py) registry
- Patched [`train_classifier.py`](computer://E:\astro\app\medini\ml\train_classifier.py) with `lean` kwarg + `--lean` CLI (default OFF after falsification)
- Built [`round5b_compare.py`](computer://E:\astro\app\medini\ml\round5b_compare.py) for head-to-head
- Result: LEAN wins 4/10, mean Δ AUC **−0.0137**. Acceptance FAILED.
- Report: [`data/ml_runs/round5b_compare/report.md`](computer://E:\astro\data\ml_runs\round5b_compare\report.md)

### 5. Phase 2 — Per-class ablation matrix (PARTIAL WIN)
- Built [`round8_class_matrix.py`](computer://E:\astro\app\medini\ml\round8_class_matrix.py) — 33-cell multi-class ablation
- Built [`round8_per_class_validate.py`](computer://E:\astro\app\medini\ml\round8_per_class_validate.py) for binary validation
- Matrix report: [`data/ml_runs/round8_class_matrix/report.md`](computer://E:\astro\data\ml_runs\round8_class_matrix\report.md)
- Validation: [`data/ml_runs/round8_per_class_validate/report.md`](computer://E:\astro\data\ml_runs\round8_per_class_validate\report.md)
- Result: 4/10 wins, mean Δ −0.0028. Three classes validated (Death by Disease, career, Publication). FAILED universal acceptance.

### 6. Critical pipeline review (the turning point)
- [CRITICAL_REVIEW_R8.md](computer://E:\astro\CRITICAL_REVIEW_R8.md) — 273 lines diagnosing 4 root causes:
  1. Selection bias: 85,113 of 90,197 charts never used as negatives
  2. Era confounding: 60-year birth-decade gap between event classes
  3. Non-independence: 54% of rows are (name, event_date) duplicates
  4. Event-positive-only training (no proper negative class)

### 7. Round 8.5 — Substrate repair (DONE)
- Built [`build_screening_cohort.py`](computer://E:\astro\app\medini\etl\build_screening_cohort.py) — per-class era-stratified jittered-control cohort builder
- Generated 10 cohorts at `app/medini/data/screening_*.parquet`
  - [career](computer://E:\astro\app\medini\data\screening_career.parquet) (951 rows)
  - [fame](computer://E:\astro\app\medini\data\screening_fame.parquet) (1,035 rows)
  - [marriage](computer://E:\astro\app\medini\data\screening_marriage.parquet) (1,290 rows)
  - [death_cause_unspec](computer://E:\astro\app\medini\data\screening_death__cause_unspecified.parquet) (4,254 rows)
  - + 6 more
- Built honest eval harness [`round8_screening_eval.py`](computer://E:\astro\app\medini\ml\round8_screening_eval.py)
- Result: **the honest 0.5240 mean AUC**
- Report: [`data/ml_runs/round8_screening_eval/report.md`](computer://E:\astro\data\ml_runs\round8_screening_eval\report.md)

### 8. Final narrative
- [NOTES_round8.md](computer://E:\astro\NOTES_round8.md) — 415 lines, the full Round-8 / Round-8.5 story

---

## What changed in the codebase

### New files
| File | Purpose |
|---|---|
| `app/medini/ml/feature_groups.py` | Central feature-group registry + drop lists |
| `app/medini/ml/dequant_deep_dive_chunked.py` | Sandbox-resumable ablation runner |
| `app/medini/ml/round5b_compare.py` | Phase 1 lean-vs-full head-to-head |
| `app/medini/ml/round8_class_matrix.py` | Phase 2 per-class ablation matrix |
| `app/medini/ml/round8_per_class_validate.py` | Phase 2.3 binary validator |
| `app/medini/ml/round8_screening_eval.py` | Phase 0.5 honest eval harness |
| `app/medini/etl/build_screening_cohort.py` | Era-stratified screening cohort builder |
| `implementation_plan_round8.md` | The original plan |
| `CRITICAL_REVIEW_R8.md` | Root-cause analysis |
| `NOTES_round8.md` | Running narrative |
| `SESSION_SUMMARY_R8.md` | This file |

### Modified files
| File | Change |
|---|---|
| `app/medini/ml/train_classifier.py` | Added `lean` kwarg + `--lean` CLI flag (default False after falsification) |
| `app/medini/ml/dequant_deep_dive.py` | Refactored to import groups from `feature_groups` |
| `NOTES_round6_phases.md` | Appended Tier-2 §1, Tier-2 §2 sections |

### Generated data artifacts (`data/ml_runs/`)
- `round8_master_eval/` — locked holdout indices
- `round5b_compare/` — Phase 1 results
- `round8_class_matrix/` — Phase 2 matrix
- `round8_per_class_validate/` — Phase 2.3 validation
- `round8_screening_eval/` — Round-8.5 honest results
- `dequant_deep_dive/` — Tier-2 (refreshed)

---

## Where to pick up next session

**The honest substrate is ready.** Future architectural work (EGNN bridge,
LoRA, continuous-spacetime features) should be evaluated against the
10 screening cohorts using `round8_screening_eval.py`'s protocol.

**The realistic bar to clear**:
- Beat 0.60 AUC on career/fame, OR
- Push any of the 6 currently-noise classes to ≥ 0.55 AUC.

**Suggested Round 9 starts (in priority order)**:

1. **Family per-era anomaly investigation** — per-era mean AUC 0.7150
   vs overall 0.5166 suggests era stratification over-controlled.
   Relax the 2:1 strict era-matching to allow some cross-decade
   negatives; might recover real signal cheaply. (~1 day of work)

2. **Repaired-cohort BPHS audit** — re-run the 154-rule Round-7
   audit using the screening cohorts. Most "validated" rules will
   probably collapse; the survivors are real findings. (~2 days)

3. **astrov2 EGNN bridge** — now justified to run, against the
   honest substrate. If EGNN can push career/fame past 0.65, that's
   a real architectural win. If it sits at 0.55-0.60, the architecture
   isn't the bottleneck. (~3 days + GPU)

4. **Corpus expansion to 91k** — the 5,084 → 22,939 unique-event-people
   gap suggests we can ~4x the cohort by mining more dated events
   from events_all.csv. Bigger N would tighten the noise-class CIs.

**Avoid** the original Round 8 Phases 4 (LoRA) and 5 (continuous
spacetime) until the substrate work above produces a model that's
clearly outperforming XGBoost-FULL on the screening cohort. They're
expensive bets on a foundation that's now properly modest.

---

## Open issues / cleanup

- **Git commit was blocked** by `.git/index.lock` (filesystem
  permission). All files are on disk; just need to manually `rm
  .git/index.lock` from Windows side before next `git add` /
  `git commit -m "Round 8 unification + substrate repair"`.
- The `round8-unification` branch exists but has no commits yet.
- `astrov2/` codebase remains untracked; still a parallel research
  branch.

---

## Five sentences to take away

1. Tier-2's "+0.0065 lean lift" was a row-level split artifact;
   under proper name-grouped split, lean lost by −0.0137.
2. The 0.86-0.94 AUCs from Round 6/7 were almost entirely era-decoding
   (60-year birth-decade gap between event classes).
3. On a properly-controlled substrate, only career and fame show
   genuine ~0.60 AUC; six other classes are essentially noise.
4. The lean-feature drop list is dead in every controlled setting
   tested (3 consecutive falsifications).
5. The substrate is now honest; future architecture work needs to
   clear 0.60 AUC on career/fame OR push noise classes past 0.55.
