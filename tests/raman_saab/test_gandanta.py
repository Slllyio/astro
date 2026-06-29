"""Gandanta — the water/fire sign-junction sandhi (within one pada of 120/240/360 deg)."""
from __future__ import annotations

from app.raman_saab.primitives import nakshatra as nk


def test_gandanta_zones_around_the_three_junctions():
    # last pada of Cancer (119 deg) and first pada of Leo (121 deg)
    assert nk.is_gandanta(119.0) and nk.is_gandanta(121.0)
    # Scorpio/Sagittarius junction
    assert nk.is_gandanta(239.0) and nk.is_gandanta(241.0)
    # Pisces/Aries junction (wraps 360/0)
    assert nk.is_gandanta(358.0) and nk.is_gandanta(2.0)


def test_non_gandanta_mid_sign():
    assert not nk.is_gandanta(15.0)         # mid-Aries
    assert not nk.is_gandanta(100.0)        # mid-Cancer, away from the cusp
    assert not nk.is_gandanta(200.0)


def test_exact_pada_boundary_is_gandanta():
    assert nk.is_gandanta(120.0 - 30.0 / 9.0 + 0.01)
    assert not nk.is_gandanta(120.0 - 30.0 / 9.0 - 1.0)
