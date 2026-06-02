import dataclasses, pytest
from app.raman_saab.chart.model import BirthData, PlanetPos, RamanChart

def test_chart_is_frozen():
    p = PlanetPos(name="Sun", lon=100.0, sign=4, rasi_house=10, bhava=10,
                  bhava_sandhi=False, nakshatra=9, pada=2, retrograde=False,
                  navamsa_sign=7, vargottama=False, dispositor="Moon")
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.lon = 1.0  # type: ignore[misc]

def test_from_stated_positions_builds_chart_without_ephemeris():
    """Track-B constructor: inject Raman's printed positions, derive the rest, no swisseph."""
    stated = {"Sun": {"lon": 100.0, "bhava": 10}, "Moon": {"lon": 40.0, "bhava": 6}}
    chart = RamanChart.from_stated_positions(stated, asc_lon=15.0, ayanamsa="raman")
    assert chart.asc_sign == 1                      # 15° -> Aries
    assert chart.planets["Sun"].sign == 4            # 100° -> Cancer
    assert chart.planets["Sun"].bhava == 10          # taken from stated
    assert chart.planets["Sun"].rasi_house == 4      # whole-sign Cancer from Aries lagna
    assert chart.ayanamsa == "raman"
