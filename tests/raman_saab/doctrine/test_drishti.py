"""Raman drishti: whole-sign aspects; special aspects Mars 4/8, Jupiter 5/9,
Saturn 3/10; Rahu/Ketu 7th-ONLY (the Raman Saab divergence)."""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import drishti


def _c(lons: dict[str, float]) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()}, asc_lon=0.0, ayanamsa="raman")


def test_seventh_aspect_for_all():
    # Aries lagna: Sun in 1st (Aries), Moon in 7th (Libra). Each aspects the other (7th).
    c = _c({"Sun": 5.0, "Moon": 185.0})
    assert drishti.aspects_planet("Sun", "Moon", c) is True
    assert drishti.aspects_planet("Moon", "Sun", c) is True
    assert drishti.mutual_aspect("Sun", "Moon", c) is True


def test_mars_special_4_8():
    # Mars in 1st (Aries) aspects the 4th (Cancer) and 8th (Scorpio), not the 5th.
    c = _c({"Mars": 5.0, "Venus": 100.0, "Saturn": 220.0, "Jupiter": 130.0})  # 4th, 8th, 5th
    assert drishti.aspects_planet("Mars", "Venus", c) is True    # 4th
    assert drishti.aspects_planet("Mars", "Saturn", c) is True   # 8th
    assert drishti.aspects_planet("Mars", "Jupiter", c) is False # 5th — Mars does NOT aspect


def test_jupiter_5_9_and_saturn_3_10():
    c = _c({"Jupiter": 5.0, "Sun": 130.0, "Moon": 250.0})  # Jupiter 1st; 5th(Leo), 9th(Sag)
    assert drishti.aspects_planet("Jupiter", "Sun", c) is True    # 5th
    assert drishti.aspects_planet("Jupiter", "Moon", c) is True   # 9th
    c2 = _c({"Saturn": 5.0, "Mars": 65.0, "Venus": 275.0})  # Saturn 1st; 3rd(Gem), 10th(Cap)
    assert drishti.aspects_planet("Saturn", "Mars", c2) is True   # 3rd
    assert drishti.aspects_planet("Saturn", "Venus", c2) is True  # 10th


def test_nodes_cast_only_the_seventh_NOT_5_9():
    # THE DIVERGENCE: Rahu aspects only the 7th — never the 5th or 9th.
    c = _c({"Rahu": 5.0, "Sun": 130.0, "Moon": 250.0, "Mars": 185.0})  # 5th, 9th, 7th
    assert drishti.aspects_planet("Rahu", "Mars", c) is True     # 7th — yes
    assert drishti.aspects_planet("Rahu", "Sun", c) is False     # 5th — NO (not Jupiter-style)
    assert drishti.aspects_planet("Rahu", "Moon", c) is False    # 9th — NO
    assert drishti.ASPECT_HOUSES["Rahu"] == frozenset({7})
    assert drishti.ASPECT_HOUSES["Ketu"] == frozenset({7})


def test_aspecting_planets_and_house():
    c = _c({"Sun": 5.0, "Saturn": 185.0})  # Saturn in 7th aspects the 1st (Sun)
    assert "Saturn" in drishti.aspecting_planets("Sun", c)
    assert "Saturn" in drishti.aspecting_house(1, c)
