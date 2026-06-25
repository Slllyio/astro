"""H7.C.85 — decisive coverture rule (vaidhavya: Mars-in-8th + debilitated 7th lord).

Mars (the natural maraka) in the 8th (the spouse's death house) AND the 7th lord
debilitated-without-cancellation, no full-benefic relief on the 8th -> death of the
married partner (HTJAH-II:298-305; Chart 22/h7_10). The Mars-in-8th sibling of
H7.C.84. Pins the fire + the boundary negatives. Each test states the fact verified.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.rule_sets.house_07_kalatra import combinations as cm

_RULE = {r.id: r for r in cm.RULES}["H7.C.85"]


def _chart(lons: dict[str, float], asc_lon: float) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


# Aquarius Lagna (asc ~305) -> 7th lord = Sun. Sun debilitated in Libra (~200) sits in the
# 9th. 8th house = Virgo (~150-180). A minimal chart (no dispositor present) leaves the
# debilitation un-cancelled (neecha_bhanga False).
_ASC_AQ = 305.0
_SUN_DEBIL = 200.0   # Libra = Sun's debilitation sign
_MARS_8TH = 165.0    # Virgo = the 8th house from Aquarius


def test_h7c85_fires_mars8_with_debil_lord():
    """Mars in the 8th + 7th lord Sun debilitated (un-cancelled), no benefic relief ->
    fires (the Chart 22/h7_10 vaidhavya signature)."""
    chart = _chart({"Mars": _MARS_8TH, "Sun": _SUN_DEBIL}, _ASC_AQ)
    assert _RULE.fires(chart) is True


def test_h7c85_silent_when_lord_not_debilitated():
    """Mars in the 8th but the 7th lord Sun in own sign Leo (not debilitated) ->
    does not fire (the powerless-mangalya leg is required)."""
    chart = _chart({"Mars": _MARS_8TH, "Sun": 130.0}, _ASC_AQ)  # Sun in Leo (own)
    assert _RULE.fires(chart) is False


def test_h7c85_silent_when_mars_not_in_8th():
    """7th lord Sun debilitated but Mars in the 7th (Leo), not the 8th -> does not fire."""
    chart = _chart({"Mars": 130.0, "Sun": _SUN_DEBIL}, _ASC_AQ)  # Mars in Leo = 7th
    assert _RULE.fires(chart) is False


def test_h7c85_silent_with_full_benefic_relief_on_8th():
    """Mars in the 8th + debilitated 7th lord, BUT Jupiter (a full benefic) also in the
    8th -> the sowbhagya relief guard spares it -> does not fire."""
    chart = _chart({"Mars": _MARS_8TH, "Sun": _SUN_DEBIL, "Jupiter": 160.0}, _ASC_AQ)
    assert _RULE.fires(chart) is False
