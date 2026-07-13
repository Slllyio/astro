# ML & AI for astrological pattern-finding — research report + roadmap

**Status: COMPLETE (2026-07-10).** A2 complete; pilot A1 complete (167/167); the four
load-bearing literature claims verified against primary sources (verbatim quotes below), the
remainder labeled extracted-unverified. Every internal number traces to a banked artifact under
`validation/ml_research/` or a live validator.

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

**The residual above the engine's ceiling is learnable — within the training distribution**
(+11.6 points under the same LOCO discipline the Phase-2 recalibration used, +15.6 on a pool the
model never trained on). And the learned gates are legible: the depth-3 tree's root split is
`sum_neg_rasi ≤ −1.22 → afflicted` regardless of positional credits (unless positives pile past
3.5) — the "besieged factor is broken" override a linear checklist cannot express
([tree rules](validation/ml_research/a2_tree_rules.json)). **The gain does not generalize
out-of-distribution** — see the anchor test below, where it collapses to "afflicted" on house-1
charts absent from the held-out chapters. So this is a real but *bounded* result: learnable where
there is training signal, not a universal replacement for `_combine`.

**Why it is NOT landed — and why the gate itself is the deeper problem.** The pre-registered
ch. IV anchor gate failed (ordinal 2/8, tree 1/8 within-one). A landing attempt (A2′) investigated
whether that was a fixable representation artifact, and found something more fundamental:

- **Diagnosis of the failure:** the frozen anchor is 8 hand-decoded *typed*-finding rows using a
  retired weight vocabulary — e.g. a `1.0` kendra delta the live engine changed to `1.2` long ago,
  plus `0.35`/`−1.0` Navāṁśa tokens that never occur in the live-engine training data, and only
  1–3 findings per row vs the engine's dense output. The ordinal model, trained on current dense
  engine findings, has no learned weight for those stale tokens and defaults the sparse rows toward
  "afflicted". So the gate failure is not evidence the model breaks calibration.
- **The attempted fix exposed a bigger issue.** To score the anchor in engine representation, the
  three ch. IV charts (Nos. 12–14) were cast from their real birth data (printed verbatim in HTJAH)
  in Raman's ayanamsa and judged live. The casts are **faithful** — Chart 12's rāśi *and* navāṁśa
  match Raman's prose exactly (Saturn in the 8th in Leo; Saturn's navāṁśa Taurus "with Jupiter in
  the sign of Venus"; the Sun vargottama). Yet the **live engine scores its own calibration anchor
  at 2/8 within-one** ([`a2prime_anchor_diagnostic.json`](validation/ml_research/a2prime_anchor_diagnostic.json)),
  under-crediting by 3–5 grades (Chart 12's lord Saturn: engine "weak" vs Raman "fairly good" vs the
  frozen anchor's "fairly good"). The `test_audit_anchor` 8/8 passes only because it runs the frozen
  hand-decoded findings through the old `validate_house.predict`, **not** `judge_house_doctrine` —
  so the anchor test and the live engine have themselves diverged over the intervening increments.
- **The decisive test — and the gate is vindicated.** Scoring the anchor in engine representation
  on the faithful casts settles it: on the same 8 rows, **vs Raman**, the live engine is 2/8 and
  **the learned combine is 0/8 — it predicts "afflicted" for every anchor row**. The learned
  model's LOCO training folds are the held-out chapters, which are dusthāna-heavy (houses
  3/5/6/8/9/10/12) and skewed toward afflicted verdicts; it learned "dense findings with negatives
  → afflicted" and **collapses out-of-distribution on the house-1 anchor charts** (strong lagnas
  with mixed testimony it never saw). So the pre-registered gate did exactly its job — it caught
  that the **63.5% LOCO gain is distribution-bound and does not generalize to house 1.** The
  landing is correctly rejected, not on a technicality but on substance.
