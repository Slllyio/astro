# Sub-gate D.2 — DeepHit model verification on smoke

**Date**: 2026-05-25 · **Commit**: post-`85b9f4a`

## Result: **PASS**

```
Dataset: 3006 rows × 617 features (5-person slim slice of smoke parquet)
Model:   StageDModel(n_features=617, hidden=256, k_bins=50) → 1,471,965 params
Forward: pmf shape (32, 1501), row sums ≈ 1.0 ✓
Loss:    3.7952 (finite; log(1501)≈7.3 is uniform-PMF ceiling)
Backward: total grad norm 8.07 (non-zero; gradients flow cleanly)
```

All four sub-gate D.2 criteria satisfied:
- ✓ Forward pass shape correct (PMF over 30×50+1 = 1501 cells)
- ✓ Loss finite on real data
- ✓ Backward pass produces non-zero gradients
- ✓ Save/load round-trip bit-identical (verified by test_round_trip_identical in commit 85b9f4a)

## Note on `n_features`

The actual smoke parquet exposes **617 numeric feature columns** after the deny list filter, vs the spec's ~250 estimate. The extra columns come from the rebuilt full-coverage Vedic Tensor (`ml_astro_features_full.parquet`, 530 cols vs the legacy 199). Parameter count grew accordingly (1.47M vs spec's 1.3M estimate) — modest, no architectural concern.

## Next

Phase D.3 — `stage_d_preflight.py` (5 mandatory checks) + `stage_d_train.py` (single-seed driver).
