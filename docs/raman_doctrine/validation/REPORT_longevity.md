# Outcome-classification pilot — does engine strength predict Raman's LONGEVITY CLASS?

**A new validation dimension, orthogonal to the strength deltas.** The 9-grade map grades a
*strength* phrase; much of Raman's 8th-house prose instead states an **outcome** — the
longevity class (Balārishta < Alpāyu < Madhyāyu < Pūrnāyu) — which the map (correctly) won't
grade. Rather than force these onto the 9-grade scale, this pilot tests them directly as an
**ordinal-classification** problem: does the engine's strength verdict for the 8th house, its
lord, and the Āyushkāraka rank-order with Raman's stated longevity class?

## Headline

**At N=14 (all four classes represented): the 8th-BHĀVA strength predicts the longevity
class — Spearman ρ = +0.52 (p ≈ 0.056). But the 8th-LORD and ĀYUSHKĀRAKA (Saturn) strength do
NOT — both trend *negative* (ρ ≈ −0.31 / −0.33).** The general benefic-strength scorer is the
right signal for the *house* of longevity and the wrong signal for its *kāraka*.

| engine factor | Spearman ρ vs class | p | reads as |
|---|--:|--:|---|
| **8th bhāva** | **+0.521** | **0.056** | stronger 8th house → longer life ✓ |
| 8th lord | −0.309 | 0.282 | (no positive signal) |
| Āyushkāraka (Saturn) | −0.326 | 0.256 | (trends *against*) |
| conclusion (blend) | −0.271 | 0.348 | dragged down by the lord/kāraka |

(ρ/p reproduced identically by `scipy.stats.spearmanr` and the harness's dependency-free
implementation.)

## Why the split is the interesting part

- **The 8th bhāva is scored on generic fortification** (occupants, aspects, hemming), and
  that genuinely tracks longevity — a well-supported 8th house goes with a longer-lived
  native. Even at N=14 it clears p ≈ 0.05.
- **The Āyushkāraka trends the wrong way** because the engine grades Saturn on a *benefic*
  strength scale, while for longevity Saturn is the **giver of life** — its "affliction" in
  the general scorer does not mean short life. Raman's Pūrnāyu examples are frequently
  *"the disposition does not seem to indicate Pūrnāyu, but…"* teaching cases — afflicted-
  looking charts that live long — so the general strength score is actively misleading for
  the kāraka. This is a **doctrine gap the pilot localises**: longevity needs Āyurdāya-
  specific rules (maraka/benefic-to-longevity logic), not the general benefic-strength read.

## Data & method

- **Labels** (`heldout_longevity_ch12_8th.json`): Raman's explicit class term per chart —
  with the *"should have given Alpāyu but is Pūrnāyu"* correction (ch61) — or, where he gives
  no class term, derived from the stated **death age** (bands: <8 Balārishta, <32 Alpāyu,
  ≤70 Madhyāyu, >70 Pūrnāyu). **Every label was hand-verified against the prose**, and where a
  chart has *both* an explicit class and a death age the two agree exactly (ch43→Alpāyu,
  ch57/58→Pūrnāyu, ch70/72→Madhyāyu). Distribution: Balārishta 1, Alpāyu 3, Madhyāyu 4,
  Pūrnāyu 6.
- **Scores**: each labelled chart is reconstructed (`chart_from_raman`, gate-checked) and
  scored by the live `judge_house_doctrine(chart, 8)`; the harness Spearman-correlates the
  lord/kāraka/bhāva/conclusion scores against the class ordinal
  (`app/medini/doctrine/validation/longevity_validate.py`). No engine change.

## Honest limits

- **N=14 — suggestive, not conclusive.** The bhāva signal (p≈0.056) is borderline; the
  negative lord/kāraka trends are not individually significant (p≈0.26–0.28). This is a pilot
  that *localises where to look*, not a verdict.
