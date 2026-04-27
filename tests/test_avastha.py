"""Tests for `app.core.avastha` -- Baladi + Jagradadi planetary states."""
from __future__ import annotations

import pytest

from app.core.avastha import (
    baladi_state,
    compute_avasthas,
    jagradadi_state,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALL_GRAHAS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
    "Saturn", "Rahu", "Ketu",
)


def _planet(sign: int, deg: float) -> dict:
    """Minimal D1-chart entry for a graha."""
    return {
        "sign": sign,
        "degree_in_sign": deg,
        "longitude": (sign - 1) * 30 + deg,
    }


def _empty_chart_with(planet_name: str, sign: int, deg: float) -> dict:
    """9-graha chart where only `planet_name` matters; the other 8 grahas
    are placed in houses where NO planet's drishti rule reaches `sign`.

    Drishti distances across ALL planets union = {3, 4, 5, 7, 8, 9, 10}
    (Mars 4/8, Jupiter 5/9, Saturn 3/10, Rahu/Ketu 5/9, all 7th).
    The safe complement of "incoming whole-sign distances to `sign`" is
    {1, 2, 6, 11, 12} -- distance 1 is conjunction (we exclude it from
    drishti), and 2/6/11/12 are not drishti targets for ANY planet.

    For the target `sign`, the corresponding "from_sign" values are:
      d=1   -> from = sign            (conjunction; safe-by-exclusion)
      d=2   -> from = sign - 1        (mod 12)
      d=6   -> from = sign - 5        (mod 12)
      d=11  -> from = sign - 10       (mod 12)
      d=12  -> from = sign - 11       (mod 12)
    """
    safe_distances = [2, 6, 11, 12]
    others = [g for g in ALL_GRAHAS if g != planet_name]
    chart: dict = {planet_name: _planet(sign, deg)}
    for i, g in enumerate(others):
        d = safe_distances[i % len(safe_distances)]
        # Solve ((sign - from) % 12) + 1 == d  ->  from = sign - (d - 1) (mod 12).
        # Working in 1..12 indexing:
        from_sign = ((sign - 1 - (d - 1)) % 12) + 1
        chart[g] = _planet(from_sign, 5.0)
    return chart


# ---------------------------------------------------------------------------
# Test 1 -- Baladi odd-sign boundaries (sign=1, Aries)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "deg,expected",
    [
        (0.0, "Bala"),
        (3.0, "Bala"),
        (6.0, "Kumara"),    # boundary -> upper
        (9.0, "Kumara"),
        (15.0, "Yuva"),
        (21.0, "Vriddha"),
        (27.0, "Mrita"),
    ],
)
def test_baladi_odd_sign_aries(deg: float, expected: str) -> None:
    assert baladi_state(1, deg) == expected


# ---------------------------------------------------------------------------
# Test 2 -- Baladi even-sign boundaries (sign=2, Taurus)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "deg,expected",
    [
        (0.0, "Mrita"),
        (3.0, "Mrita"),
        (6.0, "Vriddha"),   # boundary -> upper (in reversed table)
        (9.0, "Vriddha"),
        (15.0, "Yuva"),
        (21.0, "Kumara"),
        (27.0, "Bala"),
    ],
)
def test_baladi_even_sign_taurus(deg: float, expected: str) -> None:
    assert baladi_state(2, deg) == expected


# ---------------------------------------------------------------------------
# Test 3 -- Exact-cusp boundary tests
# ---------------------------------------------------------------------------

def test_baladi_exact_cusps_odd_sign() -> None:
    assert baladi_state(1, 6.0) == "Kumara"
    assert baladi_state(1, 12.0) == "Yuva"
    assert baladi_state(1, 18.0) == "Vriddha"
    assert baladi_state(1, 24.0) == "Mrita"
    # Just below each cusp -> previous bucket.
    assert baladi_state(1, 5.999) == "Bala"
    assert baladi_state(1, 11.999) == "Kumara"
    assert baladi_state(1, 23.999) == "Vriddha"


def test_baladi_exact_cusps_even_sign() -> None:
    assert baladi_state(2, 6.0) == "Vriddha"
    assert baladi_state(2, 12.0) == "Yuva"
    assert baladi_state(2, 18.0) == "Kumara"
    assert baladi_state(2, 24.0) == "Bala"
    assert baladi_state(2, 5.999) == "Mrita"
    assert baladi_state(2, 11.999) == "Vriddha"
    assert baladi_state(2, 23.999) == "Kumara"


# ---------------------------------------------------------------------------
# Test 4 -- Jagradadi Jagrad (no aspects)
# ---------------------------------------------------------------------------

def test_jagradadi_jagrad_no_aspects() -> None:
    chart = _empty_chart_with("Sun", 1, 10.0)
    state, b, m = jagradadi_state("Sun", 1, chart)
    assert state == "Jagrad"
    assert b == 0
    assert m == 0


# ---------------------------------------------------------------------------
# Test 5 -- Jagradadi Swapna (one benefic + one malefic aspect)
# ---------------------------------------------------------------------------

def test_jagradadi_swapna_jupiter_and_saturn() -> None:
    """Sun in Aries (sign=1). Jupiter in Libra (sign=7) gives 7th-aspect.
    Saturn in Cancer (sign=4) gives 10th-aspect onto Aries
    (whole_sign_house_distance(4, 1) = ((1 - 4) % 12) + 1 = 10).
    All other planets parked in safe houses.
    """
    chart = _empty_chart_with("Sun", 1, 10.0)
    chart["Jupiter"] = _planet(7, 5.0)   # 7th from Aries -> opposition
    chart["Saturn"] = _planet(4, 5.0)    # 10th-aspect onto Aries

    state, b, m = jagradadi_state("Sun", 1, chart)
    assert state == "Swapna"
    assert b == 1
    assert m == 1


