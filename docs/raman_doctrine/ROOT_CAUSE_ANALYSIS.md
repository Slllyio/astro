---
title: Root-Cause Analysis — why the strength engine plateaus, and whether it can be broken
tags: [moc, raman-doctrine, analysis, ceiling]
updated: 2026-07-13
---

# Root-Cause Analysis: the strength ceiling

*A three-front forensic investigation (three parallel agents, all measurement-based) into WHY the
strength engine plateaus at ~57% within-one against Raman's verdicts — testing three hypotheses:
OCR/label noise, poor feature choice, and "could deeper ML do better?". The finding revises the
earlier "holistic gap, unclosable" conclusion into something sharper and more actionable.*

## The one-sentence finding

**The ceiling is not OCR/label noise and not a missing exotic feature — it is an
AGGREGATION defect: the engine sums every factor's testimony into a single scalar, which (a) cannot
express Raman's upper register (range compression) and (b) discards the planet/house/aspect IDENTITY
that separates a strong-but-afflicted factor from a weak one. The separating signal is still present
in the engine's own structured findings; the sum throws it away.**

---

## Evidence 1 — the ceiling is ENGINE, not label/data noise

Measured live over 131 rows (58 sign-reconstructed + 73 degree). Pooled exact 27.5%, within-one 51.1%,
mean Δ **−0.66** (the engine *under*-credits).

- **Label noise is small.** Binning rows by their FULL engine testimony (the finding-token multiset)
  gives 123 distinct bins for 131 rows — i.e. **identical engine testimony almost never maps to
  different Raman grades.** Pure feature-level label noise is a couple of points, not the gap. The
  OCR/clean-text hypothesis is **largely refuted**: the labels are clean enough.
- **The error is range compression, sharply localized.** Within-one is **82% for Raman grades 0–1
  (afflicted/weak) but only 13% for grades 4–8.** The engine emits a grade ≥4 for just **16.8%** of
  rows; Raman assigns ≥4 for **35.1%**. It structurally **never reaches grade 8 and reaches grade 7
  once.** 59% of all misses — and 58% of total error magnitude — are the engine **flooring Raman's
  strong verdicts.**

Confusion matrix (rows = Raman grade, cols = engine grade 0–8), the smoking gun:

```
raman\eng     0   1   2   3   4   5   6   7   8    n
0 afflicted  29  17   4   2   2   0   2   0   0   56
4 fairly good 2   9   7   1   0   0   2   0   0   21
5 fairly str  3   3   1   0   2   1   1   0   0   11
7 very strong 3   5   1   0   0   1   0   0   0   10   ← graded 0–1 almost every time
8 very pow    0   2   0   0   0   0   0   1   0    3
```

- **The additive-score Bayes ceiling is ~57–61%.** Binning by the SCALAR the engine actually
  thresholds (not the full testimony), the best any monotone recalibration of that score could reach
  is ~57% (bin 0.5) / ~61% (bin 0.25). The live engine (51%) sits only ~6–10 points below it. **The
  single scalar is nearly uninformative above the afflicted band** — score ≈ −0.75 holds 14 rows
  spanning Raman grades 0…7. *This is the price of aggregation, not of noisy labels.*
- **9 grades vs coarser bands** barely helps the real problem: 3-band exact (55.7%) ≈ 9-grade
  within-one (51%), i.e. most within-one credit is just adjacent-band smearing; the big high-grade
  misses are 4–7 grades apart and survive even a weak/moderate/strong collapse. Output granularity is
  a minor contributor.
- **Degrees do NOT help** — sign within-one 56.9% vs degree 46.6%. Sub-degree resolution scatters the
  score without improving the aggregation. Degree accuracy is not the lever.
- **The verdict map** drops ~18 genuine soft verdicts ("in great strength", "not sufficiently strong")
  its word-boundary matcher misses, and flattens soft prose — real but secondary (a few points).

---

## Evidence 2 — a feature-REPRESENTATION problem, not a feature-SPACE problem

- **The engine reduces each factor to one scalar** (`_combine`, `house_judgment.py:829`): a capped sum
  of positive deltas plus the negatives. Identity — *which* planet, in *which* house, aspected by
  *whom* — is destroyed at the sum. The learned model doesn't recover it either: its tokens are
  `(round(delta,2), frame)` only, dropping criterion, planet and house. The true structured space is
  **73 distinct `(criterion, frame, planet, house)` keys** — 3× richer than the token bag — and none
  of that identity reaches the score.
