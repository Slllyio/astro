"""H3.C.40 — decisive ear-affliction rule (HTJAH-I:3722, Chart 56).

Saturn aspecting the 3rd AND the 3rd lord debilitated in a dusthana -> partial
deafness (decisive). Pins the conjunction + the three boundary negatives so the
narrow gate that keeps it off favourable ear charts (54/60) can't loosen. Each
test states the astronomical fact being verified.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets.house_03_sahaja import combinations as cm

_RULE = {r.id: r for r in cm.RULES}["H3.C.40"]


def _chart(lons: dict[str, float], asc_lon: float) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


# Aquarius Lagna (asc ~305) -> 3rd house = Aries, 3rd lord = Mars.
#   Mars in Cancer (~100) = DEBILITATED and in the 6th house (a dusthana).
#   Saturn in Libra (~185) = the 9th house, whose 7th aspect falls on the 3rd.
_ASC_AQ = 305.0
_MARS_DEBIL_6TH = 100.0   # Cancer
_SATURN_9TH = 185.0       # Libra (aspects the 3rd)


def test_h3c40_fires_on_saturn_aspect_plus_debil_lord_in_dusthana():
    """Saturn aspects the 3rd + 3rd lord (Mars) debilitated in the 6th -> fires
    (the Chart 56 deafness signature, HTJAH-I:3722)."""
    chart = _chart({"Mars": _MARS_DEBIL_6TH, "Saturn": _SATURN_9TH}, _ASC_AQ)
    assert _RULE.fires(chart) is True


def test_h3c40_silent_without_saturn_aspect():
    """Same debilitated 3rd lord but Saturn NOT aspecting the 3rd (Saturn in the
    2nd, aspecting 4/8/11 — not the 3rd) -> does not fire."""
    chart = _chart({"Mars": _MARS_DEBIL_6TH, "Saturn": 345.0}, _ASC_AQ)  # Pisces = 2nd
    assert _RULE.fires(chart) is False


def test_h3c40_silent_when_lord_not_debilitated():
    """3rd lord Mars in own sign Scorpio (8th house, a dusthana) — in a dusthana
    but NOT debilitated -> does not fire (the debilitation leg is required)."""
    chart = _chart({"Mars": 220.0, "Saturn": _SATURN_9TH}, _ASC_AQ)  # Scorpio = 8th
    assert _RULE.fires(chart) is False


def test_h3c40_silent_when_lord_not_in_dusthana():
    """Capricorn Lagna (asc ~275) -> 3rd house Pisces, 3rd lord Jupiter. Jupiter
    debilitated in Capricorn sits in the 1st (a kendra, NOT a dusthana), with
    Saturn in Virgo (the 9th) aspecting the 3rd -> a debilitated lord and a
    Saturn aspect, but the lord is not in a 6/8/12, so the rule does not fire."""
    chart = _chart({"Jupiter": 278.0, "Saturn": 155.0}, 275.0)  # Cap Lagna; Jup in 1st
    assert _RULE.fires(chart) is False
