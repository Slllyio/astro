"""Tests for `app.core.sade_sati`.

These tests pin Sade Sati phase detection to whole-sign Vedic math:
phase depends only on the sign of transit Saturn relative to the natal
Moon sign, never on the degree within the sign.

Pinned baselines (do NOT regenerate from function output):

  - Sign indexing: 1-indexed, 1=Aries..12=Pisces (matches
    ``app/core/ephemeris_engine.py``).
  - House distance formula: ``((transit - natal) % 12) + 1``, yielding
    a value in 1..12 (also matches the project's whole-sign house math
    in ``ephemeris_engine.whole_sign_house``).
  - Phase mapping: house 12 -> RISING, house 1 -> PEAK, house 2 -> SETTING.
    Any other house -> not in Sade Sati (returns ``None``).
  - Real-world reference (test 7): Saturn entered Sagittarius (sign=9)
    on approximately 2017-01-26 and stayed until 2020-01-23, so a native
    with natal Moon in Sagittarius experienced PEAK phase during that
    window.
"""
from __future__ import annotations

import pytest

from app.core.sade_sati import (
    SadeSatiInfo,
    SadeSatiPhase,
    is_in_sade_sati,
)

# Convenience aliases so the test data reads like Vedic prose rather than
# magic numbers. 1-indexed throughout.
ARIES, TAURUS, GEMINI, CANCER = 1, 2, 3, 4
LEO, VIRGO, LIBRA, SCORPIO = 5, 6, 7, 8
SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES = 9, 10, 11, 12


# ============================================================================
# Test 1: Peak (1st house) — natal Moon Sagittarius, transit Saturn Sagittarius
# ============================================================================
def test_peak_phase_same_sign_as_moon() -> None:
    """Transit Saturn in the same sign as the natal Moon -> PEAK phase
    (1st house from Moon)."""
    result = is_in_sade_sati(
        transit_saturn_sign=SAGITTARIUS,
        natal_moon_sign=SAGITTARIUS,
    )

    assert result is not None
    assert result["phase"] is SadeSatiPhase.PEAK
    assert result["house_distance"] == 1
    assert "Peak" in result["description"]


# ============================================================================
# Test 2: Rising (12th house) — natal Moon Sagittarius, Saturn in Scorpio
# ============================================================================
def test_rising_phase_twelfth_from_moon() -> None:
    """From Sagittarius, the 12th house is Scorpio. Transit Saturn there
    triggers the RISING phase."""
    result = is_in_sade_sati(
        transit_saturn_sign=SCORPIO,
        natal_moon_sign=SAGITTARIUS,
    )

    assert result is not None
    assert result["phase"] is SadeSatiPhase.RISING
    assert result["house_distance"] == 12
    assert "Rising" in result["description"]


# ============================================================================
# Test 3: Setting (2nd house) — natal Moon Sagittarius, Saturn in Capricorn
# ============================================================================
def test_setting_phase_second_from_moon() -> None:
    """From Sagittarius, the 2nd house is Capricorn. Transit Saturn there
    triggers the SETTING phase."""
    result = is_in_sade_sati(
        transit_saturn_sign=CAPRICORN,
        natal_moon_sign=SAGITTARIUS,
    )

    assert result is not None
    assert result["phase"] is SadeSatiPhase.SETTING
    assert result["house_distance"] == 2
    assert "Setting" in result["description"]


# ============================================================================
# Test 4: Out of phase — natal Moon Sagittarius, Saturn in Cancer (8th)
# ============================================================================
def test_out_of_phase_returns_none() -> None:
    """From Sagittarius, Cancer is the 8th house — that's Ashtama Shani,
    not Sade Sati. v1 returns None for any house outside {12, 1, 2}."""
    result = is_in_sade_sati(
        transit_saturn_sign=CANCER,
        natal_moon_sign=SAGITTARIUS,
    )
    assert result is None


# ============================================================================
# Test 5: Wrap boundary 1 — natal Moon Aries, Saturn Pisces -> RISING
# ============================================================================
def test_wrap_boundary_aries_moon_pisces_saturn_is_rising() -> None:
    """The 12th from Aries wraps backwards through the zodiac to Pisces.
    Verifies the modulo math handles the zodiac wrap-around correctly."""
    result = is_in_sade_sati(
        transit_saturn_sign=PISCES,
        natal_moon_sign=ARIES,
    )

    assert result is not None
    assert result["phase"] is SadeSatiPhase.RISING
    assert result["house_distance"] == 12


# ============================================================================
# Test 6: Wrap boundary 2 — natal Moon Pisces, Saturn Aries -> SETTING
# ============================================================================
def test_wrap_boundary_pisces_moon_aries_saturn_is_setting() -> None:
    """The 2nd from Pisces wraps forwards through the zodiac to Aries.
    Mirror of test 5 — verifies the wrap goes both directions."""
    result = is_in_sade_sati(
        transit_saturn_sign=ARIES,
        natal_moon_sign=PISCES,
    )

    assert result is not None
    assert result["phase"] is SadeSatiPhase.SETTING
    assert result["house_distance"] == 2