- **The separation is recoverable from features the engine ALREADY computes.** Of 37 verdict-pairs
  Raman separates by **≥2 grades** that land on the *same* engine scalar, **36 differ in their
  structured finding-set.** Only **1 of 37** is genuinely identical in structured features yet graded
  differently — i.e. almost none of the residual is truly outside chart-derived features. Example: at
  score +0.35, an own-sign Mars in a kendra with mixed aspects (Raman "fairly good") lands on the
  *same scalar* as a 10th-lord with a navāṁśa-exalted Moon (Raman "afflicted"). The sum can't tell
  them apart; the structured findings can.
- **Fancier features are the wrong instinct.** The exotic strength systems one reaches for — shadbala,
  dig-bala, retrogression, planetary war, avasthā, higher vargas — are cited **zero times** in Raman's
  83 worked analyses. He justifies strength almost entirely with the vocabulary the engine already
  has: aspect, from-the-Moon, placement, navāṁśa, conjunction, dignity, kendra/trikoṇa/dusthāna,
  kartari, vargottama. And ashtakavarga is already computed but **weighted to zero** (increment 9: it
  *hurt* accuracy). Adding more feature types is not the lever.
- **The genuine feature-CHOICE gaps, all in Raman's own vocabulary:** (a) the **from-the-Moon**
  reckoning — Raman uses it in **37/83** charts, the engine computes it but leaves it in a *separate*
  Chandra-Lagna sub-verdict that never enters the graded factor; (b) **dispositor-chain** strength
  ("the lord is in the sign of an exalted planet"); (c) **exaltation depth** (`DEGREE_DIGNITY=False`,
  dormant).

---

## Evidence 3 — deeper ML is capped, and not by model capacity

- **The labeled budget is tiny:** ~130 clean Raman-labeled rows (57 held-out + 73 NH),
  afflicted-skewed (52% at afflicted/weak), a **~15-row strong tail**, and **~0 house-1-strong**
  training rows. The 82k population corpus and 61k timed charts have outcomes but **no Raman strength
  verdicts** — they cannot supervise this task (five pre-registered runs on them were null).
- **Why the learned model collapsed (0/8 on the anchor), diagnosed:** primarily a **representation**
  problem (the `(delta,frame)` token bag doesn't separate the strong slice — NH-only training still
  scored 0/8, so more strong data can't teach a boundary the features don't express); secondarily a
  **missing engine-base floor** (the model was free to default dense-negative rows to "afflicted",
  making it *worse* than the engine); data scarcity is real but not the operative cause.
- **The bound is Raman himself.** A blinded frontier LLM matched the engine at 47%; the live engine
  scores Raman's *own* calibration anchor at 2/8; the literature puts inter-astrologer agreement at
  ~0.10 effect size. "Truer to Raman" is bounded by how self-consistent Raman is — roughly ±1 grade,
  which is *within-one itself*.

---

## The synthesis — reconciling with the four prior "documented negatives"

This revises the earlier conclusion ("the strong side is a holistic feature-SPACE gap, unclosable")
into a more precise one:

> **The strong-side under-credit is MOSTLY a representation/aggregation collapse (recoverable), with a
> SMALL genuinely-holistic residual (~1/37, irreducible).**

Why every prior attempt failed *the same way* is now explained: **they all operated on the lossy
representation.** Gate F read an *aggregate* fortification tally; the structural-token diagnostic
tested three *aggregate* signals; the learned combine tokenized to `(delta, frame)`. All three are the
scalar-collapse bottleneck viewed from different angles — they discard the very identity that carries
the separation. They correctly proved *aggregate* features don't separate; they did **not** test
whether the engine's *structured* findings, read with identity intact, separate.

**Honest caveat (the open risk).** "36/37 pairs are separable in structured features" is *necessary*
but not *sufficient*: it shows the information is present, not that a hand-coded rule (or a 130-row
model) can exploit it and **generalize**. Increment 29 (Gate F) is the cautionary tale — it read a
richer-than-scalar fortification signal and still over-fired on afflicted rows. And increment 30 found
three *specific* structured tokens (yoga/dispositor/cluster) that anti-separate. So the frontier is
genuinely untested, not proven-winnable: *does a representation that preserves finding identity
separate the strong slice AND generalize?*

---

## What this means for the three hypotheses

