"""Divisional-chart (varga) sign computation — the 16 Shodashavarga, Parashara formulas.

Boundary values are deterministic from the rules. The full set: D1,D2,D3,D4,D7,D9,D10,D12,D16,
D20,D24,D27,D30,D40,D45,D60.
"""
from __future__ import annotations

from app.raman_saab.chart import varga


def test_supported_vargas_is_the_shodashavarga():
    assert varga.SUPPORTED_VARGAS == frozenset({1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60})


def test_unsupported_varga_raises():
    try:
        varga.varga_sign(0.0, 5)
    except ValueError as e:
        assert "unsupported varga D5" in str(e)
    else:
        raise AssertionError("expected ValueError for D5")


def test_zero_aries_per_varga():
    # 0deg Aries (odd, Fire, movable): most start from the sign -> Aries(1); D2 & D24 start from Leo(5).
    expect = {1: 1, 2: 5, 3: 1, 4: 1, 7: 1, 9: 1, 10: 1, 12: 1, 16: 1, 20: 1,
              24: 5, 27: 1, 30: 1, 40: 1, 45: 1, 60: 1}
    for n, sgn in expect.items():
        assert varga.varga_sign(0.0, n) == sgn, f"D{n}"


def test_drekkana_same_fifth_ninth():
    assert (varga.drekkana_sign(5.0), varga.drekkana_sign(15.0), varga.drekkana_sign(25.0)) == (1, 5, 9)


def test_saptamsa_even_sign_from_seventh():
    assert varga.saptamsa_sign(30.0) == 8          # Taurus -> 7th (Scorpio)
    assert varga.saptamsa_sign(29.9) == 7          # Aries last saptamsa -> Libra


def test_dasamsa_even_sign_from_ninth():
    assert varga.dasamsa_sign(30.0) == 10          # Taurus -> 9th (Capricorn)
    assert varga.dasamsa_sign(29.9) == 10          # Aries last dasamsa -> Capricorn


def test_hora_d2():
    assert varga.hora_sign(0.0) == 5               # Aries odd, first half -> Leo
    assert varga.hora_sign(16.0) == 4              # Aries odd, second half -> Cancer
    assert varga.hora_sign(30.0) == 4              # Taurus even, first half -> Cancer
    assert varga.hora_sign(46.0) == 5              # Taurus even, second half -> Leo


def test_chaturthamsa_d4_kendras():
    assert (varga.chaturthamsa_sign(0.0), varga.chaturthamsa_sign(10.0),
            varga.chaturthamsa_sign(20.0), varga.chaturthamsa_sign(28.0)) == (1, 4, 7, 10)


def test_siddhamsa_d24_start():
    assert varga.siddhamsa_sign(0.0) == 5          # Aries odd -> Leo
    assert varga.siddhamsa_sign(30.0) == 4         # Taurus even -> Cancer


def test_trimsamsa_d30_planet_signs():
    assert varga.trimsamsa_sign(3.0) == 1          # Aries odd, <5 -> Mars -> Aries
    assert varga.trimsamsa_sign(7.0) == 11         # Aries odd, 5-10 -> Saturn -> Aquarius
    assert varga.trimsamsa_sign(33.0) == 2         # Taurus even, <5 -> Venus -> Taurus


def test_shashtiamsa_d60():
    assert varga.shashtiamsa_sign(0.0) == 1
    assert varga.shashtiamsa_sign(0.5) == 2        # part 1 -> next sign


def test_navamsa_dispatch_matches_direct():
    for lon in (0.0, 12.3, 47.8, 199.99, 300.4, 359.9):
        assert varga.varga_sign(lon, 9) == varga.navamsa_sign(lon)
