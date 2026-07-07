# Phase B — fitted scheme parameters (FIT_REPORT)

**Fitting the house-strength scheme as a constrained ordinal model, trained on the tuned corpora (h2/7/9/11 + ch. IV anchor, 112 rows) and validated on the disjoint held-out Ch VII set (12 rows) through the LIVE engine.**

## Headline

| set | current (hand-decoded) | fitted |
|---|---|---|
| train (112 rows) within-one | 79% | 83% |
| **held-out (12 rows) within-one** | **50%** | **58%** |
| anchor within-one (hard constraint) | 100% | 100% |

- train: current n=112  exact=54 (48%)  within-one=89 (79%)  mean=-0.018 → fitted n=112  exact=53 (47%)  within-one=93 (83%)  mean=-0.062
- held-out: current within-one 6/12 (50.0%), mean +0.667 → fitted 7/12 (58.3%), mean +0.417

## What moved (|Δ| ≥ 0.02, vs the decoded prior)

| parameter | current | fitted | Δ |
|---|---|---|---|
| `s.pos_knee` | +1.600 | +1.298 | -0.302 |
| `w.kendra_trikona` | +1.200 | +0.913 | -0.287 |
| `dg.friendly` | +0.800 | +0.604 | -0.196 |
| `dg.debilitated` | -1.600 | -1.445 | +0.155 |
| `w.kartari_papa` | -1.000 | -0.866 | +0.134 |
| `w.dusthana` | -1.000 | -0.876 | +0.124 |
| `w.conjunct` | +0.700 | +0.579 | -0.121 |
| `w.kartari_subha` | +1.000 | +1.089 | +0.089 |
| `s.rescue_knee` | +1.200 | +1.117 | -0.083 |
| `dg.inimical` | -0.800 | -0.860 | -0.060 |
| `w.dusthana_lord` | -1.000 | -0.941 | +0.059 |
| `dg.exalted` | +1.600 | +1.656 | +0.056 |
| `s.rescue_w_weak` | +0.900 | +0.846 | -0.054 |
| `t.gap2` | +0.850 | +0.797 | -0.053 |
| `t.gap3` | +0.300 | +0.253 | -0.047 |
| `t.gap4` | +0.350 | +0.312 | -0.038 |
| `w.bhava_aspect_mul` | +0.500 | +0.532 | +0.032 |
| `s.afflict_floor` | -1.000 | -1.028 | -0.028 |
| `t.gap5` | +0.350 | +0.324 | -0.026 |
| `w.vargottama` | +1.200 | +1.226 | +0.026 |
| `s.pos_slope` | +0.100 | +0.125 | +0.025 |
| `dg.own` | +1.200 | +1.220 | +0.020 |

## Held-out divergences (fitted)

- ch64 bhava: engine `moderately good` vs Raman `fairly strong` (-2)
- ch64 lord: engine `moderate` vs Raman `afflicted` (+2)
- ch70 lord: engine `moderate` vs Raman `afflicted` (+2)
- ch70 karaka: engine `moderate` vs Raman `afflicted` (+2)
- ch74 bhava: engine `weak` vs Raman `moderately good` (-2)

## Interpretation

The optimizer had no access to the held-out set, yet it moved the scheme in the direction the hand-analysis predicted:
- **Positive-saturation earlier:** the cap knee `s.pos_knee` dropped 1.60 → 1.30 (-0.30) — stacked positives saturate sooner, the exact over-crediting the audit flagged.
- **Kendra over-credit trimmed:** `w.kendra_trikona` dropped 1.20 → 0.91 (-0.29) — the kendra-placement lift the held-out kāraka rows said was too high.
- **Over-crediting bias reduced:** held-out mean Δ moved +0.67 → +0.42 toward Raman (0 = unbiased), and held-out within-one rose 50% → 58%.
- **The residual gap is structural, not parametric.** The surviving held-out misses are opposite-signed — the lord/kāraka is still *over*-rated (+2) while clean bhāvas are *under*-rated (−2). No single re-weighting can push both toward Raman at once, which is why weight-fitting plateaus here: closing them needs new terms (a structural-purity lift for clean houses; a harder affliction penalty for a malefic-hemmed kāraka), i.e. the next engine increments, not a coefficient.

## Guardrails honored

- **Sign constraints:** every benefic weight stayed ≥ 0 and every malefic weight ≤ 0 (bounds derived from doctrinal class) — no polarity inverted.
- **Train/test wall:** the held-out Ch VII rows were never seen by the optimizer; they were scored only through the live engine with the fitted constants patched in.
- **Anchor:** the ch. IV calibration anchor stayed 100% within-one.
- **Regularized toward the decoded priors:** thresholds held hardest (reg 4.0), weights/structural looser (0.4/0.6).

## Promotion

Adopting any fitted constant into `house_judgment.py` is a SEPARATE, explicitly-gated engine increment (guarded by the anchor + audit gates), never automatic. `fitted_weights.json` holds the full vector.

