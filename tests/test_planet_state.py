"""Tests for `app.core.planet_state` — combustion, vargottama, retrograde.

References:
- Combustion orbs: BPHS 27 (Sphuta Bala Adhyaya) — orb depends on the planet.
- Vargottama: planet in the same rashi in D1 and D9 (Navamsa).
- Retrograde: ecliptic longitude speed < 0 (Lahiri sidereal, project convention).
"""
from __future__ import annotations

import pytest

from app.core.planet_state import (
    COMBUSTION_ORBS,
    angular_separation,
    combustion_orb,
    is_combust,
    is_retrograde,
    is_vargottama,
)


# --------------------------------------------------------------------------- #
# Combustion orbs                                                             #
# --------------------------------------------------------------------------- #

def test_combustion_orbs_canonical_bphs() -> None:
    """BPHS Adhyaya 27 combustion orbs (in degrees of ecliptic separation)."""
    assert COMBUSTION_ORBS["Moon"] == 12.0
    assert COMBUSTION_ORBS["Mars"] == 17.0
    assert COMBUSTION_ORBS["Mercury"] == 14.0
    assert COMBUSTION_ORBS["Jupiter"] == 11.0
    assert COMBUSTION_ORBS["Venus"] == 10.0
    assert COMBUSTION_ORBS["Saturn"] == 15.0


def test_combustion_orb_for_uncombustible_planets() -> None:
    """Sun, Rahu, Ketu are never combust."""
    assert combustion_orb("Sun") is None
    assert combustion_orb("Rahu") is None
    assert combustion_orb("Ketu") is None


def test_combustion_orb_unknown_planet_raises() -> None:
    with pytest.raises(ValueError):
        combustion_orb("Pluto")


# --------------------------------------------------------------------------- #
# Angular separation (circular distance)                                      #
# --------------------------------------------------------------------------- #

def test_angular_separation_zero() -> None:
    assert angular_separation(10.0, 10.0) == 0.0


def test_angular_separation_simple() -> None:
    assert angular_separation(10.0, 25.0) == 15.0
    assert angular_separation(25.0, 10.0) == 15.0


def test_angular_separation_wraps_at_360() -> None:
    """The shortest arc across the 0/360 cusp must be measured correctly."""
    assert angular_separation(355.0, 5.0) == 10.0
    assert angular_separation(5.0, 355.0) == 10.0


def test_angular_separation_max_is_180() -> None:
    """Maximum possible separation is 180° (antipodal)."""
    assert angular_separation(0.0, 180.0) == 180.0
    assert angular_separation(90.0, 270.0) == 180.0


def test_angular_separation_handles_values_outside_0_360() -> None:
    """Implementation should normalise inputs modulo 360."""
    assert angular_separation(370.0, 25.0) == 15.0
    assert angular_separation(-5.0, 5.0) == 10.0


# --------------------------------------------------------------------------- #
# Combustion detection                                                        #
# --------------------------------------------------------------------------- #

def test_is_combust_inside_orb() -> None:
    """Mercury 5° from Sun: well inside the 14° orb -> combust."""
    assert is_combust("Mercury", planet_lon=125.0, sun_lon=120.0) is True


def test_is_combust_at_orb_edge_is_combust() -> None:
    """At exactly the orb boundary, the planet is considered combust.
    (Inclusive — matches Jagannatha Hora and Parashara's Light convention.)"""
    assert is_combust("Jupiter", planet_lon=131.0, sun_lon=120.0) is True


def test_is_combust_outside_orb() -> None:
    """Saturn 20° from Sun: outside its 15° orb -> not combust."""
    assert is_combust("Saturn", planet_lon=140.0, sun_lon=120.0) is False


def test_is_combust_wraps_at_360() -> None:
    """Planet at 355°, Sun at 5° -> 10° separation -> Mercury is combust."""
    assert is_combust("Mercury", planet_lon=355.0, sun_lon=5.0) is True


def test_is_combust_for_sun_is_false() -> None:
    """The Sun cannot combust itself."""
    assert is_combust("Sun", planet_lon=120.0, sun_lon=120.0) is False


def test_is_combust_for_nodes_is_false() -> None:
    """Rahu/Ketu are shadow points — no combustion concept applies."""
    assert is_combust("Rahu", planet_lon=121.0, sun_lon=120.0) is False
    assert is_combust("Ketu", planet_lon=121.0, sun_lon=120.0) is False


def test_is_combust_unknown_planet_raises() -> None:
    with pytest.raises(ValueError):
        is_combust("Pluto", planet_lon=120.0, sun_lon=120.0)


# --------------------------------------------------------------------------- #
# Vargottama                                                                  #
# --------------------------------------------------------------------------- #

def test_is_vargottama_same_sign() -> None:
    """Same sign in D1 and D9 -> vargottama (strengthening factor)."""
    assert is_vargottama(d1_sign=5, d9_sign=5) is True


def test_is_vargottama_different_signs() -> None:
    assert is_vargottama(d1_sign=5, d9_sign=6) is False


@pytest.mark.parametrize("sign", list(range(1, 13)))
def test_is_vargottama_all_signs_self_match(sign: int) -> None:
    assert is_vargottama(d1_sign=sign, d9_sign=sign) is True


def test_is_vargottama_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        is_vargottama(d1_sign=0, d9_sign=1)
    with pytest.raises(ValueError):
        is_vargottama(d1_sign=1, d9_sign=13)


# --------------------------------------------------------------------------- #
# Retrograde passthrough                                                      #
# --------------------------------------------------------------------------- #

def test_is_retrograde_reads_flag() -> None:
    entry = {"sign": 5, "longitude": 130.0, "is_retrograde": True}
    assert is_retrograde(entry) is True


def test_is_retrograde_false_by_default() -> None:
    entry = {"sign": 5, "longitude": 130.0, "is_retrograde": False}
    assert is_retrograde(entry) is False


def test_is_retrograde_missing_flag_is_false() -> None:
    """A chart entry with no flag is treated as direct motion."""
    assert is_retrograde({"sign": 5, "longitude": 130.0}) is False


def test_is_retrograde_none_entry_is_false() -> None:
    """Defensive: a missing planet entry doesn't crash, returns False."""
    assert is_retrograde(None) is False
