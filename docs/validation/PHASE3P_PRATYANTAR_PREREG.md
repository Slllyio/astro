# Pre-registration: Phase 3P, Raman's PRATYANTAR level (sub-sub-period) timing

Committed 2026-10-14, BEFORE any pratyantar exposure has been computed for any event or person.
User request: "Raman's pratyantar level". Raman engine unchanged; Phases 3 and 3R are not re-read.

## Doctrine (the engine's own technique, cited)
- `vimshottari.pratyantars(bh)`: the 9 Antaras of a Bhukti, proportional (HPA ch.24); HTJAH-II:668-702
  names all three levels, "as lords of the Dasas… Bhuktis… or… Antaras", as carriers of a house's results.
- The engine's own event scoring (`rectification/scoring.py`, Channel A): at each level, the running
  lord **matches** iff it is in the event's significators, `timer_set(H)` ∪ `timer_set(aux)`. The
  Bhukti triggers and the Pratyantar refines. A level is scorable only when the event's date precision
  resolves it, so **day-dated events only** (a Pratyantar lasts ~2 months).
- Raman gives no four-tier scheme at the pratyantar level, so none is invented here.

## Instruments (Raman engine, Raman ayanamsa; timers exactly as Phase 3R)
- **P3a: the Pratyantar lord activates the event's house(s):** PD lord ∈ timers(H). Death: PD lord ∈
  `maraka_set(chart).primary`.
- **P3b: triple convergence:** MD, AD **and** PD lords all ∈ timers(H) (death: all three primary marakas).
- Holm across {P3a, P3b}.

## Design
Exactly the Phase 3 AD-level risk sets (day-dated A+B events, the doctrine-reviewed event map, 10
same-tier same-decade controls on their own charts at the event age, seed 20261014, persons in the
Raman-engine population).
**Lesson from Phase 3R, registered here:** two effects per primary:
- **E_rs** (risk-set): case exposure − mean of the controls' exposure;
- **E_wp** (within-person): case exposure at the event − the case's OWN lifetime exposure share
  (exact time-share of exposed pratyantars over ages 15–75). This is immune to chart-level
  selection (the 3R artefact).

**SIGNAL requires BOTH** E_rs and E_wp to have a 95% CI above 0 (the predicted direction), Holm-adjusted.
**BOUNDED_NULL** = TOST at SESOI 0.03 passes for E_rs. Anything else is UNDERPOWERED. A CI entirely
below 0 is reported as "opposite to prediction", never as support.

## Controls (before the real comparison)
- Replicated 500-draw sham (within-set label permutation) and planted (+0.03) gates, as Amendment 1.
- Placebo dasha: the engine's dasha seeded one nakshatra ahead (Moon +13°20′); its PD-level E_rs and E_wp
  are reported. A real effect must exceed the placebo.

## Secondaries / sensitivity (descriptive)
- S1: dose-response over the number of activating levels (0–3: MD, AD, PD), CLR slope.
- Lahiri frame (same instrument, `ayanamsa="lahiri"`), per-family E, Rodden AA vs A.

## Holdout
C1 claimed once as `phase3P_confirm`, only on a discovery SIGNAL as defined above.

## Prior
Null expected. A PD lord is one of the ~5–6 timer lords out of 9, so PD activation covers roughly
half of all time, and the doctrine's own breadth works against single-date precision. Power: n ≈ 2,365
day-dated events, MDE80 ≈ 0.03 on E_rs, at the edge of the SESOI.
