"""Jaimini Chara Dasha — Phase 5 of the astrologer's-lens framework.

Provides the *parallel confirmation track* that Phase 6's three-pillar
Bhava Judge reads alongside Vimshottari. Where Vimshottari is nakshatra-
based (Moon-anchored), Chara is sign-based (Lagna-anchored) — two
independent doctrinal timekeepers.

## Algorithm (per Iyer / K.N. Rao / Narasimha Rao formulation)

1. **Start sign**: the Lagna sign itself.
2. **Direction**: forward for movable (1/4/7/10) and dual (3/6/9/12),
   backward for fixed (2/5/8/11).
3. **Period for each sign**: distance from sign to its lord, counted
   inclusively in the dasha direction.
   * If the lord is *in* the sign itself, period = 12 years.
   * Otherwise period = inclusive-distance − 1 years.
4. **Dual rulers** (Mars: Aries/Scorpio; Mercury: Gemini/Virgo;
   Jupiter: Sagittarius/Pisces; Venus: Taurus/Libra;
   Saturn: Capricorn/Aquarius): pick the lord-sign **closer in the
   dasha direction**.
5. **Sequence**: 12 signs, starting from Lagna, stepping forward or
   backward per direction.

## Output contract

* ``chara_sequence(asc_sign)`` → list of ``(sign, years)``.
* ``chara_active_at(asc_sign, birth_jd, target_jd)`` → the active
  Chara MD sign at the target Julian Day, or ``None`` if the target
  is before birth or past the natal cycle's end.

The dasha years are in **mean Gregorian years** per the project lock:
``DAYS_PER_VEDIC_YEAR = 365.2425``. Phase 7's gochara engine and
Phase 6's bhava judge both call ``chara_active_at`` directly.
"""
from __future__ import annotations

from typing import Final

# Locked: see CLAUDE.md / ephemeris_engine for the year-length decision.
DAYS_PER_VEDIC_YEAR: Final[float] = 365.2425

# Sign rulership (single sign per planet for luminaries, dual for others).
_SIGN_LORDS: Final[dict[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun",
    6: "Mercury", 7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn",
    11: "Saturn", 12: "Jupiter",
}

# Inverse mapping — planet → its owned signs (tuple of 1-2).
_PLANET_OWNS: Final[dict[str, tuple[int, ...]]] = {
    "Sun":     (5,),
    "Moon":    (4,),
    "Mars":    (1, 8),
    "Mercury": (3, 6),
    "Jupiter": (9, 12),
    "Venus":   (2, 7),
    "Saturn":  (10, 11),
}

_MOVABLE: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_FIXED:   Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_DUAL:    Final[frozenset[int]] = frozenset({3, 6, 9, 12})


def direction_for(lagna_sign: int) -> int:
    """+1 (forward) for movable + dual, −1 (backward) for fixed."""
    if lagna_sign in _MOVABLE or lagna_sign in _DUAL:
        return 1
    if lagna_sign in _FIXED:
        return -1
    raise ValueError(f"lagna_sign must be 1..12, got {lagna_sign}")


def _step_sign(sign: int, direction: int) -> int:
    """Next sign in the dasha direction (1-indexed, wraps)."""
    return ((sign - 1 + direction) % 12) + 1


def _inclusive_distance(a: int, b: int, direction: int) -> int:
    """Inclusive sign-count from a to b, in the given direction.

    Going forward from sign 1 to sign 4: count 1,2,3,4 = 4 inclusive.
    Going backward from sign 4 to sign 1: count 4,3,2,1 = 4 inclusive.
    """
    if direction == 1:
        return ((b - a) % 12) + 1
    return ((a - b) % 12) + 1


def _pick_lord_sign(sign: int, direction: int) -> int:
    """Resolve the relevant lord-sign for one dasha sign.

    For dual-ruler planets, return whichever owned sign is *closer*
    to the dasha sign in the chosen direction (Narasimha Rao rule).
    For single-sign owners (Sun, Moon), the unique owned sign is
    returned directly.
    """
    lord = _SIGN_LORDS[sign]
    owned = _PLANET_OWNS[lord]
    if len(owned) == 1:
        return owned[0]
    # Pick the closer of the two in the dasha direction.
    a, b = owned
    da = _inclusive_distance(sign, a, direction)
    db = _inclusive_distance(sign, b, direction)
    return a if da <= db else b


def period_for(sign: int, direction: int) -> int:
    """Chara MD period (years) for one sign.

    If the lord-sign equals the sign itself (distance 1, lord IS the
    sign), classical rule returns 12; otherwise (distance − 1).
    """
    lord_sign = _pick_lord_sign(sign, direction)
    d = _inclusive_distance(sign, lord_sign, direction)
    return 12 if d == 1 else d - 1


def chara_sequence(lagna_sign: int) -> tuple[tuple[int, int], ...]:
    """The 12-sign Chara MD cycle starting from Lagna.

    Returns:
        Tuple of (sign, years) pairs in dasha order.
    """
    direction = direction_for(lagna_sign)
    result: list[tuple[int, int]] = []
    current = lagna_sign
    for _ in range(12):
        years = period_for(current, direction)
        result.append((current, years))
        current = _step_sign(current, direction)
    return tuple(result)


def chara_windows_jd(
    lagna_sign: int, birth_jd: float,
) -> tuple[tuple[int, float, float], ...]:
    """The Chara MD calendar as ``(sign, start_jd, end_jd)`` triples.

    Cumulative-year offsets converted via ``DAYS_PER_VEDIC_YEAR``.
    """
    out: list[tuple[int, float, float]] = []
    cursor = birth_jd
    for sign, years in chara_sequence(lagna_sign):
        end = cursor + years * DAYS_PER_VEDIC_YEAR
        out.append((sign, cursor, end))
        cursor = end
    return tuple(out)


def chara_active_at(
    lagna_sign: int, birth_jd: float, target_jd: float,
) -> int | None:
    """Active Chara MD sign at ``target_jd`` — None if outside the cycle.

    Returns:
        The sign number (1..12) whose MD window covers target_jd, or
        None if target_jd is before birth_jd or past the end of the
        natal Chara cycle.
    """
    if target_jd < birth_jd:
        return None
    for sign, start, end in chara_windows_jd(lagna_sign, birth_jd):
        if start <= target_jd < end:
            return sign
    return None
