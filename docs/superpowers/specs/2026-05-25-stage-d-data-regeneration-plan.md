---
date: 2026-05-25
type: handoff-spec
status: ready for execution (next session)
parent: docs/superpowers/specs/2026-05-24-fork-a-stage-d-design.md
blocks: docs/superpowers/plans/2026-05-24-fork-a-stage-d.md (Tasks 7-22)
discovered_at: Sub-gate D.0 on f1d95ec (commit on round8-unification)
---

# Stage D upstream-parquet regeneration — handoff spec

## Why this exists

Sub-gate D.0 (Task 6 of `2026-05-24-fork-a-stage-d.md`) surfaced that **198 of
395 columns in the materialized Stage D smoke parquet are 100% NaN.** Root cause:
the dasha corpus and the upstream feature parquets were built from
**non-overlapping person sets.**

| Parquet | Persons | Overlap with smoke (100p) | Overlap with full corpus (10,239p) |
|---|---|---:|---:|
| `dasha_mdadpd_corpus.parquet` (smoke variant) | 100 | (is the smoke corpus) | — |
| `dasha_mdadpd_corpus.parquet` (full) | 10,239 | — | (is the full corpus) |
| `natal_lord_houses.parquet` | 84,337 | **100%** ✅ | likely high |
| `ml_astro_features.parquet` (Vedic Tensor) | 14,070 | **0%** ❌ | likely partial |
| `screening_career_yogas.parquet` | 951 | **0%** ❌ | likely very partial |
| `doctrine_scores.parquet` | (missing) | n/a | n/a (optional per spec) |

If we proceed to Tasks 7-22 of the plan with the current parquets, Stage D's
model trains on ~120 of ~395 cols carrying real signal — drastically lower
information than the spec assumed, almost certainly failing the gate for
the wrong reasons.

User decision on 2026-05-25: **regenerate the upstream parquets to cover the
dasha corpus's full 10,239-person set before continuing to Task 7.**

## Required regeneration steps

### Step 1 — Source the per-person birth data (lat/lon/jd) for all 10,239 dasha-corpus persons

The dasha corpus has `name_norm` and `birth_jd` but NOT `latitude` / `longitude`.
The Vedic Tensor computation requires all three.

**Likely source:** the original CSV that fed `build_dasha_event_corpus.py`
(probably `data/astro_databank/merged_all.csv` per the docstring at
[build_dasha_event_corpus.py:21](../../../app/medini/etl/build_dasha_event_corpus.py)).
The CSV should carry `name`, `date_of_birth`, `time`, `latitude`, `longitude` for
each Astro-Databank person.

**Concrete task:**
- Read the source CSV.
- Filter to the 10,239 persons whose `name_norm` is in the dasha corpus.
- Output `app/medini/data/dasha_corpus_birth_data.parquet` with columns
  `name_norm, birth_jd, latitude, longitude`. Validate: 10,239 unique rows,
  zero NaN.

**Effort:** ~30 minutes. CPU-trivial.

### Step 2 — Build the full-coverage Vedic Tensor parquet

Use `app.medini.etl.feature_engineering.compute_chart_features` (already
exists, no need to modify):

```python
from app.medini.etl.feature_engineering import compute_chart_features
import pandas as pd

births = pd.read_parquet("app/medini/data/dasha_corpus_birth_data.parquet")
rows = []
for _, r in births.iterrows():
    feats = compute_chart_features(
        jd=float(r["birth_jd"]),
        latitude=float(r["latitude"]),
        longitude=float(r["longitude"]),
    )
    feats["name_norm"] = r["name_norm"]
    rows.append(feats)

out = pd.DataFrame(rows)
out.to_parquet("app/medini/data/ml_astro_features_full.parquet", index=False)
```

**Important:** write to a NEW filename (`ml_astro_features_full.parquet`) so
the existing `ml_astro_features.parquet` (which other scripts may rely on) is
not clobbered. Then update `_VEDIC_TENSOR_PARQUET` in `stage_d_features.py`
to point at the new file — OR leave the constant as `ml_astro_features.parquet`
and rename the new file into place after verifying it's complete.

**Effort:** **~3 hours of CPU** (10,239 persons × ~1 sec/person of ephemeris
computation, single-threaded). Parallelize with `multiprocessing.Pool` +
`init_worker` from `app.medini.etl.lahiri_worker` for an 8× speedup → ~25
minutes on an 8-core machine.

### Step 3 — Build the full-coverage yoga parquet

Run the existing `add_yoga_features.py` ETL on the new Vedic Tensor:

