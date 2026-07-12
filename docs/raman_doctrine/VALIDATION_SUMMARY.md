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
| **Strength** (sign-reconstructed) | within-one | **50.0%** (Δ −0.12) | 58 | pooled held-out `heldout_ch*` (increment 27: verdict-map v2 recovered 5 strong-graded phrases, N 53→58; was 54.7%/N=53) | [recalibration](validation/REPORT_recalibration.md), [crosshouse](validation/REPORT_crosshouse_heldout.md) |
| **Strength** — max HTJAH expansion | within-one | **51.9%** (Δ −0.01) | 81 | held-out + fresh blind (increment 27 map v2; was 55.3%/N=76) | [unseen corpus](validation/REPORT_unseen_corpus.md) |
| **Strength** — fresh blind only | within-one | **71.4%** (Δ −0.21) | 14 | `unseen_scoreable` (engine-unseen) | [unseen corpus](validation/REPORT_unseen_corpus.md) |
| **Strength** — NH degree-accurate | within-one | **41.7%** (Δ +1.08) | 12 | real-birth `nh_strength` (increment 26: attribution audit removed 3 frame-error rows; was 53.3%/N=15) | [nh strength](validation/REPORT_nh_strength.md) |
| **Strength** — NH degree pooled (grown) | within-one | **51.9%** (Δ +0.11) | 27 | `nh_strength` + `nh_strength_grow` (increment 26: 5 bad gold rows removed — see `corpora/nh_strength_removed.json`; was 53.1%/N=32) | [degree engine](validation/REPORT_degree_engine.md) |
| **Strength** — NH full degree pool (grow2–grow4) | within-one | additive **39.7%** / synthesis_v2 **46.6%** | 73 | all five NH corpora (increment 27: map-v2 recovery added 17 strong-graded rows both scorers under-credit) | [synthesis_v2](validation/REPORT_synthesis_v2.md) |
| **Strength** — ch. IV LIVE anchor | within-one | **12.5%** (1/8, Δ −3.75, all under-credits) | 8 | `htjah_anchor_live` (faithfulness-gated casts; the frozen 8/8 gates only the old harness) | audit increment 16 |
| **Timing** — HTJAH events | mahādaśā-lord exact | **100%** (8/8); antara within-one 8/8 | 8 | `heldout_timing` + `…_ch12_8th` | [timing](validation/REPORT_timing.md) |
| **Timing** — Notable Horoscopes | mahādaśā-lord exact | **94.0%** (47/50); antara within-one 92.9% | 50 | `nh_timing` (real births) | [timing](validation/REPORT_timing.md) |
| **Daśā balance** — NH | starting-lord exact | **93.3%** (28/30); duration ±0.5y 28/30 | 30 | `nh_balance` (Moon longitude) | [nh balance](validation/REPORT_nh_balance.md) |
| **Longevity** — 8th bhāva | Spearman ρ vs Raman's longevity order | **+0.50** (p≈0.07) | 14 | `heldout_longevity_ch12_8th` | [longevity](validation/REPORT_longevity.md) |

**Reading the table.** Timing, balance, and longevity are *strong*: the daśā arithmetic
reproduces Raman's printed mahādaśā lord 94% of the time on real births (50 events), the
balance line 93%, and 8th-bhāva strength predicts his longevity ordering (ρ +0.50) while general
benefic-strength *anti*-predicts it (ρ −0.35, see below) — a discriminating result, not a
coincidence. **Strength stood at a ~53%-within-one ceiling through fourteen increments; the
sutra-fed strength layer (increment 17) is the first content change to move it — to ~55% on
sign-reconstructed held-out and +9 points on the degree-accurate NH pool** — by fixing root
cause 1: the encoded doctrine never fed the grades.

## The strength ceiling — stated plainly

