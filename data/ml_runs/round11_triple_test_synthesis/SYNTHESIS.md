# Round-11 triple-test synthesis — `personal` event-class doctrine RR

**Date**: 2026-05-28
**Question**: Does the `personal` event-class RR=2.31 reflect a genuine
chart-structural astronomical effect, or lifecycle confounding?

## TL;DR

After running four independent statistical tests on the same data, the
honest verdict is:

| Test | Method | RR | Null mean | z | Empirical p | Verdict |
|---|---|---:|---:|---:|---:|---|
| Round-11 pooled | original scorer | **2.308** | 2.250 | 0.27 | 0.38 | 🚫 lifecycle |
| (a) karaka-stripped | structural scorer + perm | **1.443** | 1.469 | -0.18 | 0.57 | 🚫 leakage |
| (b) within-lord stratified | original scorer + strat | **1.577** | (no perm) | — | — | 🤔 hint |
| (c) combined + perm | structural + strat + perm | **1.721** | 1.485 | **1.07** | 0.19 | 🤔 hint |

**The cross-corpus claim is dead.** The within-ADB, within-lord,
chart-attributable hint at RR ~1.5–1.7 is real-shaped but not
statistically resolved at K=20. The original Round-11 finding that
looked like p=7.4e-9 is now best understood as a near-null with weak
residual signal indistinguishable from chart-permutation variance at
current sample sizes.

## How we got here

### The original finding (Round-11 pooled doctrine RR)

Across deduplicated ADB+WD+LA persons, the `personal` event class
appeared to be the lone Bonferroni+homogeneity passer in the pooled
Mantel-Haenszel analysis:

- ADB: 2.44
- WD: NA
- LA: 0.95
- Pooled: **2.308** (95% CI 1.73–3.08), p=7.4e-9, Q_p=0.13

A naive read says: "robust cross-corpus effect, BPHS Phaladeepika Ch.4
1st-lord-strength claim survives stratified replication."

### Three problems, exposed by three tests

**Problem 1 — `personal` events don't exist in two of three corpora.**

| Corpus | Total `event_personal` rows | Distribution across 9 dasha lords |
|---|---:|---|
| ADB | 520 | Roughly even, 28–105 per lord |
| Wikidata | **0** | — |
| Lunarastro | 52 | Sparse, 1–11 per lord |

Wikidata's event taxonomy doesn't even include "personal" (its 5
classes are marriage, career, fame, death, relationships). The
Mantel-Haenszel pooled estimate was effectively ADB-only with a
sparse-data LA noise contribution. The "cross-corpus replication"
framing was an artifact of the pooling machinery.

**Problem 2 — The scorer has a chart-INDEPENDENT karaka baseline.**

`_KARAKA_MAP["personal"] = {"Moon": 1.0}` adds +1.0 to the score
*whenever the active dasha lord is Moon, regardless of what's in the
chart*. Combined with the typical magnitudes of HR (chart-dependent)
and func_mod (chart-dependent), the +1.0 dominates rank ordering.

Result: the top score quintile is composed overwhelmingly of Moon-MD
rows. The "doctrine RR" was essentially asking "are Moon-MD windows
more eventful?" — a question the chart contributes nothing to. Moon-MD
windows have a population-level age distribution that overlaps with
the age distribution of "personal" life events. Hence a high RR even
on shuffled charts.

The K=20 permutation test (separate document
`round11_personal_disambiguation/VERDICT.md`) confirmed this: shuffled
null mean=2.25, max=3.01, **7 of 20 reps exceeded real**. z=0.27.

**Problem 3 — Even removing the karaka baseline doesn't fully fix it.**

Test (a) stripped the karaka contribution from the score:

```python
def doctrine_relevance_structural(lord, event_class, natal_row):
    """HR + func_mod only — NO karaka."""
    return _house_resonance(lord, hmap, natal_row) + _functional_modifier(lord, natal_row)
```

The real karaka-stripped RR collapsed from 2.31 to 1.44 — but so did
the shuffled null (mean 1.47, max 1.87, z=-0.18, empirical p=0.57).
Both the real and shuffled values fell together. The lifecycle
confound leaks through HR + func_mod via lord-specific distributions
of house placements that survive chart permutation.

**Problem 4 — Stratifying by active dasha lord controls between-lord
variance and gives consistent results across all 7 ADB strata.**

