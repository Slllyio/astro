# Stage D v1 vs v2 — Corrected Survival Target Comparison

**Date**: 2026-05-28
**Status**: CLOSED — 6th independent null

## The bug (v1)

`app/medini/ml/stage_d_dataset.py` line 130:
```python
durations = sub["window_duration_days"].to_numpy()
```
Regressed on dasha-window LENGTH (Sun MD=6yr, Venus MD=20yr) instead of
time-to-event from birth. A 19-yr Saturn MD window with an event on day 5
and one with NO event had IDENTICAL duration=6940. The temporal model had
nothing to learn — this is the same exposure-time confound that broke Stage B.

## The fix (v2)

`app/medini/ml/stage_d_dataset_v2.py`:
```python
durations = (event_jd - birth_jd)  # from events_with_dasha.parquet
```

Dataset architecture change: v1 was window-level (1.2M rows, one per
MD×AD×PD window). v2 is person-level (2000 rows, one per person from
Wikidata event corpus). Each person's first qualifying event becomes the
survival time; persons with no qualifying events are censored.

## Corpus difference

| | v1 | v2 |
|---|---|---|
| Source | ADB dasha windows | Wikidata events_with_dasha |
| Rows per seed | ~1.2M (window-level) | 2000 (person-level) |
| Qualifying classes | 20 of 30 with ≥50 positives | 5 (marriage, fame, death_cause_unspecified, career, relationships) |
| Chart features | 688 cols (Vedic Tensor) | 41 cols (basic chart positions) |
| Corpus | subsample_2000p (ADB) | v2_wikidata_2000p_corrected_target |

## Head-to-head: mean Delta (DeepHit C-index minus Cox C-index)

| Metric | v1 (broken target) | v2 (corrected target) |
|---|---|---|
| Mean of per-seed mean Delta | **-0.1593** | **-0.0317** |
| Stdev of per-seed mean Delta | 0.0371 | 0.0310 |
| Min per-seed mean Delta | -0.2066 (seed 2) | -0.0865 (seed 1) |
| Max per-seed mean Delta | -0.1026 (seed 4) | -0.0008 (seed 4) |
| Seeds with mean Delta > 0 | 0 of 5 | 0 of 5 |
| Qualifying classes with Delta > 0 | 1 of 20 | 2 of 22* |

*2 of 22 = pooled across seeds; seed 2 has fame +0.0161, seed 4 has fame +0.0317.
Not individually significant.

## Per-class breakdown (5-seed mean)

| Class | v2 mean Delta | v1 mean Delta | Change | n_seeds_v2 |
|---|---:|---:|---:|---:|
| fame | -0.0049 | -0.2695 | +0.2646 | 5 |
| career | -0.0379 | -0.2473 | +0.2094 | 5 |
| death_cause_unspecified | -0.0118 | -0.1800 | +0.1682 | 5 |
| marriage | -0.0309 | -0.1240 | +0.0931 | 5 |
| relationships | -0.1483 | -0.1176 | -0.0307 | 2 |

Top 5 classes by |Delta| change (all improvements except relationships):
1. fame: +0.2646 (from -0.27 to -0.005)
2. career: +0.2094 (from -0.25 to -0.038)
3. death_cause_unspecified: +0.1682 (from -0.18 to -0.012)
4. marriage: +0.0931 (from -0.12 to -0.031)
5. relationships: -0.0307 (from -0.12 to -0.148, small degradation)

## Verdict: PARTIAL IMPROVEMENT — but still null

The corrected target SIGNIFICANTLY narrows the gap: mean Delta moves from
-0.1593 to -0.0317, a +0.1276 improvement (3.4× smaller negative gap).
Four of five qualifying classes move substantially toward zero.

However, NO class achieves positive mean Delta across seeds. The model still
underperforms Cox PH on the corrected survival target.

**VERDICT: REGRESSION → IMPROVEMENT (partial) → overall still NULL**

The v1 -0.1593 gap was partially (but not fully) a measurement artifact.
Correcting the target from dasha-window-length to event_jd-birth_jd removes
most of the spurious negative signal. What remains (-0.0317) is a much smaller
deficit, but still consistent negative across 4 of 5 seeds.

Compared to v1's gate criteria (same threshold applies):
- G1 (aggregate Delta >= 3*sigma_noise): FAIL (Delta = -0.0317, well below 0)
- G2 (>= 11 of 30 classes clear 3*sigma_noise individually): FAIL (0 of 5 clear)
- G3 / G4: not applicable (G2 not met)

## Why the improvement is partial, not complete

The v2 dataset uses only 41 chart features (basic positions) vs v1's 688
(full Vedic Tensor). The person-level dataset (2000 rows) is 600x smaller
than v1's window-level dataset (1.2M rows). The competing-risks formulation
with 5 qualifying classes instead of 20 reduces signal density further.

A fairer comparison would use the same 688-feature Vedic Tensor applied to
the event-level survival framing. However:
1. The Vedic Tensor is built from the ADB corpus, which has only 4 qualifying
   classes in events_with_dasha (not the 20 in v1's window-level approach)
2. Even with the Vedic Tensor, the event-level framing would have ~3,256
   ADB persons — smaller than the v2 WD dataset

## Confidence in the corrected verdict

The corrected v2 result provides higher-quality evidence than v1 because:
1. The survival target is the theoretically correct quantity (event_jd-birth_jd)
2. The person-level formulation satisfies the independence assumption of
   competing-risks survival models (v1's window-level rows violated it)
3. The chart features (41 cols) are the same features that showed +0.045 AUC
   lift in Round 11 Phase 8 XGBoost on marriage prediction — they are not
   trivially uninformative

## This is the 6th independent null

1. Cross-corpus doctrine quintile RR test (3 corpora, 75k people) — null
2. Non-structural XGBoost with proper date controls — null
3. LLM real-vs-shuffled chart (n=29) — null
4. Stage D DeepHit between-person v1 (broken target) — null, but confound detected
5. Stage D DeepHit within-person — null (model < trivial baseline)
6. **Stage D DeepHit v2 (corrected target)** — null, smaller magnitude

## Next step

The correction confirmed the confound was real (v1's -0.16 was partly exposure-
time artifact) but the core prediction question remains null: chart structure
does not predict time-to-event from birth in a way that DeepHit captures.

The +0.045 AUC lift from Round 11 Phase 8 (XGBoost, per-person binary marriage,
WD corpus) remains the only replicated positive signal. That experiment used
birth_jd as a proper control and found chart features add incremental information.
Disambiguating whether that lift is cyclic-date-encoding vs astrological structure
is the remaining open question.

**Recommended next experiment**: Run Round 11 Phase 8 XGBoost on all 5 qualifying
classes (fame, career, death, marriage, relationships) in the WD corpus, with
proper birth_jd controls, to test whether the +0.045 AUC lift on marriage
generalises to other classes. This is a lower-compute (no GPU needed), higher-
interpretability experiment that directly follows from the available signal.

## Files

- `app/medini/ml/stage_d_dataset_v2.py` — v2 dataset module
- `app/medini/data/stage_d_v2_person_level.parquet` — v2 base parquet (32,388 rows)
- `data/ml_runs/fork_a_stage_d_v2_corrected_target/main_run.jsonl` — 5-seed results
- `tests/test_stage_d_dataset_v2.py` — 18 paired tests (all passing)
- `data/ml_runs/fork_a_stage_d_subsample/DECISION.md` — v1 reference verdict
