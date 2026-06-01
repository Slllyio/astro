---
date: 2026-05-27
type: retrospective / lessons-learned
status: closed
project: Medini Vedic astrology ML research (Rounds 8-10 + Stage D)
companion_to: docs/round9_doctrine_findings.md
---

# Deep Retrospective — Lessons from 5 Null Verdicts

After 9+ rounds of attempting to demonstrate that Vedic chart structure
predicts life events, the project closed with 5 independent NULL VERDICTS:

1. Cross-corpus doctrine quintile RR test (3 corpora, 75k people) — null
2. Non-structural XGBoost with proper date controls — null
3. LLM with real chart vs LLM with shuffled chart (n=29) — null
4. Stage D Dynamic-DeepHit between-person — null (Δ = −0.16)
5. Stage D Dynamic-DeepHit within-person — null (model < trivial baseline)

This document extracts the lessons. It is the reference for any future
person (or agent) considering ML work on this corpus or on astrology
prediction generally.

---

## The single meta-insight

**The confound family in astrology ML is small, well-known, and recurring.**
Every "positive" result across 5 sessions had one of three confounds:

| Confound | First appeared | Recurred | Fix |
|---|---|---|---|
| Exposure-time (longer dasha = more events) | Stage B Fisher-exact marriage RR=1.54 | Stage D within-person C=0.60 | Pre-register exposure-adjusted Poisson OR within-person test as a gate |
| Birth-date proxy (chart features = birth date in disguise) | Round 9 Stage F doctrine AD-only fame RR=1.43 | Non-structural XGBoost +0.04-0.12 lift | Always add `birth_jd` (day-precision) as control, never just `birth_year` |
| Single-corpus selection bias | Doctrine quintile RR on AD | Same scorers reversed direction on Lunarastro/Wikidata | 3-corpus replication is MINIMUM, not optional |

These three confounds are **baked into the data structure of Vedic
astrology itself** (fixed-length dashas, planets-encode-birthdate,
biographied-people corpora). They will reappear in every future project
unless pre-controlled at the design stage.

---

## Scientific / methodological lessons

### 1. The "looks like signal, controls reveal confound" pattern fired TWICE

- **Stage B 2026-05-24**: marriage RR=1.54 (p=2.5e-6) → exposure-adjusted
  Poisson → RR=1.05 (p=0.31)
- **Stage D within-person 2026-05-27**: C_within=0.60 (p<0.01) → duration
  baseline → C=0.74 (baseline beats model)

Both times the missing control was time-exposure. If we'd had a "duration
confound" check in our standard pre-flight, we'd have saved weeks.

### 2. Cross-corpus replication is the only valid gate

3-corpus intersection of Bonferroni-significant classes was **empty**. Each
corpus produced its own "winner" (fame on AD, family on Lunarastro, career
on Wikidata) but none survived to a second corpus. The Bonferroni-on-one-
corpus discipline is *not enough* — selection bias varies more between
corpora than between random splits within one corpus.

**Rule**: If you tested 5 scorers and picked the winner on corpus A, you
can't claim a result until corpus B and corpus C both reproduce it.

### 3. Negative model comparison is diagnostic, not a tuning problem

DeepHit underperformed Cox by 4σ in the WRONG direction across 5 seeds
with stdev=0.04 (very tight). The instinct is "model is undertrained, tune
it." The correct read: **when a higher-capacity model with competing-risks
structure systematically degrades vs a simpler baseline, the features
don't carry the structure the model is designed for.**

### 4. Within-person is the cleanest control for between-person confounds — but has its own

- Within-person removes birth-year cohort, selection density, documentation bias
- Within-person does NOT remove Vimshottari duration structure
- Within-person does NOT remove age-of-life patterns per event class
- **Must run age-alone AND duration-alone baselines simultaneously to
  interpret a within-person C-index**

### 5. The LLM real-vs-shuffled chart test is cheap and sharp

n=29, one API call per subject, p=0.43 dead null. This is the simplest
"does the chart pipeline carry signal at all?" test. **Worth
pre-registering in any future individual-prediction study** because it
bypasses all feature-engineering choices and tests the
doctrine→chart→prediction mechanism end-to-end.

