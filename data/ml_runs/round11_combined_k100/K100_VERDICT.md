# K=100 high-resolution falsifier — Final verdict on `personal` doctrine RR

**Date**: 2026-05-28
**Test**: K=100 chart-shuffle permutation on the karaka-stripped + within-lord
stratified combined scorer (the cleanest available control).

## Headline

| Metric | K=20 (earlier) | **K=100 (now)** | Direction |
|---|---:|---:|---|
| Real combined RR | 1.721 | 1.721 | (same) |
| Shuffled null mean | 1.485 | **1.576** | ↑ closer to real |
| Shuffled null max | 2.011 | **2.343** | ↑ wider tail |
| z-score | 1.07 | **0.55** | ↓ effectively null |
| Empirical p | 0.19 | **0.307** | ↑ much further from significant |
| Shuffled ≥ real | 3/20 (15%) | **31/100 (31%)** | ↑ true exceedance now resolved |

**Verdict: The chart contributes nothing to the `personal`-event RR.**
Even with the cleanest available control (karaka-stripped score, within-lord
stratification, K=100 chart-shuffle permutation), the real RR sits only 0.55
standard deviations above where random shuffling would put it. Thirty-one
percent of random chart assignments produce RRs equal-to-or-larger than
the "real" effect.

## What changed between K=20 and K=100

The K=20 z=1.07 was a small-sample optimism. With only 20 shuffled reps:
- Standard error of the null mean is ~10% of the RR scale
- The TRUE exceedance rate (31%) appeared as a sampling-fortunate 15%
- Tail estimates (max, p99) are unreliable

At K=100:
- SE of null mean shrinks to ~4% — tight enough to localize
- The null mean rose from 1.485 to 1.576 (a 6% shift in RR units)
- The max rose from 2.011 to 2.343 — well above real
- 31 of 100 shuffles produce ≥ real RR. No way to interpret this as signal.

## Why the within-lord stratified test gave 1.58 isn't a failed control

The within-lord pooled RR=1.58 from test (b) might look like signal at first
glance. But the K=100 shuffled mean is also 1.58 (1.576). That means the
RR=1.58 baseline is **not signal** — it's the **expected value under the null
distribution** after stratification.

Why does shuffling give RR=1.58 instead of 1.00?

**Small-sample Poisson positive bias.** Each stratum has 7-19 events per
quintile. The standard RR estimator (n_top/exp_top) / (n_bot/exp_bot) has
known upward bias at small counts. The Mantel-Haenszel pooling inherits
this bias. Real and shuffled estimates BOTH inflate by the same amount.

So the right comparison is **real vs shuffled at equivalent bias**, not
real vs 1.00. That comparison gives z=0.55. Null.

## The complete sequence of tests on `personal`

| Test | Method | RR | Null mean | z | Verdict |
|---|---|---:|---:|---:|---|
| Round-11 pooled | original scorer | 2.308 | 2.250 | 0.27 | 🚫 lifecycle |
| (a) Karaka-stripped + K=20 perm | structural scorer | 1.443 | 1.469 | -0.18 | 🚫 HR/fmod leak |
| (b) Within-lord stratified | original scorer + strat | 1.577 | (no perm) | — | 🤔 ADB-only hint |
| (c) Combined + K=20 perm | structural + strat | 1.721 | 1.485 | 1.07 | 🤔 ambiguous |
| (c) Combined + K=100 perm | structural + strat | **1.721** | **1.576** | **0.55** | **🚫 NULL** |

Five tests. Three full-confidence nulls, one ambiguous, one definitive null.
The progression of z-scores: 0.27 → -0.18 → 1.07 → 0.55. The K=20 z=1.07
peak was a sampling artifact; the true z is 0.55 ± ~0.1.

## What this means

### For the `personal` doctrine claim

**Retracted entirely.** The original RR=2.31, p=7.4e-9 was lifecycle
confounding amplified by the karaka baseline mechanism. The within-ADB
within-lord chart-attributable residual is statistically indistinguishable
from chart-permutation noise at K=100. No structural astronomical signal.

### For the broader project verdict

**Round-9/10/11 broad-null verdict is now triple-confirmed.**
Across five distinct statistical methodologies (per-corpus RR, pooled
MH, karaka-stripped, within-lord stratified, K=100 permutation), no test
recovers chart-structural signal at population scale on this corpus
after appropriate lifecycle controls.

This is the strongest possible evidence-by-falsification we can produce
with the current data layout. Future ML work that asks the SAME question
("does chart structure predict event class at population scale") will
produce the same answer.

### For the BPHS doctrine

**The coarse layer is confirmed; the fine layer is unfalsifiable at scale.**
- Lord-karaka correlations (Moon ↔ personal, Venus ↔ marriage, etc.) are real
  population-level statistical patterns. BPHS's claim that "lord identity
  matters for event class" is borne out.
- The fine-grained chart-structural claims (HR, dignity, drishti effects on
  predictions) cannot be validated by population-scale RR tests. Whether
  they're real or not, this framework can't tell us.

## What's left to try

The exhausted directions:
- ❌ Population-scale per-corpus doctrine RR (Round-9)
- ❌ Cross-corpus pooled doctrine RR (Round-11 pooled)
- ❌ Karaka-stripped doctrine RR (test a)
- ❌ Within-lord stratified RR (test b)
- ❌ Combined controls + K=100 permutation (this test)

The unexplored:
1. **AD-level timing analysis** — `dasha_tree.parquet` has all the BPHS Ch.46-47
   mutual-relation features (mutual_house_distance, mutual_aspect, dispositor_
   match) but we never built a model that uses them for sub-MD event timing.
2. **Per-person sequence prediction** — instead of "does score quintile
   predict rate across cohort", test "does the score sequence predict the
   event sequence for one person." Fundamentally different statistical
   framework (per-person Bayesian or sequence model).
3. **Transit point process (Phase 6 deferred)** — natal layer is exhausted
   but transits are when astrologers say things actually fire. Untested.
4. **Deterministic doctrine reading** (the sibling `astro-reading` project) —
   pivot from validation to application. Use the now-clean data infrastructure
   to feed a BPHS-faithful reading engine.

## Files

- `data/ml_runs/round11_combined_k100/combined_test.md` — auto-generated
- `data/ml_runs/round11_combined_k100/combined_test.json` — full results
- This file — human-readable K=100 verdict
- `data/ml_runs/round11_triple_test_synthesis/SYNTHESIS.md` — pre-K=100 triple-test writeup (now superseded by this verdict)
