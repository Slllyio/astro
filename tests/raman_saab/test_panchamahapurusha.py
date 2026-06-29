"""Pancha Mahapurusha yogas (3HC:3432-4060) — a planet in its OWN/EXALTATION sign occupying a
KENDRA (1/4/7/10 from the Lagna). Detected + cited; verdict-invariant (kind='other')."""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.yogas import detect_yogas

_PMP = {"Y.RUCHAKA", "Y.BHADRA", "Y.HAMSA", "Y.MALAVYA", "Y.SASA"}


def _ids(chart: RamanChart) -> set[str]:
    return {fy.id for fy in detect_yogas(chart)}


def test_ruchaka_fires_mars_exalt_in_kendra():
    """Mars exalted in Capricorn occupying the 10th (a kendra) -> Ruchaka."""
    ch = RamanChart.from_stated_positions({"Mars": {"lon": 295.0, "bhava": 10}},
                                          asc_lon=5.0, ayanamsa="raman")  # Aries Lagna
    assert ch.planets["Mars"].rasi_house in (1, 4, 7, 10)
    assert "Y.RUCHAKA" in _ids(ch)


def test_sasa_fires_saturn_own_in_kendra():
    """Saturn in own Aquarius occupying the 4th (a kendra) from a Scorpio Lagna -> Sasa."""
    ch = RamanChart.from_stated_positions({"Saturn": {"lon": 315.0, "bhava": 4}},
                                          asc_lon=215.0, ayanamsa="raman")  # Scorpio Lagna
    assert "Y.SASA" in _ids(ch)


def test_no_mahapurusha_when_not_in_kendra():
    """Exalted Mars in the 3rd (NOT a kendra) does not form Ruchaka."""
    ch = RamanChart.from_stated_positions({"Mars": {"lon": 295.0, "bhava": 3}},
                                          asc_lon=335.0, ayanamsa="raman")  # Pisces Lagna -> Cap = 11th
    assert "Y.RUCHAKA" not in _ids(ch)


def test_no_mahapurusha_when_not_dignified():
    """Mars in a kendra but in a neutral sign (no own/exalt) does not form Ruchaka."""
    ch = RamanChart.from_stated_positions({"Mars": {"lon": 95.0, "bhava": 4}},
                                          asc_lon=5.0, ayanamsa="raman")  # Cancer (debil), 4th
    assert "Y.RUCHAKA" not in _ids(ch)
