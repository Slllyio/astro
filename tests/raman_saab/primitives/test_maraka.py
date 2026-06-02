from __future__ import annotations
from app.raman_saab.primitives.maraka import maraka_points
from app.raman_saab.chart.model import RamanChart


def _c(lons, asc_lon=0.0):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=asc_lon, ayanamsa="raman")


def test_22nd_drekkana_lord_pins_ramans_printed_example():
    # Raman HTJAH-II:3692-3695: Lagna 27° Aquarius -> lagna drekkana = 3rd of Aquarius;
    # the 22nd drekkana from this = 1st drekkana of Libra -> lord Venus.
    c = _c({"Moon": 0.0}, asc_lon=10 * 30 + 27.0)   # 27° Aquarius
    assert maraka_points(c).drekkana22_lord == "Venus"


def test_64th_navamsa_lord_is_reckoned_from_the_moon():
    # HTJAH-II:4544: "the lord of the 64th Navamsa occupied by the Moon" -> from the MOON.
    # Structural: a valid sign-lord; and it MUST change when only the Moon moves.
    c1 = _c({"Moon": 5.0}, asc_lon=0.0)
    c2 = _c({"Moon": 100.0}, asc_lon=0.0)           # same lagna, different Moon
    from app.raman_saab.chart.constants import SIGN_LORDS
    assert maraka_points(c1).navamsa64_lord in SIGN_LORDS.values()
    assert maraka_points(c1).navamsa64_lord != maraka_points(c2).navamsa64_lord


def test_second_and_seventh_lords_are_primary_marakas():
    # Aries lagna: 2nd lord = Venus (Taurus), 7th lord = Venus (Libra) -> Venus primary.
    c = _c({"Venus": 35.0, "Moon": 0.0}, asc_lon=0.0)
    mp = maraka_points(c)
    grahas = {u.graha for u in mp.units if u.tier == "primary"}
    assert "Venus" in grahas
