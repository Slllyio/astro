---
date: 2026-05-25
type: handoff-spec
status: ready for execution (next session or background run)
parent: docs/superpowers/plans/2026-05-24-fork-a-stage-d.md
parent_spec: docs/superpowers/specs/2026-05-24-fork-a-stage-d-design.md
covers: Tasks 18, 19, 19.5, 20, 20.5, 22
---

# Stage D Tasks 18-22 — execution handoff

## Why this exists

All Stage D **code** (Tasks 0-17, 21) is committed on `round8-unification`. The remaining tasks (18, 19, 19.5, 20, 20.5, 22) are **training runs + verdict generation**. They're not new code work — they're CPU-time work that didn't fit in the implementation session.

Sub-gates D.0, D.1 (smoke), D.2, D.3 (smoke) all PASS. The pipeline runs end-to-end on smoke in 26 min/seed.

## Files referenced

| Task | What | Status |
|---|---|---|
| 18 — Noise floor | Run 20 seeds, freeze `noise_floor.json` | PENDING |
| 19 — Main run | Run 10 seeds, evaluate G1/G2/G3 | PENDING |
| 19.5 — K_BINS sensitivity | Run K_BINS=30, 50, 80 for 1 seed; F5 defense | PENDING |
| 20 — Replication (conditional) | Run 10 seeds at test_size=0.25; only if main passed | PENDING |
| 20.5 — sksurv cross-check | F11 defense; lifelines vs sksurv concordance agreement | PENDING |
| 22 — Generate DECISION.md | `py -3.12 -m app.medini.ml.stage_d_evaluate` | PENDING |

## Pre-flight before any of these runs

### 1. Decide on compute scale

**At full corpus (6.17M rows)**, one seed takes an unknown amount of time. Smoke (60K rows) took 26 min. Naive linear scaling = 43 hours per seed (infeasible). Cox PH's complexity is closer to O(n × log n × iterations); realistic estimate is 1-3 hours per seed at full corpus.

Three execution strategies:

**A. Full corpus, status quo** (~25-100 hours for 20 seeds, single machine)
- Risk: Cox baseline pickling 30 copies of (train, test) per seed kills wall-clock
- **Strongly recommended**: refactor `_fit_all_classes_parallel` first (see step 2 below)

**B. Person-subsample, status quo** (~5-10 hours)
- Subsample dasha_corpus_birth_data.parquet to ~1000 persons
- Re-materialize features at subsample scale (Step 5 of `2026-05-25-stage-d-data-regeneration-plan.md` but with `--limit 1000`)
- Run all 20+10+10 seeds on the smaller substrate
- Caveat: gate verdict carries an "n=1000-subsample" footnote

**C. Cloud / batch** (out of scope of this handoff)

### 2. Recommended optimization before Task 18: refactor `_fit_all_classes_parallel`

In `app/medini/ml/stage_d_baseline.py`, current implementation pickles (train, test) DataFrames 30 times per seed. On Windows (no fork), this is the bottleneck.

Refactor to use `ProcessPoolExecutor(initializer=...)`:

```python
def _init_worker_data(train_pickle: bytes, test_pickle: bytes) -> None:
    import pickle
    global _WORKER_TRAIN, _WORKER_TEST
    _WORKER_TRAIN = pickle.loads(train_pickle)
    _WORKER_TEST = pickle.loads(test_pickle)


def _fit_one_shared(args: tuple[str, int]) -> CoxFitResult:
    cls, seed = args
    return fit_cause_specific_cox(_WORKER_TRAIN, _WORKER_TEST, event_class=cls, seed=seed)


def _fit_all_classes_parallel(train, test, *, seed):
    import pickle
    n_workers = max(1, (os.cpu_count() or 2) - 1)
    train_p = pickle.dumps(train)
    test_p = pickle.dumps(test)
    args_list = [(cls, seed) for cls in QUALIFYING_EVENT_CLASSES]
    with ProcessPoolExecutor(
        max_workers=n_workers,
        initializer=_init_worker_data,
        initargs=(train_p, test_p),
    ) as ex:
        results = list(ex.map(_fit_one_shared, args_list))
    return results
```

