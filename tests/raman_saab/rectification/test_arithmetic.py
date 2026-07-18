"""HPA ch.12 arithmetic-rule tests — pure rule math + a real-chart sunrise sanity check.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.rectification import arithmetic as A
from app.raman_saab.rectification.candidates import light_chart
import swisseph as swe


class TestRuleMath:
    def test_rule1_matches_group_position(self) -> None:
        """(whole-ghatis x 4) mod 9 must equal the nakshatra's position in its 9-group;
        the group repeats from Aswini (1), Makha (10), Moola (19)."""
        # 10 ghatis -> 40 mod 9 = 4: Rohini (nak 4, pos 4) and Chitra (nak 13, pos 4).
        assert A.rule1_nakshatra(10.0, 4)
        assert A.rule1_nakshatra(10.0, 13)
        assert not A.rule1_nakshatra(10.0, 5)

    def test_rule1_remainder_zero_reads_as_ninth(self) -> None:
        """Remainder 0 denotes the 9th star of the group (Aslesha/Jyeshta/Revati)."""
        # 9 ghatis -> 36 mod 9 = 0 -> position 9.
        assert A.rule1_nakshatra(9.0, 9)      # Aslesha, group position 9
        assert not A.rule1_nakshatra(9.0, 1)

    def test_rule2_inclusive_count_from_sun_sign(self) -> None:
        """Quotient+1 counted inclusively from the Sun's sign gives the rising sign."""
        # ghatis=5, sun 10 deg in sign -> (30+10)//30 = 1 -> the 2nd sign from Sun's.
        assert A.rule2_rising_sign(5.0, 10.0, sun_sign=6, asc_sign=7)
        assert not A.rule2_rising_sign(5.0, 10.0, sun_sign=6, asc_sign=6)

    def test_rule3_full_candidate_set(self) -> None:
        """Asc in {5th, 7th, 9th from the Moon-sign-lord's sign} or the Moon's own sign."""
        # lord in sign 1 (Aries): candidates {5, 7, 9} + moon_sign.
        assert A.rule3_janma_lagna(moon_sign=11, moon_sign_lord_sign=1, asc_sign=5)
        assert A.rule3_janma_lagna(moon_sign=11, moon_sign_lord_sign=1, asc_sign=7)
        assert A.rule3_janma_lagna(moon_sign=11, moon_sign_lord_sign=1, asc_sign=11)
        assert not A.rule3_janma_lagna(moon_sign=11, moon_sign_lord_sign=1, asc_sign=4)

    def test_channel_is_capped(self) -> None:
        """All three rules passing yields exactly the documented channel cap."""
        s = A.ArithmeticScore(ghatis=10.0, r1_nakshatra=True, r2_rising_sign=True,
                              r3_janma_lagna=True)
        assert s.subtotal == pytest.approx(A.CHANNEL_CAP)


class TestRealChart:
    def test_ghatis_at_morning_birth_are_plausible(self) -> None:
        """rect_case_01 (10:02 IST, 27.2N): sunrise ~06:10-06:30 IST in October, so the
        elapsed ghatis at birth must land near (3.5-4 h)/24 min ~ 9-10."""
        birth = BirthData(name="x", year=1989, month=10, day=12, hour=10, minute=2,
                          tz_offset=5.5, latitude=27.23, longitude=79.03)
        sunrise = A.sunrise_jd(birth, "raman")
        jd_birth = swe.julday(1989, 10, 12, 10.0333 - 5.5, swe.GREG_CAL)
        ghatis = A.ghatis_from_sunrise(jd_birth, sunrise)
        assert 8.0 < ghatis < 11.0

    def test_arithmetic_score_runs_on_a_light_chart(self) -> None:
        """The secondary channel needs only Tier-L positions (never Shadbala)."""
        jd = swe.julday(1989, 10, 12, 10.0333 - 5.5, swe.GREG_CAL)
        chart = light_chart(jd, 27.23, 79.03, "raman")
        birth = BirthData(name="x", year=1989, month=10, day=12, hour=10, minute=2,
                          tz_offset=5.5, latitude=27.23, longitude=79.03)
        s = A.arithmetic_score(chart, birth)
        assert 0.0 <= s.subtotal <= A.CHANNEL_CAP
        assert 8.0 < s.ghatis < 11.0
