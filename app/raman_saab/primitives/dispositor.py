from __future__ import annotations
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.chart.constants import SIGN_LORDS


def dispositor(planet: str, chart: RamanChart) -> str:
    """Lord of the rasi sign occupied by `planet`."""
    return SIGN_LORDS[chart.planets[planet].sign]


def dispositor_chain(planet: str, chart: RamanChart, *, max_hops: int = 12) -> list[str]:
    """Follow lord-of-occupied-sign until a planet in its OWN sign (or a cycle/limit).

    Returns the sequence of lords visited, ending at the first planet that occupies
    its own sign (that planet IS included in the chain).
    """
    chain: list[str] = []
    cur = planet
    seen: set[str] = {planet}
    for _ in range(max_hops):
        lord = dispositor(cur, chart)
        if lord in ("Rahu", "Ketu") or lord not in chart.planets:
            break
        chain.append(lord)
        if SIGN_LORDS[chart.planets[lord].sign] == lord:   # lord in own sign -> terminus
            break
        if lord in seen:                                   # cycle guard
            break
        seen.add(lord)
        cur = lord
    return chain


def navamsa_lord_of(planet: str, chart: RamanChart) -> str:
    """Lord of the D9 (navamsa) sign of `planet`."""
    return SIGN_LORDS[chart.planets[planet].navamsa_sign]


def drekkana_lord_of(planet: str, chart: RamanChart) -> str:
    """Lord of the D3 (drekkana) sign of `planet`."""
    lon = chart.planets[planet].lon
    sign_idx = int(lon // 30)
    drek = int((lon % 30) // 10)                   # 0, 1, 2
    d3_sign = ((sign_idx + drek * 4) % 12) + 1    # classical: +0/+4/+8 signs
    return SIGN_LORDS[d3_sign]
