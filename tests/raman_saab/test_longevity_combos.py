"""Qualitative longevity combinations — Alpayu/Madhyayu/Purnayu (HTJAH-II:3251-3474). Additive."""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.primitives import longevity_combos as lc

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def test_alpayu_sun_moon_mars_in_5th():
    stated = {"Sun": {"lon": 125.0, "bhava": 5}, "Moon": {"lon": 128.0, "bhava": 5},
              "Mars": {"lon": 131.0, "bhava": 5}}          # all in Leo = 5th from Aries Lagna
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")
    assert any(cls == "Alpayu" for cls, _span, _desc in lc.fired(ch))


def test_madhyayu_all_seven_in_5th():
    stated = {p: {"lon": 120.0 + i, "bhava": 5} for i, p in enumerate(
        ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"))}   # all 7 in Leo (5th)
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")
    fired = {cls for cls, _s, _d in lc.fired(ch)}
    assert "Madhyayu" in fired


def test_fired_shape_and_classes():
    out = lc.fired(cast_chart(_MAINPURI, ayanamsa="raman"))
    for cls, span, desc in out:
        assert cls in ("Alpayu", "Madhyayu", "Purnayu") and span and desc
