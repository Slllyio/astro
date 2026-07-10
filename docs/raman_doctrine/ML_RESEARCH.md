# ML & AI for astrological pattern-finding — research report + roadmap

**Status: Stage-1 checkpoint (2026-07-10).** A2 complete; pilot A1 at 139/167 (slice re-run
pending); literature section pending adversarial verification (the deep-research verification
pass died on a session token limit and resumes from cache). Every internal number traces to a
banked artifact under `validation/ml_research/` or a live validator.

## The question, split honestly in two

"Astrology is pattern identification — can ML help?" Our validation record splits that into two
problems with opposite evidence, and they must never be conflated:

- **Track A — the doctrine's patterns.** Does Raman's judgment compute a learnable function?
  Here there IS supervised signal: the engine reproduces his mahādaśā verdicts 94% (N=50) and
  daśā balance 93% (N=30), but his 9-grade strength judgment plateaued at ~53% within-one
  across eight landed increments and six documented negatives ([VALIDATION_SUMMARY](VALIDATION_SUMMARY.md)).
- **Track B — reality's patterns.** Do charts predict real outcomes? Five pre-registered
  population runs (N up to 82,589) were null; run 5's dissociation — held-out PASS on Raman's
  own casebook, exact chance on 2,091 real deaths — showed the doctrine's coherence is internal.

## What 12 rounds of in-repo ML already established (do not re-run)

The repo carries a 12-round ML history (`NOTES_round6_phases.md`, `docs/round9_lessons_learned.md`,
`data/ml_runs/`). The arc: Rounds 5–7 produced many in-sample, single-corpus positives (Cox
survival +0.13 C-index; contrastive embeddings 0.738 held-out Jaccard; DML causal audit of 154
BPHS rules → 11 validated / 12 *reversed*; Vedic-beats-Western +0.113 AUC). Rounds 9–11 applied
the controls — birth-date/era proxies, exposure time, 3-corpus replication, K=100 permutation —
and collapsed nearly all of it: Stage-D DeepHit null 3× (loses to a duration-only baseline),
R-GCN relational hypothesis falsified (0.548 vs flat XGBoost 0.679), the `personal`-daśā RR 2.31
retracted (chart-independent Moon term; K=100 p=0.307), AD-level timing null, karaka-MoE −0.10,
LLM real-vs-shuffled null (n=29, p=0.43). **Exactly two positives survived, both fragile:**

1. per-person marriage XGBoost **+0.043 AUC** over birth-date+cyclic controls (n=32,932,
   replicated; era-documentation-bias alternative never tested);
2. framework Career→10H strong-verdict **lift 1.37** (N=11,753; no multiple-testing correction).

**Exclusion list** (refuted with recorded nulls — not re-proposed): DeepHit/Stage-D variants,
R-GCN/GNN chart encoders, karaka-MoE, AD-level timing scores, `personal`-RR variants,
cross-corpus doctrine quintile RR, non-structural XGBoost windows, LLM real-vs-shuffled.

## NEW — Track A experiment 1 (A2): the learned combine. Synthesis hypothesis CONFIRMED.

The ceiling diagnostic and the degree engine (increment 14) converged on one diagnosis: the
bottleneck is **synthesis, not features** — `_combine`/`_THRESH` aggregate findings as a blended
checklist where Raman applies gate-like overrides. A2 tested exactly that: keep the engine's
feature extraction byte-identical, replace only the aggregation with small interpretable models
(proportional-odds ordinal logistic; depth≤3 decision tree) over (delta, frame) finding tokens +
the engine's own aggregates. Harness: `app/medini/doctrine/validation/learned_combine.py`;
results: [`validation/ml_research/a2_learned_combine.json`](validation/ml_research/a2_learned_combine.json).

| protocol | learned combine | live engine, same rows |
|---|---|---|
| LOCO-CV over the 7 held-out chapters (N=52) | **63.5%** within-one | 51.9% |
| NH degree pool, single-shot (N=32, in no fold) | **62.5%** | 46.9% |
| tuned-corpora-only training (robustness) | 61.5% / 50.0% | — |

**The residual above the engine's ceiling is learnable** — +11.6 points under the same LOCO
discipline the Phase-2 recalibration used, +15.6 on a pool the model never trained on. And the
learned gates are legible: the depth-3 tree's root split is `sum_neg_rasi ≤ −1.22 → afflicted`
regardless of positional credits (unless positives pile past 3.5) — the "besieged factor is
broken" override a linear checklist cannot express
([tree rules](validation/ml_research/a2_tree_rules.json)).

**Why it is NOT landed:** the pre-registered ch. IV anchor gate failed (ordinal 2/8, tree 1/8
within-one), so per protocol the model is rejected as an engine change. The failure is
confounded: the anchor exists only in the audit's old *typed*-finding vocabulary while the model
trains on live engine findings — a representation shift, not necessarily a true regression.
**Landing path:** grid-extract the ch. IV anchor charts so the anchor can be scored in engine
representation; if the gate then passes, landing the learned combine becomes a reviewed
increment with the drift-guard renumbered.

## NEW — Track A experiment 2 (A1): the blinded LLM-as-scorer pilot (139/167 graded)

