# Pre-registration: Phase 3R, dasha timing through the RAMAN ENGINE's own house-activation code

Committed 2026-10-14, BEFORE any Raman-engine activation has been computed for any person.
User request: "follow the Raman technique of house activation; we used that technique in the
Raman engine". This is the one open path named in `VALIDATION_SUMMARY.md` ("Raman's own judge
driving the timing"). It is a NEW instrument under its own pre-registration. Phase 3 is not re-run
or re-read.

## Why this differs from Phase 3
Phase 3 applied Raman's four-tier SCHEME to the Parashara engine's inputs (Lahiri, Parashara
aspects, and a tools/-side rebuild of his influence factors). Phase 3R calls the Raman engine
itself, unchanged:
- `app.raman_saab.chart.adapter.cast_chart(..., ayanamsa="raman")`, the engine's default frame;
- `vimshottari.mahadasha_timeline` + `vimshottari.bhuktis`, the engine's own dashas;
- `vimshottari.timer_set(chart, H)`, unioned with `timer_set` of `_EVENT_AUX_HOUSES[H]` exactly as
  `vimshottari.active_houses` does (2↔11, 9↔12). Raman's fructification significators: the
  H-lord, the **H-karaka**, occupants, aspecters, planets conjoining or aspecting the lord, the
  H-lord from the Moon, and a **node whose dispositor is a timer**. Raman's drishti applies (nodes:
  7th only, the locked convention);
- `vimshottari.lords_associated` + `vimshottari.bhukti_tier`, exactly as `detailed_report.graded_buckets`
  uses them: par excellence (4) > ordinary (3) > limited (2) > feeble (1) > none (0).
- Death: the same tier scheme over the engine's `maraka_set(chart).primary` (Raman's primary
  marakas, consistent with the Phase 3 doctrine review). `maraka_set(...).all()` is a sensitivity arm.
The engine code is untouched. The store builder only calls it.

## Everything else is Phase 3, unchanged
Event → house map (doctrine-reviewed, `riskset_timing.EVENT_MAP` at 08058ff6 + audit fixes);
discovery tiers A+B; risk sets (10 same-tier, same-decade controls on their own charts, seed
20261014); P1 = AD tier ≥ 3 (day-dated), P2 = MD lord activates (tiers 1/3/4, year-dated);
E = case − mean(controls); SESOI 0.03; Holm over {P1, P2}; replicated 500-draw sham + planted gates
(`PHASE3_AMENDMENT_1`); placebo dasha (Moon +13°20′, the same elapsed fraction, built with the
engine's own `calculate_vimshottari_mahadasha` / `_sequence_from` / `bhuktis`); S1 tier
dose-response, S2 specificity. S3 (double transit) keeps Phase 3's Parashara-natal transit
definition and is labelled as such.

## Sensitivity arms (descriptive)
- **Lahiri frame:** the same Raman-engine instrument cast with `ayanamsa="lahiri"`.
- Death with `maraka_set().all()` (all three tiers).
- Rodden AA vs A precision gradient; per-family E; conjunction-only association.

## Holdout
C1 (`tools/validation/holdout_manifest_tierC1.json`) is claimed once as `phase3R_confirm`, and
**only if P1 or P2 is SIGNAL on discovery**.

## Prior and reading rules
- Expected: null. The engine's own docstring calls `active_houses` "broad-recall / low-precision by
  design: a slow lord times most houses", and Phase 3 found the narrower Parashara version null.
- The comparison with Phase 3 is reported side by side. A Raman-engine SIGNAL that Phase 3 lacked
  would be the most important result of the program and goes straight to C1.
