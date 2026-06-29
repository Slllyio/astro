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


def test_madhyayu_benefics_own_moon_exalt_lagna():
    """HTJAH-II:3397 — benefics in own Rasis and the Moon exalted in Lagna (60y, Madhyayu)."""
    stated = {"Moon": {"lon": 40.0, "bhava": 1},        # Taurus = Lagna, exalted
              "Mercury": {"lon": 65.0, "bhava": 2},      # Gemini, own
              "Venus": {"lon": 195.0, "bhava": 6},       # Libra, own
              "Jupiter": {"lon": 245.0, "bhava": 8}}     # Sagittarius, own
    ch = RamanChart.from_stated_positions(stated, asc_lon=35.0, ayanamsa="raman")  # Taurus Lagna
    fired = {desc: cls for cls, _span, desc in lc.fired(ch)}
    assert "benefics in their own signs and the Moon exalted in the Lagna" in fired
    assert fired["benefics in their own signs and the Moon exalted in the Lagna"] == "Madhyayu"


def test_purnayu_lagna_lord_joined_by_benefic():
    """HTJAH-II:3404 — benefics in kendras + Lagna lord JOINED by a benefic (Purnayu)."""
    stated = {"Mars": {"lon": 185.0, "bhava": 7},        # Aries-Lagna lord in Libra (7th, a kendra)
              "Jupiter": {"lon": 190.0, "bhava": 7}}      # benefic conjoined the Lagna lord
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")   # Aries Lagna
    descs = {desc for _cls, _span, desc in lc.fired(ch)}
    assert "benefics in kendras and the Lagna lord joined by, or aspected by, a benefic/Jupiter" in descs


def test_purnayu_lagna_lord_aspected_by_jupiter():
    """HTJAH-II:3404 — the disjunct: Lagna lord ASPECTED by Jupiter (not conjoined)."""
    stated = {"Jupiter": {"lon": 10.0, "bhava": 1},      # Aries (1st, a kendra); 7th-aspects Libra
              "Mars": {"lon": 185.0, "bhava": 7}}          # Aries-Lagna lord in Libra, alone, aspected
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")   # Aries Lagna
    fired = {cls for cls, _span, _desc in lc.fired(ch)}
    assert "Purnayu" in fired, "Jupiter's 7th aspect on the Lagna lord must satisfy the disjunct"


def test_fired_shape_and_classes():
    out = lc.fired(cast_chart(_MAINPURI, ayanamsa="raman"))
    for cls, span, desc in out:
        assert cls in ("Alpayu", "Madhyayu", "Purnayu") and span and desc