Can a frontier LLM's *holistic* reading beat the engine? Design
(`app/medini/doctrine/validation/llm_scorer_pilot.py`, artifacts under
[`validation/ml_research/llm_pilot/`](validation/ml_research/llm_pilot/)): all 85 held-out
strength rows (53 sign + 32 NH degree) rendered as fully blinded prompts — structure only, no
names/dates/book markers (the audit hard-fails on any leak; it caught the prompt template itself
naming the method's author) — plus one **perturbed twin** per row: a planet moved such that the
judged factor's engine-finding multiset is unchanged, so the structural question is identical
but the chart matches no published nativity. The real-vs-twin gap is the memorization detector.
Zero-shot, opaque ids, graded on the same 9-grade lattice as the validators.

Partial result (139/167; slice 4 lost to the token limit, re-run pending):

| | within-one | mean Δ |
|---|---|---|
| LLM zero-shot, real rows (n=70) | 47.1% | +1.11 |
| LLM zero-shot, perturbed twins (n=69) | 47.8% | +1.20 |
| live engine on the same real rows | **52.9%** | +0.59 |

Three findings, stable enough at n=139 to state:
- **The LLM does not beat the engine** zero-shot, and it over-credits harder (+1.11 vs +0.59) —
  the same positive bias Raman's engine had to be beaten out of by increments.
- **No contamination detected**: the real-vs-twin gap is −0.7pp ≈ 0. The blinding + twin design
  worked; the LLM's score reflects reasoning over the blinded structure, not book recall.
- It reads **degree charts better than sign grids** (57.7% vs 40.9%) — plausibly because
  longitudes let it compute what the grids leave implicit.

Taken together with A2, the story is coherent and important: **the residual is learnable, but by
fitting Raman's specific weighing — not by generic astrological expertise.** A tiny model trained
on 52 of his verdicts outperforms both his own hand-decoded rule set and a frontier LLM.

## Literature (extracted; verification pass pending — labels UNVERIFIED)

The deep-research sweep extracted these claims with sources before its adversarial-verification
phase was cut off by the session limit; it resumes from cache (`wf_26461ec4-be0`). Until then
each claim is **unverified** and stated with its source:

- **Carlson 1985 (Nature 318:419)** — double-blind chart-to-CPI matching; 28 vetted astrologers
  chose correctly 0.34 ± 0.044 vs chance 1/3, 3.3σ below their own predicted 0.5 floor;
  falsification criteria fixed in advance. The canonical pre-registered null.
- **Dean & Kelly 2003 time-twins** — 2,101 persons born in London 3–9 Mar 1958 (mean 4.8 min
  apart), 110 variables at ages 11/16/23: effect size 0.00 ± 0.03. The largest population-scale
  natal-similarity null; the direct parallel to our N=82,589 nulls.
- **McGrew & McFall 1990** — six expert astrologers matching 23 charts to full case files:
  median 1 correct (chance), and **pairwise inter-astrologer agreement itself at chance** —
  each astrologer applies an idiosyncratic weighting system.
- **Meta-analytic baselines** (astrology-and-science.com compilations): ~40 chart-matching
  studies, mean effect 0.051 (p=0.66) with publication-bias indications; inter-astrologer
  agreement across 25 studies ≈ 0.101.
- **Gauquelin Mars effect** — the one long-contested positive; skeptic-organized replications
  negative/contested; Dean's documentation-bias account (era birth-reporting practices) is the
  live mundane explanation — the same confound class as our marriage-XGBoost survivor.
- **Published ML-astrology studies** are thin and weak: chance-level results on synthetic data,
  an explicit April-Fools parody, and an IEEE paper whose headline 88.76% dissolves under its
  SMOTE/evaluation choices. No credible ML positive exists in the published record.

Two of these bear directly on our results. The inter-astrologer-agreement-at-chance findings
recast Track A: **expert astrological judgment is idiosyncratic, so "learning the doctrine" is
only coherent per-expert** — exactly what A2 shows (Raman-specific weighing is learnable) and
what A1 shows (a generic expert prior does not transfer to Raman's grades). And Dean's
documentation-bias account of the Mars effect is the template for B1's kill protocol.

## Roadmap (ranked; each pre-registered with a kill criterion)

| # | experiment | data | protocol | status |
|---|---|---|---|---|
| A1′ | finish the pilot (slice 4, 28 prompts) | on disk | same blinded design | pending token reset |
| A2′ | anchor re-derivation → landing decision | ch. IV grids (extract) | gate re-run in engine representation; land only if 9/9 | next increment |
| A3 | symbolic regression / program synthesis over chart primitives | tuned+held-out | discovered rule admitted only if it matches a sutra | after A2′ |
| B1 | kill-or-confirm marriage XGBoost (+0.043 AUC) | holos/parquet rebuild via ETL | permutation null shuffling charts **within birth-decade × region cohorts** (outer planets encode era) | needs data rebuild |
| B2 | kill-or-confirm Career→10H (lift 1.37) | parquet rebuild | BH-FDR across the full house×verdict×class family + K=100 label permutation + corpus split | needs data rebuild |
| B3 | daśā-lord survival covariates | dasha_windows rebuild | Cox vs the duration/age baselines that beat DeepHit; doctrine-grounded hypothesis from the 94% timing result; pre-declared kill | after B1/B2 |

## Verdict so far

ML's honest role in this project is now demonstrated on both tracks. On the doctrine track it
does what six feature increments could not: a 30-token interpretable model recovers Raman's
holistic gating and beats the hand-decoded engine by ~12 points under cross-validation — while
a frontier LLM, properly blinded, cannot. On the reality track the record (ours and the
literature's) says discovery runs are not the next step; **adversarially stress-testing the two
surviving weak signals is** — and if they die under cohort-shuffled and FDR-corrected nulls,
the program's conclusion is complete: the doctrine is a learnable, internally consistent expert
system with no demonstrated external predictive power.
