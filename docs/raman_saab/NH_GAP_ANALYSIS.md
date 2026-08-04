---
title: "Notable Horoscopes — engine-vs-Raman gap analysis"
kind: analysis
topic: validation
measured: true
updated: 2026-08-03
words: 2237
tags: [raman-saab, analysis, validation]
---
# Notable Horoscopes — engine-vs-Raman gap analysis (2026-06-27)

36 NH DRAFT rows where the engine's verdict disagreed with Raman's were each analyzed against Raman's
cited reasoning (Workflow, 6 agents). Classification: **34 doctrine_gap, 1 extraction_error, 1 ambiguous.**

**Critical synthesis (the honest shape): the 34 gaps collapse into ~6 recurring principles, dominated by
ONE already-known mechanism (B1). This is NOT 34 new rules.** Each theme is a judge-mechanism change that
will move the ratchet, so each must go through the full anti-overfit pipeline (cite → bphs-doctrine-reviewer
→ over-fire scan → zero-regression → human bump), tuned not hand-fit. Direction split was symmetric
(13 fav→affl, 10 affl→fav, 6 mixed→fav, 4 mixed→affl) — confirming several distinct principles pulling
both ways, not one bug.

## Theme 1 — B1 three-factor comparative weighing (THE dominant cluster, ~17 rows) `judge-mechanism`
Raman lets the **strongest** of {bhava, lord, karaka} dominate, and a **decisively weak/afflicted dominant
factor drags the house down** even when another factor is strong. The engine's preponderance count
under-weights a strong/dignified LORD/KARAKA/benefic-OCCUPANT against malefic aspects (and vice-versa).
- **Positive leg (strong factor should LIFT; fav→affl/mixed):** chart_25 H2, chart_26 H2, chart_32 H1,
  chart_33 H1, chart_65 H1, chart_53 H7, chart_57 H1, chart_61 H10, chart_42 H10 (+ Neechabhanga).
- **Negative leg (weak factor should DRAG; the engine too lenient):** chart_26 H1 (vitality-karaka Sun
  eclipsed), chart_45 H2 (debilitated lord), chart_53 H2 (lord in dusthana), chart_65 H2, chart_67 H5,
  chart_57 H5.
**This IS the deferred backlog item B1** (HTJAH-I:3713/3788/3815/2760/2111). NH now provides ~17 charts of
corroboration — the strongest case yet to build B1. Highest yield; highest risk (must not regress chart_54).

## Theme 2 — Malefic-concentration / aspect-aggregation threshold (~5 rows) `threshold`
"≥3 malefics afflicting the lord/house → afflicted"; "house free of malefic aspect AND benefic-aspected →
not afflicted"; "two malefics OCCUPYING a house → at least mixed regardless of competing yogas."
- chart_55 H1, chart_75 H1, chart_26 H9, chart_61 H10, chart_35 H4.
Codeable + general; tune the count threshold (do not hand-set). Pairs with B1.

## Theme 3 — Functional-yogakaraka malefic does NOT afflict its house (~3 rows) `judge-mechanism`
A natural malefic that is the chart's **functional yogakaraka** should not afflict the house it occupies/
aspects. The primitives exist (`IsYogaKaraka`, `functional_nature`); the suppression rule does not.
- chart_69 H1, chart_57 H1, chart_61 H9.

## Theme 4 — Lord "blemished" (combust / node-conjunct / afflicted-dispositor) downgrades the house (~3) `new-rule`
- chart_54 H9 (lord exact-conjunct Rahu), chart_75 H9 (lord combust + afflicted constellation-lord),
  chart_54 H1 (debil malefic occupant + lord aspected by 8th-lord).

## Theme 5 — Karaka-papakartari + Navamsa(D9) cross-check (~2 rows) `new-rule` (over-fire risk)
Papakartari read on the **karaka** (not just the lord), and a **D9** condition of the bhava, temper the D1
verdict. Engine's papakartari is D1-only and lord-only.
- chart_37 H5, chart_63 H1. **Caution:** D9 overlays over-fire easily — gate hard.

## Theme 6 — Singletons (each n≈1; document, low priority)
- chart_33 H6: 6th as **upachaya** — a malefic there gives victory over enemies → mixed, not afflicted.
- chart_75 H10: a **Mahapurusha (Hamsa) yoga** occupant should floor an otherwise-afflicted house at mixed.

