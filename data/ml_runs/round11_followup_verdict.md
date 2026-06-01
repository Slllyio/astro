---
date: 2026-05-27
type: round-11 follow-up verdict
parent: data/ml_runs/round11_data_architecture_refactor/RESULTS.md
companion: docs/round9_lessons_learned.md
---

# Round 11 Follow-up — 3 Experiments Converge

After the Round 11 data architecture refactor surfaced a +0.045 AUC lift
(per-person Wikidata marriage prediction with chart features over `birth_jd`
only), three follow-up experiments were dispatched in parallel to:

1. Disambiguate the lift from cyclical date encoding
2. Rerun Stage D on the corrected `event_jd - birth_jd` target
3. Pool Round 9 doctrine RR across corpora via Mantel-Haenszel

This document synthesizes their outputs into a single updated verdict.

---

## TL;DR

The +0.045 AUC lift on per-person Wikidata marriage is **not cyclical date
confound** — it survives explicit `birth_month + birth_day_of_year` controls.
Stage D's between-person delta shrunk 5× when retrained on the corrected target
(-0.16 → -0.03) but is still slightly negative, so the original "DeepHit beats
Cox" claim still fails — the model is competitive, not winning. Mantel-Haenszel
pooling confirmed the Round 9 doctrine null at higher precision and uncovered a
*directional miscalibration* in the `relationship` scorer (both ADB and LA agree
the scorer points the wrong way for this class).

**Net change to the overall verdict**: from "definitively null at 5 angles" to
**"narrow positive signal on one task + 6th null on doctrine generally, with one
calibration bug surfaced."** The corpus + chart-engine product thesis is
unchanged; the doctrine-as-prediction claim is still empirically false; the
*one* surviving signal (per-person marriage lift on WD) is narrow and not yet
extended to other classes.

---

## Experiment 1 — Disambiguation: cyclic date vs chart structure

**Question**: is the +0.045 lift from chart features just sub-year date
precision in disguise (Saturn-sign = ±2.5yr birth band, etc.) that XGBoost
can't extract from continuous `birth_jd`?

**Design**: 5 conditions on Wikidata marriage (n=32,932, person-disjoint
5-fold StratifiedKFold, seed=42, XGBoost n_est=100 depth=4 lr=0.1):

| Cond | Feature set | n_feat | Mean AUC | ± Std |
|---|---|---|---|---|
| A | birth_jd ONLY | 1 | 0.6340 | 0.0035 |
| B | birth_jd + cyclic date (month/doy/dom) | 4 | **0.6368** | 0.0047 |
| C | birth_jd + chart features | 29 | 0.6788 | 0.0045 |
| D | birth_jd + cyclic + chart features | 32 | **0.6797** | 0.0048 |
| E | cyclic date only | 3 | 0.5396 | 0.0070 |

**Decisive metric: `D - B = +0.0429 AUC`**

The cyclic-date confound hypothesis is **REJECTED**. Three supporting facts:
1. Condition B adds only +0.0028 over A — sub-year precision alone is nearly
   worthless, so there was nothing for chart features to confound with.
2. Condition E = 0.5396 — month/day/day-of-year on their own is barely above
   chance. No seasonal-marriage-documentation effect drives the lift.
3. Condition D ≈ C (0.6797 vs 0.6788) — adding cyclic date on top of chart
   features contributes essentially nothing, so chart features already capture
   whatever temporal signal exists.

**Open question**: era-specific documentation bias (within Wikidata, marriage
records may differ systematically by birth century in ways that correlate with
planet positions via birth-era proxy) remains a live alternative. The next
stage to test it is birth-century stratification + SHAP inspection.

**Files**:
- `app/medini/ml/xgboost_date_disambiguation.py`
- `tests/test_xgboost_date_disambiguation.py` (13 tests)
- `data/ml_runs/round11_disambiguation/disambiguation_v1.{md,json}`

---

## Experiment 2 — Stage D rerun on corrected `event_jd - birth_jd` target

**Question**: did the Stage D between-person verdict (Δ=-0.16) reflect a real
DeepHit failure, or was it driven by the now-known bug (regressing on
`window_duration_days` = dasha length, not time-to-event from birth)?

**Design**: new module `stage_d_dataset_v2.py` sources from
`events_with_dasha.parquet` (Round 11 Phase 2 output) and uses
`(event_jd - birth_jd)` as the duration. Same 2000-person subsample, same 5
seeds, same DML+CPU split (DeepHit on AMD Radeon, Cox on CPU).

