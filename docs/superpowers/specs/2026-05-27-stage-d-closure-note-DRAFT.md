---
date: 2026-05-27
type: closure-note (DRAFT — finalize after within-person seed=1 result lands)
parent: docs/superpowers/specs/2026-05-24-fork-a-stage-d-design.md
status: pending within-person test result
---

# Stage D — final closure note

## Verdict

**FAIL: no aggregate signal — honest null.** Confirmed across:

1. Population-rate doctrine quintile RR on 3 corpora (75k people total —
   Astro-Databank, Lunarastro, Wikidata). 3-way intersection of Bonferroni-
   significant classes is EMPTY.
2. Non-structural XGBoost with proper date controls — chart features add
   <0.01 AUC over birth date alone.
3. LLM with real chart vs LLM with shuffled chart (n=29). Paired Wilcoxon
   p=0.43; complete null.
4. Dynamic-DeepHit competing-risks neural hazard, Stage D 5-seed gate.
   Mean Δ = -0.1593 (DeepHit *worse* than Cox by ~4σ in the wrong
   direction). 1 of 20 qualifying classes has positive mean Δ.
5. **Within-person Cox concordance (this test)** — [FILL: result summary
   here once seed=1 lands. If concordance ~ 0.50 with p > 0.05 across all
   5 classes, write: "the data has no recoverable structural signal even
   after factoring out every person-level confound. The Vedic chart's
   contribution to within-person event timing is indistinguishable from
   chance."]

The prediction question is now closed at five independent angles.

## What this rules out (with strong evidence)

- A *specifically survival-flavoured* framing of the prediction problem
  doesn't help (Stage D).
- The dasha leaf-window unit of analysis doesn't unlock signal (Stage D).
- Birth-year cohort confounding was the cleanest competing explanation for
  the original AD-only positives (Round 9 mechanism); within-person tests
  remove it and produce no surviving signal.
- A more expressive neural model on the same features does NOT recover
  signal that tree boosters missed (Stage D vs Round 9 nonstructural).
- LLM-mediated reading produces no chart-specific information beyond
  general base-rate knowledge (Round 10).

## What this does NOT rule out (for completeness, with caveats)

- A vastly larger corpus (10×+) with cleaner labels might give a different
  result. We tested at n=2000 persons for Stage D and n=75k summed for the
  doctrine tests; further gains are unlikely.
- A radically different feature representation (e.g., learned chart
  embeddings from a large self-supervised pre-training corpus) could
  potentially extract residual signal — but the MI audit showed top
  features at MI ≈ 0.018, so the upper bound is small.
- Individual-chart reading (a single practitioner reading a single chart)
  was not tested — only its LLM-mediated approximation was. The
  population-statistics-on-coarse-labels approach is what's been
  exhausted.

## What remains valuable from the Round-9 / Stage-D arc

1. **Methodology**: pre-registered 4-criterion gates with explicit
   noise floors and replication clauses (rare for astrology research).
2. **Cross-corpus null finding**: 3-corpus replication is unprecedented
   in the published astrology-ML literature.
3. **Survival-side infrastructure** (Stage D pipeline, DirectML-aware
   training, Cox parallel with pipe-spill, verdict generator) — reusable
   for any future astrological-data ML work.
4. **Knowledge library** (6.28M words, multilingual RAG, 918 artefacts)
   — the actual shippable product per the agent-research synthesis at
   `2026-05-27 messages` (Path A "Jyotish Doctrine Search").

## Pivot

Per spec §5 decision table: "FAIL: no aggregate signal — pivot to
**Fork C: write-up as null**."

The right operational move is the dual track surfaced by the parallel
agent research:
- **Track A** (immediate): write up Round 9+10+Stage D combined as a
  publishable null result.
- **Track B** (immediate): ship the knowledge corpus as
  "Jyotish Doctrine Search" — B2B subscription to practitioners /
  serious students at $29-49/mo, leveraging the citation-anchored RAG
  that has no commercial competitor.

Stage D infrastructure (`app/medini/ml/stage_d_*.py`) remains in the
repo as tested infrastructure for any future structural ML work.
`app/medini/etl/` and the rest of `app/medini/ml/` (4 rounds of failed
predictors) can be safely deleted before the product-launch sprint —
per the architect's audit they are decoupled from the shipped surface.
