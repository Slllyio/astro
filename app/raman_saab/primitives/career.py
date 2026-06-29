"""Career / profession reading via the navamsa-dispositor of the 10th lord.

Raman's systematic profession indicator (How to Judge a Horoscope Vol II, HTJAH-II:10249-10274):
"the lord of the Navamsa occupied by the 10th lord" names the native's line of work. This both
closes the navamsa-dispositor-routing gap (the predicate "read the matter from the lord's navamsa
dispositor") and gives the H10 trade catalogue. ADDITIVE / reported, parallel to the Parashari H10
verdict — it does not alter it.

Usage:
    from app.raman_saab.primitives import career
    career.career_indication(chart)   # -> (tenth_lord, navamsa_dispositor, trade) or None
"""
from __future__ import annotations

from typing import Final, Optional

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.dispositor import navamsa_lord_of

#: HTJAH-II:10249-10274 — navamsa-dispositor of the 10th lord -> the native's profession.
TRADE_BY_NAVAMSA_DISPOSITOR: Final[dict[str, str]] = {
    "Sun":     "medicine, gold, wool/grain, diplomacy, mediation, arbitration",
    "Moon":    "ships, pearls & sea-products, agriculture, horticulture, women & clothes, humour",
    "Mars":    "metals, minerals, buildings, fire-trades, military, surgery/chemists, driving",
    "Mercury": "mathematics, writing, poetry, art & sculpture, journalism, astrology, priestcraft",
    "Jupiter": "judge, teacher, counsellor, lawyer, banker, minister, preacher",
    "Venus":   "gold & gems, textiles & apparel, perfumes, conveyances, hoteliering, show-business",
    "Saturn":  "labour & crafts, tilling/mining, factory work, jailoring, shoe-making, humble trades",
}


def tenth_lord(chart: RamanChart) -> str:
    """Lord of the 10th sign from the Lagna."""
    tenth_sign = ((chart.asc_sign - 1) + 9) % 12 + 1
    return SIGN_LORDS[tenth_sign]


def career_indication(chart: RamanChart) -> Optional[tuple[str, str, str]]:
    """(10th-lord, its navamsa-dispositor, the trade) — or None if the 10th lord is absent (sparse
    chart) or the dispositor is a node (no profession entry)."""
    lord = tenth_lord(chart)
    if lord not in chart.planets:
        return None
    nav_disp = navamsa_lord_of(lord, chart)         # ruler of the navamsa the 10th lord occupies
    trade = TRADE_BY_NAVAMSA_DISPOSITOR.get(nav_disp)
    if trade is None:
        return None
    return (lord, nav_disp, trade)
