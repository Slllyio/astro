from __future__ import annotations
from app.raman_saab.primitives import dispositor as d
from app.raman_saab.chart.model import RamanChart


def _c(lons):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=0.0, ayanamsa="raman")


def test_dispositor_is_sign_lord():
    assert d.dispositor("Mars", _c({"Mars": 100.0})) == "Moon"   # Cancer -> Moon


def test_dispositor_chain_terminates_at_own_sign():
    # Mars in Cancer(Moon) -> Moon in Taurus(Venus) -> Venus in Libra(own) STOP.
    chart = _c({"Mars": 100.0, "Moon": 40.0, "Venus": 190.0})
    assert d.dispositor_chain("Mars", chart) == ["Moon", "Venus"]


def test_navamsa_lord_of():
    # planet whose navamsa sign is Aries -> Mars.
    chart = _c({"Sun": 0.0})    # 0° Aries -> first navamsa Aries -> Mars
    assert d.navamsa_lord_of("Sun", chart) == "Mars"


def test_dispositor_chain_own_sign_returns_single_planet():
    # Venus in Libra (own sign) — chain should return just ["Venus"].
    chart = _c({"Venus": 190.0})   # 190° = Libra (sign 7), lord Venus
    assert d.dispositor_chain("Venus", chart) == ["Venus"]
