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


# ── sub-division CUSP coverage ────────────────────────────────────────────────
# Added 2026-08-19 after a real defect. The suite pinned 0deg Aries (where 15 of 16 divisions
# return 1 by construction) and no interior cusp at all, so a navamsa off-by-one at exactly
# 10d00' and 20d00' of every sign survived unnoticed. These tests walk EVERY sub-division
# boundary of EVERY division.

#: division -> (number of parts, sign-step between consecutive parts). Most divisions count
#: consecutively (+1); the drekkana walks the trines (+4 = 1st/5th/9th) and the chaturthamsa the
#: kendras (+3). D-30 is omitted: it is the one UNEQUAL division (5/5/8/7/5) with planet-owned
#: signs, covered by its own test above.
_DIV_PARTS = {2: (2, 0), 3: (3, 4), 4: (4, 3), 7: (7, 1), 9: (9, 1), 10: (10, 1),
              12: (12, 1), 16: (16, 1), 20: (20, 1), 24: (24, 1), 27: (27, 1),
              40: (40, 1), 45: (45, 1), 60: (60, 1)}


def test_every_subdivision_cusp_lands_in_the_part_it_opens():
    """A graha exactly on a sub-division cusp belongs to the part that STARTS there.

    Astronomical fact: the k-th part of an N-fold division opens at k*(30/N) degrees and is
    half-open [start, end). Float division by (30/N) rounds the divisor UP for N=9, so a
    floor-divide put 10d00' in the 3rd navamsa when the 4th begins exactly there.
    """
    from app.raman_saab.chart import varga as V
    checked = 0
    for n, (parts, step) in _DIV_PARTS.items():
        for sign_idx in range(12):
            base = sign_idx * 30.0
            seen = [V.varga_sign(base + k * 30.0 / parts, n) for k in range(parts)]
            if n == 2:                      # the hora alternates between two signs only
                assert len(set(seen)) == 2, f"D-{n} sign {sign_idx + 1}"
                continue
            for k in range(1, parts):
                off = k * 30.0 / parts
                # Only cusps that survive the float round-trip are assertable: the engine
                # recovers deg-in-sign as `lon % 30`, and for most k that lands a hair BELOW
                # the cusp, where the earlier part is the correct answer. Asserting there would
                # pin a false requirement. 10d and 20d — the ones a printed chart actually lands
                # on — are exactly representable and always survive.
                if (base + off) % 30.0 != off:
                    continue
                checked += 1
                expected = ((seen[0] - 1 + k * step) % 12) + 1
                assert seen[k] == expected, (
                    f"D-{n}, sign {sign_idx + 1}, cusp {k} at {off:.6f}deg: "
                    f"got {seen[k]}, expected {expected}")
    assert checked > 400, f"only {checked} exactly-representable cusps checked"


def test_navamsa_at_ten_and_twenty_degrees():
    """The exact defect, pinned per sign. 10d00' opens the 4th navamsa and 20d00' the 7th.

    These are also the drekkana cusps, and Raman prints positions to the degree — three of the
    thirty-five stated-position goldens carry a graha on one of them (NH.chart_17 carries three).
    """
    from app.raman_saab.chart.constants import NAVAMSA_START
    from app.raman_saab.chart.varga import navamsa_sign
    for sign_idx in range(12):
        start = NAVAMSA_START[sign_idx % 4]
        for deg, part in ((10.0, 3), (20.0, 6)):
            got = navamsa_sign(sign_idx * 30.0 + deg)
            assert got == ((start - 1 + part) % 12) + 1, (
                f"sign {sign_idx + 1} at {deg}deg: navamsa {got}")


def test_a_longitude_negative_by_less_than_one_ulp_stays_in_aries():
    """`(-1e-18) % 360.0` is exactly 360.0 — the true value is unrepresentable — which yielded
    sign 13 and a KeyError from SIGN_LORDS in the D-1 path. Reachable from any upstream
    ayanamsa subtraction that undershoots zero."""
    from app.raman_saab.chart.varga import _sign_deg, varga_sign
    for lon in (-1e-18, -1e-16, -0.0, 0.0, 360.0):
        sign, deg = _sign_deg(lon)
        assert 1 <= sign <= 12, f"{lon!r} -> sign {sign}"
        assert 0.0 <= deg < 30.0
    for n in (1, 2, 3, 9, 10, 30, 60):
        assert 1 <= varga_sign(-1e-18, n) <= 12
