# Accuracy push — Phase 2 recalibration: a documented NEGATIVE result

**A global recalibration cannot lift held-out accuracy without destroying the tuned/anchor
calibration. It is a bad trade and was NOT applied.** The real accuracy gain from this push is
Phase 1's verdict-map bug fix (47.1% → 52.8%); Phase 2 does not add to it honestly.

## What was tried
The forensic diagnosis found the held-out over-scoring is dominated by a *global threshold
miscalibration* (`_THRESH` ~1 grade too low) plus the optimistic planet blend (`_BLEND_W`). Phase
2 fit the two global constants — a threshold up-shift `b` and the planet blend `blend_w` — by
**leave-one-chapter-out cross-validation** across the 7 held-out houses
(`app/medini/doctrine/validation/recalibrate.py`).

## Why it fails — the anchor/tuned cost the naive sweep ignored
A sweep that looks only at held-out suggests b≈0.9 → ~63% held-out. But `_THRESH`/`_BLEND_W` are
**shared with the tuned corpora and the ch IV anchor** (the anchor harness imports the live
`_verdict_label`/`_combine`). Accounting for that cost:

| b | blend_w | held-out within-one | anchor (/8) | tuned (/104) |
|--:|--:|--|--:|--:|
| 0.0 | 0.30 | 27/52 (52%) | **8** | 81 (78%) |
| 0.1 | 0.30 | 26/52 (50%) | 6 | 83 |
| 0.3 | 0.30 | 28/52 (54%) | 5 | 80 |
| 0.5 | 0.30 | 29/52 (56%) | 5 | 73 |
| 0.9 | 0.15 | 33/52 (63%) | **2** | 70 (67%) |

**Every positive shift breaks the anchor immediately** (even b=0.1 → 8/6), and the held-out-optimal
shift collapses it to **2/8** while dropping the tuned corpora 78% → 67%. There is no shift that
buys a meaningful held-out gain at an acceptable anchor/tuned cost.

And even the in-sample held-out number is inflated: the honest **leave-one-chapter-out CV** of the
aggressive fit is **30/52 (57.7%)**, not the 63.5% in-sample — the gap is the overfitting the CV
correctly discounts.

## The real reason (the deep finding)
The thresholds were **fit to the tuned corpora**, so the tuned data is well-calibrated at b=0 and
held-out is not. The over-scoring is therefore **held-out-specific**, not a uniform global error a
single constant can absorb: the shift held-out wants is exactly the shift that pushes the (already
low-edge) anchor rows out of within-one. The tuned and held-out sets are calibrated to genuinely
different levels, and a global recalibration cannot reconcile them — it can only trade one for the
other. This corroborates, from the calibration side, the forensic finding that the residual miss
is genuine engine behaviour (the over-optimistic cross-varga rescue, missing combustion, dusthāna
under-penalty, clean-house under-score), not a labelling or threshold artifact.

## Disposition
- **Not applied.** The engine's `_THRESH`/`_BLEND_W`, the anchor (8/8), and the tuned floor
  (≥81/104) are unchanged. `recalibrate.py` is kept as a measurement tool (LOCO-CV + the frontier
  table above are reproducible via `python -m app.medini.doctrine.validation.recalibrate`).
- **Honest accuracy after the push: 52.8% held-out** (Phase 1 map fix), anchor 8/8, tuned 78% — all
  integrity gates intact.
- **The remaining gap needs structural work, not calibration:** the forensic mechanisms (cap the
  cross-varga rescue, add a combustion feature, dusthāna-malefic penalty, clean-house positive
  baseline) target the ≥3-grade rows without touching the shared thresholds — the honest next
  lever. Reaching ~70–80% additionally requires a *fresh* calibration/validation set so the
  correction is not fit to these 52 rows.
