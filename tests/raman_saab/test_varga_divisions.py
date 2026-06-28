"""Divisional-chart (varga) sign computation — Parashara formulas for D3/D7/D9/D10/D12.

Boundary values are deterministic from the rules: an odd-sign varga counts from the sign itself,
an even sign from a fixed offset (D7 -> 7th, D10 -> 9th); D3 maps the three drekkanas to the
same/5th/9th sign; D12 runs 12 parts from the sign.
"""
from __future__ import annotations

from app.raman_saab.chart import varga


def test_varga_sign_dispatch_and_support():
    assert varga.SUPPORTED_VARGAS == frozenset({1, 3, 7, 9, 10, 12})
    assert varga.varga_sign(0.0, 1) == 1            # 0deg Aries, rasi = Aries
    try:
        varga.varga_sign(0.0, 5)
    except ValueError as e:
        assert "unsupported varga D5" in str(e)
    else:
        raise AssertionError("expected ValueError for D5")


def test_zero_aries_maps_to_aries_in_every_varga():
    for n in (1, 3, 7, 9, 10, 12):
        assert varga.varga_sign(0.0, n) == 1


def test_drekkana_same_fifth_ninth():
    # Aries (0deg) drekkanas: 0-10 -> Aries(1), 10-20 -> Leo(5), 20-30 -> Sagittarius(9)
    assert varga.drekkana_sign(5.0) == 1
    assert varga.drekkana_sign(15.0) == 5
    assert varga.drekkana_sign(25.0) == 9


def test_saptamsa_even_sign_starts_from_seventh():
    # Taurus (lon 30) is even -> D7 counts from the 7th sign (Scorpio = 8)
    assert varga.saptamsa_sign(30.0) == 8
    # Aries (odd) first saptamsa -> Aries
    assert varga.saptamsa_sign(0.0) == 1
    # Aries last saptamsa (part 6) -> Aries+6 = Libra(7)
    assert varga.saptamsa_sign(29.9) == 7


def test_dasamsa_even_sign_starts_from_ninth():
    # Taurus (even) first dasamsa -> 9th from Taurus = Capricorn(10)
    assert varga.dasamsa_sign(30.0) == 10
    # Aries (odd) last dasamsa (part 9) -> Aries+9 = Capricorn(10)
    assert varga.dasamsa_sign(29.9) == 10


def test_dwadasamsa_runs_from_the_sign():
    # Aries: part 0 -> Aries, last part (11) -> Aries+11 = Pisces(12)
    assert varga.dwadasamsa_sign(0.0) == 1
    assert varga.dwadasamsa_sign(29.9) == 12


def test_navamsa_dispatch_matches_direct():
    for lon in (0.0, 12.3, 47.8, 199.99, 300.4, 359.9):
        assert varga.varga_sign(lon, 9) == varga.navamsa_sign(lon)
