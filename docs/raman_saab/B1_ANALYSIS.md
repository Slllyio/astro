# B1 (effective-strength recalibration) — deep per-change analysis vs Raman (2026-06-28)

The refined B1 (fold combustion / debilitation-uncancelled / Papakartari / node-conjunction into a
planet's effective strength, so a Shadbala-strong-but-afflicted lord/karaka reads WEAK) changed **26
confirmed verdicts**. Each was judged against Raman's OWN reasoning at the cited lines (3 agents).

## Result: net distorting AS-IS, but the failure is ONE fixable gap

| Assessment | n | Meaning |
|---|---|---|
| **B1_IMPROVES** | 3 | B1 reads it more like Raman than baseline — Raman himself calls the lord weak |
| **GOLDEN_QUESTIONABLE** | 3 | B1 differs from the golden but matches Raman BETTER — the **golden label is wrong** |
| **AMBIGUOUS** | 2 | Raman states a real qualifier but lands favourable — borderline |
| **B1_REGRESSES** | 18 | B1 breaks a reading baseline got right per Raman |

So **8 of 26 (3 improve + 3 golden-questionable + 2 ambiguous) are B1-defensible or expose a bad
golden**; 18 regress.

## The 18 regressions are almost ALL the same root cause: missing CANCELLATION logic
B1 models only the **debit** side (the affliction). Raman's effective strength is the affliction
**net of cancellation**, and in case after case he *explicitly cancels* the very affliction B1 counts:
- **neecha-bhanga** — "Saturn is debilitated but gets cancellation of debility... a powerful Dhana Yoga" (h11_12)
- **benefic aspect neutralises hemming** — "slight papakartari... balanced by Jupiter's presence" (HTJAH-II ch.2); "toned down... can have no adverse effect" (h7_01)
- **lord dominates its afflictors** — "the third lord is more powerful than the third house or Mars... will have brothers" (chart_54)
- **karaka still well-placed** — Jupiter in the 6th "fairly well placed" (h11_15)
- **yogakaraka in own house confers the result** — Saturn yogakaraka in the 7th "conferred... marriage" (Tennyson); Raja-yoga 10th (Narasimha)
- **node read as a POSITIVE significator** — Rahu in 11th "rules over industries" (chart_62); Mars+Rahu in Lagna = the foreign-residence yoga (h9_17)
- **a yoga overcomes minor afflictions** — Gajakesari "powerful enough to overcome the minor afflictions" (chart_65)

Add the cancellation/exemption credit-side and most of these 18 dissolve — they are not "B1 is wrong,"
they are "B1 is half a doctrine."

## Two concrete defects surfaced
1. **Dignity-shortcut ordering bug (severe):** B1 returns `strong` for exalt/own/MT *before* checking
   afflictions, so a combust + node-afflicted exalted planet wrongly reads strong — it flipped
   chart_24 coverture from afflicted (widowhood, per Raman) to favourable. Afflictions must be
   checked even on dignified planets.
2. **3 mislabeled goldens (clean win regardless of B1):** NH.chart_36 (Vivekananda) H10 and H9-father
   are labeled `favourable`, but Raman literally says the 10th-lord Jupiter is "hemmed inbetween...
   malefics" and "weak as a kendra lord," and the father section is about how the native was
   "deprived of his father" (died 1884). B1's `afflicted` matches Raman; the goldens are the weak link.

## Bottom line for the decision
- **B1 as-specified: do NOT ship** (18 regressions, net negative by golden labels AND by Raman).
- **B1 is NOT a dead end:** its failures are concentrated in one missing mechanism (cancellation),
  plus one ordering bug. With the credit-side added it is plausibly net-positive — the same two-stage
  "affliction net of cancellation" that IS Raman's effective-strength doctrine.
- **Independently bankable now:** fix the 3 mislabeled Vivekananda goldens; fix the dignity-shortcut
  ordering bug for any future B1.

## Cancellation layer — built + measured (2026-06-28)

Decision was: build Raman's cancellation/exemption credit-side, re-test B1. Built (experiment):
benefic-aspect (healthy Jupiter/Venus/Mercury, whole-sign drishti or conjunction) neutralises
combustion & Papakartari; node-conjunction in an upachaya (3/6/11) is positive not afflicting;
debility-cancellation (neecha-bhanga) already present; affliction is checked BEFORE the dignity
shortcut (fixes the exalted-but-combust ordering bug).

**Result: B1 went from net −26 to net −8** (regressions 28 → 9). The thesis is validated — ~19 of
the regressions WERE missing cancellation, exactly as predicted. But −8 is the calibration wall:

- **Over-cancellation (3, B1 now too lenient):** h7_12 (combust+hemmed 7th lord → Raman: WIDOWHOOD,
  but benefic-aspect cancellation flips it to favourable — a dangerous inversion), h11_07, chart_26
  (Marx, debil 10th lord neecha-bhanga'd away though Raman reads it negatively).
- **Needs more cancellation (2):** chart_54 (lord-dominates: "3rd lord more powerful than its
  afflictors"), chart_65 (yoga-overcomes: Gajakesari "overcomes the minor afflictions").
- **Over-fire via karaka/occupant (4):** chart_29, h7_01, chart_51, chart_71 — B1 afflicts through a
  non-lord factor where Raman is favourable.

**Verdict on B1:** the cancellation layer more than halves the gap and proves Raman's "affliction net
of cancellation" doctrine is real and largely encodable. But the last −8 is genuine calibration: each
further cancellation rule that fixes a too-harsh case risks a too-lenient inversion (h7_12 is already
one). Reaching net-positive requires the threshold-tuner with a holdout-lock (plan B4) + lord-dominance
+ yoga-overcomes — a real grind with overfit risk, and B1 must NOT move decisive verdicts while it can
still invert a widowhood to favourable. The cancellation LOGIC itself is sound doctrine independent of
B1 and could enrich the engine's strength assessment without verdict-moving.

## Tuner grind with holdout-lock — the definitive result (2026-06-28)

Decision was: push for net-positive via the threshold-tuner + holdout-lock. Built it (charts split
70/30 train/holdout by id-hash; a cancellation rule is kept only if it improves TRAIN without
degrading HOLDOUT). Measured B1's effect on ALL graded verdicts (not just confirmed) to capture any
UPSIDE on the engine's existing misses.

| config (cancellation +) | TRAIN fix/break | HOLDOUT fix/break |
|---|---|---|
| base cancellation | +1/-6 | +1/-3 |
| + lord_dominates | +1/-5 | +1/-2 |
| + severe_combust (BEST) | +1/-4 | +1/-2 |
| + multi_block | +1/-7 (worse) | +1/-3 (worse) |

`lord_dominates` and `severe_combust` both generalised (helped train, held holdout); `multi_block`
was correctly REJECTED by the holdout (overfit). But the decisive fact is the **+1 upside is constant
across every config**. Best config, reviewed verdicts only: **2 fixes (1 CONFIRMED: chart_45 Einstein
Papakartari-9th; 1 DRAFT), 6 breaks (all CONFIRMED) → net −5 on reliable verdicts.**

### Conclusion: net-positive is UNREACHABLE for the effective-strength B1 — proven, not asserted
B1 has almost no upside because the engine's confirmed verdicts are ALREADY correct (that is what
"confirmed" means); B1's affliction-folding can only CHANGE them, which is neutral-or-worse. Its one
reliable fix (chart_45) is a genuine Papakartari case — proving the mechanism CAN help in the right
spot — but there is no POOL of strength-fixable misses to capture, because the real misses are
COMPARATIVE-WEIGHING problems (which of bhava/lord/karaka dominates), not single-planet strength.
Effective-strength recalibration is the wrong mechanism for them.

### Constructive salvage (the proven safe pattern)
- The ONE reliable win (chart_45, Papakartari on the 9th lord) can be captured as a NARROW
  demote-only gate — the project's zero-regression pattern — instead of the broad B1 that breaks 6.
- The cancellation doctrine (lord-dominates, severe-combustion-not-rescued, benefic-neutralises-
  hemming) is validated against the holdout and is sound Raman doctrine that could refine the engine's
  strength signals safely (non-verdict-moving), independent of B1.