```bash
py -3.12 -m app.medini.etl.add_yoga_features \
    --input app/medini/data/ml_astro_features_full.parquet \
    --output app/medini/data/dasha_corpus_yogas.parquet
```

Then update `_DATA_DIR / "screening_career_yogas.parquet"` in
[stage_d_features.py:add_yoga_features_with_dasha_gating](../../../app/medini/ml/stage_d_features.py)
to point at `dasha_corpus_yogas.parquet`.

**Effort:** ~10-30 min. CPU-bound on the yoga detector loop.

### Step 4 — (Optional, per spec) Generate the doctrine parquet

If you want the warm-prior doctrine columns (spec §2 marks this as Optional),
adapt `app/medini/ml/dasha_doctrine_score.py` to output per-person doctrine
scores as a parquet (it currently outputs an aggregate report).

**Effort:** ~1 day. Skip for now — accept the no-op behavior in
`add_doctrine_scores` (graceful warning, returns df unchanged).

### Step 5 — Re-materialize Stage D features

```bash
py -3.12 -m app.medini.ml.stage_d_features          # full corpus
py -3.12 -m app.medini.ml.stage_d_features --smoke  # smoke
```

**Effort:** ~5-15 min for full, seconds for smoke.

### Step 6 — Re-verify sub-gate D.0

```bash
py -3.12 -c "
import pandas as pd
df = pd.read_parquet('app/medini/data/dasha_stage_d_features.parquet')
print('rows:', len(df), 'cols:', len(df.columns))
nan_pct = (df.isna().mean() * 100).round(2)
high_nan = nan_pct[nan_pct > 5].sort_values(ascending=False)
print('cols with >5% NaN:', len(high_nan))
print(high_nan.head(20))
from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES
nonzero = sum(1 for cls in QUALIFYING_EVENT_CLASSES if df[f'event_{cls}'].sum() >= 1)
zero_classes = [cls for cls in QUALIFYING_EVENT_CLASSES if df[f'event_{cls}'].sum() == 0]
print(f'class coverage: {nonzero}/30 (zero classes: {zero_classes})')
"
```

**Pass criteria for full sub-gate D.0:**
- `cols with >5% NaN: 0` (or <10, with the remaining ones documented and acceptable)
- `class coverage: 30/30` (full corpus should have all classes by construction)
- `rows: 6,174,593` (matches dasha_mdadpd_corpus full row count)
- `cols: ~395`

If sub-gate D.0 passes on full corpus → resume the Stage D plan at Task 7.
If it still fails → escalate to the user with the specific finding before continuing.

## What this regeneration does NOT change

- `stage_d_features.py` source code (already in place from Phase D.0)
- `tests/test_stage_d_features.py` (already in place)
- The dasha corpus itself (it's the canonical input — don't touch it)
- `natal_lord_houses.parquet` (already has 100% smoke overlap; likely also fine on full)

## Effort summary

| Step | Effort | Bottleneck |
|---|---|---|
| 1. Birth data extraction | ~30 min | I/O |
| 2. Vedic Tensor regeneration | 25 min (parallel) – 3 hr (serial) | ephemeris CPU |
| 3. Yoga features regeneration | ~30 min | CPU |
| 4. Doctrine parquet (optional) | ~1 day | scope of dasha_doctrine_score |
| 5. Re-materialize Stage D features | ~5-15 min | I/O + lookups |
| 6. Re-verify sub-gate D.0 | <5 min | I/O |
| **Total (minimal path, skip step 4)** | **~1.5-4 hours wall-clock** | CPU-bound |

## Files this regeneration produces

```
app/medini/data/
  dasha_corpus_birth_data.parquet         (NEW — step 1)
  ml_astro_features_full.parquet          (NEW — step 2)
  dasha_corpus_yogas.parquet              (NEW — step 3)
  dasha_stage_d_features.parquet          (REGENERATED — step 5)
  dasha_stage_d_features_smoke.parquet    (REGENERATED — step 5)
```

After successful regeneration, update the path constants in
`app/medini/ml/stage_d_features.py`:
- `_VEDIC_TENSOR_PARQUET = _DATA_DIR / "ml_astro_features_full.parquet"`
- `natal_path = _DATA_DIR / "dasha_corpus_yogas.parquet"` (in `add_yoga_features_with_dasha_gating`)

Commit those constant updates as a single change after step 6 passes.

## Handoff to next session

This spec is the input for whoever (human or fresh Claude session) executes
the regeneration. It's standalone — no need to re-read the original Stage D
plan unless something below is unclear. Once Step 6 passes, the implementation
plan at `docs/superpowers/plans/2026-05-24-fork-a-stage-d.md` resumes at Task 7.
