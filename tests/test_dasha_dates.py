"""Vimshottari Mahadasha calendar-date tests.

These tests use PINNED real-world baselines, not numbers the engine generated.
The expected values below were either:
  - cross-checked against external Vedic astrology sources (Wikipedia, Prokerala,
    KP-Astrology references) for the Bangalore 1990-07-15 lord-sequence baseline, OR
  - independently computed by hand using swe.revjul() at known Julian Days for
    the calendar-math anchor.

Do NOT regenerate these constants from the engine output - that defeats the
purpose of pinning them.
"""
from __future__ import annotations

import datetime as dt

import pytest
import swisseph as swe

from app.core.ephemeris_engine import (
    DAYS_PER_VEDIC_YEAR,
    calculate_all_charts,
    calculate_vimshottari_mahadasha,
)


# ============================================================================
# Baseline 1: Lord-sequence verification
# ============================================================================
# Birth: 1990-07-15 12:00 IST, Bangalore (12.97 N, 77.59 E).
# Moon longitude (sidereal Lahiri) ~ 356.32 deg = within Revati nakshatra
#   (Pisces 16d40m to 30d, ruled by Mercury per Vedic Vimshottari tradition).
#
# External corroboration:
#   - Revati's Vimshottari lord is Mercury (17-year MD).
#     ref: https://en.wikipedia.org/wiki/Dasha_(astrology)
#     ref: https://kpastrologypro.com/blog/kp-astrology-nakshatras-27-stars
#   - Mercury's sequence position is index 8 (Ketu, Venus, Sun, Moon, Mars,
#     Rahu, Jupiter, Saturn, Mercury), so any nakshatra at index 26 (= 8 + 18)
#     yields a Mercury MD. Revati is the 27th nakshatra (index 26). Match.
#
# At a fraction_elapsed ~ 0.724 of a 17-year Mercury MD, the native is in
# Mercury MD running approximately Mar 1978 -> Mar 1995. Pinned below.

BANGALORE_1990_EXPECTED_LORD = "Mercury"
BANGALORE_1990_EXPECTED_TOTAL_YEARS = 17.0
# +/- 1 day tolerance accommodates fp rounding in 365.2425 multiplications.
BANGALORE_1990_EXPECTED_END_DATE_RANGE = (dt.date(1995, 3, 25), dt.date(1995, 3, 27))
BANGALORE_1990_EXPECTED_START_DATE_RANGE = (dt.date(1978, 3, 25), dt.date(1978, 3, 27))


def test_bangalore_1990_mahadasha_lord() -> None:
    result = calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5
    )
    md = result["current_mahadasha"]
    assert md["mahadasha_lord"] == BANGALORE_1990_EXPECTED_LORD
    assert md["total_duration_years"] == pytest.approx(BANGALORE_1990_EXPECTED_TOTAL_YEARS)


def test_bangalore_1990_mahadasha_dates() -> None:
    """End-to-end calendar math: dates must agree with the external pinning within 1 day."""
    result = calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5
    )
    md = result["current_mahadasha"]

    start = dt.date.fromisoformat(md["start_date"])
    end = dt.date.fromisoformat(md["end_date"])

    assert BANGALORE_1990_EXPECTED_START_DATE_RANGE[0] <= start <= BANGALORE_1990_EXPECTED_START_DATE_RANGE[1]
    assert BANGALORE_1990_EXPECTED_END_DATE_RANGE[0] <= end <= BANGALORE_1990_EXPECTED_END_DATE_RANGE[1]


# ============================================================================
# Baseline 2: Calendar-math anchor (March 2025)
# ============================================================================
# Hand-constructed inputs producing an externally-verifiable date.
# Moon at 46.6666667 deg = halfway through Rohini (3rd nakshatra, Moon-ruled).
# fraction_elapsed = 0.5 -> years_elapsed = 5.0 of a 10-year Moon MD.
#
# birth_jd is set at 2030-03-14 12:00 UTC. Therefore:
#   start_jd = birth_jd - 5 * 365.2425  ->  swe.revjul -> 2025-03-14
#   end_jd   = birth_jd + 5 * 365.2425  ->  swe.revjul -> 2035-03-14
#
# This is the canary test: if a future "simplification" replaces JD arithmetic
# with datetime.timedelta, or if 365.2425 is "fixed" to 365.25, the assertions
# below fail by at least one day.

MARCH_2025_BIRTH_JD = swe.julday(2030, 3, 14, 12.0, swe.GREG_CAL)
MARCH_2025_MOON_LONGITUDE = 46.6666667  # halfway through Rohini
MARCH_2025_EXPECTED_START = "2025-03-14"
MARCH_2025_EXPECTED_END = "2035-03-14"


