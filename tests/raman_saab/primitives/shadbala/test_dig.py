from __future__ import annotations
import dataclasses
from app.raman_saab.primitives.shadbala.dig import dig_bala, _powerless_madhya
from app.raman_saab.chart.model import RamanChart


def test_dig_bala_saturn_standard_horoscope():
    # GBB-4:91-100: Saturn lon 124°51', 7th-bhava-madhya 114°57' -> powerless 294°57' -> 56.7 Sh.
    c = RamanChart.from_stated_positions({"Saturn": {"lon": 124 + 51/60, "bhava": 1}},
                                         asc_lon=185.0, ayanamsa="raman")
    # Saturn's powerful house = 7th -> powerless = 1st; _powerless_madhya reads madhyas[0].
    # Set the 1st-madhya to 294.95° (= 7th-madhya 114.95° + 180) so Saturn's arc = 56.7.
    madhyas = tuple(((114.95 + 180.0) + i * 30) % 360 for i in range(12))
    c = dataclasses.replace(c, bhava_madhyas=madhyas)
    assert abs(dig_bala("Saturn", c) - 56.7) < 1.0


def test_dig_bala_full_at_powerful_cusp():
    # A planet exactly on its powerful bhava-madhya -> ~60.
    c = RamanChart.from_stated_positions({"Jupiter": {"lon": 0.0, "bhava": 1}},
                                         asc_lon=0.0, ayanamsa="raman")
    madhyas = tuple((i * 30) for i in range(12))   # 1st madhya = 0° (Jupiter's powerful cusp)
    c = dataclasses.replace(c, bhava_madhyas=madhyas)
    assert abs(dig_bala("Jupiter", c) - 60.0) < 1.0
