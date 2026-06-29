"""Career reading via the navamsa-dispositor of the 10th lord (HTJAH-II:10249-10274). Additive."""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import career

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def test_tenth_lord_scorpio_lagna_is_sun():
    """Scorpio Lagna -> 10th sign Leo -> lord Sun."""
    assert career.tenth_lord(cast_chart(_MAINPURI, ayanamsa="raman")) == "Sun"


def test_mainpuri_career_via_navamsa_dispositor():
    ch = cast_chart(_MAINPURI, ayanamsa="raman")
    lord, disp, trade = career.career_indication(ch)
    assert lord == "Sun"                       # 10th lord
    assert disp in career.TRADE_BY_NAVAMSA_DISPOSITOR
    assert "medicine" in trade                 # navamsa-dispositor Sun -> medicine/gold/diplomacy


def test_all_seven_planets_have_a_trade():
    assert set(career.TRADE_BY_NAVAMSA_DISPOSITOR) == {
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}


def test_career_by_sign_covers_all_twelve():
    assert set(career.CAREER_BY_SIGN) == set(range(1, 13))


def test_tenth_sign_career_scorpio_lagna_is_leo_profile():
    """Scorpio Lagna -> 10th sign Leo -> government/authority profile."""
    ch = cast_chart(_MAINPURI, ayanamsa="raman")
    assert career.tenth_sign(ch) == 5
    assert "government" in career.tenth_sign_career(ch)