**Mean Δ (DeepHit C-index − Cox C-index)**:

| | v1 (broken: window_duration_days) | v2 (corrected: event_jd − birth_jd) |
|---|---|---|
| Mean Δ | **−0.1593** | **−0.0317** |
| Stdev | 0.0371 | 0.0310 |

5× improvement. Per class:

| Class | v1 Δ | v2 Δ | Improvement |
|---|---:|---:|---:|
| fame | -0.270 | -0.005 | +0.265 |
| career | -0.247 | -0.038 | +0.209 |
| death_cause_unspecified | -0.180 | -0.012 | +0.168 |
| marriage | -0.124 | -0.031 | +0.093 |
| relationships | -0.118 | -0.148 | -0.031 |

**Verdict: IMPROVEMENT — but still NULL**

The bug was real and substantial. Fixing it closes 80% of the deficit. But
the model still doesn't BEAT Cox on any qualifying class — only ties it
within noise. This is the 6th independent null on this corpus, with the
honest caveat that the bug invalidates the strength of the v1 verdict (the
v1 -0.16 was misleadingly large; the true model-vs-Cox gap is small).

**Per-seed runtime dropped from ~3 hours to ~22 seconds** (v2 is person-level
2000 rows, not window-level 1.2M rows — much smaller training set).

**Files**:
- `app/medini/ml/stage_d_dataset_v2.py`
- `tests/test_stage_d_dataset_v2.py` (18 tests)
- `data/ml_runs/fork_a_stage_d_v2_corrected_target/COMPARISON.md`
- `data/ml_runs/fork_a_stage_d_v2_corrected_target/main_run.jsonl`

Architecture note: `stage_d_baseline.py` was updated to support both v1's
`md_lord` string column and v2's `md_lord_at_event` one-hot encoding (the
v2 dataset uses a different lord encoding because the join-at-event-time
table is per-event not per-window).

---

## Experiment 3 — Mantel-Haenszel pooled doctrine RR across 3 corpora

**Question**: Round 9 said "intersection of per-corpus Bonferroni passes is
EMPTY → null." But that's a naive rule. The right epidemiology question is
"is there a common underlying RR across strata?" — answered by inverse-variance-
weighted MH pooling + Cochran's Q heterogeneity test.

**Result**: 12 classes had ≥2 corpora available; 591 cross-corpus duplicate
persons dropped (ADB > WD > LA precedence); Bonferroni α = 0.01/12 = 0.000833.

5 classes pass Bonferroni on the POOLED test. But the heterogeneity audit
matters more than the p-value:

| Class | Pooled RR | p | Q_p | Verdict |
|---|---:|---:|---:|---|
| `personal` | 2.31 | 7.4e-9 | 0.129 | **GHOST STRATUM** — LA has only 11 events; ADB carries 94% of pool weight. It's the ADB-only RR=2.44 dressed up as cross-corpus. |
| `career` | 1.11 | 5.7e-4 | 3.5e-8 | **SPURIOUS** — ADB 0.93, WD 1.25, LA 0.76. Three corpora disagree in direction. Pool is meaningless. |
| `relationships` | 0.86 | 1.3e-5 | 1.4e-15 | **SPURIOUS** — ADB 2.28, WD 0.85, LA 0.48. Q_p effectively zero. Pool is meaningless. |
| `death_cause_unspecified` | 0.81 | 8.5e-11 | 0.0013 | **WD-DOMINATED** — ADB 1.02, WD 0.77. Disagreement; WD's larger n dominates. |
| `relationship` | 0.42 | 1.3e-23 | 0.004 | **CONSISTENT NEGATIVE** — both ADB (0.32) and LA (0.53) say the doctrine score predicts FEWER relationship events. Calibration bug. |

**MH pooling confirms the null at higher precision. Cochran's Q does exactly
what it's designed to do: warn that 3-of-5 "Bonferroni passes" should NOT be
pooled because the strata disagree.**

The one consistent finding is *negative*: the `relationship` doctrine scorer
is directionally inverted in both available corpora. This isn't evidence FOR
doctrine — it's evidence the doctrine scorer for this class has the wrong
sign on its house/karaka weights. Useful for calibration debugging if anyone
wants to rebuild the scorer; not useful as a prediction product.