## REJECT — conflicts with a LOCKED decision (do NOT assimilate)
- **chart_33 H2** — relies on **Sripathi/unequal-bhava** house division (a planet late in the Lagna sign
  counts in the 2nd bhava). The engine uses **whole-sign houses (locked)**. Assimilating this would diverge
  the engine into a different house system. **Dropped; this row stays DRAFT/documented-limit.**

## VERIFY before treating as gaps (engine may already handle)
- chart_33 H10, chart_37 H7 — "doesn't co-judge from the Moon": the engine **already builds a MOON frame**
  (`house_template` LAGNA/MOON/KARAKA). Re-examine whether the real issue is lead-frame selection, not a
  missing frame.
- chart_37 H10 — Parivartana: the engine **has** `bhangas.parivartana` + Khadga yoga; the gap (if any) is
  crediting it for the 10th, a wiring question not a missing primitive.

## Not gaps
- 1 extraction_error (drop from DRAFT on review); 1 ambiguous (n=1 chart conclusion, not a general rule).

## Recommendation
Build in this order, each through the full anti-overfit pipeline with a human baseline bump:
**B1 (Theme 1)** first — it clears the largest cluster and unblocks the deferred HPA avastha + Shankha/
Kahala/Lakshmi yogas that also need effective-strength. Then **Theme 2** (threshold, tuned), then
**Themes 3–4** (additive rules). Treat **Theme 5** cautiously (D9 over-fire). The ~17 B1 + ~5 threshold +
~6 Themes 3-4 rows are the real, faithful accuracy lever — not 34 ad-hoc fixes. The rejected Sripathi row
and the verify-first rows are the guardrails that keep this from diverging.

## B1 implementation attempt — EMPIRICAL RESULT (2026-06-27): deep redesign, not a safe increment
Built `_effective_strength` (the doctrine-faithful B1 core: Raman's "strong" = Shadbala folded with
dignity + combustion + neecha-bhanga — exalt/own/MT -> strong; combust>=0.5 or debil-uncancelled -> weak)
and ran it through the anti-overfit gates:
- **Naive "weak lord -> demote favourable":** over-fires 14/109 confirmed-favourable (lord weak but
  COMPENSATED by karaka/bhava -> rightly favourable). Unsafe.
- **Compensation-gated demote:** 0/109 over-fire but catches 0 targets (Raman weighs the debil lord more
  than the engine's compensation -> the safe form is inert).
- **Positive-leg promote (exalted benefic lord/occupant lifts an afflicted house):** catches 3/8, over-fires
  8/100 confirmed-afflicted INCLUDING chart_35/74 H8 death charts (an exalted benefic in the 8th would
  wrongly lift a real death-affliction). Unsafe.
- **Effective-strength swapped globally into `_strong`:** baseline 204 -> 200 on 238 fresh-cast confirmed
  verdicts. **IMPROVED 0, REGRESSED 4** (chart_54 H3 [the documented canary], h7_12 H7, NH.chart_26 H10,
  NH.chart_65 H5). NET -4.
**Root cause:** the B1-miss verdicts are produced by `_decide`'s OTHER clauses (dusthana-affliction,
preponderance weigh, navamsa guard), which are inter-tuned against RAW Shadbala. Changing the strength
reading regresses tuned cases without reaching the targets. **B1 is a holistic `_decide` re-derivation that
risks all 239 confirmed verdicts** — it requires the threshold-tuner (`tools/raman_saab/tune_thresholds.py`
with holdout-lock) calibrating effective-strength weighting across the WHOLE set, not a hand-written clause.
**Decision: do NOT ship.** The ~17 B1 NH-miss rows stay DRAFT (documented engine limits, honestly recorded);
the NH charts become the test set for a future dedicated B1 redesign. The discipline (no regression, no
overfit) held — the gates refused both a regressing and an overfit B1.

