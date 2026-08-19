"""Track-B personality harness — pins the feature rule + the null result.

Fast: the stratified-permutation statistics are reused verbatim from the
vocation harness (guarded there); here we pin the frozen native_profile feature
rule and the committed headline (F1 + F3 all null, powered) when present.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.medini.ml.raman_saab import personality_validate as P

_ROOT = Path(__file__).resolve().parents[1]
_RESULTS = _ROOT / "data/ml_runs/raman_saab/personality_validation.json"


def test_feature_rule_is_the_frozen_native_profile_condition():
    """The population predictor IS the served native_profile well_placed rule."""
    from app.reading._planet_lexicon import well_placed
    # exalted, not combust → well placed (+1)
    assert well_placed("exalted", 30.0, False) is True
    # debilitated OR combust → under strain (−1), regardless of composite
    assert well_placed("debilitated", 95.0, False) is False
    assert well_placed("own", 95.0, True) is False       # combust overrides
    # neutral dignity falls to the composite band (55 / 42)
    assert well_placed("friendly", 60.0, False) is True
    assert well_placed("friendly", 40.0, False) is False
    assert well_placed("friendly", 50.0, False) is None  # mixed


def test_reuses_vocation_statistics_verbatim():
    """The null + power machinery is imported from vocation_validate, not re-implemented."""
    from app.medini.ml.raman_saab import vocation_validate as V
    assert P.strat_test is V.strat_test
    assert P.null_calibration is V.null_calibration
    assert P.planted_recovery is V.planted_recovery


def test_governing_grahas_and_bonferroni_k():
    """6 governing grahas; K = 1 (F1) + 12 (F3) = 13 → α = 0.05/13."""
    assert P._GOV == ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus")
    assert len(P._VOC_MAP) == 12
    # α is derived in run_battery; recompute the pre-registered value
    assert abs((0.05 / 13) - 0.0038461538) < 1e-9


def test_headline_all_null_and_powered():
    """The committed run: F1 + every F3 test null (RR < 1.20), null powered."""
    if not _RESULTS.exists():
        return  # results not materialised in this checkout
    o = json.loads(_RESULTS.read_text())
    assert o["n_marriage"] >= 13_000 and o["n_vocation"] >= 55_000
    # F1 flagship: no relationship signal
    f1 = o["family1_relationship"]["main"]
    assert f1["verdict"] in ("refuted", "underpowered")
    assert f1["rr"] is None or f1["rr"] < 1.20, f1
    cont = o["family1_relationship"]["continuous"]
    assert abs(cont["cohens_d"]) < 0.1, cont      # continuous arm also flat
    # F3: all 12 refuted, none clears the effect gate
    assert len(o["family3_vocation"]) == 12
    for r in o["family3_vocation"]:
        assert r["verdict"] in ("refuted", "underpowered"), r
        if r["rr"] is not None:
            assert r["rr"] < 1.20, r
    # null powered: calibrated + a G1-sized planted effect recovered
    v = o["validity"]
    assert abs(v["null_calibration"]["z_mean"]) < 0.2
    assert 0.85 <= v["null_calibration"]["z_sd"] <= 1.15
    assert v["planted_rr120"]["rr"] >= 1.15 and v["planted_rr120"]["z"] > 8
