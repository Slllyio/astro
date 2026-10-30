# Amendment 2 to DOUBLE_TRANSIT_PREREG.md: withdraw the tier-C confirmation

Committed 2026-10-13, BEFORE any tier-C number was computed. No tier-C double-transit run has
happened: the holdout ledger has no claim, and the amendment-1 code could not read tier C until
commit 64721b38. Git order is the date-lock.

## What is withdrawn
Amendment 1, analysis 2: the one-shot tier-C confirmation run of the double-transit instruments.

## Why (decided by the user, recorded before any data was read)
The validation program (`docs/validation/`, Phase 6) allocates tier C once, across ALL timing
questions, rather than to one instrument:
- **C1** (hashed half, `assign_holdout(salt="tierC-split-v1")`) confirms the Phase 3 pooled risk-set
  timing test. **Double transit is one of its registered secondaries**, so the hypothesis still
  gets a held-out confirmation, at roughly 4x the power, because events are pooled across types.
- **C2** confirms the Phase 5 composite score.

Spending all of tier C on six double-transit instruments (≈200 day-dated marriages) would leave no
holdout for the better-powered tests.

## What is unchanged
Amendment 1, analysis 1 (the A+B extension, reported alone and pooled with the primary run) stands
exactly as written: same rule, instruments, controls and pass bar.
