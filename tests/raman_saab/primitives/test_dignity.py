from __future__ import annotations
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.chart.model import RamanChart


def _chart(planet_lons):
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planet_lons.items()},
        asc_lon=0.0, ayanamsa="raman")


def test_exalted_sun():
    assert dignity("Sun", _chart({"Sun": 10.0})) == "exalt"   # Aries 10


def test_debilitated_sun():
    assert dignity("Sun", _chart({"Sun": 190.0})) == "debil"  # Libra 10


def test_own_sign():
    assert dignity("Mars", _chart({"Mars": 5.0})) == "moolatrikona"  # Aries 5 (MT 0-12)
    assert dignity("Mars", _chart({"Mars": 215.0})) == "own"         # Scorpio (own, not MT)


def test_dignity_handles_sparse_chart_without_lord():
    # Mars in Aquarius (lon 310°); sign lord Saturn is absent — must return "neutral", not KeyError.
    from app.raman_saab.chart.model import RamanChart
    chart = RamanChart.from_stated_positions({"Mars": {"lon": 310.0, "bhava": 1}}, asc_lon=0.0, ayanamsa="raman")
    assert dignity("Mars", chart) == "neutral"   # Aquarius, lord Saturn absent -> neutral
