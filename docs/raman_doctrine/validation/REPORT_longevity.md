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

## Interpretation

This confirms a **third validation dimension** (after strength and daśā-timing): the engine's
8th-house *fortification* score carries real longevity signal, while its Āyushkāraka score
does not — a concrete, localised doctrine gap (longevity-specific kāraka rules) surfaced by
testing Raman's own outcomes rather than only his strength phrases. Measurement only; no
engine change. Guarded by `tests/doctrine/test_longevity_validate.py`.
