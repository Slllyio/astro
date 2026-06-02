from __future__ import annotations
from app.raman_saab.primitives import bhangas as b
from app.raman_saab.chart.model import RamanChart


def _c(lons):
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=0.0, ayanamsa="raman")


def test_exchange_and_parivartana():
    # Mars in Taurus(Venus-owned) + Venus in Aries(Mars-owned) -> exchange.
    c = _c({"Mars": 35.0, "Venus": 5.0})
    assert b.exchange("Mars", "Venus", c) is True
    # Aries lagna: 1st lord Mars in 2nd (Taurus), 2nd lord Venus in 1st (Aries) -> parivartana(1,2).
    assert b.parivartana(1, 2, c) is True
    assert b.parivartana(1, 3, c) is False


def test_neecha_bhanga_dispositor_in_kendra():
    # Sun debilitated in Libra (190). Dispositor Venus in Capricorn (280) = the 10th
    # house (a kendra) from Aries lagna (asc_lon 0) -> cancellation.
    c = _c({"Sun": 190.0, "Venus": 280.0})
    assert b.neecha_bhanga("Sun", c) is True
    assert b.effective_dignity("Sun", c) == "neecha_bhanga"


def test_no_neecha_bhanga_when_not_debilitated():
    c = _c({"Sun": 10.0})            # exalted, not debilitated
    assert b.neecha_bhanga("Sun", c) is False
    assert b.effective_dignity("Sun", c) == "exalt"


def test_kemadruma_moon_isolated():
    # Moon alone, nothing in 2nd/12th from Moon, nothing with it (Sun excluded) -> kemadruma.
    c = _c({"Moon": 100.0})
    assert b.kemadruma(c) is True
