"""Pure-function tests for Vedic aspect detection. No DB, no Swiss Ephemeris."""
from __future__ import annotations

import pytest

from app.daemon.nadi_rules import (
    AspectResult,
    VEDIC_ASPECTS,
    circular_distance,
    compute_vedic_aspect,
    whole_sign_house_distance,
)


# ---------- circular_distance ----------

@pytest.mark.parametrize("a,b,expected", [
    (0.0, 0.0, 0.0),
    (10.0, 10.0, 0.0),
    (10.0, 20.0, 10.0),
    (20.0, 10.0, 10.0),
    (180.0, 0.0, 180.0),
    (90.0, 270.0, 180.0),  # antipode the other way
    (350.0, 10.0, 20.0),   # cusp wrap
    (359.0, 2.0, 3.0),     # 3-degree separation across Pisces/Aries cusp
    (2.0, 359.0, 3.0),     # symmetric
    (0.0, 360.0, 0.0),     # 0 == 360
])
def test_circular_distance(a: float, b: float, expected: float) -> None:
    assert circular_distance(a, b) == pytest.approx(expected, abs=1e-9)


def test_circular_distance_is_symmetric() -> None:
    for a, b in [(7.5, 142.3), (350.1, 9.4), (180.0, 359.99)]:
        assert circular_distance(a, b) == pytest.approx(circular_distance(b, a))


# ---------- whole_sign_house_distance ----------

@pytest.mark.parametrize("from_sign,to_sign,expected", [
    (1, 1, 1),    # Aries -> Aries: 1st (same sign)
    (1, 7, 7),    # Aries -> Libra: 7th
    (1, 12, 12),  # Aries -> Pisces: 12th
    (7, 1, 7),    # Libra -> Aries: 7th (forward wrap)
    (12, 1, 2),   # Pisces -> Aries: 2nd (wrap)
    (5, 5, 1),    # any same-sign is 1st
])
def test_whole_sign_house_distance(from_sign: int, to_sign: int, expected: int) -> None:
    assert whole_sign_house_distance(from_sign, to_sign) == expected


def test_whole_sign_house_distance_validates_range() -> None:
    with pytest.raises(ValueError):
        whole_sign_house_distance(0, 1)
    with pytest.raises(ValueError):
        whole_sign_house_distance(1, 13)


# ---------- compute_vedic_aspect: positive cases for every rule ----------

# Each tuple: (transit_planet, transit_sign, natal_sign, expected_alert_type)
# We pick transit_sign=1 (Aries) so the house distance equals the natal sign.
ASPECT_CASES = [
    ("Saturn", 1, 1, "CONJUNCTION"),
    ("Saturn", 1, 7, "OPPOSITION"),
    ("Saturn", 1, 3, "SATURN_3RD"),
    ("Saturn", 1, 10, "SATURN_10TH"),
    ("Jupiter", 1, 1, "CONJUNCTION"),
    ("Jupiter", 1, 7, "OPPOSITION"),
    ("Jupiter", 1, 5, "JUPITER_5TH"),
    ("Jupiter", 1, 9, "JUPITER_9TH"),
    ("Mars", 1, 1, "CONJUNCTION"),
    ("Mars", 1, 7, "OPPOSITION"),
    ("Mars", 1, 4, "MARS_4TH"),
    ("Mars", 1, 8, "MARS_8TH"),
    ("Rahu", 1, 1, "CONJUNCTION"),
    ("Rahu", 1, 7, "OPPOSITION"),
    ("Rahu", 1, 5, "NODE_5TH"),
    ("Rahu", 1, 9, "NODE_9TH"),
    ("Ketu", 1, 1, "CONJUNCTION"),
    ("Ketu", 1, 5, "NODE_5TH"),
]


@pytest.mark.parametrize("planet,t_sign,n_sign,expected", ASPECT_CASES)
def test_aspect_positive(planet: str, t_sign: int, n_sign: int, expected: str) -> None:
    """Every row in VEDIC_ASPECTS must produce a hit at the matching house distance."""
    result = compute_vedic_aspect(
        transit_planet=planet,
        transit_sign=t_sign,
        transit_lon=(t_sign - 1) * 30 + 15.0,
        natal_planet="Moon",
        natal_sign=n_sign,
        natal_lon=(n_sign - 1) * 30 + 15.0,
        orb_degrees=3.0,
    )
    assert isinstance(result, AspectResult)
    assert result.alert_type == expected


def test_inner_planet_has_no_rules() -> None:
    """Sun/Mercury/Venus/Moon are not transit sources in v1; lookup must return None."""
    for planet in ("Sun", "Moon", "Mercury", "Venus"):
        assert compute_vedic_aspect(
            transit_planet=planet,
            transit_sign=1, transit_lon=15.0,
            natal_planet="Saturn", natal_sign=1, natal_lon=15.0,
            orb_degrees=3.0,
        ) is None


