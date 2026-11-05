---
title: "Fidelity fixes R1-R6: results (2026-10-24)"
kind: analysis
topic: validation
measured: true
updated: 2026-10-24
tags: [raman-saab, holdout, prereg-result]
---
# Fidelity fixes R1-R6: what happened

The user asked to implement every recommendation in `WHY_273_OF_396.md`. Each fix was
pre-registered before any number existed (`FIDELITY_FIXES_PREREG.md`, commit 45607ef) with one
decision rule: real errors may not rise overall or in any book, within-one may not fall, and
exact must rise or real errors fall.

## Outcome

- **The measurement got more truthful; the engine did not change.** Two engine-blind
  reviewers re-read 102 labels. They corrected 23: 15 "mixed" rows were one-sided conclusions,
  1 one-sided row was two-sided, and 7 held no conclusion and left the scored pool.
- **None of the five engine fixes passed.** Each one that gained exact rows also created at
  least one new inversion (table below).
- **There is now an out-of-sample figure.** On 36 unseen Raman conclusions the engine scores
  63.9% exact and 77.8% within one, with 22% inversions.

| | Exact | Within one | Real errors |
|---|---|---|---|
| Golden pool before (396 rows) | 273 (68.9%) | 363 (91.7%) | 33 |
| Golden pool after label review (389 rows) | 275 (70.7%) | 351 (90.2%) | 38 |
| Sealed hold-out, unseen (36 rows) | 23 (63.9%) | 28 (77.8%) | 8 |

| Fix (re-labelled pool) | Exact | Within one | Real errors | Why it failed |
|---|---|---|---|---|
| R1 lord/karaka condition from Raman's grammar (old 396-row pool; not re-run after it failed gate 1) | 238 | 338 | 58 | agrees with Raman's own strong/weak words less often than Shadbala |
| R2 re-scope ten rules from their citations | 277 | 350 | 39 | one new inversion (HTJAH-II h11_08 gains) |
| R3b tie-break by preponderance, cast charts | 280 | 335 | 54 | sixteen new inversions |
| R4 tie-break by preponderance, stated charts | 284 | 350 | 39 | one new inversion (NH) |
| R5 general lord-affliction rule | 271 | 350 | 39 | fixes four inversions, creates five |

## What it means

1. Raman reasons past a malefic-afflicted lord about as often as he lets it decide. R1, R5 and
   the earlier disposition prereg all hit this from three directions. Nothing the engine
   computes separates his two behaviours, so any lord-affliction signal trades errors one for one.
2. R2 and R4 each come within one row of passing. R2 makes ten rules say exactly what Raman's
   sentences say; it fails only because one chart was right by accident through the rule it
   corrects. Both are held as patches (`held_patches/`) for a user decision.
3. The hold-out confirms the warning in the audit: the in-sample figure is flattered. The
   out-of-sample inversion rate is about twice the pool's.

## What would actually move fidelity next

- More unseen Raman charts. Thirty-six rows give a wide interval (exact 47% to 79%). The 3HC
  charts rejected only for OCR-garbled dates (13 balance mismatches, 10 missing fields) can be
  recovered from page images, and Studies in Jaimini and HPA have more.
- A different mechanism, not a tuned one: the misses cluster where Raman weighs a malefic contact
  against something the engine does not read (the native's status, the dasha that ran, the
  specific matter). That is design work for a separate decision.
