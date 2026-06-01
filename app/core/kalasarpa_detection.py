"""Kalasarpa Dosha detection — strict arc-membership rule (round-8 helper).

Kalasarpa is active when ALL SEVEN visible planets (Sun, Moon, Mars,
Mercury, Jupiter, Venus, Saturn) lie within the 180-degree arc bounded
by Rahu and Ketu — i.e. they are all on the same hemicycle of the
node-axis. If even one visible planet lies in the opposite hemicycle,
the dosha is said to be "broken" and Kalasarpa is inactive — this is
the doctrinal negation case repeatedly emphasised by KN Rao.

Twelve named variants are recognised, keyed on the natal house in which
Rahu sits (BPHS commentary tradition, modern Sanjay Rath synthesis):

  Rahu in 1H  -> Anant      (eternal, gain through endurance)
  Rahu in 2H  -> Kulika     (poison-tongue, financial volatility)
  Rahu in 3H  -> Vasuki     (sibling karma, courageous mission)
  Rahu in 4H  -> Shankhapal (heart-home wound, hidden anchor)
  Rahu in 5H  -> Padma      (lotus, intellect through purification)
  Rahu in 6H  -> Mahapadma  (great lotus, victory through service)
  Rahu in 7H  -> Takshaka   (the cutter, marriage karma)
  Rahu in 8H  -> Karkotaka  (deep transformation, occult)
  Rahu in 9H  -> Shankhachuda (guru-karma, dharma trial)
  Rahu in 10H -> Ghatak     (slayer of obstacles in career)
  Rahu in 11H -> Vishadhar  (poison-bearer, network volatility)
  Rahu in 12H -> Sheshnag   (cosmic serpent, moksha vehicle)

Doctrine notes:
  - Uses sidereal longitudes (Lahiri per CLAUDE.md lock).
  - Arc membership measured via circular forward distance from Rahu
    (``(p_lon - rahu_lon) % 360``); a planet is "inside" the Rahu->Ketu
    arc when 0 < forward_distance < 180.
  - A planet exactly on the node-axis (forward distance ~0 or ~180) is
    treated as straddling and does NOT count as inside — Kalasarpa
    requires all 7 strictly within the arc.

Usage:
    from app.core.kalasarpa_detection import detect_kalasarpa
    result = detect_kalasarpa(chart)
    if result.active:
        print(result.kalasarpa_type)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

from app.core.chart_model import Chart

logger = logging.getLogger(__name__)


_VISIBLE_SEVEN: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


_TYPE_BY_RAHU_HOUSE: Final[dict[int, str]] = {
    1: "Anant",
    2: "Kulika",
    3: "Vasuki",
    4: "Shankhapal",
    5: "Padma",
    6: "Mahapadma",
    7: "Takshaka",
    8: "Karkotaka",
    9: "Shankhachuda",
    10: "Ghatak",
    11: "Vishadhar",
    12: "Sheshnag",
}


@dataclass(frozen=True)
class KalasarpaResult:
    """Kalasarpa detection verdict + supporting evidence.

    Attributes:
        active: True iff all 7 visible planets are inside the Rahu->Ketu
            arc (strict arc membership). False if even one planet lies
            outside — including the case where a planet is on the axis.
        kalasarpa_type: One of the 12 classical names (e.g. "Anant",
            "Takshaka") when ``active`` is True; "None" otherwise.
        planets_on_one_side: True iff all 7 visibles share the same
            hemicycle (== ``active``); preserved for downstream callers
            that want the boolean separately from the named type.
        all_planets_signs: Tuple of (planet, sign) pairs for all 7
            visibles, in canonical order. Useful for debugging.
        rahu_sign: Sign hosting Rahu (1..12).
        ketu_sign: Sign hosting Ketu (1..12).
        outside_planets: Tuple of planets that broke the dosha (sit
            outside the Rahu->Ketu arc OR on the axis). Empty when active.
    """
    active: bool
    kalasarpa_type: str
    planets_on_one_side: bool
    all_planets_signs: tuple[tuple[str, int], ...]
    rahu_sign: int
    ketu_sign: int
    outside_planets: tuple[str, ...]


def _forward_arc(from_lon: float, to_lon: float) -> float:
    """Circular forward distance from ``from_lon`` to ``to_lon`` (0..360)."""
    return (to_lon - from_lon) % 360.0


def detect_kalasarpa(chart: Chart) -> KalasarpaResult:
    """Detect Kalasarpa dosha by strict arc membership.

    Algorithm:
      1. Take Rahu's longitude. Ketu is implicitly at Rahu + 180.
      2. For each of the 7 visible planets, compute the forward arc
         from Rahu to the planet (mod 360).
      3. The Rahu->Ketu hemicycle is the arc (0, 180). The Ketu->Rahu
         hemicycle is the arc (180, 360).
      4. If all 7 planets fall strictly in EITHER hemicycle (same one),
         Kalasarpa is active. The variant name is keyed on Rahu's
         natal house.
      5. If even one planet lies in the opposite half OR sits exactly
         on the axis (forward distance ~0 or ~180), Kalasarpa is broken.

    Args:
        chart: A populated ``Chart``. Requires Rahu's longitude/house
            and all 7 visibles' longitudes/signs.

    Returns:
        ``KalasarpaResult`` with the active verdict, named type, and
        debug fields enumerating which planets broke the dosha.
    """
    rahu_lon = chart.planet_lons.get("Rahu")
    rahu_sign = chart.sign_of("Rahu")
    rahu_house = chart.house_of("Rahu")
    ketu_sign = chart.sign_of("Ketu")
    if rahu_lon is None or rahu_sign is None or rahu_house is None:
        raise ValueError("chart missing Rahu longitude/sign/house")
    if ketu_sign is None:
        # Derive Ketu sign from Rahu sign if missing.
        ketu_sign = ((rahu_sign + 6 - 1) % 12) + 1

    # Tolerance for "on-axis" — 0.01 deg is well below ephemeris noise
    # but tight enough to never mis-classify a real planet.
    on_axis_eps = 0.01

    first_half: list[str] = []      # 0 < arc < 180  (Rahu -> Ketu hemicycle)
    second_half: list[str] = []     # 180 < arc < 360 (Ketu -> Rahu hemicycle)
    on_axis: list[str] = []
    all_signs: list[tuple[str, int]] = []

    for p in _VISIBLE_SEVEN:
        p_lon = chart.planet_lons.get(p)
        p_sign = chart.sign_of(p)
        if p_lon is None or p_sign is None:
            raise ValueError(f"chart missing position for visible planet {p}")
        all_signs.append((p, p_sign))
        arc = _forward_arc(rahu_lon, p_lon)
        if arc < on_axis_eps or abs(arc - 180.0) < on_axis_eps or arc > (360.0 - on_axis_eps):
            on_axis.append(p)
        elif arc < 180.0:
            first_half.append(p)
        else:
            second_half.append(p)

    # Dosha requires no axis-sitters AND all 7 in the same hemicycle.
    all_in_first = (len(first_half) == 7 and not second_half and not on_axis)
    all_in_second = (len(second_half) == 7 and not first_half and not on_axis)
    active = all_in_first or all_in_second
    if active:
        kalasarpa_type = _TYPE_BY_RAHU_HOUSE.get(rahu_house, "Unknown")
        outside: tuple[str, ...] = ()
    else:
        kalasarpa_type = "None"
        # "Outside" = the minority hemicycle + on-axis sitters.
        if len(first_half) >= len(second_half):
            outside = tuple(second_half) + tuple(on_axis)
        else:
            outside = tuple(first_half) + tuple(on_axis)

    logger.debug(
        "Kalasarpa: rahu_lon=%.2f first=%s second=%s axis=%s active=%s type=%s",
        rahu_lon, first_half, second_half, on_axis, active, kalasarpa_type,
    )
    return KalasarpaResult(
        active=active,
        kalasarpa_type=kalasarpa_type,
        planets_on_one_side=active,
        all_planets_signs=tuple(all_signs),
        rahu_sign=rahu_sign,
        ketu_sign=ketu_sign,
        outside_planets=outside,
    )
