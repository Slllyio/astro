"""Guards for the Phase B weight-fitting harness (app.medini.doctrine.validation.fit_weights).

Pins the cheap invariants (no optimizer run — the fit itself is a ~30s CLI job):
  * the parameterized scheme reproduces the LIVE engine at the default vector,
  * ``apply_to_engine`` patches then fully restores the live constants,
  * the COMMITTED ``fitted_weights.json`` still honors its guarantees on the live engine:
    the anchor stays 100% within-one and held-out within-one does not regress below the
    hand-decoded baseline (6/12).
"""
from __future__ import annotations

import copy

from app.medini.doctrine.domains import house_judgment as HJ
from app.medini.doctrine.validation import fit_weights as F


def _rows():
    return F.load_rows(F.TUNED_FILES)


def test_parameterized_scheme_matches_live_at_defaults():
    """delta_of + _combine + _verdict_label, re-expressed with explicit params, must
    equal the live engine row-for-row at the decoded defaults -- else the optimizer is
    fitting a different model than the one it patches for validation."""
    assert F.self_check_rows(_rows()) == 0


def test_apply_to_engine_restores_constants():
    before = {k: copy.deepcopy(getattr(HJ, k)) for k in
              ("_DIGNITY_W", "_W", "_POS_KNEE", "_POS_SLOPE", "_BLEND_W",
               "_RESCUE_KNEE", "_RESCUE_W_WEAK", "_AFFLICT_FLOOR", "_THRESH")}
    dg, w, s, b = F.load_fitted()
    restore = F.apply_to_engine(dg, w, s, b)
    # while patched, at least one constant differs
    assert HJ._POS_KNEE != before["_POS_KNEE"] or HJ._W != before["_W"]
    restore()
    for k, v in before.items():
        assert getattr(HJ, k) == v, f"{k} not restored"


def test_committed_fit_holds_anchor_and_does_not_regress_heldout():
    dg, w, s, b = F.load_fitted()
    # anchor stays 100% within-one (the hard constraint)
    assert F.anchor_within1(_rows(), dg, w, s, b)
    # held-out through the LIVE engine does not fall below the hand-decoded baseline
    base = F.heldout(*F._unpack(F.DEFAULTS))
    fitted = F.heldout(dg, w, s, b)
    assert fitted["within1"] >= base["within1"]
    # constants are fully restored after each heldout() call
    assert HJ._POS_KNEE == F._unpack(F.DEFAULTS)[2]["pos_knee"]
