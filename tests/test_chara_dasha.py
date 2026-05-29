"""Tests for app.core.chara_dasha — Jaimini parallel dasha track."""
from __future__ import annotations

import pytest

from app.core.chara_dasha import (
    DAYS_PER_VEDIC_YEAR,
    chara_active_at,
    chara_sequence,
    chara_windows_jd,
    direction_for,
    period_for,
)


class TestDirection:
    """Movable + dual go forward (+1); fixed goes backward (−1)."""

    @pytest.mark.parametrize("lagna", [1, 4, 7, 10])
    def test_movable_signs_go_forward(self, lagna):
        """Movable lagnas (Ar/Ca/Li/Cp) → +1 direction."""
        assert direction_for(lagna) == 1

    @pytest.mark.parametrize("lagna", [2, 5, 8, 11])
    def test_fixed_signs_go_backward(self, lagna):
        """Fixed lagnas (Ta/Le/Sc/Aq) → −1 direction."""
        assert direction_for(lagna) == -1

    @pytest.mark.parametrize("lagna", [3, 6, 9, 12])
    def test_dual_signs_go_forward(self, lagna):
        """Dual lagnas (Ge/Vi/Sg/Pi) → +1 direction (Iyer convention)."""
        assert direction_for(lagna) == 1


class TestPeriodCalculation:
    """Sign-lord distance arithmetic per Narasimha Rao."""

    def test_aries_period_uses_mars_distance_forward(self):
        """Aries Lagna, forward: Mars owns Aries (1) and Scorpio (8).
        Aries IS the dasha sign → lord-in-sign → 12-year period."""
        assert period_for(1, direction=1) == 12

    def test_leo_period_for_aries_lagna(self):
        """Aries Lagna (movable, forward). Leo (sign 5) — its lord Sun
        owns Leo. Distance 1 → 12 years."""
        assert period_for(5, direction=1) == 12

    def test_virgo_period_for_aries_lagna(self):
        """Aries Lagna, forward. Virgo (sign 6) — Mercury owns Gemini (3)
        and Virgo (6). Lord-in-sign → 12 years."""
        assert period_for(6, direction=1) == 12

    def test_taurus_period_for_aries_lagna(self):
        """Aries Lagna, forward. Taurus (2) — Venus owns Taurus (2) and
        Libra (7). Lord-in-sign → 12 years."""
        assert period_for(2, direction=1) == 12


class TestSequence:
    """12-sign cycle integrity."""

    def test_sequence_has_12_signs(self):
        """Exactly 12 entries in the cycle."""
        seq = chara_sequence(1)
        assert len(seq) == 12

    def test_sequence_starts_at_lagna(self):
        """First sign in sequence is the Lagna itself."""
        for lagna in (1, 5, 8, 12):
            assert chara_sequence(lagna)[0][0] == lagna

    def test_sequence_walks_forward_for_aries(self):
        """Aries Lagna walks 1,2,3,...,12."""
        signs = [s for s, _ in chara_sequence(1)]
        assert signs == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    def test_sequence_walks_backward_for_taurus(self):
        """Taurus Lagna (fixed) walks 2,1,12,11,...,3."""
        signs = [s for s, _ in chara_sequence(2)]
        assert signs == [2, 1, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3]

    def test_period_years_positive_int(self):
        """Each sign's MD length is 1..12 years (no zero, no negative)."""
        for lagna in range(1, 13):
            for _, years in chara_sequence(lagna):
                assert 1 <= years <= 12


class TestWindowsAndActiveLookup:
    """JD-based window construction and active-MD-at lookup."""

    def test_windows_start_at_birth_jd(self):
        """First window starts exactly at birth_jd."""
        birth = 2447988.0
        windows = chara_windows_jd(1, birth)
        assert windows[0][1] == pytest.approx(birth)

    def test_windows_are_contiguous(self):
        """Each window's end equals next window's start (no gaps)."""
        windows = chara_windows_jd(1, 2447988.0)
        for i in range(len(windows) - 1):
            assert windows[i][2] == pytest.approx(windows[i + 1][1])

    def test_active_at_returns_first_sign_for_birth(self):
        """At birth_jd, active sign is the Lagna sign."""
        birth = 2447988.0
        assert chara_active_at(7, birth, birth) == 7

    def test_active_at_in_second_md(self):
        """After exhausting first MD, active sign is the next in sequence."""
        birth = 2447988.0
        first_sign, first_years = chara_sequence(7)[0]
        mid_second = birth + (first_years + 0.5) * DAYS_PER_VEDIC_YEAR
        next_sign = chara_sequence(7)[1][0]
        assert chara_active_at(7, birth, mid_second) == next_sign

    def test_active_at_returns_none_before_birth(self):
        """Target JD before birth — no active sign."""
        birth = 2447988.0
        assert chara_active_at(1, birth, birth - 100) is None

    def test_active_at_wraps_past_cycle_end(self):
        """Audit-fix: past first cycle, doctrine says wrap to second cycle.

        For a native past ~120 years, the cycle repeats — Chara MD reads
        ``(elapsed % cycle_length)`` rather than returning None.
        """
        birth = 2447988.0
        windows = chara_windows_jd(1, birth)
        cycle_length = windows[-1][2] - birth
        # Sample inside first cycle
        target_first = birth + 5.0 * 365.2425  # 5 years in
        sign_first = chara_active_at(1, birth, target_first)
        # Same offset in second cycle
        target_second = birth + cycle_length + 5.0 * 365.2425
        sign_second = chara_active_at(1, birth, target_second)
        assert sign_first == sign_second  # cycle repeats


class TestInvalidInputs:
    """Out-of-range Lagna fails fast."""

    def test_direction_rejects_invalid_lagna(self):
        """Lagna 0 and 13 must raise."""
        with pytest.raises(ValueError):
            direction_for(0)
        with pytest.raises(ValueError):
            direction_for(13)
