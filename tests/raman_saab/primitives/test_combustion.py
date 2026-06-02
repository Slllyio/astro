from __future__ import annotations
from app.raman_saab.primitives.combustion import combust_fraction
from app.raman_saab.chart.model import RamanChart


def _c(sun, other_name, other_lon):
    return RamanChart.from_stated_positions(
        {"Sun": {"lon": sun, "bhava": 1}, other_name: {"lon": other_lon, "bhava": 1}},
        asc_lon=0.0, ayanamsa="raman")


def test_mars_far_from_sun_not_combust():
    assert combust_fraction("Mars", _c(0.0, "Mars", 100.0)) == 0.0


def test_mars_on_sun_fully_combust():
    assert combust_fraction("Mars", _c(50.0, "Mars", 50.0)) == 1.0


def test_partial_combustion_scales_with_orb():
    f = combust_fraction("Mars", _c(0.0, "Mars", 8.5))   # half of Mars' 17° orb
    assert 0.4 < f < 0.6


def test_sun_itself_never_combust():
    assert combust_fraction("Sun", _c(0.0, "Sun", 0.0)) == 0.0
