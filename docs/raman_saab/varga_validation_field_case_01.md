# Shodasavarga validation — field_case_01 (the confirmed real nativity)

Generated from `build_shodasavarga_report` on the field_case_01 birth (raman ayanamsa,
Scorpio lagna — a **vargottama lagna**: Scorpio rises in D1 and D9 both). Engine reading
vs the owner-confirmed life facts, with an honest match / miss / ambiguous column —
misses are recorded as misses per the Prime Directive (measure honestly). Hard pins for
the robust rows live in `tests/raman_saab/test_field_case_01_vargas.py`; this table is
the reviewed soft comparison.

| D | domain | engine reading (key facts) | status | owner's life | verdict |
|---|--------|---------------------------|--------|--------------|---------|
| D1 | body/whole | lord Mars enemy-sign H11; Venus on lagna | neutral | fair vitality, mild BP | ✅ match |
| D2 | wealth | Sun own-hora; **Jupiter (Dhana-kāraka) exalted**; 5 grahas in Moon-hora | **confirms** | wealth rising since 2020 | ✅ match |
| D3 | siblings/courage | lord Jupiter enemy-sign in D3 8th | **weakens** | 2 brothers, very close; bold officer | ❌ **miss** (consistent with the D1 H3 too-harsh finding — the engine's known 3rd-house over-affliction seam) |
| D4 | property/fortune | Venus friend-sign H10; benefics in kendras | neutral | property booming since 2021 | ◽ under-calls (neutral vs a clearly favourable life fact) |
| D7 | children | **Mars + Ketu ON the Sapthamsa lagna**; Jupiter enemy-sign in 3rd | neutral | two daughters; elder autistic, constant worry | ✅ **striking structural match** (the affliction is visible exactly where doctrine says to look) |
| D9 | marriage | **vargottama lagna**; Venus own-sign (12th); Mars debil 9th | neutral | marriage realized, turbulent-but-stable | ✅ match (neutral = strife-with-substance; Venus own = the enduring bond) |
| D10 | career | **lagna lord Jupiter OWN-sign in the D10 lagna**; Mercury enemy 8th | neutral | IFS 2016; reputation cemented 2025 | ✅ **structural match** (the own-sign lagna-lord is the career backbone; the mixed kendra explains the chargesheet turbulence) |
| D12 | parents | **lagna lord Venus EXALTED** in H11 | **confirms** | both parents alive & well | ✅ match |
| D16 | vehicles | **lagna lord Mars in the D16 8th** | neutral | **never purchased a vehicle** | ✅ **striking structural match** |
| D20 | spiritual | Venus enemy-sign H10; Mars on lagna | neutral | deep, deepening practice | ◽ under-calls (life is clearly favourable here) |
| D24 | education | **lagna lord Moon DEBILITATED in D24 5th** | **weakens** | IIT Roorkee; research papers | ❌ **miss — the honest counter-example**, recorded not papered over. (Possible readings: the 2002 schooling disruption + two UPSC final-stage failures ARE education-path afflictions; or D24 interpretation needs the missing classical doctrine — deferred with the BPHS v2 item.) |
| D27 | strength/weakness | Saturn friend-sign; Mercury+Jupiter on lagna | neutral | resilient constitution | ✅ loose match |
| D30 | evils/misfortune | **Mars EXALTED in D30 11th** (kāraka); benefics crowd the kendras | **confirms** | no lifetime catastrophes; crises weathered (2019, 2024-25) | ✅ match (confirms = strength AGAINST evils) |
| D40 | general auspice | Mercury exalted in D40 4th | confirms | — | (no testable fact) |
| D45 | conduct | Moon neutral in D45 6th | weakens | upright officer | ◽ ambiguous (thin doctrine, no strong fact either way) |
| D60 | karma/all | Mercury neutral H9; Jupiter on lagna | neutral | — | (no testable fact) |

**Vargavisesha (GBB-3 Art.28):** Sun **Parijatamsa** (2×: D2, D9) · Mercury **Parvathamsa**
(3×: D1, D3, D30 — the chart's exalted-Mercury signature, fitting the intellect/writing
life) · others below threshold.

## Scorecard

- **Structural matches (the domain-chart shows the life fact where doctrine says to look): 4
  striking** (D7 children-affliction, D10 career-spine, D16 vehicle-void, D12 parents) **+ 5
  ordinary matches** (D1, D2, D9, D27, D30).
- **Misses: 2** — D3 (siblings/courage weakens vs a close-brothers bold life; the same seam
  as the D1 H3 too-harsh finding) and D24 (education weakens vs IIT; the known
  counter-example). Both recorded, neither papered over.
- **Under-calls: 2** (D4 property, D20 spiritual — engine neutral where life is favourable);
  **ambiguous/untestable: 3** (D40, D45, D60).

## v2 deferrals (recorded)

1. **BPHS/Phaladeepika corroboration-tier registry admission** + re-ingestion of the missing
   chapters (BPHS per-varga domain slokas, Vimsopaka bala) — prerequisite for authoring any
   per-varga RULES beyond the general-principles judge.
2. **Vimsopaka bala** on the RamanChart model (its Raman-citable source is not on disk).
3. Extending `conditions.py` varga predicates beyond D9; unifying the three `_varga_dignity`
   helpers into one primitives function.
4. D24/D3 interpretation refinement — only after the classical doctrine is admitted (the two
   recorded misses are the motivating cases; fixing them by tweaking thresholds against one
   nativity would be overfitting and is explicitly declined).