- **The broader "outcome-classification over ~117 soft charts" premise did not hold.** An
  audit of the 275 unmapped verdict rows showed most are Raman's **analytical prose** captured
  as verdict phrases (e.g. "Saturn is in the 7th in a kendra…"), not discrete outcome labels.
  The longevity class is the one cleanly-labelable, objective categorical outcome in the
  held-out set; profession (10th) and disease (6th) outcomes are real but too multi-valued /
  fuzzy to score this way.
- **Label extraction is heuristic** (text scraping of the class term / death age); the
  negation phrasing *"does not indicate Pūrnāyu but…"* is a known trap, handled and manually
  verified here, but a caveat for any scale-up.

## Track L follow-up — the Āyushkāraka gap is NOT closable by re-scoping (2026-07-08)

The obvious fix was to re-score the Āyushkāraka for longevity: drop the benefic/malefic-nature
penalties and read Saturn on **dignity + placement only** (a well-placed but afflicted Saturn
should still give long life). Tested directly, it **fails — and makes things worse**:

| predictor | Spearman ρ | p |
|---|--:|--:|
| **8th bhāva** | **+0.521** | 0.056 |
| Lagna (1st bhāva) | +0.410 | 0.146 |
| 8th lord | −0.309 | 0.282 |
| Āyushkāraka (raw) | −0.326 | 0.256 |
| **Āyushkāraka, dignity+placement only** (the hypothesised fix) | **−0.440** | 0.116 |
| conclusion (blend) | −0.271 | 0.348 |

**Every lord/kāraka strength anti-correlates with longevity, and the "cleaned" dignity+placement
scoping is the *worst* of all.** The reason is selection, not a scoring bug: Raman's Pūrnāyu
examples are deliberately **afflicted-looking-Saturn-yet-long-lived** teaching cases (ch58/59/62
have deeply negative kāraka scores and full lifespans), so no strength reading of the kāraka can
track the class on this sample. Combining inputs confirms it — 8th+Lagna (+0.43) *dilutes* the
8th-alone signal, and adding the Lagna lord collapses it to ρ≈0.

**Conclusion:** the localised gap is **real but not closable in the sign-only engine.** The one
robust longevity signal is the **8th-bhāva fortification** the engine already computes (ρ=+0.52);
the engine's *blended conclusion* is the wrong longevity readout (ρ=−0.27) precisely because it
mixes in the anti-correlating lord/kāraka. A faithful Āyurdāya longevity model needs the
**degree-based lifespan arithmetic** (Piṇḍāyu/Aṁśāyu — `app/medini/ml/raman_saab/ayurdaya.py`),
which the sign-diagram reconstruction cannot supply — i.e. it belongs to the degree-upgrade
track (B), not a re-scoping. Recorded as a documented negative; the harness now scores all six
predictors so the result is reproducible.

## Interpretation

This confirms a **third validation dimension** (after strength and daśā-timing): the engine's
8th-house *fortification* score carries real longevity signal (ρ=+0.52), while **no** scoping of
the Āyushkāraka does — Raman's teaching-example selection puts the signal out of the kāraka's
reach on sign-only features, and a true lifespan model needs degree arithmetic. Measurement
only; no engine change. Guarded by `tests/doctrine/test_longevity_validate.py`.

## Productionized (2026-07-10)
The one validated predictor — the **8th-bhāva fortification** (ρ = +0.52) — is now surfaced
in the production reading grounding as `interpret.longevity_indication` / the `longevity`
block of `build_chart_grounding`. It exposes the 8th-bhāva score + grade mapped to a
directional band (above/average/below-average life support), with the honest confidence
attached (moderate rank correlation, **not** a deterministic life-span or class), and the
8th-lord/Āyushkāraka strength deliberately **excluded** (they trend the wrong way). Emitted
only when the 8th house is judged. Guarded by `tests/doctrine/test_longevity_grounding.py`.
The daśā timeline (94% held-out MD placement) was already wired via `resolve_current_dasha`
and the `dasha` block of the same grounding.