# ============================================================================
# Test 7: Pinned real-world reference
# ============================================================================
def test_real_world_2017_2020_saturn_in_sagittarius() -> None:
    """Real-world reference: Saturn entered Sagittarius (sign=9) on
    approximately 2017-01-26 and stayed there until 2020-01-23. A native
    with natal Moon in Sagittarius experienced the PEAK phase of Sade
    Sati during that ~3-year window.

    This is functionally the same assertion as test 1, pinned here with
    a docstring referencing the externally-verifiable transit dates so
    the test continues to encode "this real-world scenario must always
    detect as PEAK" even if test 1 is later refactored.
    """
    # Pick any moment during the 2017-01-26 .. 2020-01-23 window: Saturn
    # was in Sagittarius (sign=9). Sign-only math, so the exact moment
    # is irrelevant — only the sign matters.
    result = is_in_sade_sati(
        transit_saturn_sign=SAGITTARIUS,
        natal_moon_sign=SAGITTARIUS,
    )

    assert result is not None
    assert result["phase"] is SadeSatiPhase.PEAK
    assert result["house_distance"] == 1


# ============================================================================
# Test 8: All 144 (transit_saturn_sign, natal_moon_sign) combinations
# ============================================================================
# Comprehensive correctness sweep. For each pair we recompute the expected
# phase from first principles (the formula in the module docstring) and
# assert the function returns the matching SadeSatiInfo or None.

def _expected_phase(saturn: int, moon: int) -> SadeSatiPhase | None:
    """Reference implementation for the parametrized sweep.

    Deliberately re-derives the phase from the formula rather than
    importing helpers from the module under test, so a regression in
    the module would not also corrupt the expected value."""
    house = ((saturn - moon) % 12) + 1
    if house == 12:
        return SadeSatiPhase.RISING
    if house == 1:
        return SadeSatiPhase.PEAK
    if house == 2:
        return SadeSatiPhase.SETTING
    return None


@pytest.mark.parametrize("saturn", range(1, 13))
@pytest.mark.parametrize("moon", range(1, 13))
def test_all_sign_combinations(saturn: int, moon: int) -> None:
    """Sweep all 12 x 12 = 144 (transit Saturn, natal Moon) sign pairs."""
    expected_phase = _expected_phase(saturn, moon)
    expected_house = ((saturn - moon) % 12) + 1

    result = is_in_sade_sati(
        transit_saturn_sign=saturn,
        natal_moon_sign=moon,
    )

    if expected_phase is None:
        assert result is None, (
            f"Expected None (house={expected_house}) for "
            f"saturn={saturn}, moon={moon}, got {result!r}"
        )
    else:
        assert result is not None, (
            f"Expected phase={expected_phase} for saturn={saturn}, "
            f"moon={moon} (house={expected_house}), got None"
        )
        assert result["phase"] is expected_phase
        assert result["house_distance"] == expected_house
        # Sanity: the phase string round-trips through the enum value.
        assert result["phase"].value == expected_phase.value


# ============================================================================
# Test 9: Input validation — out-of-range signs raise ValueError
# ============================================================================
@pytest.mark.parametrize(
    "saturn, moon",
    [
        (0, 1),       # saturn below range
        (1, 0),       # moon below range
        (13, 1),      # saturn above range
        (1, 13),      # moon above range
        (-1, 5),      # negative saturn
        (5, -1),      # negative moon
        (100, 100),   # both wildly out of range
    ],
)
def test_invalid_sign_raises_value_error(saturn: int, moon: int) -> None:
    """Signs outside [1, 12] must raise ValueError. We never silently
    coerce or wrap — invalid input is a programmer error, not a
    transient data condition."""
    with pytest.raises(ValueError):
        is_in_sade_sati(transit_saturn_sign=saturn, natal_moon_sign=moon)


@pytest.mark.parametrize(
    "saturn, moon",
    [
        (1.5, 1),     # float saturn
        (1, 1.5),     # float moon
        ("1", 1),     # str saturn
        (1, "1"),     # str moon
        (None, 1),    # None saturn
        (True, 1),    # bool saturn (subclass of int — must still reject)
    ],
)
def test_non_int_sign_raises_value_error(saturn: object, moon: object) -> None:
    """Non-int sign inputs (floats, strings, bools, None) must raise
    ValueError. ``bool`` deserves an explicit case because it's a
    subclass of ``int`` and would otherwise pass an ``isinstance(.., int)``
    check while clearly being the wrong type."""
    with pytest.raises(ValueError):
        is_in_sade_sati(
            transit_saturn_sign=saturn,  # type: ignore[arg-type]
            natal_moon_sign=moon,  # type: ignore[arg-type]
        )


# ============================================================================
# Bonus: TypedDict shape sanity — the result is a plain dict at runtime
# ============================================================================
def test_result_is_a_plain_dict_with_expected_keys() -> None:
    """`SadeSatiInfo` is a TypedDict, so at runtime the function returns
    a regular dict. Pin the key set so consumers (FastAPI response
    models, the daemon's TransitAlert builder) can rely on the shape."""
    result = is_in_sade_sati(
        transit_saturn_sign=SAGITTARIUS,
        natal_moon_sign=SAGITTARIUS,
    )
    assert result is not None
    assert isinstance(result, dict)
    assert set(result.keys()) == {"phase", "house_distance", "description"}
    # Optional structural check: SadeSatiInfo's typed schema matches.
    info: SadeSatiInfo = result  # noqa: F841 — type-check at runtime via assignment
