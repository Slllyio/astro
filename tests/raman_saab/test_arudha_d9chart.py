"""Jaimini Arudha padas + full-D9-chart helpers (navamsa lagna, 7th-from-navamsa spouse)."""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import arudha
from app.raman_saab.primitives import special_points as sp

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def _ch():
    return cast_chart(_MAINPURI, ayanamsa="lahiri")


def test_arudha_lagna_mainpuri():
    # Scorpio Lagna (8), lord Mars in Virgo (6): AL = 2*6 - 8 = 4 (Cancer); no 1st/7th exception.
    assert arudha.arudha_lagna(_ch()) == 4


def test_arudha_matches_special_points():
    ch = _ch()
    assert arudha.arudha_lagna(ch) == sp.arudha_lagna(ch).sign


def test_arudha_pada_and_upapada_in_range():
    ch = _ch()
    for h in range(1, 13):
        assert 1 <= arudha.arudha_pada(ch, h) <= 12
    assert 1 <= arudha.upapada_lagna(ch) <= 12


def test_lord_in_lagna_arudha_is_tenth():
    """When the lagna lord sits in the lagna, the Arudha falls in the 1st -> exception -> 10th."""
    stated = {"Mars": {"lon": 8.0, "bhava": 1}}        # Aries lagna, Mars (lord) in Aries
    from app.raman_saab.chart.model import RamanChart
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")
    assert arudha.arudha_lagna(ch) == 10               # Capricorn (10th from Aries)


def test_navamsa_lagna_helpers_mainpuri():
    ch = _ch()
    # D9 lagna is Scorpio (vargottama with the rasi lagna); lord Mars; 7th-from = Taurus -> Venus.
    assert sp.navamsa_lagna(ch).sign == 8
    assert sp.navamsa_lagna_lord(ch) == "Mars"
    assert sp.navamsa_seventh_lord(ch) == "Venus"
