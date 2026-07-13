# Increment 33 — identity-preserving learned scorer: the ML/representation lever, a decisive negative

## The question
Every feature-side lever is a documented negative (Gates C/F, structural tokens incr. 30, the mid-slice
threshold trade incr. 32); the ROOT_CAUSE_ANALYSIS reframed the ceiling as an **aggregation collapse** —
the additive scalar (and every gate over it) discards *identity* (which criterion, which placement, which
aspect-source nature), and of 37 verdict-pairs Raman separates by ≥2 grades **on the same additive score,
36 differ in structured features the engine already computes** but sums away. The A2 experiment
(`learned_combine`) tried a learned model, but at the "aggregation altitude" — each finding collapsed to a
`(delta, frame)` token, still identity-blind — and it failed the anchor gate (0/8), which it attributed to
the anchor being sourced from the OLD typed audit vocabulary.

The user chose to **try a richer model**. Increment 33 tests the one representation never tried:
**identity-preserving features**, and removes A2's fatal flaw by collecting *every* corpus (held-out, NH,
AND the live ch. IV anchor) through the same `judge_house_doctrine` path, so the featurizer is uniform.
The identity vector **strictly nests** A2's aggregates (sum_pos/neg per frame, extremes, counts, is_bhava),
so any gain over A2 is attributable to identity, not to a different model family. Harness:
`app/medini/doctrine/validation/identity_scorer.py` (measurement only, engine untouched).

## The representation
Per factor, from the same live `Finding` objects, for each frame (Rāśi / Navāṁśa): net signed count per
criterion (all 10: dignity/placement/lordship/aspect/conjunction/kartari/vargottama/combustion/ashtakavarga/
sutra), negative-multiplicity counts for the affliction criteria, aspect/conjunction **source-nature**
counts (yogakāraka / malefic / benefic — the closed tag vocabulary), the `synthesis_v2` reduction (tier,
besieged, fort), the SAV bindu-vs-average difference, plus A2's 9 aggregates. 50 features total.

## Result — identity does NOT beat aggregation, and overfits more (N held-out 57, NH 73, anchor 9)

LOCO-CV within-one over the 7 held-out chapters (identity vs A2 tokens, **same folds**; gap = train − test):

| model | best LOCO within-one | overfit gap |
|---|---|---|
| **A2 token** ordinal L2=4.0 | **61.4%** | **+3.2** (generalizes) |
| A2 token ordinal L2≤2.0 | 57.9–59.6% | +9.5 … +13.3 |
| **identity** ordinal L2=4.0 | **57.9%** | +9.1 |
| identity ordinal L2≤2.0 | 50.9–52.6% | +18.9 … +22.8 |
| identity / A2 tree d2–d3 | 45.6–52.6% | +12 … +23 |

Live synthesis_v2 baseline on these rows: held-out **58.6%** (pinned), NH **47.9%** (pinned), anchor **2/9**.

- **The richer representation loses:** best identity **57.9%** < best A2 **61.4%** < it also fails to clear
  the live engine's 58.6%. Adding identity did not separate the pairs — it *hurt* generalization.
- **The overfit signal is unambiguous:** every identity config carries a larger train−test gap than the
  matching A2 config (identity ordinal-L2=4.0 gap +9.1 vs A2 +3.2; the depth-3 trees blow out to +23).
  More expressive representation + ~130 rows = worse generalization — textbook bias/variance.
- **Anchor GATE FAILS:** the full-fit identity model scores **0/9** within-one on the live anchor (engine
  **2/9**) — the same collapse A2 hit, now on the *uniform* representation, so it is NOT a vocabulary
  artifact: a model fit to 130 held-out points simply does not reproduce the strong-lagna anchor factors.

## Verdict — documented negative; the ML/representation lever is closed

The root-cause analysis was correct that Raman's separated pairs *differ in identity features* — but that
signal is **not learnable** from this corpus: at N≈130 a model expressive enough to read identity overfits
and generalizes worse than the lower-dimensional aggregate model, and neither learned model reproduces the
anchor. The decisive comparison (identity **57.9%** vs A2 **61.4%** vs engine **58.6%**, identity anchor
**0/9**) says plainly: **no learned scorer over the sign/degree Finding vocabulary beats the doctrine-gated
engine while holding the anchor.** The ceiling is holistic *and* data-bound, bounded by Raman's own
~1-grade self-consistency (a blinded frontier LLM matched the engine only at ~47%).

A quiet affirmation falls out of it: the a-priori **doctrine gates** (synthesis_v2) generalize to the
anchor where *both* fitted models fail (0/9 and 0/8) — encoding Raman's structure beats fitting 130 points.
No engine change lands; pinned by `tests/doctrine/test_identity_scorer.py`. Reproduce:
`PYTHONPATH=. python3 -m app.medini.doctrine.validation.identity_scorer`.