def test_no_aspect_at_unmapped_house() -> None:
    """Saturn at Aries vs natal in Taurus (2nd house) is not in Saturn's drishti map."""
    result = compute_vedic_aspect(
        transit_planet="Saturn",
        transit_sign=1, transit_lon=15.0,
        natal_planet="Moon", natal_sign=2, natal_lon=45.0,
        orb_degrees=3.0,
    )
    assert result is None


# ---------- is_exact orb behavior ----------

def test_is_exact_only_for_conjunction() -> None:
    """Drishti aspects (3rd/10th/etc.) ignore degree distance; only conjunction is_exact-checked."""
    result = compute_vedic_aspect(
        transit_planet="Saturn",
        transit_sign=1, transit_lon=0.0,           # 0deg Aries
        natal_planet="Moon",
        natal_sign=10, natal_lon=270.0,            # 0deg Capricorn (Saturn's 10th)
        orb_degrees=1.0,
    )
    assert result is not None
    assert result.alert_type == "SATURN_10TH"
    assert result.is_exact is False


def test_is_exact_within_orb() -> None:
    result = compute_vedic_aspect(
        transit_planet="Saturn",
        transit_sign=1, transit_lon=10.0,
        natal_planet="Moon",
        natal_sign=1, natal_lon=12.0,
        orb_degrees=3.0,
    )
    assert result is not None
    assert result.alert_type == "CONJUNCTION"
    assert result.is_exact is True


def test_is_exact_outside_orb() -> None:
    result = compute_vedic_aspect(
        transit_planet="Saturn",
        transit_sign=1, transit_lon=10.0,
        natal_planet="Moon",
        natal_sign=1, natal_lon=20.0,
        orb_degrees=3.0,
    )
    assert result is not None
    assert result.alert_type == "CONJUNCTION"
    assert result.is_exact is False


def test_is_exact_at_orb_boundary_inclusive() -> None:
    """Orb test must be <=, not <, so the boundary is a hit."""
    result = compute_vedic_aspect(
        transit_planet="Saturn",
        transit_sign=1, transit_lon=10.0,
        natal_planet="Moon",
        natal_sign=1, natal_lon=13.0,
        orb_degrees=3.0,
    )
    assert result is not None
    assert result.is_exact is True


# ---------- Cusp boundary: constraint #1 (Pisces/Aries 359/2 deg case) ----------

def test_cusp_conjunction_is_exact_with_orb_3() -> None:
    """Transit at 359 deg Pisces, natal at 2 deg Aries: true distance is 3 deg.

    Naive abs() math returns 357 and would silently miss this exact conjunction.
    The circular_distance helper is the only thing standing between us and a
    silently-wrong production output.
    """
    # Same sign? No - 359 is in Pisces (sign 12), 2 is in Aries (sign 1).
    # So this is NOT a whole-sign conjunction. Use a cusp case where both are
    # in the same sign but near opposite ends.
    # For the *circular distance* part (which only governs is_exact), let's set
    # both to sign 1 and place the longitudes on the boundary.
    result = compute_vedic_aspect(
        transit_planet="Saturn",
        transit_sign=1, transit_lon=359.0,  # treated as 359deg in the boundary calc
        natal_planet="Moon",
        natal_sign=1, natal_lon=2.0,
        orb_degrees=3.0,
    )
    assert result is not None
    assert result.alert_type == "CONJUNCTION"
    assert result.is_exact is True


def test_cusp_conjunction_outside_tighter_orb() -> None:
    result = compute_vedic_aspect(
        transit_planet="Saturn",
        transit_sign=1, transit_lon=359.0,
        natal_planet="Moon",
        natal_sign=1, natal_lon=2.0,
        orb_degrees=2.5,
    )
    assert result is not None
    assert result.alert_type == "CONJUNCTION"
    assert result.is_exact is False


def test_zero_and_360_treated_identically() -> None:
    """0 deg and 360 deg are the same point on the ecliptic."""
    assert circular_distance(0.0, 360.0) == pytest.approx(0.0)
    assert circular_distance(360.0, 0.0) == pytest.approx(0.0)


def test_aspect_table_covers_all_transit_planets() -> None:
    """Every planet the daemon transits MUST have a rules entry, else the
    daemon's _detect_aspects loop would skip it silently."""
    from app.daemon.nadi_rules import TRANSIT_PLANETS
    for planet in TRANSIT_PLANETS:
        assert planet in VEDIC_ASPECTS, f"missing rules for transit planet {planet}"