## SHIPPED 2026-06-27: two-malefic-occupancy demote gate (Theme 2, partial)
`_malefic_occupancy_gate` (house_template.py): >=2 cruel malefics {Mars,Saturn,Rahu,Ketu} tenant a bhava
AND the lead lord is not Shadbala-strong -> favourable demoted to MIXED. DEMOTE-ONLY. Cite NH:5890 (Tagore
4th by Mars+Ketu -> desultory/unconventional education). Reviewer SOUND-WITH-CAVEAT (KEEP). Validated:
with/without-gate diff changes 0 confirmed verdicts; closed NH chart_35 H4 -> CONFIRMED. Ratchet 205/239 ->
206/240. The strong-lord twin (chart_42 H2) is spared by the compensation clause. The other user-flagged
cases stay DRAFT/limits: chart_45 H2 (neecha-lord, identical-signature counterexample chart_57 H4) and
chart_67 H5 (Mars-on-progeny, strong lord present -> can't gate without over-firing). Bose H1/H2 confirmed
B1-class (benefic-occupant floor over-fires 17/100), not isolated bugs -> need the deferred B1 recalibration.

## B1 SCOPING via the miss table (2026-06-27): confirmed a calibration problem, not a rule problem
The 69-miss table classified 53/69 (77%) as B1 comparative-weighing and named the EXACT afflictions Raman
uses that the engine's `lord_strong` (raw Shadbala) ignores: Papakartari on the lord, a node-conjunct lord,
a dusthana-placed (6/8/12) lord, a 1st-6th lord contact, combustion. Tested the refined hypothesis — fold
ALL of these into an effective `lord_strong`/`karaka_strong`:
- **Refined effective-strength (papakartari+dusthana+node+combust+dignity):** CONFIRMED 205 -> 165,
  IMPROVED 1, REGRESSED 41, **NET -40** (worse than the earlier dignity+combustion-only attempt's -4).
- **Benefic-occupant-fortifies (the top doctrine_gap, drives Bose H1/H2):** over-fires 21/129 confirmed
  afflicted/mixed even gated to non-dusthana + <2 malefic occupants; catches only 5/35. Collapses into B1.
**Conclusion (final):** every hand-coded B1 form regresses the confirmed set because Raman applies these
afflictions CONTEXTUALLY (a dusthana/papakartari lord dooms the house only when uncompensated — the
comparative weighing). The current `lord_strong` is crude but CALIBRATED; editing one factor breaks the
whole. B1 is only buildable as a CALIBRATED re-fit via `tools/raman_saab/tune_thresholds.py` searching the
affliction-weighting holdout-locked to 206/240 — a dedicated, uncertain research effort (the -40 hand-start
makes the tuner's job hard). The faithful near-term ceiling is the current 206/240; the only safe additive
wins are the rare clean gates with a real compensation discriminator (e.g. the shipped two-malefic gate).

## SHIPPED 2026-06-27: Theme 3 (yogakaraka-Lagna gate, partial) + B3/B4 superseded
`_yogakaraka_lagna_gate`: a natural malefic (Mars/Saturn) that is the chart's functional yogakaraka
occupying the Lagna is a Raja-yoga that fortifies the self -> an over-harsh afflicted self rises to
favourable. Comparative-weighing guard withholds the lift when >=2 non-yogakaraka malefics co-occupy
(reviewer FLAG). Closed NH chart_69 H1 (Cancer Lagna, Mars-YK+Ketu; Raman 'confers imagination') ->
CONFIRMED, ratchet 207/240 -> 208/241. chart_57 EXCLUDED by the guard (3 malefics; Raman credits its
favourable self to Moon-in-10th, a different/B1 mechanism — and its cast is doubtful per reviewer) ->
stays DRAFT. Theme-3 row chart_61 H9 (Saturn-YK aspecting the 9th) is the any-house case deliberately
left to the deferred general form. **B3 (non-death marital maraka guard) and B4 (blemishless/yogakaraka-
Venus override) are SUPERSEDED**: their sole target was the chart_03/08 marriage over-harsh, now fully
closed by B2 (chart_08) + earlier work (chart_03). With no live targets, building them would add over-fire
risk for zero upside — not built.

## Session tally (2026-06-27): three clean gates + the gap map, 205/239 -> 208/241
two-malefic-occupancy (+1 Tagore), GBB B2 marginal-karaka (+1 chart_08, real-error resolved), Theme-3
yogakaraka-Lagna (+1 chart_69). Plus the 69-miss MISS_TABLE (77% B1) and the B1 scoping (calibration, not
hand-codeable: -40). Refused as over-firing/unfaithful and documented: B1 effective-strength, benefic-
occupant-fortifies, neecha-lord, Mars-on-progeny, B3, B4. Every shipped gate: over-fire-scanned, reviewer-
KEEP, zero-regression, human-bumped.

## B1 harness + exhaustive holdout-gated search (2026-07-24): the `_strong`-seam fold is confirmed dead
Built the parameterized B1 seam the earlier sessions said was the ONLY viable path: `_effective_strength`
(`judges/house_template.py`) folds five affliction weights — `EFF_W_{PAPAKARTARI,DUSTHANA,NODE,COMBUST,
DIGNITY}` (`primitives/shadbala/total.py`) — into the raw Rupas before `is_powerful`, and extended
`tools/raman_saab/tune_thresholds.py` to search them holdout-locked. All weights DEFAULT 0.0 -> a strict
no-op (early return), so the shipped engine is byte-identical (ratchet 209/241, verified).
- **Greedy coordinate descent (0.5-Rupa steps, --holdout-lock):** converged at iter 0 — no single step
  crosses a `MIN_REQUIRED` threshold, and B1 is a multi-factor interaction descent can't see.
- **Exhaustive coarse grid (each weight in {0,1,2} Rupa, 242 configs, fit n=189 / holdout n=53):** BEST
  fit correct = 168 = baseline. **ZERO configs beat baseline fit.** The mechanism is NOT inert — a
  validity check shows it flips 9–24 fit verdicts per aggressive config, but essentially every flip is
  WRONG (all=2 -> +1/-22; papakartari=2 -> 0/-9; dusthana=2 -> 0/-14; dignity=2 -> +1/-3). This
  independently reproduces the -4/-40 hand-attempts a 4th time.
**Root cause (reconfirmed, now with an exhaustive holdout gate):** penalising afflictions AT THE `_strong`
GATE double-counts — `_decide`'s downstream clauses already price these afflictions CONTEXTUALLY (only when
uncompensated), so an unconditional strength-gate penalty wrongly demotes tuned-correct verdicts. The fold
belongs (if anywhere) INSIDE `_decide`'s comparative weighing, not at the raw `_strong` gate.
**Decision:** KEEP the no-op harness (it is the reusable, holdout-gated weight-search infrastructure the
backlog called for, at zero ratchet risk) and RECORD this negative result so the `_strong`-seam approach is
not blindly re-attempted. The remaining B1 avenue is the deeper, riskier `_decide` contextual re-derivation
(a dedicated effort that "risks all confirmed verdicts") — deferred, not attempted here. The faithful
ceiling stands at 209/241.

## The faithful ceiling — confirmed on the EXPANDED corpus (2026-07-24): every systematic lever exhausted
> **Later note (2026-08-03).** The 261/293 below is the figure as it stood when this sweep ran, and
> the sweep's conclusion is unchanged: every systematic lever is still exhausted. The live ratchet
> is now **259/293 = 88.4% exact / 283/293 = 96.6% within-1** — re-based DOWN deliberately when the
> B1 dominant-factor guard was enabled, buying real errors 12 -> 10. That was a TRADE, not a lever;
> it did not beat the ceiling this section proves. See `DOCTRINE_BACKLOG` B1.

After the NH corpus expansion (192 -> 225 charts, fidelity 209/241 -> 261/293 = 89.1% exact) a full sweep
of every systematic accuracy lever was run, and ALL are exhausted:
1. **Placement discriminators** (`tools/raman_saab/discriminator_scan.py`): of 35 miss-significations only 2
   are empirically "clean", and BOTH failed the shippable bar on implementation — death (8th-lord-in-8th) is
   Vipareeta-spurious; siblings (malefic-3rd) is inert (the reading is already encoded; the miss is B1). The
   ONE real placement win, H10.C.61 (benefic-fortified malefic-free 10th -> favourable career), is the last.
2. **Karaka frame** (mother-from-Moon): the Moon-Matrukaraka affliction OVER-FIRES — 4 favourable-mother
   charts have an afflicted Moon. Mother is B1, not a clean frame.
3. **Global B1 tuner** on the EXPANDED corpus (holdout-locked, fit 204/225 / holdout 58/69): greedy descent
   converges at iter 0; the exhaustive {0,1,2}-Rupa grid over all 5 effective-strength weights finds ZERO
   configs beating baseline fit — the SAME null result as the smaller corpus. The `_strong`-seam fold is
   dead with 5x the data (5th confirmation).
4. **Over-lenient cited-fix leads** (the 9 CONFIRMED-afflicted the engine reads favourable): each is a
   DIFFERENT mechanism (self x2, siblings, wealth, children, elder_siblings, expenditure, father, disease) —
   no clean n>=2 decisive pattern; every one is a contextual weighing.
**Conclusion:** the engine is at its faithful ARCHITECTURAL CEILING (~89% exact Track-B / ~91% fit / ~84%
holdout). The residual is contextual B1 comparative-weighing that (a) hand-coding regresses (-4 / -40,
documented above), and (b) the tuner cannot reach (no generalizing config, now proven on 5x the data). The
only remaining paths are per-chart n=1 fixes (overfitting — forbidden by the Prime Directive) or a
fundamentally different `_decide` architecture (learned/re-derived, risks all confirmed verdicts). Pushing
the number further within the current faithful, non-overfit architecture is not available.
