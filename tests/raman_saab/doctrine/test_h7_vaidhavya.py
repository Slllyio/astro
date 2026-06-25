"""H7.C.84 — decisive coverture rule (vaidhavya: 7th lord in the 8th).

The 7th lord cast into the 8th (the spouse's maraka / death house), aggravated by a
node conjoining it OR Saturn's aspect, with no full-benefic relief on the 8th ->
death of the married partner (HTJAH-II:298-305; Chart 21/h7_09). Pins the fire +
the three boundary negatives (no aggravator, full-benefic relief, lord-not-in-8th).
Each test states the astronomical fact verified.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets.house_07_kalatra import combinations as cm

_RULE = {r.id: r for r in cm.RULES}["H7.C.84"]


def _chart(lons: dict[str, float], asc_lon: float) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


# Aquarius Lagna (asc ~305) -> 7th house Leo, 7th lord = Sun (a malefic, so it does not
# trip the full-benefic relief guard). 8th house = Virgo (~150-180).
_ASC_AQ = 305.0
_SUN_8TH = 165.0     # Virgo = the 8th house
_NODE_8TH = 168.0    # Rahu in Virgo, conjoining the 7th lord


def test_h7c84_fires_lord_in_8th_with_node():
    """7th lord Sun in the 8th conjoined by Rahu, no benefic relief -> fires
    (the vaidhavya signature; Chart 21/h7_09 idiom)."""
    chart = _chart({"Sun": _SUN_8TH, "Rahu": _NODE_8TH}, _ASC_AQ)
    assert _RULE.fires(chart) is True


def test_h7c84_silent_without_aggravator():
    """7th lord Sun in the 8th but NO node conjoining and NO Saturn aspect (Saturn in
    the 5th aspects the 7th/11th/2nd, not the 8th) -> does not fire (bare lord-in-8th
    is survivable; the aggravator is required)."""
    chart = _chart({"Sun": _SUN_8TH, "Saturn": 75.0}, _ASC_AQ)  # Saturn in Gemini (5th)
    assert _RULE.fires(chart) is False


def test_h7c84_silent_with_full_benefic_relief_on_8th():
    """7th lord Sun in the 8th + Rahu, BUT Jupiter (a full benefic) also in the 8th ->
    the sowbhagya relief guard spares it (HTJAH-II:961) -> does not fire."""
    chart = _chart({"Sun": _SUN_8TH, "Rahu": _NODE_8TH, "Jupiter": 160.0}, _ASC_AQ)
    assert _RULE.fires(chart) is False


def test_h7c84_silent_when_lord_not_in_8th():
    """7th lord Sun in the 9th (Libra), not the 8th, with Rahu -> does not fire."""
    chart = _chart({"Sun": 200.0, "Rahu": 205.0}, _ASC_AQ)  # Sun in Libra = 9th
    assert _RULE.fires(chart) is False
