# Round-11 follow-up — Verdict: `personal` doctrine RR is a lifecycle artifact

**Date**: 2026-05-27
**Test**: K=20 permutation of natal chart features within each corpus, keeping
events / ages / dasha windows / dasha-lord-identity intact.

## Headline

| Quantity | Value |
|---|---|
| Real pooled `personal` RR | **2.308** (95% CI 1.73–3.08) |
| Real pooled p-value | **7.37e-9** (looked Nobel-strength) |
| Shuffled-chart null mean | 2.250 |
| Shuffled-chart null max | 3.010 |
| Shuffled reps ≥ real | **7 / 20 (35%)** |
| Empirical p-value | 0.381 |
| z-score (real vs null) | 0.27 |

**The chart is not load-bearing.** Scrambling natal planets across persons
gives the same answer.

## The mechanism

The s6 scorer for `personal` events is:

```
mix_score(L, "personal", chart) = relevance(L, "personal", chart) × dignity_strength(L, sign)

relevance(L, "personal", chart) = HR(L, chart)   ← chart-dependent
                                + KR(L)          ← chart-INDEPENDENT
                                + func_mod(L)    ← chart-dependent
```

Critically, the karaka contribution `KR(L, "personal")` is:

```python
_KARAKA_MAP["personal"] = {"Moon": 1.0}
```

This adds **+1.0 to the score whenever the active dasha lord is Moon —
regardless of what's in the chart.**

Combined with the typical magnitudes of HR and func_mod (both bounded by
a couple of points), the +1.0 karaka contribution is enough to dominate
the rank ordering. Result: the top score quintile is composed
overwhelmingly of *Moon-MD windows*, no matter whose chart you paired
with whose name.

## Why the lifecycle effect survives shuffling

1. Moon-MD lasts 10 years and is part of every person's Vimshottari cycle.
2. *Within a population*, Moon-MD windows cluster at characteristic age
   bands (depending on each person's natal nakshatra, but with
   population-level structure).
3. Documented "personal" events (health, identity, self-directed
   milestones) have their own age distribution.
4. The overlap between (2) and (3) produces RR ≈ 2.2 with random charts
   just as well as with real charts.

The "doctrine score" was essentially a fancy proxy for "is this row's
active dasha lord Moon?" — a question the chart contributes nothing to.

## What this overturns

- **Round-9 Stage F-6 `personal` ADB result** (RR=2.44, Bonferroni
  PASS) — same mechanism applies; the ADB-only signal is also
  lifecycle artifact.
- **Round-11 pooled `personal` finding** (this folder's parent
  analysis, claiming cross-corpus replicated structural effect) —
  retracted.

The Round-9 broad-null verdict ("no chart-structural signal robustly
reproducible across corpora") is **strengthened**, not weakened. The
one positive we thought we had recovered turns out to be the same
lifecycle confound that the broader null was already implicitly
flagging.

## What this implies for the s5 / s6 / s8_3 framework

Every per-class entry in `_KARAKA_MAP` injects a chart-independent
+1.0 to the score for the specified karaka lord(s). For any scorer
where that contribution is non-trivial relative to HR / func_mod, the
top-quintile binning is partially or fully determined by which lord
is active — not by chart structure.

A genuine doctrine-test framework would need to **strip the karaka
baseline** and bin only on the chart-dependent component:

```python
def _structural_score(lord, event_class, natal_row):
    """Chart-dependent component ONLY."""
    return doctrine_relevance_HR_only(lord, event_class, natal_row) * \
           dignity_strength(lord, natal_row.get(f"sign_{lord.lower()}"))
```

Or alternatively, stratify the RR by dasha lord: ask "*within Moon-MD
windows*, does the score predict events?" — which removes the
between-lord age confound by construction.

## Files

- `permutation_test.md` — auto-generated markdown summary
- `permutation_test.json` — full results including all 20 shuffled RRs
- This file — the human-readable verdict

## Bottom line

The Round-11 pooled analysis is methodologically clean (Mantel-Haenszel,
Cochran's Q, birth_jd dedup). The bug isn't in the pooling; it's in the
scoring function the pooling was applied to. The Cochran's Q said "all
corpora agree on this signal"; the permutation test says "they agree
because the signal doesn't depend on the chart in the first place."

Both tests are correct. Together they tell the right story.
