# Astrological Rule Discovery — `is_event`

_Generated 2026-06-17 19:00 UTC_

## Run metadata

- **Target**: `is_event` (binary classification)
- **Training samples**: 1,886
- **Holdout test samples**: 472
- **Base positive rate**: 50.000%
- **Magnitude filter**: rules below 5% probability shift suppressed

## Model performance

- **Cross-validation ROC-AUC** (5-fold stratified): 0.5416 ± 0.0146
- **Holdout test ROC-AUC**: 0.5512

ROC-AUC interpretation: 0.5 = no signal, 1.0 = perfect discrimination. Astrological targets typically reach 0.6–0.75 if real signal exists; below 0.55 indicates the model didn't find discriminating features.

## Top features (by mean |SHAP|)

| Rank | Feature | Importance |
|---|---|---|
| 1 | `cross_lon_saturn` | 0.5171 |
| 2 | `cross_lon_jupiter` | 0.2152 |
| 3 | `cross_lon_rahu` | 0.1567 |
| 4 | `ad_elapsed_years` | 0.1003 |
| 5 | `cross_lon_mars` | 0.0959 |
| 6 | `md_elapsed_years` | 0.0956 |
| 7 | `t_lat_moon` | 0.0826 |
| 8 | `transit_bav_moon` | 0.0806 |
| 9 | `transit_bav_venus` | 0.0775 |
| 10 | `t_d10_mars_sign` | 0.0748 |
| 11 | `pd_elapsed_years` | 0.0687 |
| 12 | `t_dist_moon_jupiter` | 0.0686 |
| 13 | `active_ad_lord` | 0.0662 |
| 14 | `active_md_lord` | 0.0656 |
| 15 | `active_pd_lord` | 0.0653 |
| 16 | `t_dist_mercury_ketu` | 0.0642 |
| 17 | `t_nak_pos_moon` | 0.0634 |
| 18 | `t_aspect_orb_jupiter_sun` | 0.0633 |
| 19 | `t_nak_pos_sun` | 0.0609 |
| 20 | `t_house_pos_ketu` | 0.0591 |

## Discovered rules

_No rules passed the 5% magnitude filter — the model's signal is too diffuse to yield clean threshold rules. This often means the target class is too small (~943 positives) or the discriminating features genuinely interact in ways simple thresholds can't capture. Try a related but larger target class, lower the magnitude filter, or examine the SHAP summary plot directly._

## Plot artifacts

- `shap_summary.png`
- `shap_dependence_cross_lon_saturn.png`
- `shap_dependence_cross_lon_jupiter.png`
- `shap_dependence_cross_lon_rahu.png`

## Reproducibility notes

- Training pipeline: `python -m app.medini.ml.train_classifier --target is_event --features <parquet>`
- Random seed pinned in the trainer to ensure deterministic outputs across reruns.
- Astrological features computed under sidereal Lahiri ayanamsa via the project's pyswisseph engine (see `app/core/ephemeris_engine.py`).