---

## Engineering / infrastructure lessons (the runbook)

### 6. Compute-budget estimation must precede spec commitment

We discovered "CPU would take 200-400 hours" only AFTER starting Stage D.
The arithmetic was knowable in 5 minutes from smoke-scale timing.

**Rubric**: if naive CPU exceeds 50 hours, GPU is mandatory — decide
BEFORE implementation, not when the first slow seed completes.

### 7. Windows multiprocessing has a hard ~2 GB pipe pickle limit

Hit at subsample scale (1.2M rows). Fix pattern lives in
`app/medini/ml/stage_d_baseline.py:235-335`:

- Probe `memory_usage(deep=True)` before deciding transport
- <1.5 GB → pickle through `initargs` (fast)
- ≥1.5 GB → spill to temp parquet, pass paths through `initargs`
- Cap workers at 4 (each worker's parquet read transiently mallocs 2-3×
  DataFrame size)
- Don't try-catch the OSError; route up front

Pattern is production-tested. Copy for any Windows ML project with
DataFrame >500 MB.

### 8. DirectML AMD-GPU gotcha list

- Backend registers as `privateuseone` in torch, NOT `dml` — use
  `device.type == "privateuseone"` to detect
- Some ops (`aten::lerp.Scalar_out`, certain sparse) silently fall back to CPU
- Batch size must be ≥512 to saturate the device (256 was 4× slower than
  1024 on Radeon 9060 XT)
- `torch_directml.empty_cache()` is required between phases or memory
  accumulates
- `torch_directml.manual_seed_all(seed)` for reproducibility (separate
  from `torch.manual_seed`)
- Checkpoints saved on DML need `map_location="cpu"` to reload portably

`app/medini/ml/stage_d_device.py` (62 lines) abstracts all of this.
Copy verbatim for next PyTorch+Windows project.

### 9. Checkpoint reuse is a 60× speedup lever

Within-person test ran in **20 seconds per seed** via GPU forward pass on
existing DeepHit checkpoints vs the originally-planned **20 minutes per
seed** via Cox CPU refit.

**Default question for any post-hoc analysis**: "do I already have a
trained model that can answer this with inference?" before re-fitting.

### 10. Single-source-of-truth split function prevents confounding bugs

`stage_d_baseline.split_train_test(df, seed=k)` is called identically by
DeepHit and Cox. The gate's Δ is only meaningful because both models
score on the same test set. **20 lines, prevents the entire class of
split-drift bugs.** Mandatory pattern for any multi-model comparison.

### 11. Subsample sizing rubric for null research

We hit the null with 5 seeds at 19.5% subsample (stdev=0.04, mean=−0.16).
The tight stdev signaled "verdict won't flip — stop."

**Rule**: if stdev across 5 subsample seeds is < 0.25 × |mean|, the
verdict is locked. Don't pay for 20 more seeds at full scale.

---

## Process / decision-making lessons

### 12. The "one more test" trap is the biggest time sink

We spent 5 sessions running predictive ML when 4 prior rounds had
already returned null. Each session's "this time will be different" cost
roughly a week of compute + design.

