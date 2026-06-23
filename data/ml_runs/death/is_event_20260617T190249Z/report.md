# Astrological Rule Discovery — `is_event`

_Generated 2026-06-17 19:02 UTC_

## Run metadata

- **Target**: `is_event` (binary classification)
- **Training samples**: 2,144
- **Holdout test samples**: 537
- **Base positive rate**: 50.019%
- **Magnitude filter**: rules below 5% probability shift suppressed

## Model performance

- **Cross-validation ROC-AUC** (5-fold stratified): 0.4389 ± 0.0210
- **Holdout test ROC-AUC**: 0.4543

ROC-AUC interpretation: 0.5 = no signal, 1.0 = perfect discrimination. Astrological targets typically reach 0.6–0.75 if real signal exists; below 0.55 indicates the model didn't find discriminating features.

## Top features (by mean |SHAP|)

| Rank | Feature | Importance |
|---|---|---|
| 1 | `cross_lon_saturn` | 0.1118 |
| 2 | `t_d12_jupiter_sign` | 0.1041 |
| 3 | `t_dist_jupiter_saturn` | 0.1027 |
| 4 | `t_d12_rahu_deg` | 0.0997 |
| 5 | `t_aspect_orb_ketu_moon` | 0.0847 |
| 6 | `t_house_pos_jupiter` | 0.0803 |
| 7 | `cross_lon_rahu` | 0.0729 |
| 8 | `t_d10_venus_deg` | 0.0655 |
| 9 | `t_aspect_orb_moon_venus` | 0.0649 |
| 10 | `cross_lon_mercury` | 0.0648 |
| 11 | `active_pd_lord` | 0.0623 |
| 12 | `t_final_dispositor` | 0.0612 |
| 13 | `t_nak_pos_moon` | 0.0597 |
| 14 | `active_ad_lord` | 0.0595 |
| 15 | `t_aspect_orb_moon_mercury` | 0.0592 |
| 16 | `md_elapsed_years` | 0.0590 |
| 17 | `t_jerk_jupiter` | 0.0572 |
| 18 | `t_sav_house_1` | 0.0524 |
| 19 | `t_d12_mercury_deg` | 0.0523 |
| 20 | `t_dist_mercury_venus` | 0.0508 |

## Discovered rules

_No rules passed the 5% magnitude filter — the model's signal is too diffuse to yield clean threshold rules. This often means the target class is too small (~1072 positives) or the discriminating features genuinely interact in ways simple thresholds can't capture. Try a related but larger target class, lower the magnitude filter, or examine the SHAP summary plot directly._

## Plot artifacts

- `shap_summary.png`
- `shap_dependence_cross_lon_saturn.png`
- `shap_dependence_t_d12_jupiter_sign.png`
- `shap_dependence_t_dist_jupiter_saturn.png`

## Reproducibility notes

- Training pipeline: `python -m app.medini.ml.train_classifier --target is_event --features <parquet>`
- Random seed pinned in the trainer to ensure deterministic outputs across reruns.
- Astrological features computed under sidereal Lahiri ayanamsa via the project's pyswisseph engine (see `app/core/ephemeris_engine.py`).
