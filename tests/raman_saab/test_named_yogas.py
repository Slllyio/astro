"""Named Raja/Dhana yogas (3HC) — Budha-Aditya, Chatussagara, Vasumathi, Parvata, Jaya. Reported,
verdict-invariant (kind='other')."""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.yogas import detect_yogas


def _ids(chart: RamanChart) -> set[str]:
    return {fy.id for fy in detect_yogas(chart)}


def test_budha_aditya_when_sun_mercury_conjunct():
    ch = RamanChart.from_stated_positions(
        {"Sun": {"lon": 5.0, "bhava": 1}, "Mercury": {"lon": 12.0, "bhava": 1}},
        asc_lon=5.0, ayanamsa="raman")
    assert "Y.BUDHA_ADITYA" in _ids(ch)


def test_chatussagara_when_all_kendras_occupied():
    stated = {"Sun": {"lon": 5.0, "bhava": 1}, "Moon": {"lon": 95.0, "bhava": 4},
              "Mars": {"lon": 185.0, "bhava": 7}, "Mercury": {"lon": 275.0, "bhava": 10}}
    assert "Y.CHATUSSAGARA" in _ids(RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman"))


def test_chatussagara_absent_when_a_kendra_empty():
    stated = {"Sun": {"lon": 5.0, "bhava": 1}, "Moon": {"lon": 95.0, "bhava": 4},
              "Mars": {"lon": 185.0, "bhava": 7}}                 # 10th empty
    assert "Y.CHATUSSAGARA" not in _ids(RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman"))
