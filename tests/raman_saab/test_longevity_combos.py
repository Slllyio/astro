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
              "Jupiter": {"lon": 190.0, "bhava": 7},      # benefic conjoined the Lagna lord
              "Venus": {"lon": 95.0, "bhava": 4}}          # 2nd benefic in a kendra (Cancer = 4th)
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")   # Aries Lagna
    descs = {desc for _cls, _span, desc in lc.fired(ch)}
    assert "benefics in kendras and the Lagna lord joined by, or aspected by, a benefic/Jupiter" in descs


def test_purnayu_lagna_lord_aspected_by_jupiter():
    """HTJAH-II:3404 — the disjunct: Lagna lord ASPECTED by Jupiter (not conjoined)."""
    stated = {"Jupiter": {"lon": 10.0, "bhava": 1},      # Aries (1st, a kendra); 7th-aspects Libra
              "Venus": {"lon": 95.0, "bhava": 4},         # 2nd benefic in a kendra (Cancer), NOT with the lord
              "Mars": {"lon": 185.0, "bhava": 7}}          # Aries-Lagna lord in Libra, alone, aspected
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")   # Aries Lagna
    assert "benefics in kendras and the Lagna lord joined by, or aspected by, a benefic/Jupiter" in _descs(ch), \
        "Jupiter's 7th aspect on the Lagna lord must satisfy the disjunct (with >=2 benefics in kendras)"


def _descs(chart):
    return {desc for _cls, _span, desc in lc.fired(chart)}


def test_alpayu_moon_leo_sun_saturn_8th_venus_2nd():
    """HTJAH-II:3266 — Moon in Leo (sign), Sun & Saturn in the 8th, Venus in the 2nd."""
    stated = {"Moon": {"lon": 125.0, "bhava": 5},        # Leo (sign), not 5th-house dependent
              "Sun": {"lon": 215.0, "bhava": 8}, "Saturn": {"lon": 220.0, "bhava": 8},  # Scorpio = 8th
              "Venus": {"lon": 40.0, "bhava": 2}}          # Taurus = 2nd
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")   # Aries Lagna
    assert "the Moon in Leo with the Sun and Saturn in the 8th and Venus in the 2nd" in _descs(ch)


def test_alpayu_lord1_lord8_planet8_aspected_by_malefic():
    """HTJAH-II:3289 — exercises lord-of-house + the malefic-aspect-on-8th-occupant clause."""
    stated = {"Venus": {"lon": 40.0, "bhava": 1},        # Taurus-Lagna lord in the 1st
              "Jupiter": {"lon": 275.0, "bhava": 9},      # 8th lord (Sag) sitting in the 9th
              "Sun": {"lon": 245.0, "bhava": 8},          # a planet in the 8th (Sagittarius)
              "Saturn": {"lon": 65.0, "bhava": 2}}        # Gemini — 7th-aspects the 8th, hitting the Sun
    ch = RamanChart.from_stated_positions(stated, asc_lon=35.0, ayanamsa="raman")  # Taurus Lagna
    assert ("the Lagna lord in the Lagna, the 8th lord in the 9th and a planet in the 8th aspected by a malefic"
            in _descs(ch))


def test_purnayu_tenth_lord_exalted_malefic_eighth():
    """HTJAH-II:3422 — 10th lord exalted (dignity) + a malefic in the 8th."""
    stated = {"Saturn": {"lon": 195.0, "bhava": 7},      # Aries-Lagna 10th lord, exalted in Libra
              "Mars": {"lon": 215.0, "bhava": 8}}          # malefic in the 8th (Scorpio)
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")   # Aries Lagna
    assert "the 10th lord exalted and malefics in the 8th" in _descs(ch)


def test_purnayu_lord1_kendra_supported_by_venus_and_jupiter():
    """HTJAH-II:3429 — Lagna lord in a kendra, joined by Venus AND aspected by Jupiter."""
    stated = {"Mars": {"lon": 95.0, "bhava": 4},         # Aries-Lagna lord in Cancer (4th, a kendra)
              "Venus": {"lon": 100.0, "bhava": 4},        # conjoins the lord
              "Jupiter": {"lon": 275.0, "bhava": 10}}      # Capricorn — 7th-aspects the lord in Cancer
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")   # Aries Lagna
    assert "the Lagna lord in a kendra, joined or aspected by both Venus and Jupiter" in _descs(ch)


