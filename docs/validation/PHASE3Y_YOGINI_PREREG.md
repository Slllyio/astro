# Pre-registration: Phase 3Y, YOGINI dasha timing (Parashara engine, Phase 3 instrument)

Committed 2026-10-21, BEFORE any Yogini exposure has been computed for any person. User-approved
(the open option named in `VALIDATION_SUMMARY.md` "Handoff"). Phases 3, 3R and 3P are not re-run
or re-read. The engine code is untouched; the runner only calls it.

## Doctrine (the Parashara engine's own, cited)
- **Mahadashas:** `app/parashara/primitives/yogini_dasha.py` (BPHS-46:199). Eight Yoginis, lords Moon,
  Sun, Jupiter, Mars, Mercury, Saturn, Venus, Rahu, of 1..8 years (36 in total). The seed is
  (janma nakshatra + 3) mod 8, with remainder 0 = the 8th, Sankata. BPHS's own worked example is
  Mrigasira (5): 5+3 = 8, so Sankata (Rahu). Birth balance = `reading._birth_balance` (the Moon's arc
  through its nakshatra, BPHS-46:21-22), the same fraction the engine passes to `yog.timeline` in
  `reading._dashas`.
- **Antardashas:** `nakshatra_dasha.bhukti_timeline(yog.CYCLE, ...)` (BPHS-46:110, proportional parts):
  8 sub-periods starting with the MD lord's own, each MD × AD years / 36. The birth MD's antardashas are
  anchored at its true start (`elapsed` × its length before birth), exactly as `reading._dashas` does for
  Vimshottari. The engine reports no Yogini antardashas itself, so this is the engine's generic
  sub-period routine applied to the Yogini cycle. Nothing is invented.
- **Cycle repetition (stated, not hidden):** `yog.timeline` returns ONE 36-year cycle. A life of 5–95
  years spans up to three. The cycle repeats: each further cycle is `dasha_timeline(yog.CYCLE, seed)`
  with no balance, starting where the last one ended. The module calls the sequence a "cycle" whose
  order "IS" the dasha. The repo's legacy `app/core/yogini_ashtottari_dasha.py` repeats it the same way.
  Without repetition, ages ≥ 36 would have no Yogini period, and no other reading is possible.
- **Rahu (Sankata), from the engine:** Rahu owns no sign (`relationships.SIGN_LORDS`), so it is never a
  house lord or the lord-from-the-Moon. It casts no drishti (`graha_drishti.drishti_value`: "the nodes
  have no drishti in this BPHS-root engine"; `ASPECTING_GRAHAS` excludes it). So Rahu influences H only
  by **occupying H or conjoining H's lord**. It is a primary maraka only by occupying the 2nd/7th or
  conjoining their lords, and it is "associated" with another lord only by conjunction. This is
  exactly how Phase 3 treated Rahu as a Vimshottari lord. Ketu has no Yogini.

## Instrument (Phase 3's, unchanged, with the Yogini lords substituted)
`tools/validation/activation_store.influence` (Raman's factors a–e via `activation.influences`, plus (f)
lord-from-the-Moon), `associated` (conjunction or mutual aspect), `tier` (4 par excellence / 3 ordinary /
2 limited / 1 feeble / 0), and `primary_maraka` for own death (HTJAH-II:4494-4509). Lahiri primary.
- **P1 (Yogini AD level, day-dated events):** the (Yogini MD, Yogini AD) period has tier ≥ 3 for H
  (death: `t_mk` ≥ 3).
- **P2 (Yogini MD level, year-dated events at mid-year):** the Yogini MD lord influences H
  (tier ∈ {1, 3, 4}; death: the MD lord is a primary maraka).
- Multi-house sets take the max tier over the set, as `riskset_timing.Store.tier` does.

## Design (Phase 3's risk sets, identical)
`riskset_timing.load_events` / `build_sets`, EVENT_MAP at 08058ff6 plus the audit fixes, A+B discovery,
population = the people in the Phase 3 Lahiri activation store, 10 same-tier, same-decade controls on
their own charts at the event age, seed 20261014 (same draw order, so the same 13,034 sets: 2,365
day-dated → P1, 10,669 year-dated → P2). Per the Phase 3R lesson, there are **two effects per primary**:
- **E_rs** = case exposure − mean of its 10 controls' exposure;
- **E_wp** = case exposure at the event − the case's OWN lifetime exposure share (exact time-share
  over ages 15–75, same level and house set).

**SIGNAL** = both E_rs and E_wp have a 95% CI above 0 (person-clustered bootstrap, 2,000) and Holm p
< .05 across {P1, P2}. **BOUNDED_NULL** = TOST at SESOI 0.03 passes for E_rs. Otherwise
**UNDERPOWERED**. An E_rs CI wholly below 0 is reported as **"opposite to prediction"**, never as support.
The CLR OR and MDE80 are reported alongside.

## Controls (before the real comparison; any failure stops the run)
- Replicated 500-draw sham (within-set label permutation, target 0) and planted (+0.03) gates for P1
  and P2, as `PHASE3_AMENDMENT_1`.
- **Placebo Yogini:** the same pipeline with the janma nakshatra one ahead (seed +1, same elapsed
  fraction). Right chart, wrong Yogini sequence. Its E_rs and E_wp are reported. A real effect must
  exceed it.

## Secondaries / sensitivity (descriptive, no tests)
- S1 dose-response: CLR slope on the Yogini tier 0–4 (P1 sets). S2 specificity: E_rs(target) − mean
  E_rs over the non-target houses (Phase 3 definition). S3 (double transit) is not run.
- **Raman ayanamsa** (`SIDM_RAMAN` via `reliability.install_ayanamsa_patch`), same sets.
- **Rodden AA vs A**, per event family (≥ 30 events).

## Holdout
C1 (`holdout_manifest_tierC1.json`) is claimed ONCE via `HoldoutGuard` as `phase3Y_confirm`, and
**only if P1 or P2 is SIGNAL as defined above**. Otherwise C1, C2, Gauquelin and Wikidata stay unread.

## Prior and power
Expected: null. Phases 3, 3R and 3P found Vimshottari activation null at every level. The Yogini MDs are
1–8 years, so P2 coverage is lower-grained than Vimshottari's, and MD exposure sits near half of all
time. Power: P1 n = 2,365, MDE80 ≈ 0.03 on E_rs (at the SESOI edge); P2 n = 10,669, MDE80 ≈ 0.014.
