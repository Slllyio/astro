---
title: "Stage-9 v1 completion scorecard — first full measurement"
kind: record
topic: process
measured: true
updated: 2026-08-17
tags: [raman-saab, record, process]
---
# Stage-9 v1 completion scorecard — first full measurement (2026-08-17)

EXECUTION_PLAN.md Stage 9 defines "done (v1)". The accuracy figure is reported at
every ratchet run; the OTHER gates had never been measured. This is the first full
measurement — reproduce with `python -m tools.raman_saab.stage9_scorecard`.
Engine state: main-aug + B3/B4 (PR #17 head `c562b87`).

| # | Gate | Bar | Measured | Verdict |
|---|---|---|---|---|
| 1 | Track-B accuracy | ≥90% over ≥150 confirmed | **259/293 = 88.4%** (volume ✓) | **NOT MET** — and per the Measured-Truth record this is the PROVEN CEILING (five independent methods); the bar exceeds what faithful encoding reaches on this corpus. See "Verdict" below. |
| 2 | Per-house minimum | ≥8 confirmed per house | all 12 houses ≥15 (min H3=15, max H7=45) | **MET** |
| 3 | Abstain ceiling | insufficient-evidence on ≤10% of decisive goldens | **0/292 = 0.0%** | **MET** (the engine never hides behind abstention) |
| 4 | Holdout | reported separately, within 10 pts of fit, gated ≥20 | **NOT OPERATIONALIZED** — no fit/holdout split exists in the golden harness; every confirmed verdict participates in the ratchet | **NOT MEASURABLE** as specified |
| 5 | Rule corpus | ≥ ~900 evaluable cited rules | **718 evaluable** of 847 placement/combination rules (all 847 cited) + 72 yogas | **NOT MET** (bar is a volume proxy, not fidelity) |
| 6 | Mismatch documentation | every remaining mismatch has a doctrinal reason on file | **16/34** of the current mismatches appear in DOCTRINE_BACKLOG.md | **NOT MET** — the 18 undocumented are almost all H9–H12 rows post-dating the documented-limits register (list below) |

Per-house confirmed accuracy (the honest heat map of where the engine is weak):
H1 0.739 · H2 0.846 · H3 0.867 · H4 **1.000** · H5 0.909 · H6 0.941 · H7 **1.000** ·
H8 **1.000** · H9 0.800 · H10 0.921 · H11 0.810 · H12 **0.750**.

## What this measurement changes

1. **The H4-frame priority was mis-ranked.** NH_DRAFT_BACKLOG's "H4 mother/education
   cluster (~7 misses)" targets **DRAFT (unconfirmed) NH rows** — confirmed H4 is
   already perfect (16/16). Encoding the Moon-frame would move nothing on the ratchet
   until those DRAFTs are user-confirmed. The frame work should therefore WAIT on
   DRAFT confirmation, not precede it.
2. **The real weak houses are H1 (0.739), H12 (0.750), H9 (0.800), H11 (0.810)** —
   and gate 6 shows exactly those houses carry the undocumented mismatches. The
   cheapest honest next step is documenting each with its doctrinal reason (or
   fixing where a cited fix exists), not new mechanism work.
3. **Gate 4 needs a decision, not code**: either operationalize a confirmed-verdict
   holdout (freeze a random ≥20-verdict subset out of the ratchet — a one-way door
   worth taking deliberately) or amend Stage 9 to drop the gate with a reason.
4. **Gate 1 vs the ceiling**: the 90% bar predates the measured ceiling
   (88.4% exact / 96.6% within-1; five methods showed exceeding it requires
   overfitting). Recommend amending the bar to the two-axes form
   ("≥88% exact AND ≥96% within-1 AND real-errors ≤10") — with the USER's sign-off,
   since Stage 9 is the definition of done.

## Undocumented mismatches (gate 6 worklist)

HTJAH-I: chart_12, chart_17, chart_31, chart_45, chart_48 ·
HTJAH-II: h9_07, h9_08, h9_09, h9_12, h9_15, h10_04, h10_06, h11_02, h11_03,
h11_17, h12_01, h12_04, h12_08.
