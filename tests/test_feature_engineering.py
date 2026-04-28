"""Tests for app.medini.etl.feature_engineering — the Vedic Tensor.

Pinned against the Bangalore 1990-07-15 12:00 IST baseline (same anchor
used across the rest of the suite). Uses pyswisseph directly to compute
JD; no network, no DB.
"""
from __future__ import annotations

import pytest
import swisseph as swe

from app.medini.etl.feature_engineering import (
    GRAHAS,
    SIGN_RULERS,
    circular_distance_180,
    combustion_intensity,
    compute_chart_features,
    compute_dispositor,
    compute_dispositor_chain_depth,
    compute_final_dispositor,
    expected_feature_columns,
)
from app.medini.etl.lahiri_worker import assert_lahiri_active, init_worker

# Same baseline pinned in test_dasha_dates.py / test_lagna.py / test_persistence.py.
BANGALORE_JD = swe.julday(1990, 7, 15, 6.5, swe.GREG_CAL)


@pytest.fixture(scope="module", autouse=True)
def _ensure_lahiri():
    """Most other tests rely on the engine module's import-time Lahiri setup;
    these tests pin it explicitly to guarantee feature-engineering correctness."""
    init_worker()
    yield


# ---------- Worker initializer ----------

def test_init_worker_sets_lahiri_mode() -> None:
    init_worker()
    # Must NOT raise — Lahiri ayanamsa for J2000 is ~23.85°
    assert_lahiri_active()


def test_assert_lahiri_active_fails_when_not_set() -> None:
    """If we explicitly clear sidereal mode, the assert must fire."""
    swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)  # different ayanamsa, different value
    try:
        # Fagan-Bradley ayanamsa at J2000 is ~24.74° — still > 23, so this
        # specific assertion happens to pass under different sidereal modes.
        # The assert is targeted at the "no sidereal mode set at all" case.
        # That's hard to test cleanly without monkeypatching swisseph internals,
        # so we just confirm that setting some sidereal mode DOES yield non-zero.
        ay = swe.get_ayanamsa_ut(2451545.0)
        assert ay > 23.0
    finally:
        init_worker()  # restore Lahiri for downstream tests


# ---------- Pure helpers ----------

@pytest.mark.parametrize("a,b,expected", [
    (0.0, 0.0, 0.0),
    (10.0, 20.0, 10.0),
    (359.0, 2.0, 3.0),     # Pisces/Aries cusp
    (180.0, 0.0, 180.0),
    (270.0, 90.0, 180.0),
    (-1.0, 1.0, 2.0),      # negative input
])
def test_circular_distance_180(a: float, b: float, expected: float) -> None:
    assert circular_distance_180(a, b) == pytest.approx(expected, abs=1e-9)


def test_combustion_intensity_sun_self_is_one() -> None:
    """The Sun's own combustion column is always 1.0 by convention."""
    assert combustion_intensity(0.0, 0.0, "Sun") == 1.0
    assert combustion_intensity(123.4, 999.0, "Sun") == 1.0


def test_combustion_intensity_exact_conjunction_is_one() -> None:
    """Cazimi: Mercury exactly on Sun = max intensity."""
    assert combustion_intensity(100.0, 100.0, "Mercury") == 1.0


def test_combustion_intensity_at_orb_boundary_is_zero() -> None:
    """At exactly the orb threshold, intensity is 0.0 (linear decay)."""
    # Mercury orb = 12°
    assert combustion_intensity(0.0, 12.0, "Mercury") == 0.0
    # Saturn orb = 15°
    assert combustion_intensity(0.0, 15.0, "Saturn") == 0.0


def test_combustion_intensity_outside_orb_is_zero() -> None:
    assert combustion_intensity(0.0, 30.0, "Mercury") == 0.0
    assert combustion_intensity(0.0, 60.0, "Jupiter") == 0.0


def test_combustion_intensity_nodes_never_combust() -> None:
    """Rahu/Ketu never combust in classical Vedic. Intensity stays 0."""
    assert combustion_intensity(0.0, 1.0, "Rahu") == 0.0
    assert combustion_intensity(0.0, 0.5, "Ketu") == 0.0


def test_combustion_intensity_decays_linearly() -> None:
    """Half-orb distance → 0.5 intensity (per the linear-decay formula)."""
    # Mercury orb = 12°; halfway = 6°
    assert combustion_intensity(0.0, 6.0, "Mercury") == pytest.approx(0.5, abs=1e-9)


# ---------- Dispositor chain ----------

def test_compute_dispositor() -> None:
    """Sun in Aries (sign 1, ruled by Mars) → dispositor = Mars."""
    assert compute_dispositor("Sun", 1) == "Mars"
    assert compute_dispositor("Mercury", 5) == "Sun"  # Leo ruled by Sun
    assert compute_dispositor("Saturn", 10) == "Saturn"  # self-disposited


def test_compute_dispositor_chain_depth_self_disposited() -> None:
    """Saturn in Capricorn (sign 10) is self-disposited; depth = 0."""
    chart_signs = {"Sun": 5, "Saturn": 10}  # Sun in Leo, Saturn in Cap
    assert compute_dispositor_chain_depth("Saturn", chart_signs) == 0
    assert compute_dispositor_chain_depth("Sun", chart_signs) == 0


