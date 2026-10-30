# Pre-registration: Phase 3, dasha activation timing at full power (risk-set design)

Status: committed after doctrine review (bphs-doctrine-reviewer, 2026-10-14: 9 confirm, 4 revise,
2 blocking issues, all applied above). Git order is the date-lock. No Phase-3 instrument has been evaluated
against any event. Plan: `purpose-build-out-the-linked-stearns.md` Phase 3. Thresholds come from
`SESOI_PREREG.md` (a52ccb63). Reliability inputs come from `PHASE2_READING.md` (c641d22e).

## Hypothesis (the user's, in classical form)
A chart promises many things at once. A matter fructifies when the running Vimshottari periods
**activate the house that signifies it**. So, compared with other people of the same age, a person
should be more often inside an activating period of the relevant house on the date an event happens.

## Engine and instrument (frozen)
- Parashara engine, Lahiri (locked convention). The chart comes from `cast`; Vimshottari comes from the
  engine's own primitives (`vimshottari_dasha.timeline` + `bhukti_timeline`, identical to `read()`;
  equality is asserted in a test).
- **Influence** = `activation.influences(chart, planet, house)` (the planet owns, occupies or aspects the
  house, or conjoins or aspects its lord: Raman's factors a–e, HTJAH-I:1586-1588) **plus factor (f)**:
  the planet is the lord of the H-th house counted from the Moon (HTJAH-I:2586; the locked convention's
  "lord-from-the-Moon"). The engine omits (f), so it is added in `tools/validation/activation_store.py`.
  The engine itself is untouched.
- **Death uses primary marakas, not house influence** (doctrine review): a dasha lord counts for death
  iff it is the lord of the 2nd or 7th, an occupant of the 2nd or 7th, or conjunct the 2nd/7th lord
  (HTJAH-II:4494-4509). The same tier scheme is applied with "maraka" in place of "influence" (`t_mk`).
  8th-house chidra grahas are secondary and are left out.
- **Activation tier** of an (MD, AD) period for house H, Raman's uniform four-tier scheme
  (HTJAH-I:1592-1596, 1635-1640, 2588-2599):
  4 = both MD and AD lords influence H **and** the lords are associated. Raman never defines
  "associated" and keeps association separate from aspect (HTJAH-I:1587-1588), so the textual reading
  is conjunction. Tier 4 here also admits mutual aspect, per the project lock (CLAUDE.md). A
  conjunction-only tier 4 is a sensitivity arm. P1 (tier ≥ 3) is unaffected by this choice;
  3 = both influence, not associated; 2 = only the AD lord; 1 = only the MD lord; 0 = neither.
- **P1 exposure (AD level):** the date falls in an (MD, AD) period of tier ≥ 3. Raman: results
  "ordinary" or "par excellence" only when both lords influence.
- **P2 exposure (MD level):** the MD lord influences H.
- For own-death events, read "influences H" as "is a primary maraka": P1 = `t_mk` ≥ 3, P2 = the MD lord
  is a primary maraka.

## Event → house map (fixed from the significations, before any outcome is read)
Own-death events → **primary-maraka instrument** (`t_mk`, above). Marriage, divorce, begin/end
significant relationship, death of mate → **7**. Death of father → **9**. Death of mother → **4**.
Death of child, birth/adoption of a child, conception, abortion/miscarriage → **5**. Death of sibling → **3**. Work: new job/career,
fired/laid off/quit, retired, prize, gain social status, published/released, begin major project,
career ± → **10** (HTJAH-I:460-462). Illness, medical diagnosis/procedure, health negative → **6**
(HTJAH-I:455). Non-fatal accident, violent trauma, accidents → **6** ("the sixth house rules
accidents", HTJAH-I:5984). Trial, lawsuit, legal ± → **6** (HTJAH-I:455, 8345). Arrest → **12**
("incarceration", HTJAH-I:17344-17345). Education ± → **4**. Gain/lose money, finance ±,
business ± → **{2, 11}** (HTJAH-I:3983-3986). Inherited money → **8** ("legacies… unearned wealth",
HTJAH-I:457-458). Death of mother → 4 is an approximation: Raman times it by marakas from the 4th or
the Moon (HTJAH-I:4479-4518). This is noted, not modelled.
**Excluded (ambiguous or contested house, decided now):** "Change in family responsibilities",
fame ± (5th / 9th / 10th in Raman), "Institutionalized – prison, hospital" and its reverse (prison =
12th, hospital = contested), Social misc./publicity/group, Mundane, Misc., Other*, Death of significant
person, Crime perpetration, Secrets revealed, Change of lifestyle, Parents divorced.
No event type may be dropped or remapped after this commit.

## Samples
- **Discovery:** tiers A + B (person_master `quality_tier`), all people with a castable chart (store
  and outside it). Day-precision events → P1. Year-precision events → P2, evaluated at mid-year.
  Ages 5–95.
- **Holdout C1:** `assign_holdout(tier-C ids, fraction=0.5, salt="tierC-split-v1")`, claimed once via
  `HoldoutGuard` as `phase3_confirm`, read **only if P1 or P2 is SIGNAL on discovery**. C2 (the other
  half) is reserved for Phase 5.

## Design: risk sets
For each event (person i, age a, house H): 10 controls drawn without replacement from discovery-tier
people with the **same tier and birth decade**, born ≥ a years before the data cutoff (2024), with
no recorded own death before age a, and ≠ i. Each control is scored on **their own** chart at
age a for the same H. Seed 20261014. (There is no sex field in person_master, so no sex matching.)

**Primary statistic** (P1 and P2 each): risk-set excess E = mean over events of
[x_case − mean(x_controls)], 95% CI by person-clustered bootstrap (2,000). SESOI 0.03 (hit-rate
difference). Verdict per `tools/validation/result.py`. Conditional-logistic OR (strata = risk sets)
is reported alongside as the model estimate.
**Multiplicity:** Holm across {P1, P2}.

**Power (computed before data, recorded honestly).** Discovery has ~3.1k day-dated A+B events
before exclusions. At coverage ~0.5, the P1 observed-scale MDE80 ≈ 0.029–0.033, about equal to the
SESOI. After reliability (ρ_AD 0.64–0.82) the true-scale MDE is ≈ 0.036–0.050, above the SESOI.
**P1 can therefore only deliver SIGNAL or UNDERPOWERED for effects under ~0.04. A BOUNDED_NULL at
0.03 is unlikely on discovery alone.** P2 (~20k+ year-precision events) is well powered. The
reported MDE80 is computed from the realised n and coverage before E is computed.

## Controls (run first; any failure stops the run)
1. **Pipeline sham:** case label permuted within each risk set → E must be null (`GatedScorer`
   order: sham before real).
2. **Placebo dasha:** the same pipeline with the Vimshottari seeded one nakshatra ahead (Moon
   +13°20′, the same elapsed fraction). Right chart, wrong dasha sequence. Reported. A real-instrument
   E that the placebo matches is not attributable to the dasha.
3. **Planted recovery:** relabel so the instrument carries +0.03, and confirm the CI recovers it at
   the realised n.

## Secondaries (Holm within the three; descriptive unless P1 or P2 is SIGNAL)
- **S1 dose-response:** CLR slope of event-vs-control on activation tier 0–4 (Raman's ordering
  feeble < limited < ordinary < par excellence).
- **S2 specificity:** E(target house) − mean E over the houses the event's type does NOT map to,
  on the same events and risk sets. A real activation effect must be house-specific. For death,
  E(maraka) − mean E over the 12 house-influence instruments.
- **S3 double transit:** P1 exposure AND transiting Jupiter and Saturn both bear on H or its lord
  (DOUBLE_TRANSIT_PREREG definitions), pooled across event types.

## Sensitivity arms (descriptive, no tests)
- **Raman ayanamsa:** P1 and P2 recomputed under `SIDM_RAMAN` (patch from tools/). Phase 2 showed
  this changes ~half of all AD calls, so an effect present in one frame only is reported as frame-fragile.
- **Conjunction-only association:** S1 recomputed with tier 4 requiring conjunction (`conj`).
- **Precision gradient:** E in Rodden AA vs Rodden A (within discovery). Prediction fixed now: if the
  AD effect is real, AA/A ≈ 0.82/0.64 ≈ 1.3. P2 should depend far less on rating.
- **Engine-agreement stratum:** events where Raman's and Parashara's house verdicts agree (Phase 2: rare).
- Per event-family E (death / relationship / career / health / other), descriptive only.

## What each outcome means
- **SIGNAL on P1 or P2**, with clean shams, placebo below real, planted recovery passing and S2
  positive → confirm once on C1 (one-sided p < .05). Confirmation = the strongest support possible
  here for "dasha selects activation".
- **UNDERPOWERED P1 + BOUNDED_NULL P2** → year-scale (MD) activation is excluded at practical size,
  and AD-level stays open until more day-dated events exist.
- **BOUNDED_NULL on both** → the hypothesis is excluded at practical size for this corpus, with the
  bound stated ρ-disattenuated.
- A signal the placebo matches, or one that S2 shows is not house-specific → an artefact (age,
  recording or structure), not dasha timing.
