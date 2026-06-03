"""Unit tests for Sthana Bala sub-components (GBB-3).

Each test pins an astronomical fact: deep exaltation/debilitation arcs, Kendra by sign,
sex-decanate Drekkana, odd/even parity, and the additive total.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.shadbala import sthana


def _c(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    """Build a Track-B chart from stated longitudes (all in bhava 1)."""
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


def test_ochcha_bala_exalted_is_max_debilitated_is_zero():
    """Sun deep-exalt (Aries 10) -> 60; deep-debil (Libra 10) -> 0 (GBB-3:43-115)."""
    assert abs(sthana.ochcha_bala("Sun", _c({"Sun": 10.0})) - 60.0) < 0.1
    assert sthana.ochcha_bala("Sun", _c({"Sun": 190.0})) < 0.1


def test_kendra_bala_by_sign():
    """Kendra/Panapara/Apoklima give 60/30/15 by rasi-house (GBB-3:609)."""
    assert sthana.kendra_bala("Mars", _c({"Mars": 5.0}, 0.0)) == 60.0     # 1st (kendra)
    assert sthana.kendra_bala("Mars", _c({"Mars": 35.0}, 0.0)) == 30.0    # 2nd (panapara)
    assert sthana.kendra_bala("Mars", _c({"Mars": 65.0}, 0.0)) == 15.0    # 3rd (apoklima)


def test_drekkana_bala_by_sex():
    """Masculine Sun gains in 1st decanate; feminine Moon in 3rd (GBB-3:653-671)."""
    assert sthana.drekkana_bala("Sun", _c({"Sun": 5.0})) == 15.0
    assert sthana.drekkana_bala("Sun", _c({"Sun": 15.0})) == 0.0
    assert sthana.drekkana_bala("Moon", _c({"Moon": 25.0})) == 15.0


def test_ojayugma_bala():
    """Sun prefers ODD; in Aries (odd rasi) it scores 15 for the rasi (GBB-3:546-601)."""
    val = sthana.ojayugma_bala("Sun", _c({"Sun": 5.0}))
    assert val in (15.0, 30.0)


def test_sthana_bala_sums_subcomponents():
    """Total Sthana = exact sum of the 5 sub-components (GBB-3:699)."""
    c = _c({"Sun": 10.0}, 280.0)   # Sun deep-exalt, Capricorn lagna
    total = sthana.sthana_bala("Sun", c)
    assert total == round(
        sthana.ochcha_bala("Sun", c) + sthana.saptavargaja_bala("Sun", c)
        + sthana.ojayugma_bala("Sun", c) + sthana.kendra_bala("Sun", c)
        + sthana.drekkana_bala("Sun", c), 3)


def test_nodes_get_zero_sthana():
    """Rahu/Ketu (chayagrahas) receive no Sthana Bala."""
    c = _c({"Rahu": 50.0, "Ketu": 230.0})
    assert sthana.sthana_bala("Rahu", c) == 0.0
    assert sthana.ochcha_bala("Ketu", c) == 0.0
    assert sthana.saptavargaja_bala("Rahu", c) == 0.0
