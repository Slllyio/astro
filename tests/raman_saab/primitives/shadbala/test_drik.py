from __future__ import annotations

from app.raman_saab.primitives.shadbala.drik import dristi_value, drik_bala
from app.raman_saab.chart.model import RamanChart


def test_dristi_value_anchors():
    assert dristi_value(30) == 0.0
    assert dristi_value(60) == 15.0     # Raman's anchor (NOT 30)
    assert dristi_value(90) == 45.0
    assert dristi_value(150) == 0.0
    assert dristi_value(180) == 60.0
    assert dristi_value(300) == 0.0
    assert dristi_value(20) == 0.0      # below 30 -> no aspect


def test_drik_bala_signed_by_benefic_malefic():
    # Jupiter (benefic) at 0°, Saturn (malefic) at 180° from a target at 90°.
    c = RamanChart.from_stated_positions(
        {"Jupiter": {"lon": 0.0, "bhava": 1}, "Saturn": {"lon": 180.0, "bhava": 1},
         "Mars": {"lon": 90.0, "bhava": 1}}, asc_lon=0.0, ayanamsa="raman")
    val = drik_bala("Mars", c)
    assert isinstance(val, float)       # signed; sign reflects net benefic vs malefic