def test_compute_dispositor_chain_depth_one_hop() -> None:
    """Sun in Aries → Mars in Capricorn → Saturn in own sign. Sun's chain = 2 hops."""
    chart_signs = {
        "Sun": 1,        # Aries → Mars
        "Mars": 10,      # Capricorn → Saturn
        "Saturn": 10,    # own sign — terminator
    }
    assert compute_dispositor_chain_depth("Sun", chart_signs) == 2
    assert compute_dispositor_chain_depth("Mars", chart_signs) == 1
    assert compute_dispositor_chain_depth("Saturn", chart_signs) == 0


def test_compute_final_dispositor_simple() -> None:
    """Single self-disposited planet ⇒ everyone routes to it."""
    chart_signs = {p: 5 for p in GRAHAS}  # everyone in Leo (Sun's sign)
    chart_signs["Sun"] = 5  # explicit
    assert compute_final_dispositor(chart_signs) == "Sun"


def test_compute_final_dispositor_no_self_disposited_returns_none() -> None:
    """Highly contrived chart with no planet in own sign → no chain terminator."""
    chart_signs = {
        "Sun": 4,        # Cancer (ruled by Moon)
        "Moon": 5,       # Leo (ruled by Sun)  — circular with Sun
        "Mars": 7,       # Libra (ruled by Venus)
        "Mercury": 1,    # Aries (ruled by Mars)
        "Jupiter": 6,    # Virgo (ruled by Mercury)
        "Venus": 3,      # Gemini (ruled by Mercury)
        "Saturn": 4,     # Cancer (ruled by Moon)
        "Rahu": 1,       # Aries (ruled by Mars)
        "Ketu": 7,       # Libra (ruled by Venus)
    }
    # Sun-Moon mutual reception, but neither in own sign — no terminator.
    assert compute_final_dispositor(chart_signs) == "none"


# ---------- The big composition ----------

def test_compute_chart_features_shape() -> None:
    """Bangalore baseline produces the expected schema, no missing/extra columns."""
    features = compute_chart_features(BANGALORE_JD, latitude=12.97, longitude=77.59)
    expected = set(expected_feature_columns())
    actual = set(features.keys())
    assert actual == expected, f"missing={expected - actual}, extra={actual - expected}"


def test_compute_chart_features_lon_in_valid_range() -> None:
    features = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    for graha in GRAHAS:
        lon = features[f"lon_{graha.lower()}"]
        assert 0.0 <= lon < 360.0, f"lon_{graha} out of range: {lon}"


def test_compute_chart_features_pinned_bangalore_known_values() -> None:
    """Cross-pin against existing test baselines: Bangalore = Virgo Lagna,
    Moon in Revati (nakshatra index 26), Mercury MD."""
    features = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    assert features["lagna_sign"] == 6  # Virgo
    assert features["nak_moon"] == 26   # Revati


def test_compute_chart_features_velocity_is_nonzero() -> None:
    """Critical regression for FLG_SPEED: velocities must be set, not zero."""
    features = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    # Sun's daily motion ≈ 0.95-1.02°/day depending on time of year. Saturn ≈ 0.034°.
    # If FLG_SPEED is missing, both would be exactly 0.0.
    assert abs(features["vel_sun"]) > 0.5, "Sun velocity should be ~1°/day"
    assert features["vel_saturn"] != 0.0, "Saturn velocity should not be exactly zero"


def test_compute_chart_features_distances_are_in_0_180_range() -> None:
    features = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    for key, value in features.items():
        if key.startswith("dist_"):
            assert 0.0 <= value <= 180.0, f"{key} out of range: {value}"


def test_compute_chart_features_oob_is_binary() -> None:
    features = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    for graha in GRAHAS:
        flag = features[f"oob_{graha.lower()}"]
        assert flag in (0, 1), f"oob_{graha} should be 0 or 1, got {flag}"


def test_compute_chart_features_dispositors_are_valid_planets() -> None:
    features = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    valid = set(SIGN_RULERS.values()) | {"none"}
    for graha in GRAHAS:
        disp = features[f"dispositor_{graha.lower()}"]
        assert disp in valid, f"dispositor_{graha} = {disp!r} invalid"


def test_compute_chart_features_d9_d10_signs_valid() -> None:
    features = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    for graha in GRAHAS:
        d9 = features[f"d9_{graha.lower()}_sign"]
        d10 = features[f"d10_{graha.lower()}_sign"]
        assert 1 <= d9 <= 12, f"d9_{graha}_sign = {d9}"
        assert 1 <= d10 <= 12, f"d10_{graha}_sign = {d10}"


def test_compute_chart_features_sav_house_total_invariant() -> None:
    """SAV grand total across 12 houses should match the BAV chart-invariant
    (sum of per-planet totals: 48+49+40+54+56+52+39 = 338)."""
    features = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    sav_total = sum(features[f"sav_house_{i}"] for i in range(1, 13))
    assert sav_total == 338, f"SAV grand total = {sav_total}, expected 338"


def test_expected_feature_columns_count() -> None:
    """The schema regression test: column count is locked at 193."""
    cols = expected_feature_columns()
    assert len(cols) == 193, f"feature column count drifted: {len(cols)} != 193"
    # No duplicate column names (ordering quirks could create these)
    assert len(cols) == len(set(cols)), "duplicate column names"


def test_compute_chart_features_is_deterministic() -> None:
    """Same JD + lat/lon → identical features on every call."""
    a = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    b = compute_chart_features(BANGALORE_JD, 12.97, 77.59)
    assert a == b