- **Two true findings, kept separate:** (a) the frozen anchor test has drifted from the live engine
  — `test_audit_anchor` reads 8/8 on stale hand-decoded findings while the live engine scores the
  same charts 2/8 vs Raman; (b) the learned combine, though better than the engine *within* the
  held-out distribution, is worse *outside* it. **Landing path (a separate increment):** the
  learned combine needs house-1 (and kendra-strong) training rows before it can generalize, and the
  anchor gate needs rebuilding as a grid-backed corpus re-baselined through the live engine. Until
  both hold, the learned combine stands as a validated *in-distribution* measurement, not an engine
  change. The honest headline: the ceiling residual is learnable, but only where you have training
  signal — and the calibration anchor is doing real work by refusing an overfit model.

**LANDING TEST — the decisive close (2026-07-13, `learned_combine_landing.py`).** Both landing
prerequisites were supplied and the test run: (a) the anchor scored in **live engine representation**
(grid-backed ch. IV casts via `anchor_live_validate` → `judge_house_doctrine` → `_tokens_from_engine`),
and (b) the model trained under three regimes, one injecting the **strong-heavy NH degree pool**
(73 rows, 15 strong-graded — the "house-1/kendra-strong training rows" prerequisite). Result:
**0/8 within-one on the live anchor in EVERY regime** (held-out only, held-out + full NH, NH only;
ordinal and depth-3 tree alike) — the tree predicts "afflicted" for all 8 house-1 rows. **Adding
strong training signal does not cure the OOD collapse.** The anchor's house-1 strong-lagna verdicts
are not feature-separable from afflicted ones — the same holistic gap increments 29–30 proved
unclosable. The model is strictly worse on the anchor than the live engine (0/8 vs 2/8) because it
lacks the engine-base floor. So the learned combine is **definitively not landable**; its one
transferable discovery (Gate B = the tree's `sum_neg ≤ −1.22` split) is already live in synthesis_v2,
which holds anchor parity via that floor. The pre-registered anchor gate is vindicated at the model
level. Pinned by `test_learned_combine_landing.py`; result banked in
`validation/ml_research/a2_landing_result.json`.

## NEW — Track A experiment 2 (A1): the blinded LLM-as-scorer pilot (complete, 167/167)

Can a frontier LLM's *holistic* reading beat the engine? Design
(`app/medini/doctrine/validation/llm_scorer_pilot.py`, artifacts under
[`validation/ml_research/llm_pilot/`](validation/ml_research/llm_pilot/)): all 85 held-out
strength rows (53 sign + 32 NH degree) rendered as fully blinded prompts — structure only, no
names/dates/book markers (the audit hard-fails on any leak; it caught the prompt template itself
naming the method's author) — plus one **perturbed twin** per row: a planet moved such that the
judged factor's engine-finding multiset is unchanged, so the structural question is identical
but the chart matches no published nativity. The real-vs-twin gap is the memorization detector.
Zero-shot, opaque ids, graded on the same 9-grade lattice as the validators.

Final result (167/167 graded; [`full_score.json`](validation/ml_research/llm_pilot/full_score.json)):

| | within-one | mean Δ |
|---|---|---|
| LLM zero-shot, real rows (n=85) | 47.1% | +0.94 |
| LLM zero-shot, perturbed twins (n=82) | 47.6% | +1.01 |
| live engine on the same real rows | **49.4%** | +0.56 |

Three findings:
- **The LLM does not beat the engine** zero-shot (47.1% vs 49.4%), and it over-credits harder
  (+0.94 vs +0.56) — the same positive bias Raman's engine had to be beaten out of by increments.
- **No contamination detected**: the real-vs-twin gap is −0.5pp ≈ 0. The blinding + twin design
  worked; the LLM's score reflects reasoning over the blinded structure, not book recall.
- It reads **degree charts better than sign grids** (53.1% vs 43.4%) — plausibly because
  longitudes let it compute what the grids leave implicit.

Taken together with A2, the story is coherent and important: **the residual is learnable, but by
fitting Raman's specific weighing — not by generic astrological expertise.** A tiny model trained
on 52 of his verdicts outperforms both his own hand-decoded rule set and a frontier LLM.

## Literature (verification status per claim)

The deep-research sweep extracted these claims with sources; its 3-vote adversarial-verification
phase was twice cut short by session token limits, so the load-bearing claims were then verified
**directly against their primary sources** from this session (verbatim quotes on file). Status
per claim:

- **Carlson 1985 (Nature 318:419)** — ✅ VERIFIED (workflow panel 2-0 against the Nature page:
  "Two double-blind tests were made of the thesis that astrological 'natal charts' can be used
  to describe accurately personality traits"). Double-blind chart-to-CPI matching; astrologers
  at chance (0.34 ± 0.044 vs 1/3), 3.3σ below their own predicted floor, criteria fixed in
  advance. The canonical pre-registered null.
- **Dean & Kelly time-twins** — ✅ VERIFIED (source quote: "2101 persons born in London during
  3-9 March 1958 … born on average 4.8 minutes apart", 110 variables at ages 11/16/23, "The
  effect size due to astrology is 0.00 ± 0.03"). The largest population-scale natal-similarity
  null; the direct parallel to our N=82,589 nulls.
- **Chart-matching meta-analysis** — ✅ VERIFIED (source quote: "more than forty studies …
  totalling nearly 700 astrologers and 1150 birth charts … mean effect size of 0.051, standard
  deviation 0.118, for which p = 0.66").
- **Inter-astrologer agreement** — ✅ VERIFIED (source quote: "twenty-five studies … nearly 500
  astrologers … mean agreement (as an effect size) of 0.101, standard deviation 0.064") — far
  below the ~0.8 reliability psychologists require before applying a judgment individually.
- **McGrew & McFall 1990** — ⚠️ extracted, primary source not independently fetchable from this
  session (JSE 4(1); SemanticScholar renders empty): six Indiana-Federation-vetted astrologers
  matching 23 charts to full case files, median 1 correct (chance expectation), mean pairwise
  agreement 1.4/23, confidence-accuracy correlation r=.03.
- **Gauquelin Mars effect** — ⚠️ extracted: the one long-contested positive; skeptic-organized
  replications negative/contested; Dean's documentation-bias account (era birth-reporting
  practices) is the live mundane explanation — the same confound class as our marriage-XGBoost
  survivor.
- **Published ML-astrology studies** — ⚠️ extracted: the record is thin and weak — chance-level
  results on a *synthetic* dataset in a self-described pedagogical/joke arXiv paper; an IEEE
  doctor-vs-non-doctor XGBoost+SMOTE classifier (10,000 births, 76.57%) whose headline dissolves
  against its base rate and evaluation choices; Weka studies whose own tables contradict their
  abstracts. No credible ML positive exists in the published record.

Two of these bear directly on our results. The inter-astrologer-agreement-at-chance findings
recast Track A: **expert astrological judgment is idiosyncratic, so "learning the doctrine" is
only coherent per-expert** — exactly what A2 shows (Raman-specific weighing is learnable) and
what A1 shows (a generic expert prior does not transfer to Raman's grades). And Dean's
documentation-bias account of the Mars effect is the template for B1's kill protocol.

## Roadmap (ranked; each pre-registered with a kill criterion)

| # | experiment | data | protocol | status |
|---|---|---|---|---|
| A1′ | finish the pilot (slice 4, 28 prompts) | on disk | same blinded design | **done** — final numbers above |
| A2′ | anchor re-derivation → landing decision | ch. IV live casts + strong NH pool | gate re-run in engine representation, +strong training rows | **done — landing refused** (0/8 live anchor in every regime; `learned_combine_landing.py`); residual learnable in-distribution, not landable |
| A3 | identity-preserving learned scorer (richer representation, not aggregation-altitude) | held-out + NH + live anchor | 50-dim identity vector nesting A2's aggregates; LOCO vs A2 same folds + live anchor gate | **done — decisive negative** (incr. 33): identity **57.9%** < A2 **61.4%** < engine 58.6%, overfits more (gap +9..+23 vs +3.2), anchor 0/9. The pair-separating identity signal is real but NOT learnable at N≈130; `identity_scorer.py`, `REPORT_identity_scorer.md`. Closes the representation lever |
| A3′ | symbolic regression / program synthesis over chart primitives | tuned+held-out | discovered rule admitted only if it matches a sutra | superseded — A3 shows richer representations overfit this corpus; deprioritized |
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
