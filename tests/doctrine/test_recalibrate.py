"""Guard for the accuracy Phase-2 recalibration DECISION (documented negative result).

Recalibration was NOT applied: it cannot lift held-out without collapsing the anchor
(8/8 -> 2/8) and dropping the tuned corpora. These pin that the engine's shared
calibration constants remain at their un-shifted values, so the anchor/tuned gates stay
intact, and that the measurement tool still imports.
"""
from app.medini.doctrine.domains import house_judgment as HJ
from app.medini.doctrine.validation import recalibrate as RC


def test_recalibration_not_applied_engine_unchanged():
    # the top grade boundary is the un-shifted 2.4 and the planet blend is the original 0.3
    assert HJ._THRESH[0][0] == 2.4
    assert HJ._BLEND_W == 0.3


def test_recalibrate_tool_imports_and_exposes_search():
    assert hasattr(RC, "loco_cv") and hasattr(RC, "build_cache")
