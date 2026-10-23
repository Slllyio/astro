# Pre-registration: Phase 3J, Jaimini CHARA dasha timing (Parashara engine)

Committed 2026-10-24, BEFORE any chara-dasha exposure has been computed for any person.

The owner chose option A on 2026-10-21: encode chara dasha in the Parashara engine from BPHS and the Jaimini Sutras,
then test it. The engine is `app/parashara/primitives/chara_dasha.py` at 13087d3f. Its rules come from
`docs/parashara/CHARA_DASHA_RULINGS.md` (owner instruction: "find answers in ancient texts"), and a
bphs-doctrine-reviewer pass was applied. Phases 3, 3R, 3P and 3Y are not re-read.

## Doctrine, with every CONVENTION and deferral listed
TEXT-SETTLED (BPHS-46 sl.155-167):
- pada grouping (savya = signs 1-3, 7-9);
- the sequence starts at the Lagna sign, onwards iff the 9th sign is in an odd pada;
- the twelve repeat;
- years = n − 1, counted from the sign to its lord in the sign's pada direction;
- the Scorpio/Aquarius co-lords (Mars+Ketu, Saturn+Rahu): both lords in the sign → 12; one in → count to the other;
  otherwise the lord with a planet, then more planets, then the stronger sign (dual > fixed > movable).

CONVENTIONS (BPHS silent or ambiguous; the reading used is named):
1. Own-sign lord = 12 years: Raman's n − 1 form (SJ art.80); the classical anchor is Jaimini ch.9:752.
2. ±1 for the lord's exaltation/debilitation, applied to every sign and to the n − 1 figure (Jaimini ch.9:756;
   Raman art.80). Node exaltation is from BPHS-47:280-284 (Rahu Taurus, Ketu Scorpio); there is no node debilitation.
3. The dual-lord last rung: a lone exalted lord, then the larger number of years (Jaimini ch.9:797-800; Raman art.86).
4. Repetition with the same years (an inference from BPHS-46:4837).
5. **Activation (the instrument):** the running chara dasa sign activates house H iff it is the H-th sign from the
   Lagna. This is Raman, *Studies in Jaimini* art.159 (SJ ch.9:870-874): results "pertain to the events of the
   Bhava which it happens to represent from Lagna or Atmakaraka or even Karakamsa". Neither BPHS nor the Jaimini
   Sutras on disk define house activation for a rasi dasa. For a two-house set ({2, 11}) the dasa sign may be either.

DEFERRED / EXCLUDED:
- **Antardashas** (rulings Q4: BPHS-51 sl.6 vs sl.7-12 unresolved). There is therefore **no AD-level test**.
- **Death events, own and relatives'**, are excluded: SJ art.159 assigns death to Sthira / Niryana Shula Dasa, not to
  the bhava rule. Applying it to death would be an invention.
- Node debilitation (not in BPHS-47).

## Design (Phase 3's risk sets, identical draw)
`riskset_timing.load_events` / `build_sets` (EVENT_MAP at 08058ff6 + audit fixes), A+B discovery, population = the
Phase 3 Lahiri store's people, 10 same-tier same-decade controls on their own charts, seed 20261014. The draw is the
same, so the sets are Phase 3's 13,034. The 4,869 whose event is a death are then dropped, leaving **8,165**.

Every set is scored at the mahadasha level:
- **P_y:** year-dated events (n = 6,973), at mid-year;
- **P_d:** day-dated events (n = 1,192), at the exact date.

Exposure: the dasa sign running at the event age is H's sign from the Lagna. Two effects per primary:
- **E_rs** = case exposure − mean of its 10 controls;
- **E_wp** = case exposure − the case's own exact lifetime time-share, ages 15–75.

Verdicts (identical rules to 3P/3Y):
- **SIGNAL** = both 95% CIs (person-clustered bootstrap, 2,000) above 0 and Holm p < .05 over {P_y, P_d};
- **BOUNDED_NULL** = TOST at SESOI 0.03 passes on E_rs;
- otherwise **UNDERPOWERED**;
- an E_rs CI wholly below 0 = **"opposite to prediction"**.

The CLR OR and MDE80 are reported.

## Controls (before the real comparison; any failure stops the run)
- 500-draw sham (within-set permutation, target 0) and planted (+0.03) gates for P_y and P_d (`PHASE3_AMENDMENT_1`).
- **Placebo:** the chara sequence seeded one sign ahead (the engine's `timeline` from Lagna + 1, same planets).
  Activation is still judged from the real Lagna, so it is the right chart with the wrong sequence. Its E_rs and E_wp
  are reported, and a real effect must exceed it.

## Sensitivity / secondaries (descriptive, no tests)
- **Raman ayanamsa** (`SIDM_RAMAN` via `reliability.install_ayanamsa_patch`), same sets.
- **Rodden AA vs A**, and per event family (≥ 30 events).
- **Wider activation:** the dasa sign is H-th from the Lagna OR the Atmakaraka's sign OR the Karakamsa
  (`chara_karaka`, BPHS-32/33). This is the full art.159 reading.
- **S2 specificity** (Phase 3 definition).

## Holdout
C1 (`holdout_manifest_tierC1.json`) is claimed ONCE via `HoldoutGuard` as `phase3J_confirm`, only if P_y or P_d is
SIGNAL as defined. Otherwise C1, C2, Gauquelin and Wikidata stay unread.

## Prior and power
Expected: null. Every earlier timing system was a bounded null. One sign covers ~1/12 of a life, so the base rate is
~0.09 and the SESOI of 0.03 is a ~+35% relative excess: a generous bar. MDE80 ≈ 0.010 (P_y) and ≈ 0.024 (P_d), both
under the SESOI.
