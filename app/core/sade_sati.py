"""Sade Sati phase detection (whole-sign Vedic transit math).

Sade Sati is the ~7.5-year period when transit Saturn passes through the
12th, 1st, and 2nd signs from the natal Moon. It comprises three phases of
~2.5 years each:

  - **Rising / First Dhaiya**:  transit Saturn in the 12th sign from the
    natal Moon (the sign immediately preceding the natal Moon's sign).
  - **Peak / Second Dhaiya**:   transit Saturn in the 1st sign from the
    natal Moon (the same sign as the natal Moon).
  - **Setting / Third Dhaiya**: transit Saturn in the 2nd sign from the
    natal Moon (the sign immediately following the natal Moon's sign).

This is **whole-sign** math: the phase depends on the SIGN of transit
Saturn, not on the degree within the sign. So the computation reduces to a
binary check on the sign-distance between transit Saturn and the natal
Moon.

Convention (matches `app/core/ephemeris_engine.py` and the rest of the
project): signs are 1-indexed integers, 1=Aries .. 12=Pisces. House
distance is computed as ``((to_sign - from_sign) % 12) + 1``, yielding a
value in 1..12.

This module is a pure function — no IO, no database access. The transit
worker / orchestrator is responsible for fetching transit Saturn's sign
and the native's natal Moon sign and feeding them in.

TODO (out of scope for v1): Ardha Ashtama Shani / Kantaka Shani — Saturn
in 4th, 7th, 8th, or 10th from natal Moon ("small Sade Sati"). These
shorter Saturn-from-Moon transit phases should live in the same module
when implemented.
"""
from __future__ import annotations

from enum import Enum
from typing import TypedDict

# Inclusive range of valid 1-indexed zodiac signs.
_MIN_SIGN = 1
_MAX_SIGN = 12


class SadeSatiPhase(str, Enum):
    """The three phases of Sade Sati, named for Saturn's position relative
    to the natal Moon. String-valued so the enum serializes cleanly to
    JSON / database columns without an extra adapter.
    """

    RISING = "RISING"      # 12th house from natal Moon (first dhaiya)
    PEAK = "PEAK"          # 1st house — same sign as natal Moon (second dhaiya)
    SETTING = "SETTING"    # 2nd house from natal Moon (third dhaiya)


class SadeSatiInfo(TypedDict):
    """Result payload for a positive Sade Sati detection.

    Fields:
      - ``phase``: which of the three Sade Sati phases is active.
      - ``house_distance``: number of houses (1-indexed, whole-sign) from
        the natal Moon to transit Saturn. Always one of {12, 1, 2} when
        Sade Sati is active.
      - ``description``: human-readable, English-language description
        suitable for surfacing in API responses or notifications.
    """

    phase: SadeSatiPhase
    house_distance: int
    description: str


# Map of house-distance -> (phase, human-readable description fragment).
# Kept as a module-level constant so the lookup is O(1) and the strings
# don't get reconstructed on every call.
_PHASE_BY_HOUSE: dict[int, tuple[SadeSatiPhase, str]] = {
    12: (
        SadeSatiPhase.RISING,
        "Transit Saturn in 12th from natal Moon (Rising phase of Sade Sati)",
    ),
    1: (
        SadeSatiPhase.PEAK,
        "Transit Saturn in 1st from natal Moon (Peak phase of Sade Sati)",
    ),
    2: (
        SadeSatiPhase.SETTING,
        "Transit Saturn in 2nd from natal Moon (Setting phase of Sade Sati)",
    ),
}


def _validate_sign(value: int, label: str) -> None:
    """Raise ``ValueError`` if ``value`` is not a valid 1-indexed sign.

    Booleans are rejected explicitly because ``bool`` is a subclass of
    ``int`` in Python and ``True``/``False`` would otherwise sneak past
    the range check.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"{label} must be an int in [{_MIN_SIGN}, {_MAX_SIGN}], got "
            f"{value!r} of type {type(value).__name__}"
        )
    if not (_MIN_SIGN <= value <= _MAX_SIGN):
        raise ValueError(
            f"{label} must be in [{_MIN_SIGN}, {_MAX_SIGN}] (1-indexed, "
            f"1=Aries..12=Pisces), got {value}"
        )


def is_in_sade_sati(
    transit_saturn_sign: int,
    natal_moon_sign: int,
) -> SadeSatiInfo | None:
    """Detect whether the given transit Saturn position triggers a Sade
    Sati phase relative to the natal Moon sign.

    Whole-sign Vedic math: the phase depends only on the SIGN of transit
    Saturn, not on the degree within the sign. The house-distance from
    the natal Moon to transit Saturn is computed as
    ``((transit - natal) % 12) + 1`` (matching the project-wide
    convention used elsewhere in `app/core/`).

    Args:
        transit_saturn_sign: 1-indexed sign of transit Saturn (1=Aries,
            12=Pisces).
        natal_moon_sign: 1-indexed sign of the native's natal Moon.

    Returns:
        A :class:`SadeSatiInfo` dict if Saturn is in the 12th, 1st, or
        2nd house from the natal Moon. ``None`` otherwise (Saturn is in
        one of the other 9 signs and Sade Sati is not active).

    Raises:
        ValueError: if either sign is not an int in [1, 12].
    """
    _validate_sign(transit_saturn_sign, "transit_saturn_sign")
    _validate_sign(natal_moon_sign, "natal_moon_sign")

    # Whole-sign house distance, 1..12. Same convention used everywhere
    # else in the codebase (see ephemeris_engine.whole_sign_house).
    house_distance = ((transit_saturn_sign - natal_moon_sign) % 12) + 1

    match = _PHASE_BY_HOUSE.get(house_distance)
    if match is None:
        return None

    phase, description = match
    return SadeSatiInfo(
        phase=phase,
        house_distance=house_distance,
        description=description,
    )
