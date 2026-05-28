"""Shodashavarga divisional charts (D2..D60) per Parashari tradition.

Implements the 16-fold divisional scheme (Shodashavarga) as defined in
Brihat Parashara Hora Shastra. D9 (Navamsa) and D10 (Dasamsa) defer to the
existing implementation in app.core.ephemeris_engine; all other vargas are
implemented here.

Conventions:
  - Sign indices internally are 0-based (Aries=0, ..., Pisces=11), matching
    ZODIAC_SIGNS. The output dict's "sign" field is 1-based.
  - "Odd sign" (Vedic): zero-based even index (Aries=0 is odd, Taurus=1 is even).
  - Sign types:
      Movable (chara):   Aries(0), Cancer(3), Libra(6), Capricorn(9)
      Fixed (sthira):    Taurus(1), Leo(4), Scorpio(7), Aquarius(10)
      Dual (dwiswabhava):Gemini(2), Virgo(5), Sagittarius(8), Pisces(11)
"""
from __future__ import annotations

from typing import Any

from app.core.ephemeris_engine import (
    ZODIAC_SIGNS,
    calculate_divisional_longitude,
    position_from_longitude,
)

SHODASHAVARGA_DIVISORS: tuple[int, ...] = (
    2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60,
)

SHODASHAVARGA_NAMES: dict[int, str] = {
    1: "D1_Rashi",
    2: "D2_Hora",
    3: "D3_Drekkana",
    4: "D4_Chaturthamsa",
    7: "D7_Saptamsa",
    9: "D9_Navamsa",
    10: "D10_Dasamsa",
    12: "D12_Dwadasamsa",
    16: "D16_Shodasamsa",
    20: "D20_Vimsamsa",
    24: "D24_Chaturvimsamsa",
    27: "D27_Bhamsa",
    30: "D30_Trimsamsa",
    40: "D40_Khavedamsa",
    45: "D45_Akshavedamsa",
    60: "D60_Shastiamsa",
}

# Sign-type sets (0-based).
_MOVABLE = frozenset({0, 3, 6, 9})
_FIXED = frozenset({1, 4, 7, 10})
_DUAL = frozenset({2, 5, 8, 11})


def _sign_type_start(sign_index: int, movable: int, fixed: int, dual: int) -> int:
    """Return the starting sign index based on sign type (movable/fixed/dual)."""
    if sign_index in _MOVABLE:
        return movable
    if sign_index in _FIXED:
        return fixed
    return dual


def _is_odd_sign(sign_index: int) -> bool:
    """Vedic 'odd' signs have zero-based even index (Aries=0 is odd)."""
    return (sign_index % 2) == 0


def _pack(sign_index: int, fractional_degree: float) -> float:
    """Combine a 0-based sign index and intra-sign degree into a 0..360 longitude."""
    return ((sign_index % 12) * 30.0) + fractional_degree


def _hora_d2(sign_index: int, degree_in_sign: float) -> float:
    """D2 Hora: odd signs first 15° -> Leo (Sun), second 15° -> Cancer (Moon).
    Even signs reverse: first 15° -> Cancer, second 15° -> Leo.

    Output convention: place the divisional sign at 0° (degree-within-sign is
    not astrologically meaningful in D2 since each sign maps a full 15° range
    to a single varga sign). We preserve the *relative* position within the
    half by scaling the degree by 2 so consumers can still distinguish points
    inside a Hora.
    """
    in_first_half = degree_in_sign < 15.0
    if _is_odd_sign(sign_index):
        # Odd: first half -> Leo (4), second half -> Cancer (3).
        target = 4 if in_first_half else 3
    else:
        # Even: first half -> Cancer (3), second half -> Leo (4).
        target = 3 if in_first_half else 4
    # Scale 0..15 -> 0..30 so the Hora "degree" varies smoothly.
    intra = (degree_in_sign % 15.0) * 2.0
    return _pack(target, intra)