def test_purnayu_keeta_lagna_jupiter_benefics_5_9():
    """HTJAH-II:3448 — benefics in 5th & 9th, Keeta-rasi (Cancer) Lagna with Jupiter in it."""
    stated = {"Jupiter": {"lon": 100.0, "bhava": 1},     # Cancer (Keeta) Lagna, Jupiter in 1st
              "Venus": {"lon": 215.0, "bhava": 5},        # Scorpio = 5th from Cancer
              "Mercury": {"lon": 335.0, "bhava": 9}}       # Pisces = 9th from Cancer
    ch = RamanChart.from_stated_positions(stated, asc_lon=95.0, ayanamsa="raman")  # Cancer Lagna (Keeta)
    assert "benefics in the 5th and 9th with a Keeta-rasi Lagna occupied by Jupiter" in _descs(ch)


def _a3303_chart(moon_lon: float):
    """Saturn in Leo Lagna (enemy of Sun-ruled Leo), all 4 benefics in apoklimas {3,6,9,12}.
    `moon_lon` lets a test put the Moon in/out of an apoklima."""
    stated = {"Saturn": {"lon": 130.0, "bhava": 1}, "Sun": {"lon": 135.0, "bhava": 1},  # Leo
              "Jupiter": {"lon": 195.0, "bhava": 3},      # Libra = 3rd
              "Venus": {"lon": 275.0, "bhava": 6},        # Capricorn = 6th
              "Mercury": {"lon": 10.0, "bhava": 9},       # Aries = 9th
              "Moon": {"lon": moon_lon, "bhava": 12}}
    return RamanChart.from_stated_positions(stated, asc_lon=125.0, ayanamsa="raman")  # Leo Lagna


def test_alpayu_saturn_lagna_enemy_benefics_apoklima_fires():
    """HTJAH-II:3303 — fires when EVERY benefic (incl. the Moon) sits in {3,6,9,12}."""
    ch = _a3303_chart(moon_lon=95.0)  # Moon in Cancer = 12th (an apoklima)
    assert "Saturn in the Lagna in an inimical sign and the benefics in the 3rd, 6th, 9th or 12th" in _descs(ch)


def test_alpayu_saturn_lagna_combo_requires_moon_in_apoklima():
    """HTJAH-II:3303 (the doctrine-panel fix) — a well-placed Moon (kendra) must BLOCK the combo:
    'benefics' includes the Moon per the project's locked benefic set."""
    ch = _a3303_chart(moon_lon=128.0)  # Moon in Leo = 1st (a kendra), NOT an apoklima
    assert "Saturn in the Lagna in an inimical sign and the benefics in the 3rd, 6th, 9th or 12th" not in _descs(ch)


def test_aggregate_benefics_in_kendras_gives_purnayu():
    """HTJAH-II:3469 — Lagna lord + all benefics in kendras => long life."""
    stated = {p: {"lon": lon, "bhava": 1} for p, lon in
              (("Mars", 5.0), ("Jupiter", 10.0), ("Venus", 15.0), ("Mercury", 20.0), ("Moon", 25.0))}
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")  # Aries Lagna
    fired = {desc: cls for cls, _span, desc in lc.fired(ch)}
    assert fired.get("the Lagna lord and all benefics in kendras") == "Purnayu"


def test_aggregate_malefics_in_kendras_gives_alpayu_reversed():
    """HTJAH-II:3472 — the REVERSED mapping: 8th lord + all malefics in kendras => SHORT life."""
    stated = {"Mars": {"lon": 5.0, "bhava": 1}, "Sun": {"lon": 10.0, "bhava": 1},
              "Ketu": {"lon": 8.0, "bhava": 1}, "Saturn": {"lon": 95.0, "bhava": 4},  # Cancer = 4th
              "Rahu": {"lon": 185.0, "bhava": 7}}          # Libra = 7th
    ch = RamanChart.from_stated_positions(stated, asc_lon=5.0, ayanamsa="raman")  # Aries Lagna
    fired = {desc: cls for cls, _span, desc in lc.fired(ch)}
    assert fired.get("the 8th lord and all malefics in kendras") == "Alpayu"


def test_fired_shape_and_classes():
    out = lc.fired(cast_chart(_MAINPURI, ayanamsa="raman"))
    for cls, span, desc in out:
        assert cls in ("Alpayu", "Madhyayu", "Purnayu") and span and desc
