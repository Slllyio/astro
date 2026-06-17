# Astrological Rule Discovery — `dissolution`

_Generated 2026-06-17 16:10 UTC_

## Run metadata

- **Target**: `dissolution` (binary classification)
- **Training samples**: 11,422
- **Holdout test samples**: 2,856
- **Base positive rate**: 23.946%
- **Magnitude filter**: rules below 5% probability shift suppressed

## Model performance

- **Cross-validation ROC-AUC** (5-fold stratified): 0.5681 ± 0.0081
- **Holdout test ROC-AUC**: 0.5780

ROC-AUC interpretation: 0.5 = no signal, 1.0 = perfect discrimination. Astrological targets typically reach 0.6–0.75 if real signal exists; below 0.55 indicates the model didn't find discriminating features.

## Top features (by mean |SHAP|)

| Rank | Feature | Importance |
|---|---|---|
| 1 | `aspect_orb_rahu_mercury` | 0.0629 |
| 2 | `aspect_orb_ketu_mercury` | 0.0542 |
| 3 | `dist_moon_saturn` | 0.0526 |
| 4 | `lagna_lon` | 0.0505 |
| 5 | `vel_mercury` | 0.0483 |
| 6 | `d12_mars_deg` | 0.0459 |
| 7 | `d9_moon_deg` | 0.0407 |
| 8 | `d12_rahu_deg` | 0.0406 |
| 9 | `lagna_degree_in_sign` | 0.0403 |
| 10 | `d10_moon_deg` | 0.0399 |
| 11 | `aspect_orb_saturn_jupiter` | 0.0372 |
| 12 | `aspect_orb_sun_jupiter` | 0.0365 |
| 13 | `aspect_orb_rahu_mars` | 0.0349 |
| 14 | `d12_rahu_sign` | 0.0325 |
| 15 | `dist_mercury_ketu` | 0.0325 |
| 16 | `acc_rahu` | 0.0308 |
| 17 | `house_pos_ketu` | 0.0302 |
| 18 | `nak_pos_saturn` | 0.0293 |
| 19 | `aspect_orb_ketu_sun` | 0.0285 |
| 20 | `acc_mercury` | 0.0279 |

## Discovered rules

_No rules passed the 5% magnitude filter — the model's signal is too diffuse to yield clean threshold rules. This often means the target class is too small (~2735 positives) or the discriminating features genuinely interact in ways simple thresholds can't capture. Try a related but larger target class, lower the magnitude filter, or examine the SHAP summary plot directly._

## Plot artifacts

- `shap_summary.png`
- `shap_dependence_aspect_orb_rahu_mercury.png`
- `shap_dependence_aspect_orb_ketu_mercury.png`
- `shap_dependence_dist_moon_saturn.png`

## Reproducibility notes

- Training pipeline: `python -m app.medini.ml.train_classifier --target dissolution --features <parquet>`
- Random seed pinned in the trainer to ensure deterministic outputs across reruns.
- Astrological features computed under sidereal Lahiri ayanamsa via the project's pyswisseph engine (see `app/core/ephemeris_engine.py`).
