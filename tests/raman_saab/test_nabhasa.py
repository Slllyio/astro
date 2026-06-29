"""Nabhasa (Asraya/Dala/Sankhya/contiguous-Akriti) + solar-flank yogas (3HC). Systematic,
cite-verified, verdict-invariant (kind='other')."""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.doctrine.yogas import detect_yogas

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)
_SANKHYA = {"Y.VEENA", "Y.DAMINI", "Y.PASA", "Y.KEDARA", "Y.SULA", "Y.YUGA", "Y.GOLA"}


def _ids(chart: RamanChart) -> set[str]:
    return {fy.id for fy in detect_yogas(chart)}


def test_exactly_one_sankhya_on_a_full_chart():
    """The seven planets always occupy 1..7 distinct signs -> exactly one Sankhya yoga fires."""
    assert len(_ids(cast_chart(_MAINPURI, ayanamsa="raman")) & _SANKHYA) == 1


def test_rajju_when_all_seven_in_movable_signs():
    stated = {"Sun": {"lon": 5.0, "bhava": 1}, "Moon": {"lon": 95.0, "bhava": 4},
              "Mars": {"lon": 185.0, "bhava": 7}, "Mercury": {"lon": 275.0, "bhava": 10},
              "Jupiter": {"lon": 15.0, "bhava": 1}, "Venus": {"lon": 105.0, "bhava": 4},
              "Saturn": {"lon": 195.0, "bhava": 7}}      # all in Ar/Cn/Li/Cp (movable)
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")
    assert "Y.RAJJU" in _ids(ch)


def test_vesi_when_a_planet_is_second_from_sun():
    """Sun in Aries; Jupiter in Taurus (2nd from the Sun) -> Vesi (non-Moon flank)."""
    ch = RamanChart.from_stated_positions(
        {"Sun": {"lon": 5.0, "bhava": 1}, "Jupiter": {"lon": 35.0, "bhava": 2}},
        asc_lon=5.0, ayanamsa="raman")
    assert "Y.VESI" in _ids(ch)


def test_yupa_when_all_seven_in_houses_1_to_4():
    stated = {p: {"lon": lon, "bhava": (lon // 30) + 1} for p, lon in
              {"Sun": 5.0, "Moon": 35.0, "Mars": 65.0, "Mercury": 95.0,
               "Jupiter": 8.0, "Venus": 38.0, "Saturn": 68.0}.items()}   # all in signs 1-4
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")
    assert "Y.YUPA" in _ids(ch)
