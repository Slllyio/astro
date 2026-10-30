# Pre-registration: Phase 3J-AD, Jaimini chara ANTARDASHA timing (Parashara engine)

Committed 2026-10-24, BEFORE any chara antardasha exposure has been computed for any person.

The owner chose BPHS-51 sl.7-12 for the chara antardashas ("go with ur recommendation", 2026-10-24). The engine is
`app/parashara/primitives/chara_dasha.antardashas` at cec90acd (merged here as 7309c3ad). It was reviewed by
bphs-doctrine-reviewer (VALIDATED) and reproduces BPHS-51's three printed orders (Aquarius, Pisces, Aries).
Phase 3J (MD level) is not re-read.

## Doctrine (everything from Phase 3J's prereg carries over; added here)
- Antardasha length is 1/12 of the dasa (BPHS-51 sl.5). TEXT-SETTLED.
- Order (BPHS-51 sl.7-12, as the translator works it at 51:601-670). TEXT-SETTLED:
  - movable: the twelve in order;
  - fixed: every 6th rasi;
  - dual: the kendras of the dasa rasi, then of its 5th, then of its 9th;
  - onwards if the dasa (Paka) rasi is an odd sign, reverse if even.
- **CONVENTION:** a movable dasa's antardashas start at the dasa rasi itself. The verse is silent; this follows the
  translator's "(including Aries)" at 51:670 and the fixed/dual "start from it".
- **Recorded dissent, not used:**
  - sl.6's "or from the 7th, whichever is stronger";
  - Raman art.87 (a straight sequence from the 2nd rasi).
- Activation (CONVENTION, Raman *Studies in Jaimini* art.159), as in Phase 3J: a sign activates house H iff it is
  the H-th sign from the Lagna.
- Death events are excluded, as in Phase 3J.

## Design
Phase 3's risk sets (identical draw, seed 20261014), restricted to the **day-dated, non-death** sets: **1,192**,
exactly Phase 3J's P_d sets. An antardasha averages ~0.5 years, so only day-dated events can resolve it.

**Primary P_ad:** the running chara **antardasha** sign is the event house's sign from the Lagna. Holm is over this
one primary.

**Secondary S_conv** (descriptive): convergence, where the dasa sign AND the antardasha sign are both the house's
sign. Under sl.7-12 that is the house sign's own first antardasha inside its own dasa.

Two effects:
- **E_rs** = case − mean of 10 matched controls;
- **E_wp** = case − own exact lifetime share, ages 15–75.

Verdicts:
- **SIGNAL** = both 95% CIs (person-clustered bootstrap) above 0 and p < .05;
- **BOUNDED_NULL** = TOST at SESOI 0.03 passes on E_rs;
- otherwise **UNDERPOWERED**;
- an E_rs CI wholly below 0 = "opposite to prediction".

## Controls (before the real comparison; any failure stops the run)
- 500-draw sham and planted (+0.03) gates (`PHASE3_AMENDMENT_1`).
- **Placebo:** the whole chara sequence and its antardashas seeded at Lagna + 1. Activation is judged from the real
  Lagna. Reported, and a real effect must exceed it.

## Sensitivity (descriptive)
- Raman ayanamsa (same sets).
- Rodden AA vs A, and families (≥ 30).
- The wider art.159 activation (Lagna OR Atmakaraka sign OR Karakamsa).
- S2 specificity.

## Holdout
C1 is claimed ONCE via `HoldoutGuard` as `phase3J_AD_confirm`, only if P_ad is SIGNAL. Otherwise C1, C2, Gauquelin
and Wikidata stay unread.

## Prior and power
Expected: null (Phase 3J's MD level was null, and so was every Vimshottari/Yogini level). The base rate is ~1/12, and
MDE80 ≈ 0.024 at n = 1,192, below the SESOI. TOST may still fall short: Phase 3J's P_d had TOST p 0.059 at this n.
If so, the verdict is UNDERPOWERED, reported as such.

**After this phase the dasha-timing line is closed.** All four systems the engines carry (Vimshottari ×3 levels,
Yogini, chara MD, chara AD) will have been tested. Any reopening needs a genuinely new instrument and its own
prereg.