Expected speedup: 3-5× at smoke scale, much more at full scale.

After applying, verify the existing `TestFitAllClasses` parity test still passes.

## Task 18 — Noise floor (20 seeds)

```powershell
# PowerShell loop. Each seed writes one record to noise_floor_run.jsonl.
for ($s = 101; $s -le 120; $s++) {
    py -3.12 -m app.medini.ml.stage_d_train --seed $s --split noise_floor
    if (-not $?) { Write-Error "seed $s FAILED"; break }
}
```

Then compute and freeze `noise_floor.json`:

```bash
py -3.12 -c "
import json, statistics, math
from pathlib import Path
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

records = [json.loads(l) for l in
           Path('data/ml_runs/fork_a_stage_d/noise_floor_run.jsonl').read_text().splitlines()
           if l.strip()]
assert len(records) == 20, f'expected 20 seeds, got {len(records)}'

sigma = {}
for cls in QUALIFYING_EVENT_CLASSES:
    deltas = [r['per_class'][cls]['delta_test'] for r in records
              if r['per_class'][cls]['delta_test'] is not None
              and not math.isnan(r['per_class'][cls]['delta_test'])]
    sigma[cls] = statistics.stdev(deltas) if len(deltas) >= 15 else None

K_qual = sum(1 for v in sigma.values() if v is not None)
threshold = max(1, math.ceil(K_qual * 5 / 14))
out = {
    'K_qualifying': K_qual,
    'g2_threshold': threshold,
    'g2_threshold_formula': 'ceil(K * 5/14)',
    'sigma_noise_per_class': sigma,
    'sigma_noise_3x_per_class': {k: (v * 3 if v else None) for k, v in sigma.items()},
    'n_seeds': 20,
    'computed_at': __import__('datetime').date.today().isoformat(),
}
Path('data/ml_runs/fork_a_stage_d/noise_floor.json').write_text(json.dumps(out, indent=2))
print('K_qualifying:', K_qual, 'g2_threshold:', threshold)
for cls, s in sorted(sigma.items()):
    print(f'  {cls:35s} sigma={s if s is None else round(s, 4)}')
"

git add data/ml_runs/fork_a_stage_d/noise_floor.json data/ml_runs/fork_a_stage_d/noise_floor_run.jsonl
git commit -m "data(medini): Stage D noise floor — 20-seed sigma frozen"
```

Sub-gate D.4 PASS criterion: most σ_noise in [0.015, 0.04]. Any class with σ > 0.06 should be flagged.

## Task 19 — Main 10-seed run

```powershell
for ($s = 1; $s -le 10; $s++) {
    py -3.12 -m app.medini.ml.stage_d_train --seed $s --split main
}
```

## Task 19.5 — K_BINS sensitivity (F5 defense)

```bash
# Re-run seed=42 at K_BINS=30 and K_BINS=80
py -3.12 -m app.medini.ml.stage_d_train --seed 42 --split sensitivity_kbins30 --k-bins 30 \
    --out-dir data/ml_runs/fork_a_stage_d/sensitivity_kbins
py -3.12 -m app.medini.ml.stage_d_train --seed 42 --split sensitivity_kbins80 --k-bins 80 \
    --out-dir data/ml_runs/fork_a_stage_d/sensitivity_kbins
```

⚠️ **CLI gap**: `stage_d_train.py` doesn't currently accept `--k-bins`. Add to the argparse in `main()`:
```python
p.add_argument("--k-bins", type=int, default=50)
```
And pass through to `_train_one_seed(..., k_bins=args.k_bins)`.

Compare per-class Δ at K_BINS=30, 50, 80. If |Δ(50) − Δ(30)| > σ_noise on > 1/3 of classes, write a prominent warning into DECISION.md.

## Task 20 — Conditional replication (only if main passed G1∧G2∧G3)

