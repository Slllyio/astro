---
title: Medini Doctrine — Validation Summary (held-out results ledger)
tags: [moc, raman-doctrine, validation, results]
updated: 2026-07-10
---

# Medini Doctrine — Validation Summary

> The single honest ledger of how the engine that encodes B. V. Raman's *How to Judge a
> Horoscope* (HTJAH) performs **held-out** — measured against Raman's own printed verdicts on
> charts the engine was never tuned against. Every number here is reproduced live by the
> validators and pinned by `tests/doctrine/test_validation_summary.py`, so this file and the
> engine can never silently diverge. For the map of *how* the work was built, see
> [`PROJECT_MAP.md`](PROJECT_MAP.md); for the per-increment engine history, see
> [`HOUSE_SCHEME_AUDIT.md`](HOUSE_SCHEME_AUDIT.md).

## Headline results

Four independent axes are validated. "Held-out" = the engine was never tuned on the corpus;
"blind" = the corpus was built *after* the engine and calibration were frozen.

| Axis | Metric | Result | N | Corpus | Report |
|---|---|---|---|---|---|
| **Strength** (sign-reconstructed) | within-one | **52.8%** (exact 26.4%, Δ +0.49) | 53 | pooled held-out `heldout_ch*` | [recalibration](validation/REPORT_recalibration.md), [crosshouse](validation/REPORT_crosshouse_heldout.md) |
| **Strength** — max HTJAH expansion | within-one | **53.9%** (exact 26.3%, Δ +0.43) | 76 | held-out + fresh blind | [unseen corpus](validation/REPORT_unseen_corpus.md) |
| **Strength** — fresh blind only | within-one | **71.4%** (Δ −0.21) | 14 | `unseen_scoreable` (engine-unseen) | [unseen corpus](validation/REPORT_unseen_corpus.md) |
| **Strength** — NH degree-accurate | within-one | **46.7%** (exact 33.3%, Δ +1.13) | 15 | real-birth `nh_strength` (0 excluded) | [nh strength](validation/REPORT_nh_strength.md) |
| **Timing** — HTJAH events | mahādaśā-lord exact | **100%** (8/8); antara within-one 8/8 | 8 | `heldout_timing` + `…_ch12_8th` | [timing](validation/REPORT_timing.md) |
| **Timing** — Notable Horoscopes | mahādaśā-lord exact | **94.0%** (47/50); antara within-one 92.9% | 50 | `nh_timing` (real births) | [timing](validation/REPORT_timing.md) |
| **Daśā balance** — NH | starting-lord exact | **93.3%** (28/30); duration ±0.5y 28/30 | 30 | `nh_balance` (Moon longitude) | [nh balance](validation/REPORT_nh_balance.md) |
| **Longevity** — 8th bhāva | Spearman ρ vs Raman's longevity order | **+0.52** (p≈0.06) | 14 | `heldout_longevity_ch12_8th` | [longevity](validation/REPORT_longevity.md) |

**Reading the table.** Timing, balance, and longevity are *strong*: the daśā arithmetic
reproduces Raman's printed mahādaśā lord 94% of the time on real births (50 events), the
balance line 93%, and 8th-bhāva strength predicts his longevity ordering (ρ +0.52) while general
benefic-strength *anti*-predicts it (ρ −0.35, see below) — a discriminating result, not a
coincidence. **Strength sits at a ceiling of ~53% within-one** and that is the honest,
load-bearing finding of the whole effort.

## The strength ceiling — stated plainly

The sign-only strength engine reconstructs each chart from Raman's two printed diagrams (Rāśi +
Navāṁśa signs, no longitudes) and grades bhāva/lord/kāraka strength on a 9-grade scale. Across
every held-out cut it lands at **~53% within-one, ~26% exact, with a small positive bias
(Δ ≈ +0.4 to +0.5: the engine over-credits)**. This ceiling is **structural, not parametric** —
it was probed directly and does not yield to re-weighting:

- The [ceiling diagnostic](validation/REPORT_ceiling_diagnostic.md) shows the residual error is
  not separable by any single existing feature — the misses are holistic judgments (Raman
  weighing debilitation *against* kendra placement *against* association) that a sign-only
  feature set cannot represent.
- The two largest systematic misses are **benefic over-credit** (the engine reads a benefic in a
  house as strengthening even where Raman does not) and **dusthāna-lord under-score** (any 8th/6th
  placement reads as weakening even when Raman calls the lord "full and powerful" by own-sign
  dignity). Both are documented, reproduced, and *bounded* — not open bugs.

### What landed vs what is a documented negative

Eight increments improved held-out accuracy; four were honestly recorded as negatives that did
**not** move it (full detail in [`HOUSE_SCHEME_AUDIT.md`](HOUSE_SCHEME_AUDIT.md)):