def _chaturthamsa_d4(sign_index: int, degree_in_sign: float) -> float:
    """D4 Chaturthamsa: 4 parts of 7.5 degrees each, mapping to the four
    kendras (1st, 4th, 7th, 10th) from the natal D1 sign.

    1st part (0-7.5):     same sign (offset +0).
    2nd part (7.5-15):    4th sign from D1 (offset +3).
    3rd part (15-22.5):   7th sign from D1 (offset +6).
    4th part (22.5-30):  10th sign from D1 (offset +9).

    This pattern is identical for all 12 D1 signs (no parity / sign-type
    branching, distinct from D7/D9 etc.). Per BPHS Vol.I Ch.6 — D4 governs
    fixed assets / property / domestic stability.
    """
    span = 7.5
    part = int(degree_in_sign // span)
    if part > 3:
        part = 3  # clamp for fp boundary at exactly 30deg
    offset = part * 3  # part 0->0, 1->3, 2->6, 3->9 (the four kendras)
    target = (sign_index + offset) % 12
    intra = (degree_in_sign - part * span) * 4.0  # scale 0..7.5 -> 0..30
    return _pack(target, intra)


def _drekkana_d3(sign_index: int, degree_in_sign: float) -> float:
    """D3 Drekkana: 3 parts of 10° each.
    1st part (0-10°)  -> same sign.
    2nd part (10-20°) -> 5th sign from itself (offset +4).
    3rd part (20-30°) -> 9th sign from itself (offset +8).
    """
    part = int(degree_in_sign // 10.0)
    if part == 0:
        offset = 0
    elif part == 1:
        offset = 4
    else:  # part == 2
        offset = 8
    target = (sign_index + offset) % 12
    intra = (degree_in_sign - part * 10.0) * 3.0  # scale 0..10 -> 0..30
    return _pack(target, intra)


def _saptamsa_d7(sign_index: int, degree_in_sign: float) -> float:
    """D7 Saptamsa: 7 parts of 30/7 degrees each.
    Odd signs: parts start from the same sign and proceed forward.
    Even signs: parts start from the 7th sign (offset +6) and proceed forward.
    """
    span = 30.0 / 7.0
    part = int(degree_in_sign // span)
    if part > 6:
        part = 6  # clamp for fp boundary at exactly 30°
    start = sign_index if _is_odd_sign(sign_index) else (sign_index + 6) % 12
    target = (start + part) % 12
    intra = (degree_in_sign - part * span) * 7.0  # scale to 0..30
    return _pack(target, intra)


def _dwadasamsa_d12(sign_index: int, degree_in_sign: float) -> float:
    """D12 Dwadasamsa: 12 parts of 2.5° each. Starts from same sign,
    cycling through the zodiac in order."""
    part = int(degree_in_sign // 2.5)
    if part > 11:
        part = 11
    target = (sign_index + part) % 12
    intra = (degree_in_sign - part * 2.5) * 12.0
    return _pack(target, intra)


def _shodasamsa_d16(sign_index: int, degree_in_sign: float) -> float:
    """D16 Shodasamsa: 16 parts of 1.875° each.
    Movable signs start from Aries (0), fixed from Leo (4), dual from Sagittarius (8)."""
    span = 30.0 / 16.0
    part = int(degree_in_sign // span)
    if part > 15:
        part = 15
    start = _sign_type_start(sign_index, movable=0, fixed=4, dual=8)
    target = (start + part) % 12
    intra = (degree_in_sign - part * span) * 16.0
    return _pack(target, intra)


def _vimsamsa_d20(sign_index: int, degree_in_sign: float) -> float:
    """D20 Vimsamsa: 20 parts of 1.5° each.
    Movable from Aries (0), fixed from Sagittarius (8), dual from Leo (4)."""
    span = 1.5
    part = int(degree_in_sign // span)
    if part > 19:
        part = 19
    start = _sign_type_start(sign_index, movable=0, fixed=8, dual=4)
    target = (start + part) % 12
    intra = (degree_in_sign - part * span) * 20.0
    return _pack(target, intra)


def _chaturvimsamsa_d24(sign_index: int, degree_in_sign: float) -> float:
    """D24 Chaturvimsamsa: 24 parts of 1.25° each.
    Odd signs start from Leo (4); even signs start from Cancer (3)."""
    span = 1.25
    part = int(degree_in_sign // span)
    if part > 23:
        part = 23
    start = 4 if _is_odd_sign(sign_index) else 3
    target = (start + part) % 12
    intra = (degree_in_sign - part * span) * 24.0
    return _pack(target, intra)


def _bhamsa_d27(sign_index: int, degree_in_sign: float) -> float:
    """D27 Bhamsa / Saptavimsamsa: 27 parts of 30/27 degrees each.
    Movable from Aries (0), fixed from Cancer (3), dual from Libra (6).
    Each sign has 27 parts cycling through zodiac signs (mod 12)."""
    span = 30.0 / 27.0
    part = int(degree_in_sign // span)
    if part > 26:
        part = 26
    start = _sign_type_start(sign_index, movable=0, fixed=3, dual=6)
    target = (start + part) % 12
    intra = (degree_in_sign - part * span) * 27.0
    return _pack(target, intra)


# D30 Trimsamsa: unequal divisions per sign.
# Odd signs: Mars 0-5 (Aries), Saturn 5-10 (Aquarius), Jupiter 10-18 (Sagittarius),
#            Mercury 18-25 (Gemini), Venus 25-30 (Libra).
# Even signs: Venus 0-5 (Taurus), Mercury 5-12 (Virgo), Jupiter 12-20 (Pisces),
#             Saturn 20-25 (Capricorn), Mars 25-30 (Scorpio).
# The lord's "own sign" used here is the lord's mooltrikona/own sign for the
# given parity (Mars=Aries for odd, Mars=Scorpio for even, etc.) per BPHS.
_TRIMSAMSA_ODD = (
    (5.0, 0),    # Mars -> Aries
    (10.0, 10),  # Saturn -> Aquarius
    (18.0, 8),   # Jupiter -> Sagittarius
    (25.0, 2),   # Mercury -> Gemini
    (30.0, 6),   # Venus -> Libra
)
_TRIMSAMSA_EVEN = (
    (5.0, 1),    # Venus -> Taurus
    (12.0, 5),   # Mercury -> Virgo
    (20.0, 11),  # Jupiter -> Pisces
    (25.0, 9),   # Saturn -> Capricorn
    (30.0, 7),   # Mars -> Scorpio
)


def _trimsamsa_d30(sign_index: int, degree_in_sign: float) -> float:
    """D30 Trimsamsa: unequal divisions, lord's own sign is the divisional sign."""
    table = _TRIMSAMSA_ODD if _is_odd_sign(sign_index) else _TRIMSAMSA_EVEN
    prev_upper = 0.0
    for upper, target in table:
        if degree_in_sign < upper:
            span = upper - prev_upper
            intra = ((degree_in_sign - prev_upper) / span) * 30.0 if span > 0 else 0.0
            return _pack(target, intra)
        prev_upper = upper
    # Boundary at exactly 30° -> last bucket.
    upper, target = table[-1]
    span = upper - (table[-2][0] if len(table) > 1 else 0.0)
    return _pack(target, 30.0 - 1e-9 if span > 0 else 0.0)


def _khavedamsa_d40(sign_index: int, degree_in_sign: float) -> float:
    """D40 Khavedamsa: 40 parts of 0.75° each.
    Odd signs start from Aries (0), even signs start from Libra (6)."""
    span = 0.75
    part = int(degree_in_sign // span)
    if part > 39:
        part = 39
    start = 0 if _is_odd_sign(sign_index) else 6
    target = (start + part) % 12
    intra = (degree_in_sign - part * span) * 40.0
    return _pack(target, intra)


def _akshavedamsa_d45(sign_index: int, degree_in_sign: float) -> float:
    """D45 Akshavedamsa: 45 parts of 30/45 = 2/3 degrees each.
    Movable from Aries (0), fixed from Leo (4), dual from Sagittarius (8)."""
    span = 30.0 / 45.0
    part = int(degree_in_sign // span)
    if part > 44:
        part = 44
    start = _sign_type_start(sign_index, movable=0, fixed=4, dual=8)
    target = (start + part) % 12
    intra = (degree_in_sign - part * span) * 45.0
    return _pack(target, intra)


def _shastiamsa_d60(sign_index: int, degree_in_sign: float) -> float:
    """D60 Shastiamsa: 60 parts of 0.5° each.
    Each sign cycles through the zodiac starting from itself (mod 12)."""
    span = 0.5
    part = int(degree_in_sign // span)
    if part > 59:
        part = 59
    target = (sign_index + part) % 12
    intra = (degree_in_sign - part * span) * 60.0
    return _pack(target, intra)


# Dispatch table for vargas implemented in this module.
_DISPATCH = {
    2: _hora_d2,
    3: _drekkana_d3,
    4: _chaturthamsa_d4,
    7: _saptamsa_d7,
    12: _dwadasamsa_d12,
    16: _shodasamsa_d16,
    20: _vimsamsa_d20,
    24: _chaturvimsamsa_d24,
    27: _bhamsa_d27,
    30: _trimsamsa_d30,
    40: _khavedamsa_d40,
    45: _akshavedamsa_d45,
    60: _shastiamsa_d60,
}


def compute_divisional_longitude(d1_longitude: float, divisor: int) -> float:
    """Return the divisional sign + degree as a 0..360 longitude.

    For D9 and D10, defers to the existing engine implementation in
    app.core.ephemeris_engine.calculate_divisional_longitude(lon, divisor).
    For D2, D3, D7, D12, D16, D20, D24, D27, D30, D40, D45, D60, implements
    per the Parashari formulas documented in the function-level comments.
    """
    if not isinstance(divisor, int) or divisor < 1:
        raise ValueError(f"divisor must be a positive int, got {divisor!r}")
    if divisor == 1:
        return d1_longitude % 360.0
    if divisor in (9, 10):
        return calculate_divisional_longitude(d1_longitude, divisor)

    handler = _DISPATCH.get(divisor)
    if handler is None:
        raise ValueError(f"divisor {divisor} not supported in shodashavarga")

    lon = d1_longitude % 360.0
    sign_index = int(lon // 30)
    # Clamp pathological floats at the 360° wrap.
    if sign_index >= 12:
        sign_index = 11
    degree_in_sign = lon - sign_index * 30.0
    if degree_in_sign < 0:
        degree_in_sign = 0.0
    if degree_in_sign >= 30.0:
        degree_in_sign = 30.0 - 1e-12
    return handler(sign_index, degree_in_sign)


def compute_divisional_charts(d1_chart: dict[str, dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """For an input D1 chart, compute all 14 vargas (D2..D60).

    Returns a dict keyed by SHODASHAVARGA_NAMES[divisor] containing
    {planet_name: position_dict} per planet. Uses position_from_longitude
    for consistent output shape.
    """
    if not isinstance(d1_chart, dict):
        raise TypeError("d1_chart must be a dict mapping planet name -> position")

    result: dict[str, dict[str, dict[str, Any]]] = {}
    for divisor in SHODASHAVARGA_DIVISORS:
        chart_name = SHODASHAVARGA_NAMES[divisor]
        chart: dict[str, dict[str, Any]] = {}
        for planet_name, d1_pos in d1_chart.items():
            if not isinstance(d1_pos, dict):
                raise TypeError(
                    f"planet {planet_name!r} d1 position must be a dict, got {type(d1_pos).__name__}"
                )
            if "longitude" not in d1_pos:
                raise ValueError(f"planet {planet_name!r} missing 'longitude'")
            d1_lon = float(d1_pos["longitude"])
            is_retro = bool(d1_pos.get("is_retrograde", False))
            div_lon = compute_divisional_longitude(d1_lon, divisor)
            # Defensive normalization: the legacy D9/D10 helper can return
            # exactly 360.0 at sign-boundary inputs, which would crash
            # position_from_longitude (sign_index=12). Wrap to [0, 360).
            div_lon = div_lon % 360.0
            pos = position_from_longitude(div_lon, is_retro)
            pos["name"] = planet_name
            chart[planet_name] = pos
        result[chart_name] = chart
    return result
