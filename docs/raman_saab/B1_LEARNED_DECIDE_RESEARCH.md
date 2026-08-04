---
title: "B1 research — can a LEARNED `_decide` beat the hand-tuned one? (2026-07-24, branch `b1-decide-research`)"
kind: analysis
topic: validation
measured: true
updated: 2026-07-24
words: 574
tags: [raman-saab, analysis, validation]
---
# B1 research — can a LEARNED `_decide` beat the hand-tuned one? (2026-07-24, branch `b1-decide-research`)

## The question

The whole thin-house investigation converged on one lever: the engine's residual misses are B1
comparative-weighing, and every *hand-coded* and *tuner-searched* attempt to improve the weighing
failed. The last open question — "the research decision" — was whether a **learned / re-derived
`_decide`** (replacing the hand-written decision clauses with a model trained on Raman's verdicts)
could beat the hand-tuned engine. This branch answers it, in isolation (it re-opens the confirmed
verdict path, so it is kept off the main line).

## The experiment (`tools/raman_saab/b1_decide_dataset.py` + scratch trainer)

For every CONFIRMED Track-B verdict (n=293; 139 favourable / 124 afflicted / 30 mixed) extract the
LEAD frame's `FrameLedger` features — the SAME inputs `house_template._decide` consumes: lord/karaka/
bhava-bala strength (tri-state, None on Track-B), navamsa status, karaka-intact / maraka-active /
parivartana / lord-karaka-identical, the benefic/malefic/neutral fired-rule COUNTS, lead-frame,
degree, and house-class (19 features). Split fit/holdout on the tuner's stable ~20% hash slice
(224 fit / 69 holdout). Train shallow trees, a random forest, gradient boosting, and logistic
regression on the FIT set; compare HOLDOUT accuracy to the hand-tuned `_decide`.

## Result: the hand-tuned `_decide` WINS decisively

| model | fit | 5-fold CV | holdout |
|---|---|---|---|
| **hand-tuned `_decide` (baseline)** | **0.911** | — | **0.841** |
| decision tree (depth 5) | 0.804 | 0.700 | 0.710 |
| random forest (best model) | 0.929 | 0.755 | 0.725 |
| gradient boosting | 0.996 | 0.750 | 0.580 |
| logistic regression | 0.688 | 0.512 | 0.551 |

**Every learned model underperforms `_decide` on the holdout by 12–29 points.** The best (random
forest) reaches 0.725 vs 0.841. Gradient boosting memorised the fit set (0.996) and collapsed on the
holdout (0.580) — the overfitting the small corpus guarantees.

## Why — and what it means

1. **The aggregate features are LOSSY vs the doctrine.** `_decide` does not see counts — it reads
   *which specific, cited doctrine rules fired* (the signification-precise decisive rules:
   H7.C.84/85/86, H5.C.38, H9.A.20a, H10.C.61, …). "2 malefics fired" collapses a decisive maraka
   rule and a mild aspect into the same number. A model over the counts cannot reconstruct that logic.
2. **The data is far too small for the rich alternative.** Giving a model the specific fired rules
   (multi-hot over ~800 rules) with only 293 examples would overfit catastrophically — the aggregate
   models already generalise only to ~0.70–0.75 (5-fold CV).
3. **Therefore the hand-tuned `_decide` + cited doctrine is NEAR-OPTIMAL for this feature/data
   regime — and it is BETTER than ML on the same inputs.** The ~89% ceiling is *not* a hand-coding
   artifact; it is the faithful limit of the current feature substrate on a non-overfit corpus. The
   interpretable tree even rediscovered `_decide`'s own factors (degree, benefic/malefic balance,
   maraka, navamsa, dusthana) — at lower accuracy.

## Conclusion / decision

**The learned-`_decide` path does NOT beat the hand-tuned engine and is not shipped.** This validates
the existing architecture and closes the research question: going beyond ~89% within a faithful,
non-overfit engine would require *richer features* (computing the effective-strength / specific
afflictions Raman weighs — which hand-coding regressed −40 and which the discriminator scan showed
are not cleanly separable) or *materially more confirmed data* — not a black-box model over the
current ledger. The branch keeps the dataset tool for reproducibility; nothing merges to the verdict
path (the research re-opened the confirmed set and found no faithful gain).
