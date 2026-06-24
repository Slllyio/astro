# Session R10 — H2 Accuracy Fix (Rule Refinement)

**Date:** 2026-06-13, ~2:00–2:15pm IST
**Branch:** `round8-unification`
**Commit:** `b0a9126` feat(raman_saab): H2 rule refinement — 6 fixes, ratchet 16/37 -> 18/37

---

## What Was Done

### Step 1: Rule-Level Fixes in `combinations.py` (ALL SHIPPED)

| Fix | Rule | What Changed |
|-----|------|-------------|
| 1a | H2.C.6 | Added `FunctionalNature("Jupiter", {"malefic"})` guard to Jupiter-in-2nd branch. Prevents false benefic when Jupiter is 3L/12L (e.g. Capricorn Lagna) |
| 1b | H2.C.65 | Chandramangala Yoga: descriptive -> evaluable. Condition: `Conjunct("Moon","Mars") OR MutualAspect("Moon","Mars")` |
| 1c | H2.C.65a | Mars-Moon mutual kendra: descriptive -> evaluable. Uses `InHouseFrom("Mars","Moon",{1,4,7,10})` with Not guards to prevent double-fire with C.65 |
| 1d | H2.C.66 | Gajakesari Yoga: descriptive -> evaluable. Condition: `InHouseFrom("Jupiter","Moon",{1,4,7,10})` |
| 1e | H2.C.69 | NEW malefic rule: `AllPlanetsInDwirdwadasha()` -> wealth severely curtailed |
| 1f | H2.C.70 | NEW malefic rule: `_LordAspectsHouse(6, 2)` -> 6th lord aspects 2nd house |

New local leaf added: `_LordAspectsHouse(lord_house, target_house)` — resolves lord of a house, checks drishti on target house.

### Step 2: CONTRA_PILLAR Calibration (REVERTED)

- Changed `CONTRA_PILLAR_AFFLICT` and `CONTRA_PILLAR_FAVOUR` from 99 -> 2 in `total.py`
- **Result:** H1 regressed (7/12 -> 6/12), net score dropped (18 -> 17)
- **Decision:** REVERTED to 99. Pillar preponderance is too aggressive without more house coverage.
- Tests for preponderance behavior (`test_house_template.py`, `test_preponderance.py`) remain unchanged.

### Step 3: Measure + Re-base (SHIPPED)

- Track-B accuracy: **16/37 (43.2%) -> 18/37 (48.6%)**
- H1: 7/12 unchanged
- H2: 5/13 -> 7/13 (+2)
- H3: 4/12 unchanged
- Baseline updated in `tests/fixtures/golden_accuracy_baseline.json`
- All 1925 raman_saab tests pass

---

## Remaining H2 Mismatches (6 of 13)

| Chart | Expected | Engine | Root Cause |
|-------|----------|--------|-----------|
| 39 | afflicted (vision) | favourable | Vision signification — separate from wealth |
| 42 | afflicted (wealth) | favourable | Dwirdwadasha fires but polarity reversal persists; missing more malefic rules |
| 43 | favourable (wealth) | mixed | Both benefic+malefic fire, CONTRA=99 -> always mixed |
| 44 | afflicted (wealth) | mixed | Same contradiction issue (CONTRA=99) |
| 45 | favourable (wealth) | mixed | Same contradiction issue |
| 48 | mixed (wealth) | favourable | H2.C.70 fires malefic but other benefics still outweigh |
| 50 | afflicted (wealth) | favourable | Dhana Lagna method not yet encoded (needs ArudhaLagna predicate) |

**Key insight:** Charts 43, 44, 45 need CONTRA_PILLAR < 99 to resolve, but pillar calibration
hurts H1. This is a cross-house calibration problem — needs more house coverage (H4-H12)
before the threshold can be safely lowered.

---

## What To Do Next

1. **Stage 4 house encoding** — continue encoding H4+ houses per the execution plan
2. **Chart 50** — needs `ArudhaLagna`/`DhanaLagna` predicate (Special Dhana Lagna rules #49-58)
3. **CONTRA_PILLAR revisit** — defer until 6+ houses encoded, then re-test pillar=2
4. **H2 vision signification** (chart 39) — separate issue from wealth rules

---

## Files Modified This Session

- `app/raman_saab/doctrine/rule_sets/house_02_dhana/combinations.py` — 6 rule fixes + new leaf
- `tests/fixtures/golden_accuracy_baseline.json` — re-based 16/37 -> 18/37
- `tests/fixtures/golden_snapshots/HTJAH-I.chart_{38-51}.json` — regenerated (12 files)

## Key Observations for Memory

- `InKendraFrom` predicate does NOT exist in conditions.py. Used `InHouseFrom(planet, origin, {1,4,7,10})` with Or combinator instead.
- `FunctionalNature` takes `set[str]` not `str`: `FunctionalNature("Jupiter", {"malefic"})`.
- `Aspects` condition takes two planet names. For lord-aspects-house, need a local leaf.
- CONTRA_PILLAR=2 causes H1 false-favourable bias (strong pillars + any contradiction -> favourable, but many H1 charts should be mixed/afflicted).