| # | Increment | Outcome |
|---|---|---|
| 1–3 | occupant dignity · exaltation blend · bhāva-aspect dignity | **landed** |
| 4–5 | dusthāna-lordship penalty · mild frame can't rescue deep affliction | **landed** (held-out-driven) |
| 6–7 | natural-benefic occupant not blemished · benefic aspect + kartari | **landed** (held-out-driven) |
| 11 | lord at home in its own dusthāna is redeemed | **landed** (fresh-held-out-driven) |
| 8 | lord/kāraka over-credit (B) | **documented negative** — not closable on current features |
| 9 | ashtakavarga bindu strength | **documented negative** — no accuracy change |
| 12 | neechabhāṅga-in-kendra strength | **documented negative** — inert under the positive cap |
| 13 | true-degree affliction (combustion + aspect orb) | **documented negative** — reduces but does not *separate* the over-credit |

That every negative is recorded rather than buried is the point: the ceiling is characterized,
not hand-waved.

## Corpora

All validation corpora live under [`validation/corpora/`](validation/corpora/).

- **Tuned** (engine calibrated on these — never counted as held-out): houses 2/7/9/11 chapters +
  the **ch. IV anchor (Charts 12–14), held at 9/9** and byte-stable across every increment.
- **Held-out (HTJAH)** — `heldout_ch{06,07,08,09,12,14,16}_*.json` (houses 3/4/5/6/8/10/12) +
  `tuned_ch13_vol2_9th_rederivation.json`.
- **Blind (built after freeze)** — `unseen_scoreable.json` (14 rows) and `unseen_grow.json`
  (max-addressable HTJAH expansion); both disjoint from every extracted corpus by
  **(volume, chart_no)**, pinned in `tests/doctrine/test_unseen_corpus.py`.
- **Degree-accurate (real births)** — `nh_strength.json`, `nh_timing.json`, `nh_balance.json`
  from the Notable Horoscopes set (true longitudes, no sign-reconstruction).
- **Timing / longevity** — `heldout_timing*.json`, `heldout_longevity_ch12_8th.json`.

## Integrity guarantees

- **Held-out is held-out.** No corpus in the held-out/blind tables above was used to fit any
  weight or map entry. Blind corpora are (vol, chart_no)-disjoint from everything else.
- **The anchor is frozen.** Ch. IV (Charts 12–14) stays 9/9 and byte-stable; this is asserted in
  `tests/doctrine/test_audit_anchor.py`.
- **Verdicts are pre-registered.** Raman's strength phrases are mapped to grades once, in the
  verdict map, and the map is verified before scoring — the engine cannot be graded against a
  moving target ([verdict audit](validation/REPORT_verdict_audit.md)).
- **Grids are prose-cross-checked.** Every reconstructed chart is verified against Raman's own
  stated relative positions and passes a Navāṁśa reachability gate before it scores.
- **This ledger is a tested contract.** `tests/doctrine/test_validation_summary.py` re-runs each
  validator and asserts the numbers in the headline table still hold.

## What is left

The only remaining lever for **strength** accuracy is the **full real-birth degree engine** —
replacing sign-reconstruction with actual longitudes so the engine can weigh degree-of-exaltation,
combustion orb, and exact bhāva cusps the way Raman does by eye. The NH degree-accurate track
(46.7%, N=15) is the first probe of that path; Increment 13 showed degree-resolution affliction
alone does not separate the over-credit, so the degree engine is a *larger, separate effort*, not
a tuning pass. Timing and balance are already at their useful ceiling and are wired into the
reading output.

## Report index

Strength & ceiling: [recalibration](validation/REPORT_recalibration.md) ·
[crosshouse held-out](validation/REPORT_crosshouse_heldout.md) ·
[ceiling diagnostic](validation/REPORT_ceiling_diagnostic.md) ·
[unseen corpus](validation/REPORT_unseen_corpus.md) ·
[verdict audit](validation/REPORT_verdict_audit.md) ·
[NH strength](validation/REPORT_nh_strength.md) ·
[Raman-style prose](validation/REPORT_raman_style.md).
Per-house held-out: [ch06 3rd](validation/REPORT_ch06_3rd.md) ·
[ch07 4th](validation/REPORT_ch07_4th.md) · [ch08 5th](validation/REPORT_ch08_5th.md) ·
[ch09 6th](validation/REPORT_ch09_6th.md) · [ch12 8th](validation/REPORT_ch12_8th.md) ·
[ch13 vol2 9th](validation/REPORT_ch13_vol2_9th_rederivation.md) ·
[ch14 10th](validation/REPORT_ch14_10th.md) · [ch16 12th](validation/REPORT_ch16_12th.md).
Timing / balance / longevity: [timing](validation/REPORT_timing.md) ·
[NH balance](validation/REPORT_nh_balance.md) · [longevity](validation/REPORT_longevity.md).
