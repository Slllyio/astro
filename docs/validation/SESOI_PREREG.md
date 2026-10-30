# Pre-registration: smallest effects of interest (SESOI) and the Phase 1 re-bound

Committed 2026-10-13, BEFORE `tools/validation/rebound.py` existed or computed any bound. Git order
is the date-lock. User-approved plan: `purpose-build-out-the-linked-stearns.md`, Phase 1.

## SESOI per family (effect scale where 0 = no effect)
Each SESOI is set at or BELOW the size the doctrine's own wording implies. An effect smaller than
the SESOI would be useless for reading an individual chart, even if it were real.

| family | effect scale | SESOI |
|---|---|---|
| static house verdict vs outcome | AUC − 0.5 | 0.03 (AUC 0.53) |
| rule enrichment | log RR | log 1.20 |
| timing (within-person lift, cross-chart excess) | hit-rate difference | 0.03 |
| vocation | log RR | log 1.10 |
| lifespan | Spearman ρ | 0.05 |

## Verdict per test (`tools/validation/result.py`, unchanged)
SHAM_FAIL (sham not null) > SIGNAL (CI95 excludes 0) > BOUNDED_NULL (TOST p < .05 at the SESOI,
i.e. the 90% CI lies inside ±SESOI) > UNDERPOWERED. These re-bound records have no chartless arm,
so SIGNAL here means the CI excludes 0, nothing more.

## Inputs (read as published; nothing is re-run)
- Parashara: `static_results.json`, `timing_results.json`, `transit_results_pooled.json`
  (the pooled A+B file replaces the primary `transit_results.json`, so events are not double-counted).
- Raman: `static_results.json`, `timing_results.json`, `confirmatory_results.json`.
- SEs: the stored `se` where present, otherwise (CI width)/3.92. Sham rows are the gate, never data.
- Timing instruments the original run WITHHELD for saturation are reported, never pooled.
- Raman 91-rule enrichment: per-rule results were not persisted, so τ across rules is NOT computed
  here. It moves to Phase 4.2 (rule-level dose-response), computed from `rule_fires.parquet`.

## Pooling
- DerSimonian–Laird, **within one engine and one family only**. The two engines score the same
  people, so a cross-engine pool would count each person twice.
- Caveat fixed in advance: tests within an engine share contrast groups, so DL treats them as
  more independent than they are and the pooled CI is too narrow. **The per-test TOST is the primary
  readout; the pool is secondary** and is labelled as an optimistic bound.
- The H5-children inversion is pooled as measured (wrong-direction effects stay negative).

## Decision rule
If every non-withheld static test in an engine is BOUNDED_NULL: stop new house-AUC tests on that
engine; static questions continue only in rule-level form (Phase 4.2). UNDERPOWERED tests are
listed as the only places where new static data could still matter.
