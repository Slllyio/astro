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


def test_kemadruma_bhanga_planet_in_kendra_from_moon():
    # 3HC:2182-2185 kendra-from-Moon branch: Moon h2 isolated; Saturn h5 is the
    # 4th from the Moon (a kendra from the Moon) but NOT a kendra from the Lagna.
    c = _c({"Moon": 35.0, "Saturn": 125.0})
    assert b.kemadruma(c) is True
    assert b.kemadruma_bhanga(c) is True


def test_kemadruma_bhanga_sun_conjunct_moon():
    # 3HC:2182-2185 conjunction branch (Sun policy): the Sun conjunct the Moon
    # does not stop formation (Sun is excluded there) but DOES cancel — the
    # cited line says "a planet" with no Sun exception.
    c = _c({"Moon": 35.0, "Sun": 40.0})
    assert b.kemadruma(c) is True
    assert b.kemadruma_bhanga(c) is True


def test_kemadruma_bhanga_absent_when_moon_truly_isolated():
    # Moon alone in h6: no kendra from the Lagna, nothing in a kendra from the
    # Moon (the Moon itself never counts), no conjunction, no benefic drishti.
    c = _c({"Moon": 160.0})
    assert b.kemadruma(c) is True
    assert b.kemadruma_bhanga(c) is False
