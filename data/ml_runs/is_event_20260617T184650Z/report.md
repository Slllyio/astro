# Astrological Rule Discovery — `is_event`

_Generated 2026-06-17 18:46 UTC_

## Run metadata

- **Target**: `is_event` (binary classification)
- **Training samples**: 1,729
- **Holdout test samples**: 433
- **Base positive rate**: 50.000%
- **Magnitude filter**: rules below 5% probability shift suppressed

## Model performance

- **Cross-validation ROC-AUC** (5-fold stratified): 0.5422 ± 0.0306
- **Holdout test ROC-AUC**: 0.5424

ROC-AUC interpretation: 0.5 = no signal, 1.0 = perfect discrimination. Astrological targets typically reach 0.6–0.75 if real signal exists; below 0.55 indicates the model didn't find discriminating features.

## Top features (by mean |SHAP|)

| Rank | Feature | Importance |
|---|---|---|
| 1 | `cross_lon_saturn` | 0.6204 |
| 2 | `active_md_lord` | 0.1588 |
| 3 | `active_ad_lord` | 0.1313 |
| 4 | `cross_lon_rahu` | 0.1233 |
| 5 | `cross_lon_jupiter` | 0.1144 |
| 6 | `active_pd_lord` | 0.1032 |
| 7 | `t_house_pos_saturn` | 0.1003 |
| 8 | `transit_bav_saturn` | 0.0964 |
| 9 | `t_d10_jupiter_deg` | 0.0865 |
| 10 | `t_d10_mars_deg` | 0.0847 |
| 11 | `t_panchanga_vara` | 0.0845 |
| 12 | `t_lat_mercury` | 0.0760 |
| 13 | `t_d12_moon_deg` | 0.0756 |
| 14 | `t_lat_moon` | 0.0744 |
| 15 | `t_sav_house_4` | 0.0736 |
| 16 | `ad_elapsed_years` | 0.0709 |
| 17 | `t_dist_moon_jupiter` | 0.0679 |
| 18 | `t_tattva_rahu` | 0.0659 |
| 19 | `t_dispositor_saturn` | 0.0635 |
| 20 | `transit_bav_moon` | 0.0602 |

## Discovered rules

_No rules passed the 5% magnitude filter — the model's signal is too diffuse to yield clean threshold rules. This often means the target class is too small (~864 positives) or the discriminating features genuinely interact in ways simple thresholds can't capture. Try a related but larger target class, lower the magnitude filter, or examine the SHAP summary plot directly._

## Plot artifacts

- `shap_summary.png`
- `shap_dependence_cross_lon_saturn.png`
- `shap_dependence_active_md_lord.png`
- `shap_dependence_active_ad_lord.png`

## Reproducibility notes

- Training pipeline: `python -m app.medini.ml.train_classifier --target is_event --features <parquet>`
- Random seed pinned in the trainer to ensure deterministic outputs across reruns.
- Astrological features computed under sidereal Lahiri ayanamsa via the project's pyswisseph engine (see `app/core/ephemeris_engine.py`).