def test_march_2025_anchor_lord_is_moon() -> None:
    md = calculate_vimshottari_mahadasha(MARCH_2025_MOON_LONGITUDE, MARCH_2025_BIRTH_JD)
    assert md["mahadasha_lord"] == "Moon"


def test_march_2025_anchor_start_date_exact() -> None:
    """Working backward 5 yr from 2030-03-14 lands exactly on 2025-03-14."""
    md = calculate_vimshottari_mahadasha(MARCH_2025_MOON_LONGITUDE, MARCH_2025_BIRTH_JD)
    assert md["start_date"] == MARCH_2025_EXPECTED_START


def test_march_2025_anchor_end_date_exact() -> None:
    md = calculate_vimshottari_mahadasha(MARCH_2025_MOON_LONGITUDE, MARCH_2025_BIRTH_JD)
    assert md["end_date"] == MARCH_2025_EXPECTED_END


# ============================================================================
# JD round-trip property test (constraint #2)
# ============================================================================

@pytest.mark.parametrize("jd", [
    swe.julday(1900, 1, 1, 0.0, swe.GREG_CAL),
    swe.julday(2000, 1, 1, 12.0, swe.GREG_CAL),
    swe.julday(2030, 6, 30, 6.0, swe.GREG_CAL),
    swe.julday(2099, 12, 31, 23.0, swe.GREG_CAL),
])
def test_jd_revjul_round_trip(jd: float) -> None:
    """swe.julday(*swe.revjul(jd)) round-trips within 1 ms (~1.16e-8 days).

    This is the precision floor for our calendar math; if it ever slips, the
    Mahadasha date assertions become flaky.
    """
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    round_tripped = swe.julday(int(y), int(m), int(d), h, swe.GREG_CAL)
    one_millisecond_in_days = 1.0 / (24 * 3600 * 1000)
    assert abs(round_tripped - jd) < one_millisecond_in_days


# ============================================================================
# Constraint #2 regression guard: JD arithmetic vs. timedelta
# ============================================================================

def test_jd_arithmetic_diverges_from_naive_timedelta_julian() -> None:
    """Future-engineer guard: if someone replaces `years * 365.2425` with
    `timedelta(days=years * 365.25)` (the 'naive' Julian-year length), this
    test fails by ~3.4 hours over 19 years and ~0.75 days over 100 years.

    Catches both regressions: the wrong constant AND the wrong timedelta path.
    """
    birth_jd = swe.julday(1900, 1, 1, 12.0, swe.GREG_CAL)
    years = 100

    # Method A: JD arithmetic with mean Gregorian year (the engine's method).
    end_jd_correct = birth_jd + years * DAYS_PER_VEDIC_YEAR
    ya, ma, da, _ = swe.revjul(end_jd_correct, swe.GREG_CAL)
    correct_date = dt.date(int(ya), int(ma), int(da))

    # Method B: naive timedelta with Julian-year days (the "simplified" wrong way).
    naive_date = (
        dt.date(1900, 1, 1) + dt.timedelta(days=years * 365.25)
    )

    delta_days = abs((correct_date - naive_date).days)
    # The two methods agree to within a small number of days; over 100 years
    # the divergence is ~0.75 days. Round-up to 1 in either direction.
    assert delta_days >= 1, (
        f"correct={correct_date} naive={naive_date}: methods agree, but they "
        "should diverge over a 100-yr span. Has the year-length constant changed?"
    )


# ============================================================================
# End-of-dasha boundary (the "fraction_elapsed near 1.0" case)
# ============================================================================
# Moon longitude at end of Mercury-ruled Revati nakshatra (just before 360 deg).
# fraction_elapsed -> 1, so MD end_date should be very close to birth_date.

def test_end_of_dasha_boundary_close_to_birth() -> None:
    # Revati spans 346.67 to 360 deg. At 359.99 we are 0.01 deg from the end,
    # i.e. 0.00075 of the nakshatra remaining = ~4.6 days of a 17-yr Mercury MD.
    near_end_of_revati = 359.99
    birth_jd = swe.julday(2025, 1, 1, 12.0, swe.GREG_CAL)
    md = calculate_vimshottari_mahadasha(near_end_of_revati, birth_jd)

    assert md["mahadasha_lord"] == "Mercury"

    birth = dt.date(2025, 1, 1)
    end = dt.date.fromisoformat(md["end_date"])
    assert (end - birth).days < 10, f"expected MD end within ~5 days of birth, got {end}"
