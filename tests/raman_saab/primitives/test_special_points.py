from app.raman_saab.primitives import special_points as sp
from app.raman_saab.chart.model import RamanChart


def _c(lons, asc_lon=0.0):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


def test_atmakaraka_highest_degree_in_sign_seven_planets_only():
    # Saturn at 28° in sign beats all; Rahu at 29° must be IGNORED (chayagraha).
    c = _c({"Sun": 5.0, "Moon": 12.0, "Mars": 20.0, "Mercury": 3.0,
            "Jupiter": 18.0, "Venus": 25.0, "Saturn": 28.0, "Rahu": 29.0, "Ketu": 209.0})
    assert sp.atmakaraka(c) == "Saturn"


def test_karakamsa_is_ak_navamsa_sign():
    c = _c({"Sun": 5.0, "Moon": 12.0, "Mars": 20.0, "Mercury": 3.0,
            "Jupiter": 18.0, "Venus": 25.0, "Saturn": 28.0})
    ak = sp.atmakaraka(c)
    km = sp.karakamsa(c)
    assert km.name == "Karakamsa"
    assert km.sign == c.planets[ak].navamsa_sign


def test_arudha_lagna_raman_plain_count_no_exception():
    """Raman's formula is the plain double-count with NO Jaimini 1st/7th redirect
    (HTJAH-I:2519-2522): lagna-lord in the Lagna → Arudha stays in the Lagna."""
    # Aries lagna, lagna-lord Mars in the 1st -> Arudha = Aries (1), NOT redirected to the 10th.
    c = _c({"Mars": 5.0}, asc_lon=0.0)
    assert sp.arudha_lagna(c).sign == 1


def test_arudha_lagna_ramans_worked_example_lands_in_seventh():
    """Raman's own worked example (HTJAH-I:2521-2522): Aquarius Lagna, Saturn in Taurus →
    'the 4th from Taurus, viz., Leo becomes Arudha Lagna' — Leo is the 7th from Aquarius,
    and Raman keeps it (no exception)."""
    c = RamanChart.from_stated_positions(
        {"Saturn": {"lon": 45.0, "bhava": 4}}, asc_lon=315.0, ayanamsa="raman")
    assert sp.arudha_lagna(c).sign == 5
