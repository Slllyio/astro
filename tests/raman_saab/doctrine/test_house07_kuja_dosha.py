"""H7 Kuja-Dosha (Mangal-Dosha) exemption logic (HTJAH-II:2583-2601).

Pins the corpus exemptions the doctrine reviewer flagged: the single-chart Mars
dosha must NOT fire on the per-sign-exempt placements (e.g. Mars-in-7th-Capricorn)
nor on the wholly-exempt Leo/Aquarius Mars, and is neutralised by a Mars+Jupiter
or Mars+Moon conjunction. Each test states the astronomical fact being verified.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets.house_07_kalatra import combinations as cm


def _chart(lons: dict[str, float], asc_lon: float) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


def _fires(chart: RamanChart) -> bool:
    return cm._KujaDosha().evaluate(C.EvalContext(chart))


def test_mars_in_7th_non_exempt_sign_fires():
    """Aries Lagna, Mars in the 7th (Libra) — a dosha house in a non-exempt sign → dosha."""
    assert _fires(_chart({"Mars": 185.0}, 5.0)) is True


def test_mars_in_7th_capricorn_is_exempt():
    """Cancer Lagna, Mars in the 7th = Capricorn — HTJAH-II:2597 exempts the 7th in Cn/Cp."""
    assert _fires(_chart({"Mars": 285.0}, 100.0)) is False


def test_mars_in_leo_is_wholly_exempt():
    """Mars in Leo produces no dosha whatever (HTJAH-II:2599-2600), in any house."""
    assert _fires(_chart({"Mars": 130.0}, 5.0)) is False


def test_mars_jupiter_conjunction_neutralises():
    """Mars+Jupiter conjunction neutralises the dosha (HTJAH-II:2600-2601)."""
    assert _fires(_chart({"Mars": 185.0, "Jupiter": 186.0}, 5.0)) is False


def test_mars_moon_conjunction_neutralises():
    """Mars+Moon conjunction neutralises the dosha (HTJAH-II:2600-2601)."""
    assert _fires(_chart({"Mars": 185.0, "Moon": 184.0}, 5.0)) is False
