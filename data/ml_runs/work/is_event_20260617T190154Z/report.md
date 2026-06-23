# Astrological Rule Discovery — `is_event`

_Generated 2026-06-17 19:02 UTC_

## Run metadata

- **Target**: `is_event` (binary classification)
- **Training samples**: 3,261
- **Holdout test samples**: 816
- **Base positive rate**: 50.012%
- **Magnitude filter**: rules below 5% probability shift suppressed

## Model performance

- **Cross-validation ROC-AUC** (5-fold stratified): 0.5124 ± 0.0389
- **Holdout test ROC-AUC**: 0.5415

ROC-AUC interpretation: 0.5 = no signal, 1.0 = perfect discrimination. Astrological targets typically reach 0.6–0.75 if real signal exists; below 0.55 indicates the model didn't find discriminating features.

## Top features (by mean |SHAP|)

| Rank | Feature | Importance |
|---|---|---|
| 1 | `cross_lon_saturn` | 0.1942 |
| 2 | `cross_lon_jupiter` | 0.0974 |
| 3 | `active_ad_lord` | 0.0954 |
| 4 | `active_pd_lord` | 0.0913 |
| 5 | `cross_lon_rahu` | 0.0910 |
| 6 | `active_md_lord` | 0.0774 |
| 7 | `t_dec_venus` | 0.0690 |
| 8 | `t_house_pos_rahu` | 0.0650 |
| 9 | `t_d12_saturn_deg` | 0.0643 |
| 10 | `cross_lon_mars` | 0.0593 |
| 11 | `t_dist_mars_saturn` | 0.0544 |
| 12 | `t_sav_house_4` | 0.0527 |
| 13 | `cross_lon_mercury` | 0.0526 |
| 14 | `t_lagna_degree_in_sign` | 0.0510 |
| 15 | `t_nak_pos_ketu` | 0.0507 |
| 16 | `t_dist_mars_jupiter` | 0.0499 |
| 17 | `md_elapsed_years` | 0.0461 |
| 18 | `t_nak_pos_mars` | 0.0449 |
| 19 | `t_d10_moon_deg` | 0.0435 |
| 20 | `t_aspect_orb_mars_rahu` | 0.0431 |

## Discovered rules

_No rules passed the 5% magnitude filter — the model's signal is too diffuse to yield clean threshold rules. This often means the target class is too small (~1631 positives) or the discriminating features genuinely interact in ways simple thresholds can't capture. Try a related but larger target class, lower the magnitude filter, or examine the SHAP summary plot directly._

## Plot artifacts

- `shap_summary.png`
- `shap_dependence_cross_lon_saturn.png`
- `shap_dependence_cross_lon_jupiter.png`
- `shap_dependence_active_ad_lord.png`

## Reproducibility notes

- Training pipeline: `python -m app.medini.ml.train_classifier --target is_event --features <parquet>`
- Random seed pinned in the trainer to ensure deterministic outputs across reruns.
- Astrological features computed under sidereal Lahiri ayanamsa via the project's pyswisseph engine (see `app/core/ephemeris_engine.py`).
