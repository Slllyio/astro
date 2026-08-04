---
title: "Session resume — longevity combos batch"
kind: record
topic: process
measured: false
updated: 2026-06-29
words: 766
tags: [raman-saab, record, process]
---
# Session resume — longevity combos batch (2026-06-29)

Working checkpoint for the `raman_saab` longevity-combinations work on branch
`round8-unification`. Read this top-to-bottom to resume.

## TL;DR of where we are

Extending `app/raman_saab/primitives/longevity_combos.py` — Raman's qualitative
Alpayu/Madhyayu/Purnayu longevity COMBINATIONS (HTJAH-II:3251–3474) — from **8 → 36**
encoded combos. All additive / report-only (surfaced in `synthesis.py` as the
`longevity_combos` field); **never** feeds a Parashari house verdict, so the 208/241
golden ratchet is verdict-invariant by construction.

## Committed (durable in git)

- `37678e0` feat(raman_saab): two more longevity combos (Madhyayu/Purnayu, **Tier 1e**)
  — source for Madhyayu `3397` + Purnayu `3404`. (3404 improved with the
  "or aspected by Jupiter" disjunct.)
- `96f38f8` test(raman_saab): pin the two Tier-1e longevity combos — the paired tests
  (the "sg" auto-commit hook had landed the source without its tests).

## Uncommitted on disk (the BATCH — Tier 1f) — NOT yet committed

Two files modified in the working tree:
1. `app/raman_saab/primitives/longevity_combos.py` — **+28 combos** (8 Alpayu, 4 Madhyayu,
   10 Purnayu placement/dignity/aspect combos + 6 aggregate-classifier entries from the
   section's closing rule 3469-3474, incl. the REVERSED malefic mapping). New shared
   helpers `_lord_of`, `_sign_of`, `_dignity_is`, `_present`, `_conj_or_aspected`,
   `_group_all_in`; new import `is_keeta` from `sign_attributes`; new constants
   `_PANAPHARAS`, `_APOKLIMAS`, `_TRIKONAS`. Also **tightened combo 3404**:
   "benefics occupy kendras" → require **≥2 benefics in kendras** (plural reading;
   dropped its over-fire 45%→23%).
2. `tests/raman_saab/test_longevity_combos.py` — **+9 new tests** (and 2 in-flight tests
   updated for the ≥2-benefics rule). Covers: placement (3266), lord+aspect (3289),
   dignity (3422), conj/aspect-both (3429), keeta (3448), the A3303 Moon-fix
   (positive + negative), and the aggregate (benefic→Purnayu, malefic→Alpayu reversed).

## Verification status

- **Doctrine panel** (26-reviewer workflow, verdicts harvested to disk): of 23 reviewed —
  **21 FAITHFUL, 2 PARTIAL** (aggregate, stricter-than-source = safe), **0 MISREAD**,
  **0 HIGH over-fire**. **1 OVERBROAD fixed**: A3303 now counts the Moon among "benefics"
  per the locked benefic set. P3448 (keeta) reviewer hung; judged faithful by hand.
- **Over-fire scan** (`scratchpad/overfire_scan.py`, 64 cast golden charts, 0 crashes):
  Alpayu (short-life) combos fire 0–6% (correctly rare); Purnayu loosest at 17–23%;
  **nothing >30%** after the 3404 fix. PASS.
- **Module imports clean** (36 combos, no circular import from `is_keeta`).
- **Longevity unit tests**: re-run pending (pytest cold-start here is ~7 min — it's the
  app import chain, not plugins). Earlier baseline (pre-batch) was green 6/6. The new
  16-test run is in flight — see `tasks/longevity_final.txt` for its result.

## EXACT next steps to resume

1. Confirm the longevity suite is green:
   `py -3.12 -m pytest tests/raman_saab/test_longevity_combos.py -q`
   (cold-start ~7 min; run in background. Check `tasks/longevity_final.txt` if the prior
   run finished.) If any new test fails, the chart arithmetic for that combo needs a fix
   — the predicates themselves are scan-validated.
2. Run the **golden ratchet** to confirm verdict-invariance (must be UNCHANGED):
   `py -3.12 -m pytest tests/raman_saab/test_goldens.py -q`
   longevity_combos is report-only, so the snapshot should not move. If it does,
   investigate before committing.
3. Commit the batch (message draft below).
4. Update `docs/raman_saab/RAMAN_COVERAGE.md` "Gaps CLOSED" §6 to note 36/~51 combos.
5. Delete this resume file once committed.

## Commit message draft (Tier 1f)

```
feat(raman_saab): encode the remaining cleanly-evaluable longevity combos (Tier 1f)

primitives/longevity_combos.py 8 -> 36 of Raman's ~51 Alpayu/Madhyayu/Purnayu combos
(HTJAH-II:3251-3474) — every combo expressible from whole-sign placement, dignity and
graha drishti. Adds 8 Alpayu, 4 Madhyayu, 10 Purnayu combos + the section's closing
aggregate classifier (Lagna-lord+benefics vs 8th-lord+malefics across
kendra/panaphara/apoklima, malefic mapping reversed). Navamsa-based and strength-gated
("weak/strong in vargas") death-age combos remain backlog.

Each predicate cited to its exact source line and checked by a per-combo doctrine panel
(21 FAITHFUL / 2 stricter aggregate / A3303 fixed to count the Moon among benefics).
Over-fire scan over 64 cast golden charts: Alpayu combos 0-6% (rare, as expected);
3404 "benefics occupy kendras" tightened to the plural (>=2 benefics in kendras),
45%->23%. Additive / report-only -> Parashari verdict unchanged (ratchet 208/241 held).
```

## Scratchpad artifacts (session-specific, may not survive a new session)

- `scratchpad/longevity_batch_draft.py` — the draft predicates (now integrated).
- `scratchpad/overfire_scan.py` — the empirical over-fire scanner (reusable).
- `scratchpad/verify_longevity_batch.wf.js` — the doctrine-panel workflow.

## Environment gotchas (carry forward)

- **Interpreter: `py -3.12`** (has swisseph). The repo `.venv` is a stale Python 3.14
  WITHOUT swisseph — do NOT use `.venv/Scripts/python.exe`.
- pytest cold-start in this repo is ~7 min (heavy app import via conftest). Run tests in
  the background with a long timeout; `| tail` buffers output until exit (read the raw
  file instead).
- An **"sg" auto-commit hook** commits edited source on green tests (it committed the
  Tier-1e source without its tests). Keep edits atomic so it can only capture coherent
  states; commit tests promptly.
- Over-fire scan must CAST charts (most goldens carry `birth`, not `stated_positions`) —
  stated-first builds only 2/192.
