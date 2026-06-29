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


#: HTJAH-II:10340-10800 — the profession profile of the 10th SIGN (when the 10th/sign is strong).
CAREER_BY_SIGN: Final[dict[int, str]] = {
    1:  "military, police, surgery (esp. brain), engineering, metals & fire-trades, sport, leadership",
    2:  "banking & finance, jewellery & luxury goods, agriculture, music & voice, throat specialists",
    3:  "writing, journalism, communications, accountancy, languages, trade, teaching",
    4:  "nursing & caregiving, hospitality & food, shipping, real estate, public dealings, liquids",
    5:  "government & administration, politics, authority, gold & jewels, the stage & entertainment",
    6:  "accountancy & analysis, medicine, editing & language, research, service, statistics",
    7:  "law, the fine arts, fashion & design, diplomacy, trade & partnerships, beauty",
    8:  "surgery, investigation & research, military, chemicals, insurance, the occult",
    9:  "law, teaching & religion, philosophy, banking & advisory, travel, horses",
    10: "administration & government, mining, construction, labour & management, contracting",
    11: "science & technology, research & invention, social work, astrology, electrical work",
    12: "medicine & healing, charity, the arts, spirituality, shipping & liquids, imagination",
}


def tenth_sign(chart: RamanChart) -> int:
    """The 10th sign (1..12) from the Lagna."""
    return ((chart.asc_sign - 1) + 9) % 12 + 1


def tenth_lord(chart: RamanChart) -> str:
    """Lord of the 10th sign from the Lagna."""
    return SIGN_LORDS[tenth_sign(chart)]


def tenth_sign_career(chart: RamanChart) -> str:
    """The profession profile of the 10th sign (HTJAH-II career-by-sign catalogue)."""
    return CAREER_BY_SIGN[tenth_sign(chart)]


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