# ---------------------------------------------------------------------------
# Test 6 -- Jagradadi Sushupti (Mars + Saturn aspect, no benefic)
# ---------------------------------------------------------------------------

def test_jagradadi_sushupti_mars_and_saturn() -> None:
    """Sun in Aries. Mars in Capricorn (sign=10) -> 4th-aspect onto Aries
    (whole_sign_house_distance(10, 1) = ((1 - 10) % 12) + 1 = 4).
    Saturn in Cancer (sign=4) -> 10th-aspect onto Aries.
    All 4 benefics parked in safe houses; nodes parked safely too.
    """
    chart = _empty_chart_with("Sun", 1, 10.0)
    chart["Mars"] = _planet(10, 5.0)
    chart["Saturn"] = _planet(4, 5.0)

    state, b, m = jagradadi_state("Sun", 1, chart)
    assert state == "Sushupti"
    assert b == 0
    assert m == 2


# ---------------------------------------------------------------------------
# Test 7 -- Pinned Bangalore Saturn Avastha (Mrita)
# ---------------------------------------------------------------------------

def test_pinned_bangalore_saturn_avastha_is_mrita() -> None:
    """Bangalore 1990-07-15 12:00 IST: Saturn ~Sagittarius (sign=9, odd) at
    ~28.25 deg -> 24-30 bucket -> Mrita (per int(28.25 // 6) == 4)."""
    assert baladi_state(9, 28.25) == "Mrita"
    # Boundary checks around 24.0.
    assert baladi_state(9, 24.0) == "Mrita"
    assert baladi_state(9, 23.999) == "Vriddha"


# ---------------------------------------------------------------------------
# Test 8 -- Shape invariant for compute_avasthas
# ---------------------------------------------------------------------------

def test_compute_avasthas_returns_all_9_grahas() -> None:
    chart = {
        "Sun":     _planet(1, 10.0),
        "Moon":    _planet(2, 20.0),
        "Mars":    _planet(3, 5.0),
        "Mercury": _planet(4, 15.0),
        "Jupiter": _planet(5, 25.0),
        "Venus":   _planet(6, 8.0),
        "Saturn":  _planet(9, 28.25),
        "Rahu":    _planet(11, 12.0),
        "Ketu":    _planet(5, 12.0),
    }
    out = compute_avasthas(chart)
    assert set(out.keys()) == set(ALL_GRAHAS)

    valid_baladi = {"Bala", "Kumara", "Yuva", "Vriddha", "Mrita"}
    valid_jagradadi = {"Jagrad", "Swapna", "Sushupti"}
    for graha, info in out.items():
        assert info["baladi"] in valid_baladi
        assert info["jagradadi"] in valid_jagradadi
        assert info["benefic_aspects"] >= 0
        assert info["malefic_aspects"] >= 0

    # Pinned: Saturn at (9, 28.25) -> Mrita.
    assert out["Saturn"]["baladi"] == "Mrita"


# ---------------------------------------------------------------------------
# Defensive bonus tests (validation behavior)
# ---------------------------------------------------------------------------

def test_baladi_state_rejects_sign_zero() -> None:
    with pytest.raises(ValueError):
        baladi_state(0, 5.0)


def test_baladi_state_rejects_sign_thirteen() -> None:
    with pytest.raises(ValueError):
        baladi_state(13, 5.0)


def test_baladi_state_rejects_negative_degree() -> None:
    with pytest.raises(ValueError):
        baladi_state(1, -0.001)


def test_baladi_state_rejects_degree_over_thirty() -> None:
    with pytest.raises(ValueError):
        baladi_state(1, 30.001)


def test_baladi_state_handles_exact_thirty_via_normalization() -> None:
    # 30.0 is normalized to 0.0 -> Bala for odd signs, Mrita for even.
    assert baladi_state(1, 30.0) == "Bala"
    assert baladi_state(2, 30.0) == "Mrita"


def test_compute_avasthas_raises_on_missing_grahas() -> None:
    with pytest.raises(ValueError) as exc_info:
        compute_avasthas({})
    msg = str(exc_info.value)
    for g in ALL_GRAHAS:
        assert g in msg


def test_jagradadi_self_aspect_is_skipped() -> None:
    """A planet doesn't aspect itself even if its drishti rule could match."""
    chart = _empty_chart_with("Jupiter", 1, 10.0)
    state, b, m = jagradadi_state("Jupiter", 1, chart)
    assert state == "Jagrad"
    assert b == 0
    assert m == 0


def test_avasthainfo_typed_dict_keys() -> None:
    """AvasthaInfo entries have exactly these 4 keys."""
    chart = {
        "Sun":     _planet(1, 10.0),
        "Moon":    _planet(2, 20.0),
        "Mars":    _planet(3, 5.0),
        "Mercury": _planet(4, 15.0),
        "Jupiter": _planet(5, 25.0),
        "Venus":   _planet(6, 8.0),
        "Saturn":  _planet(9, 28.25),
        "Rahu":    _planet(11, 12.0),
        "Ketu":    _planet(5, 12.0),
    }
    out = compute_avasthas(chart)
    expected_keys = {"baladi", "jagradadi", "benefic_aspects", "malefic_aspects"}
    for info in out.values():
        assert set(info.keys()) == expected_keys
