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


def test_arudha_lagna_exception_to_tenth():
    # Aries lagna, lagna-lord Mars in the 1st -> raw Arudha = 1st -> exception -> 10th (Capricorn=10).
    c = _c({"Mars": 5.0}, asc_lon=0.0)
    assert sp.arudha_lagna(c).sign == 10
