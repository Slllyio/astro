# Phase 3J-AD: how to read PHASE3J_AD_RESULTS.md (hand-written)

Run 2026-10-24 under `PHASE3J_AD_PREREG.md` (27d0516a), runner `87318e78`. The engine is the Parashara engine's
`chara_dasha.antardashas` (cec90acd). It follows BPHS-51 sl.7-12, the owner's choice, as the BPHS translator works
it on the ch.46 chart. The doctrine reviewer VALIDATED it, and all three printed antardasha orders reproduce exactly.
The run used Phase 3J's 1,192 day-dated, non-death risk sets; all 10,866 charts were cast, and both 500-draw gates
pass (planted +0.0301).

## What was run, in plain words
Inside each chara dasa (a sign's period of 1–12 years), BPHS runs twelve sub-periods, again of signs. The question:
on the exact date of an event, is the running sub-period sign more often that matter's house (counted from the
Lagna) than it is for 10 matched people (E_rs), or than across the person's own life (E_wp)?

## The headline
**No.** The chara antardasha does not time real events.

| test | coverage | E_rs (vs matched controls) | E_wp (vs own lifetime) | verdict |
|---|---|---|---|---|
| P_ad: antardasha sign = event house | 0.094 | −0.004 (−0.022..+0.013) | +0.004 (−0.012..+0.020) | BOUNDED_NULL (TOST p 0.002) |

- **Placebo** (sequence seeded one sign ahead): −0.012 / −0.014. Real and placebo are both null.
- **S_conv** (the dasa AND the antardasha both on the house's sign; coverage 1%): −0.003. Convergence does no better.
- **Raman ayanamsa:** +0.001. **Wider activation** (Lagna/Atmakaraka/Karakamsa, coverage 0.24): −0.014.
  **Rodden AA:** −0.003. All null.
- **S2 specificity:** −0.005 (p 0.63). Families: none has a CI clear of 0.

## Why
The same reason as at every level before it. Whether the running sign is "the" house's sign on the day something
happens is no different from any other day of the person's life. Going down a level makes the clock finer; it does
not make the significator any more specific to the event.

## The dasha-timing line is now closed
| system / level | E_rs | verdict |
|---|---|---|
| Vimshottari AD / MD (Phase 3, Parashara) | −0.010 / −0.003 | bounded null |
| Vimshottari AD / MD (Phase 3R, Raman engine) | +0.003 / −0.018 (wp −0.006) | null |
| Vimshottari PD (Phase 3P, Raman engine) | +0.009 / −0.005 | bounded null |
| Yogini AD / MD (Phase 3Y) | −0.010 / +0.001 | bounded null |
| Chara MD (Phase 3J), year / day-dated | +0.001 / −0.014 | bounded null / underpowered |
| **Chara AD (Phase 3J-AD)** | **−0.004** | **bounded null** |

Every dasha system and level the two engines carry has now been tested on the same events, and none times them.

**C1 was not read.** P_ad is not SIGNAL, so C1, C2, Gauquelin and Wikidata stay unread.

## Deviations from the prereg
None.