| your hypothesis | verdict |
|---|---|
| **OCR ambiguity is the main cause** | **Largely refuted.** Label noise is small; the clean text helped; the ceiling is engine range-compression, not data. (~18 dropped soft verdicts is a minor secondary.) |
| **Feature calibration wasn't done well; choose features brilliantly** | **Correct — with a twist.** The win is NOT fancier features (Raman cites none), it is *not collapsing the features we have into a scalar* — preserving planet/house/aspect identity, and folding in from-the-Moon + dispositor-chain + exaltation-depth, all in his own vocabulary. |
| **Can deeper/efficient ML build a truer engine?** | **Only modestly, and not via capacity.** ~130 rows + contamination + Raman's ±1-grade self-consistency cap it. The lever is hand-coded doctrine that *reads structured findings*, not a bigger model. The one ML idea with upside (residual-on-engine, keeping the floor) is worth ~+2–4 in-distribution points, gated. |

---

## The recommended next experiment (highest-value, lowest-risk, not yet tried in the right form)

**Break the scalar bottleneck with identity-preserving doctrine — not ML, not exotic features.**

1. **Decompress the top of the scale.** The engine can't emit grades 7–8. Loosen the positive
   soft-cap / thresholds *only* for the clean-strong regime (a frame with decisive dignity/fortifiers
   and no deep negatives), so a genuinely strong factor can reach "very strong/very powerful". Gated
   and anchor-guarded. Expected: recover part of the ~6–10-point additive-recalibration headroom.
2. **Fold the from-the-Moon reckoning into the graded factor** (it's computed, used by Raman in 37/83
   charts, and currently discarded from the score). Cheap, doctrine-grounded.
3. **Add dispositor-chain strength and exaltation-depth** as findings (Raman's vocabulary, dormant).
4. **The frontier test:** re-run the increment-29/30 separability + ablation, but over a representation
   that **preserves finding identity** (a per-factor structured feature set, not the scalar or the
   `(delta,frame)` bag). If a doctrine gate over structured findings separates the strong slice
   *without* regressing the afflicted slice or the anchor, it lands (like Gate B did); if it
   over-fires like Gate F, it is the definitive close on the representation hypothesis too.

**Honest expected ceiling:** low-to-mid **60s%** within-one — recovering A2's in-distribution 63.5%
*landably* (with the engine-base floor), bounded above by the ~1/37 genuine-holistic residual and
Raman's own self-consistency. Not 80%+; that would require breaking Raman's own ±1-grade noise floor,
which no engine can.

### RESULT (increment 31 — Gate D landed)
The recommended experiment was run. A diagnostic (`incr31_probe`) decomposed the 24 strong-graded
floored misses: **15 deep-afflicted** (the irreducible fortified-but-afflicted residual), **6 clean
under-detection** (the engine sees no positive testimony Raman graded on — the ~1/37 genuine-holistic
residual, at scale), and **3 clean dignity crushed** — decisive dignity + strong positives that
`_cap_positive` floored to grade 1–2. The last group is tractable and became **Gate D** (dignity/
decompression floor, gated on *shallow* negatives — the condition the old Gate C lacked). It **landed**:
held-out 56.9→**58.6%**, max-expansion 61.7→**64.2%**, fresh-blind 71.4→**78.6%**, strong slice
17→**24%**, mid/afflicted/anchor all held (`REPORT_synthesis_v2.md` § increment 31). The two sibling
levers were **refuted** by the same diagnostic and *not* built: range-decompression alone touches only
3/24 misses; the **from-the-Moon** fold anti-separates (1/24 strong-floored are strong from the Moon,
below the afflicted slice's 5%). Net: the analysis was right about the mechanism (aggregation collapse,
range compression) and right that the fix is identity-preserving doctrine over the existing findings —
but only the shallow-negative dignity sub-slice was recoverable; the 15 deep-afflicted + 6
under-detection misses remain the holistic ceiling, exactly as the ~1/37 residual predicted.

---

## Reproduce

The three investigations' scripts (measurement-only, no engine change) are in the session scratchpad:
`collect.py` (miss profile + confusion matrix + Bayes ceilings), `analyze2.py` (range + verdict-map
audit), `concepts2.py` (Raman concept frequency), `collapse.py` (scalar-collapse + structured
recovery). Their headline numbers are quoted above; the standing reproducible diagnostics remain
`structural_separability.py` and `learned_combine_landing.py`.
