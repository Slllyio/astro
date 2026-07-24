# Pre-registration — the Survivors' Gauntlet (Stage 11)

> Committed before computation. Across BOTH programs (raman_saab doctrine-encoding + medini ML),
> twelve-plus rounds of testing left exactly THREE surviving positives. Each now faces the combined
> maximum-rigor protocol. Directions, samples, and success criteria locked here; results reported
> regardless of outcome. The medini audit (docs/medini/ML_AUDIT_2026-07-24.md) defines the fixes
> each re-run must include.

## G1 — medini framework career→10H verdict (exploratory lift 1.37, n=11,753 events)

The "first project-wide positive doctrinal signal across 12 rounds" (framework_validation_v1):
AND-gated Yoga×Dasha×Gochara strong-verdicts at event time vs career events. AT RISK from the
audited name-join contamination (events attached to homonyms' charts) and ghost exposure
(uncensored windows).
- **Re-run requirements:** person_id joins (no raw names); windows capped at min(death, scrape);
  the month-anchored negative sampler retained; era (birth-decade) and source stratification;
  person-clustered bootstrap CI on the lift.
- **Success:** lift > 1.0 with 95% CI excluding 1.0 after ALL fixes. Prediction: unresolved — the
  1.37 may be name-join/exposure artifact or real.

## G2 — medini WD per-person marriage (+0.043 AUC over cyclic-date controls)

The one narrow effect that survived medini's own date controls. Re-run under the clean template
(`wedge_eval_v2.py` group-split machinery) PLUS person_id dedup, source restriction to the
source(s) carrying marriage labels, and an era-only baseline arm.
- **Success:** chart-arm AUC − era/date-baseline AUC > 0 with person-grouped bootstrap CI
  excluding 0.

## G3 addendum — suicide → afflicted H8 (twice-seen, unconfirmed at p=.062)

Corpus mining found only **52 genuinely new** suicide-labeled people (medini github-source tokens
absent from our master's labels) — insufficient to power the planned n≈500 confirmation
(218+52=270, ~58% power). Registered addendum, NOT a rescue:
- **Test:** the never-tested union — the 218 tier-C held-out cases PLUS whichever of the 52 new
  cases (a) resolve to master persons with non-noon times, (b) were never in the exploratory
  matrix, the tier-C confirmatory, or the store control pool with an H8 verdict already used.
  One-sided MW-U vs the same tier-C control pool, α=.05. This is a NEW test on an enlarged
  never-tested sample (not a second look at the same sample); the p=.062 prior result stands as
  reported regardless.
- **Honest framing:** even a pass at ~270 cases is fragile; the thread's definitive resolution
  still requires data that does not yet exist.

## Order & governance

G3-addendum first (cheap, pure store query + ≤52 casts), then G2, then G1 (heaviest — corpus
rebuild). All results appended verbatim to REAL_OUTCOME_GENERALIZATION.md. Nothing tunes either
engine; medini re-runs follow the audit's clean-rerun recipe exactly.