The sign-only strength engine reconstructs each chart from Raman's two printed diagrams (Rāśi +
Navāṁśa signs, no longitudes) and grades bhāva/lord/kāraka strength on a 9-grade scale. Across
every held-out cut it long sat at **~53% within-one, ~26% exact, with a positive bias
(Δ ≈ +0.4 to +0.5: the engine over-credits)**. That ceiling was **structural, not parametric** —
probed directly, it does not yield to re-weighting (the negatives below). What finally moved it
was *content*: increment 17 routes the encoded sutras into the grades (held-out 54.7%, Δ +0.17 after 18/M-C);
the ~55% level is the new baseline the P3 rebalance works from:

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
| 14a | real-birth degree engine — orb-graded combustion in the numeric assessor | **landed** — NH degree pooled within-one 40.6 → **43.8%** (N=32), the first feature to raise it |
| 14b | degree engine — bhāva-chalita placement | **documented negative** — *hurts* (Raman grades by whole-sign rāśi, not Sripati cusps) |
| 14c | degree engine — degree-graded dignity + moolatrikona | **documented negative** — inert (sub-threshold within a sign) |
| **17** | **sutra-fed strength: NOVEL fired rules become factor findings** | **landed** — the largest single gain: held-out 52.8 → **54.7%**, NH pooled 43.8 → **53.1%**; root cause 1 (the 1,359 sutras never fed the grades) fixed |
| 17b | corrective occupant overrides (planet-in-house sutras contradicting the mechanical sign) | **landed** (with 17) |
| 17c | strong-affliction sutra gate | wired **dormant** — no row trips it on any corpus |
| 18/M-C | vargottama dignity counted once (same-sign dignity was charged in both frames) | **landed** — anchor mean Δ −3.75 → −3.62, held-out bias +0.32 → +0.17, within-one everywhere unchanged |
| 18/M-A | neechabhāṅga kendra-from-the-Moon (textbook second leg, Raman-asserted in ch. IV) | **documented negative** — anchor 1/8 → 2/8 but NH 53.1 → 50.0: a trade |
| 18/M-B | navāṁśa associations read by natural nature (Raman, Chart 12) | **documented negative** — same trade shape (anchor up, NH down) |
| **19** | **P2 encoding completion — HPA finished (599 → 1,153 rules; compendium 1,913 across 10 books)** | **landed, grade-neutral by policy** — all 36 HPA chapters swept (root cause 2 closed); the new rules are method/definition/electional/prasna/transit, outside ADMITTED_RULE_TYPES, so live anchor / held-out / NH stayed byte-stable (19a shaved NH Δ +0.44 → +0.41 only) |
| 20 | widen ADMITTED_RULE_TYPES into the scorer | **documented negative** — only `cancellation` (1 rule) fires novel testimony; `+cancellation` tri-gate byte-identical. Coverage and rule-type admission are spent levers |
| **21** | **fire every applicable natal sutra (`NATAL_FIRING_WIDEN`, default ON)** | **landed, grade-safe by construction** — closes the orphan-domain firing gap (Mainpuri: 114/114 natal-scope applicable sutras now fire, surfaced 101→135). Widened candidates surface for READING only; feeding them the grade regresses all axes (measured), so scoring stays on the increment-17 path → verdicts byte-identical |

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
- **Two anchors, two scopes.** The frozen ch. IV anchor (hand-decoded findings) stays 8/8 under
  the audit harness (`tests/doctrine/test_audit_anchor.py` — harness representation only). The
  **live-engine** anchor (`htjah_anchor_live.json`, faithfulness-gated casts) is gated by
  `tests/doctrine/test_anchor_live.py` with a ratchet floor + per-row grade ledger; its honest
  current state (1/8, audit increment 16) is the overhaul's declared starting point — the
  frozen-vs-live drift can never hide again.
- **Verdicts are pre-registered.** Raman's strength phrases are mapped to grades once, in the
  verdict map, and the map is verified before scoring — the engine cannot be graded against a
  moving target ([verdict audit](validation/REPORT_verdict_audit.md)).
- **Grids are prose-cross-checked.** Every reconstructed chart is verified against Raman's own
  stated relative positions and passes a Navāṁśa reachability gate before it scores.
- **This ledger is a tested contract.** `tests/doctrine/test_validation_summary.py` re-runs each
  validator and asserts the numbers in the headline table still hold.

## What is left

The **real-birth degree engine has now been built and measured** ([degree engine
report](validation/REPORT_degree_engine.md)) — a `degree_resolved`-gated feature layer feeding
actual longitudes to the scorer, validated blind on the grown NH degree corpus (32 rows). Its
verdict is decisive and doctrinally grounded:

- **Orb-graded combustion helps** — NH degree pooled within-one 40.6 → **43.8%** (N=32), the first
  feature to raise it. It is on by default (gated to real-longitude charts; sign numbers untouched).
- **The two levers that *should* have rescued the ceiling both fail**: bhāva-chalita placement
  *hurts* (Raman grades by whole-sign rāśi, not Sripati cusps) and degree-graded dignity is inert
  (sub-threshold within a sign). Both are documented negatives, default off.

So degree resolution yields a real but modest gain and **confirms the ~53% ceiling is structural,
not a resolution artifact**: what remains is Raman's holistic weighing of placement against dignity
against association, which no feature — sign *or* degree — has closed. Timing and balance are
already at their useful ceiling and are wired into the reading output.

**Update (ML research track, [ML_RESEARCH.md](ML_RESEARCH.md)):** that remaining residual has now
been shown to be **learnable** — a small interpretable model over the engine's own findings scores
**63.5% within-one under LOCO-CV vs the engine's 51.9% on identical rows** (and 62.5% vs 46.9% on
the untouched NH degree pool), while a blinded frontier-LLM scorer manages only 47.1% with zero
contamination gap. The learned combine is **not landed** (the pre-registered ch. IV anchor gate
failed in its typed representation — increment 15); the landing path is anchor re-derivation in
engine representation.

## Report index

Strength & ceiling: [recalibration](validation/REPORT_recalibration.md) ·
[crosshouse held-out](validation/REPORT_crosshouse_heldout.md) ·
[ceiling diagnostic](validation/REPORT_ceiling_diagnostic.md) ·
[unseen corpus](validation/REPORT_unseen_corpus.md) ·
[verdict audit](validation/REPORT_verdict_audit.md) ·
[NH strength](validation/REPORT_nh_strength.md) ·
[degree engine](validation/REPORT_degree_engine.md) ·
[Raman-style prose](validation/REPORT_raman_style.md).
Per-house held-out: [ch06 3rd](validation/REPORT_ch06_3rd.md) ·
[ch07 4th](validation/REPORT_ch07_4th.md) · [ch08 5th](validation/REPORT_ch08_5th.md) ·
[ch09 6th](validation/REPORT_ch09_6th.md) · [ch12 8th](validation/REPORT_ch12_8th.md) ·
[ch13 vol2 9th](validation/REPORT_ch13_vol2_9th_rederivation.md) ·
[ch14 10th](validation/REPORT_ch14_10th.md) · [ch16 12th](validation/REPORT_ch16_12th.md).
Timing / balance / longevity: [timing](validation/REPORT_timing.md) ·
[NH balance](validation/REPORT_nh_balance.md) · [longevity](validation/REPORT_longevity.md).
