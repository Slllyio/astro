"""Unit tests for the degree feature layer (app/medini/doctrine/domains/degree_features.py)
and its gating in the strength scorer. Deterministic, no ephemeris.

The gate is the load-bearing guarantee: degree features fire ONLY for
degree_resolved charts, so every sign-reconstructed number (the ch. IV anchor, the
HTJAH held-out) is byte-identical. The rest pin the doctrine-fixed feature maths.
"""
import math

from app.core.planet_state import COMBUSTION_ORBS
from app.medini.doctrine.domains import degree_features as D


# ---- combustion (orb-graded astangata) --------------------------------------------------

def test_combustion_zero_when_not_combust():
    # Saturn 100° away from the Sun is nowhere near combustion.
    assert D.combustion_weight("Saturn", 200.0, 100.0) == 0.0


def test_combustion_deepest_at_conjunction_and_tapers_to_zero_at_orb():
    orb = COMBUSTION_ORBS["Mercury"]           # 14°
    exact = D.combustion_weight("Mercury", 100.0, 100.0)     # exact conjunction
    mid = D.combustion_weight("Mercury", 100.0 + orb / 2, 100.0)
    near_edge = D.combustion_weight("Mercury", 100.0 + orb * 0.9, 100.0)
    assert exact < mid < 0                      # deeper (more negative) at conjunction
    assert mid < near_edge < 0                  # tapering toward 0 at the boundary
    assert math.isclose(exact, D._COMBUST_W, abs_tol=0.02)


def test_sun_and_nodes_never_combust():
    assert D.combustion_weight("Sun", 100.0, 100.0) == 0.0
    assert D.combustion_weight("Rahu", 100.0, 100.0) == 0.0


# ---- degree-graded dignity --------------------------------------------------------------

def test_shallow_exaltation_credited_below_deep():
    # Sun exalts in Aries (exact 10°). Deep (10°) keeps full +1.6 (delta 0);
    # a shallow Aries Sun (29°) is trimmed below the flat grade (delta < 0).
    deep = D.dignity_depth_delta("Sun", 1, 10.0)
    shallow = D.dignity_depth_delta("Sun", 1, 29.0)
    assert deep == 0.0
    assert shallow < 0.0


def test_dignity_depth_zero_outside_exalt_or_debil_sign():
    # Sun in Gemini (sign 3) is neither exalted nor debilitated: no degree refinement.
    assert D.dignity_depth_delta("Sun", 3, 65.0) == 0.0


def test_moolatrikona_credits_a_tier_over_own_sign():
    # Sun's moolatrikona is Leo 0-20° (abs 120-140°). In range -> positive delta;
    # own-sign Leo outside the range (25°, abs 145°) -> no MT bonus.
    assert D.moolatrikona_delta("Sun", 5, 130.0) > 0.0
    assert D.moolatrikona_delta("Sun", 5, 145.0) == 0.0


# ---- bhava-chalita placement ------------------------------------------------------------

def test_chalit_bhava_shifts_a_planet_near_a_cusp():
    from app.reading.computations.bhava_chalit import _chalit_bhava
    # Lagna at 178° (Virgo 28°). A planet at Libra 5° (185°) is whole-sign in the 2nd
    # from Virgo, but within +-15° of the Lagna madhya -> chalit-bhava 1.
    assert _chalit_bhava(185.0, 178.0) == 1
    # A planet squarely mid-sign stays put.
    assert _chalit_bhava(178.0, 178.0) == 1


# ---- the gate: sign charts are untouched ------------------------------------------------

def test_degree_features_gated_off_for_sign_reconstructed_chart():
    """A sign-reconstructed RamanChart is degree_resolved=False, so _d1_houses returns
    the whole-sign map unchanged and no combustion finding is emitted -- the guarantee
    that every established sign number stays byte-identical."""
    import json
    from pathlib import Path
    from app.medini.doctrine.validation import reconstruct as R
    from app.medini.doctrine.domains import house_judgment as HJ
    # A real, navamsa-reachable held-out record (sign reconstruction, not degrees).
    rec = json.loads(Path(
        "docs/raman_doctrine/validation/corpora/heldout_ch07_4th.json").read_text())["charts"][0]
    chart = R.chart_from_raman(rec["rasi"], rec["navamsa"],
                               rec["lagna_rasi"], rec["lagna_navamsa"])
    assert chart.degree_resolved is False
    # _d1_houses returns the whole-sign kundali map verbatim (no chalit shift).
    assert HJ._d1_houses(chart) == dict(chart.bundle.kundali.planet_house)
    # No combustion finding on any planet for a sign chart.
    assert all(HJ._combustion_finding(chart, p) is None for p in ("Sun", "Venus", "Mercury"))