**Install**: a pre-committed termination criterion (e.g., "3 consecutive
null verdicts = stop and pivot").

### 13. Parallel-agent research dispatch was the highest-leverage decision tool

The 5-agent dispatch on 2026-05-27 (product strategy + market research +
alt-ML + codebase audit + data audit) converged on a single recommendation
in ~30 minutes. **More clarity than any prior multi-day analysis.**

**Pattern**: when stuck at a decision fork, dispatch 4-5 specialized
agents in parallel BEFORE designing the next experiment.

### 14. GPU/compute decisions were reactive, not proactive

We "discovered" we needed DML 3-4 times during one session. Pattern to
install: **at the start of any ML session, the FIRST question is "what
compute am I targeting?" not the last.**

### 15. Research code → product decoupling happened by good practice, not by design

The architect's audit found `app/medini/ml/` and `app/medini/etl/` are
fully decoupled from the FastAPI surface — deletable without breaking the
user-facing app. This happened because of CLAUDE.md's "`/ml` = research,
`/api` = product" convention. **Worth keeping as an explicit principle in
any project that mixes research + product.**

---

## What we now know about Vedic astrology specifically

**Claims with strong empirical evidence AGAINST them**:

| Claim | Evidence | Strength |
|---|---|---|
| Dasha-lord predicts event class (Venus → marriage etc.) | Stage B exposure-adjusted Poisson; Stage F mix scorer on 3 corpora; Stage D between-person | Very strong (3-corpus + survival) |
| Chart structure (signs, houses, yogas) adds predictive AUC over date | Round 9 XGBoost +0.008 with date controls; LLM real-vs-shuffled p=0.43 | Very strong |
| Within-person dasha-lord attribution carries signal | Stage D within-person C < trivial age+duration baseline on every class | Very strong (this session) |
| LLM-mediated chart reading produces actionable predictions | Round 10 n=29 paired Wilcoxon p=0.43 | Moderate (small n but extremely null) |
| Single-corpus "doctrine signal" replicates across corpora | 3-corpus intersection empty | Very strong |

**Claims with modest support** (empirically real but uninteresting for prediction):

| Claim | Evidence |
|---|---|
| Longer Vimshottari dasha periods contain more documented events | Duration C_within = 0.65-0.74 (pure exposure) |
| Death events cluster in older age | Age C_within for death = 0.75 (obvious) |

**Claims NOT tested** (still open):

- Individual chart reading by a trained practitioner producing actionable advice
- Whether doctrine helps people make better decisions, regardless of predictive accuracy
- Subjective outcomes (life satisfaction, identity, personality traits) instead of objective events
- Mundane / world-event prediction at scale

---

## Assets that survive (worth more than the failed claim)

| Asset | Reusability | Value |
|---|---|---|
| Stage D pipeline (DeepHit + Cox + DML + parquet-spill + verdict gen) | Any tabular survival ML project | High — battle-tested, ~1000 lines |
| Knowledge library (6.28M words, multilingual RAG, 918 artefacts) | Direct product per agent synthesis | Very high — no commercial equivalent |
| Chart engine (Lahiri, dashas, yogas, kurma cartography) | Any Vedic-astrology software | High — 514+ tests, doctrinally pinned |
| Mundane forecast + RAG citation system | Direct product | Medium — niche but unmonetized |
| 5-method null evidence + methodology | Publication; credibility marketing | Medium — uniquely rigorous in this domain |

---

## The "next time" checklist

Before any predictive ML project on personal data:

- [ ] Pre-register a 4-criterion gate (G1 aggregate Δ, G2 per-class clears, G3 model stability, G4 replication)
- [ ] Pre-register 2-corpus or 3-corpus replication as MINIMUM
- [ ] Pre-register the confound checks: birth-date proxy, exposure-time, selection bias, age-pattern
- [ ] Pre-commit to scorer choice OR plan a held-out corpus for tuning
- [ ] Estimate compute budget BEFORE writing code; pick GPU if naive CPU exceeds 50 h
- [ ] Decide between-person vs within-person design intentionally (within = cleaner controls but exposure trap)
- [ ] Plan to reuse checkpoints for post-hoc analyses (inference > re-fit, ~60× speedup)
- [ ] Set a kill criterion ("3 consecutive nulls = stop and pivot")
- [ ] At decision forks, dispatch 4-5 parallel agents BEFORE designing the next experiment
- [ ] Verify research code stays decoupled from shipped product surface

---

## Files referenced

- `docs/round9_doctrine_findings.md` — combined Round 9+10 doctrine writeup
- `data/ml_runs/fork_a_stage_d_subsample/DECISION.md` — Stage D between-person FAIL verdict
- `data/ml_runs/fork_a_stage_d_subsample/WITHIN_PERSON_VERDICT.md` — Stage D within-person NULL
- `data/ml_runs/fork_a_stage_d_subsample/within_person_control.md` — confound controls
- `app/medini/ml/stage_d_*.py` — reusable infrastructure
- `app/medini/ml/stage_d_device.py` — DirectML device resolver (copy verbatim)
- `app/medini/ml/stage_d_baseline.py:235-335` — Windows multiprocessing parquet-spill pattern