**Files**:
- `app/medini/ml/dasha_doctrine_pooled.py` (built in Round 11)
- `data/ml_runs/round11_doctrine_pooled/pooled_rr.{md,json}`

---

## What survived and what didn't

### Survived all 3 experiments

- **Per-person Wikidata marriage XGBoost lift: +0.043 AUC over birth_jd +
  explicit cyclic date controls** (Exp 1). This is the narrowest possible
  positive claim — one task, one corpus, one event class, requires controlled
  baseline — but it's empirically real and survives the most obvious confound.

### Did NOT survive

- **DeepHit beats Cox at survival modeling** (Exp 2): still null, even after
  fixing the target bug. The model is competitive (~Δ=-0.03), not winning.
  No class shows positive Δ.
- **Doctrine RR pools across corpora when properly weighted** (Exp 3): MH
  pooling confirms the Round 9 null. Only one class shows consistent
  cross-corpus direction and it's the *wrong* direction (`relationship` scorer
  is inverted).
- **Relational R-GCN extracts more signal than flat XGBoost** (from Round 11
  proper): R-GCN MVP 0.548 vs XGBoost 0.679. Relational hypothesis falsified
  at MVP scale.

### Discovered but not yet exploited

- **The `relationship` scorer calibration bug** (Exp 3). Worth fixing if
  anyone wants to maintain the doctrine scorer as part of the corpus product,
  but doesn't change the prediction verdict.
- **Era-specific documentation bias** (Exp 1 limitation). The +0.045 lift
  could still resolve to "biographied 19th-century persons have different
  marriage documentation than 20th-century, and planet positions correlate
  with birth century." Test: birth-century-stratified XGBoost; SHAP on
  D-minus-B residuals to see which planets drive the gain.

---

## Updated overall verdict (vs `docs/round9_lessons_learned.md`)

The Round 9 lessons doc said: "5 independent angles all null; predict-question
closed; ship the corpus." Round 11 follow-ups update this to:

> **5 independent null angles still hold for population-level event-class
> prediction from doctrine scoring or survival modeling. ONE narrow positive
> signal exists: per-person binary marriage prediction on Wikidata
> (+0.043 AUC over the strongest available date control). The signal is real
> but not yet shown to be astrological (era-bias remains live). All other
> Round 9 conclusions stand. Ship the corpus.**

The +0.043 lift is *not* a basis for resurrecting the "astrology predicts
events" claim. It IS a basis for a defensible scientific note: "in our
corpus, chart features carry sub-AUC-magnitude signal for one task that
survives explicit date controls. Era-specific documentation bias is the
remaining alternative explanation. Disambiguating that requires birth-century
stratification — open question."

---

## Recommended next experiments (if any)

1. **Birth-century stratification on the +0.043 lift** (~1 hour). Run the
   disambiguation experiment separately on persons born in 1700-1799,
   1800-1899, 1900-1999. If the lift is era-specific (e.g., only present
   in one century), it's documentation bias. If consistent across eras,
   it's harder to dismiss.

2. **Extend Phase 8 to other event classes** (~30 min per class). Marriage
   showed +0.045. Does fame, career, death show similar lifts on the
   per-person task on WD? Or is marriage uniquely informative?

3. **SHAP on the (D − B) residual** (~30 min). Which planet features drive
   the +0.043 gain? If it's all Saturn + Jupiter (long-period planets =
   birth-decade proxy) → era bias. If it's Moon + Venus (short-period =
   actual chart structure) → harder to dismiss.

4. **Fix the `relationship` scorer** (~2 hours). Both ADB and LA say its
   house/karaka weights point the wrong direction. If the corpus product
   ships any doctrine-based output, this is a known bug worth a fix.

Each is cheap and falsifiable. None changes the overall verdict; they just
sharpen specific findings.

---

## Files

- `data/ml_runs/round11_followup_verdict.md` (this file)
- `data/ml_runs/round11_disambiguation/disambiguation_v1.{md,json}`
- `data/ml_runs/fork_a_stage_d_v2_corrected_target/COMPARISON.md`
- `data/ml_runs/round11_doctrine_pooled/pooled_rr.{md,json}`
- `app/medini/ml/xgboost_date_disambiguation.py`
- `app/medini/ml/stage_d_dataset_v2.py`
- `app/medini/ml/dasha_doctrine_pooled.py`
- 31 paired tests across the 3 experiments