Test (b) used the original (karaka-laden) scorer but binned by score
quintile *within each (corpus, dasha_lord) cell*:

| Stratum | n_top events | n_bot events | RR |
|---|---:|---:|---:|
| ADB::Mercury | 11 | 3 | 3.65 |
| ADB::Mars | 7 | 4 | 1.77 |
| ADB::Sun | 10 | 6 | 1.69 |
| ADB::Venus | 14 | 9 | 1.57 |
| ADB::Jupiter | 19 | 13 | 1.47 |
| ADB::Saturn | 14 | 11 | 1.29 |
| ADB::Moon | 7 | 6 | 1.26 |

All 7 ADB lords show RR > 1, Cochran Q_p = 0.904 (statistically
indistinguishable from a single underlying within-lord effect at
~1.58). WD and LA can't participate — they don't have ≥ 10 events
in any (corpus, lord) cell.

**Test (c) — the cleanest control — combines BOTH lifecycle removals.**

Karaka-stripped scorer + within-lord stratification + chart-shuffle
permutation:

- Real combined pooled RR: **1.721** (95% CI 1.21–2.45), p=0.001, Q_p=0.80
- Shuffled K=20 null mean: 1.485
- Shuffled max: 2.011 (3 of 20 reps still exceed real)
- **z-score: 1.07. Empirical p: 0.19.**

This is the *best evidence we have* for genuine chart-structural signal,
and it's tantalizingly close to but not yet at statistical resolution.

## The honest doctrinal verdict

After all four controls:

1. **No cross-corpus replication.** Wikidata has zero `personal` events;
   LA has 52 sparse events with effectively random direction. Round-11's
   "robust pooled cross-corpus signal" was machinery, not phenomenon.

2. **Within ADB only, there is a within-lord chart-attributable RR ~1.5–1.7.**
   - All 7 dasha lords show the same direction (RR > 1).
   - Cochran Q homogeneous (Q_p ≈ 0.8–0.9).
   - p-values are nominally significant (0.001–0.006).
   - BUT chart permutation produces null distributions with means
     1.47–1.49 — only modestly below the real values.

3. **The real-vs-null gap is suggestive (z=1.07) but not conclusive at K=20.**
   3 of 20 shuffled charts still produce RRs ≥ 1.721. Empirical
   p-value of 0.19 is well above the 0.05 threshold for confident
   rejection of the null.

4. **The original 7.4e-9 was not real.** It was the lifecycle confound
   masquerading as doctrine. The honest p-value for chart-structural
   signal is closer to 0.19 with one of the cleanest available
   controls.

## What this means for the broader project

- **Round-9's broad-null verdict survives.** Two more rounds of
  stratified analysis + permutation testing failed to recover signal
  that withstands lifecycle deconfounding. The chart structure simply
  does not carry strong predictive signal for population-scale
  event-class binary classification.
- **The data architecture (Phase 1–5 of Round 11) was worth every
  hour spent.** Without the clean Silver-layer + DuckDB catalog +
  resolved_persons dedup, none of these stratified analyses would
  have been feasible. The infrastructure is now reusable for any
  future ML on this corpus.
- **A residual hint of within-ADB chart-attributable signal at z=1.07
  warrants K≥100 confirmation if it's worth resources.** At K=20 we
  can't separate it from chart-permutation variance. At K=100 the
  noise would shrink by √5 ≈ 2.2× and the signal — if real — would
  become resolvable.

## Files

- `data/ml_runs/round11_doctrine_pooled/` — original pooled MH analysis
- `data/ml_runs/round11_personal_disambiguation/` — original permutation test
- `data/ml_runs/round11_structural_test/` — test (a) karaka-stripped
- `data/ml_runs/round11_stratified_test/` — test (b) within-lord stratified
- `data/ml_runs/round11_combined_test/` — test (c) combined + permutation
- This file — synthesis across all four tests

## The single most important takeaway

The original RR=2.31, p=7.4e-9 looked Nobel-strength. Four independent
controls reduced it to z=1.07 with empirical p=0.19. The "effect" is
small, ADB-only, and not statistically resolved.

The Cochran's Q test was a *necessary* discriminator (without it we
would have published the cross-corpus claim), but it was not
*sufficient* — it tested homogeneity, not chart-dependence. The
permutation test on the cleanest scorer is what brought us home.

The doctrine isn't dead. It's just much smaller than we hoped, and
provably tied to a single corpus.