```powershell
for ($s = 201; $s -le 210; $s++) {
    py -3.12 -m app.medini.ml.stage_d_train --seed $s --split replication --test-size 0.25
}
```

## Task 20.5 — sksurv cross-check (F11 defense)

```python
py -3.12 -c "
import json, numpy as np, pandas as pd, torch
from pathlib import Path
from lifelines.utils import concordance_index as ll_ci
from sksurv.metrics import concordance_index_censored as sk_ci
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
from app.medini.ml.stage_d_dataset import K_BINS, build_dataset
from app.medini.ml.stage_d_baseline import split_train_test
from app.medini.ml.stage_d_model import StageDModel

df = pd.read_parquet('app/medini/data/dasha_stage_d_features.parquet')
train_df, test_df = split_train_test(df, seed=1)
test_ds = build_dataset(test_df, name_norms=test_df['name_norm'].unique())
n_features = test_ds.features.shape[1]
model = StageDModel.load(
    Path('data/ml_runs/fork_a_stage_d/models/seed_1_deephit.pt'),
    n_features=n_features,
)
model.eval()
with torch.no_grad():
    pmf = model(test_ds.features)

print(f'| class | lifelines C | sksurv C | |diff| |')
print('|---|---|---|---|')
max_diff = 0.0
for i, cls in enumerate(QUALIFYING_EVENT_CLASSES):
    cum = pmf[:, i * K_BINS:(i + 1) * K_BINS].sum(dim=1).numpy()
    events = (test_ds.event_classes == (i + 1)).numpy().astype(bool)
    if events.sum() < 2:
        continue
    ll = ll_ci(test_ds.durations, -cum, events.astype(int))
    sk, *_ = sk_ci(events, test_ds.durations, cum)
    diff = abs(ll - sk)
    max_diff = max(max_diff, diff)
    print(f'| {cls} | {ll:.4f} | {sk:.4f} | {diff:.4f} |')
print()
print(f'Max disagreement: {max_diff:.4f} (threshold: 0.005)')
print('PASS' if max_diff < 0.005 else 'FAIL')
" > data/ml_runs/fork_a_stage_d/sksurv_crosscheck.md
```

## Task 22 — Generate DECISION.md

```bash
py -3.12 -m app.medini.ml.stage_d_evaluate --out-dir data/ml_runs/fork_a_stage_d
```

Reads `noise_floor.json`, `main_run.jsonl`, optionally `replication_run.jsonl`, evaluates the 4-criterion gate, and writes `DECISION.md`. The verdict generator is committed at `30494e2`.

## Final commit + Stage D done

```bash
git add data/ml_runs/fork_a_stage_d/DECISION.md
git commit -m "data(medini): Stage D final verdict ($OUTCOME)"
```

Per the spec §5 decision table, `$OUTCOME` is one of:
- **PASS strong** — proceed to lunarastro replication (separate spec)
- **PASS weak / replication fail** — investigate borderline classes
- **FAIL: model unstable** — reduce capacity OR pivot to Fork B
- **FAIL: signal too narrow** — class-specific follow-on
- **FAIL: no aggregate signal** — honest null; pivot to Fork B or Fork C

## What's been committed so far

| Phase | Commits |
|---|---|
| D.0 (feature pipeline) | 3255592, 2798886, 9eef447, 59ba7c5, b1c8350, b6dabd7, acd8238, 50b0eab5, 492c955, 426a08b, f1d95ec, 35d7510 |
| Regeneration | ae932ff (path constants + sub-gate D.0 PASS on full corpus) |
| D.1 (Cox baseline) | 1650efd, 446d95f, b67ae94 (sub-gate D.1 verdict) |
| D.2 (Dataset + Model) | 98c625d, 85b9f4a, e21cb2f (sub-gate D.2 verdict) |
| D.3 (Preflight + Trainer) | 3a64286, (sub-gate D.3 verdict pending) |
| D.7 (Evaluator) | 30494e2 |

**Total: 18 commits.** Stage D infrastructure is feature-complete pending the long-running gate evaluation in Tasks 18-22.
