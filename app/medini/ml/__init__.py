"""Phase 5 Stage 3: ML rule discovery via XGBoost + SHAP.

Three sub-modules:
  - shap_rules.py: extract human-readable rules from SHAP values + feature values.
  - report_writer.py: Markdown report combining model metrics + rules + plot paths.
  - train_classifier.py: orchestration CLI (XGBoost training, SHAP, output dir).

The rule-extraction pipeline runs offline and emits artifacts to
`data/ml_runs/{target}_{timestamp}/`. Phase 5C will wrap this for a live
prediction endpoint; v1 is CLI-only.
"""
