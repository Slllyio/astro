"""Brahma Graha determination — the seed of the Sthira dasha (BPHS ch.46, slokas 170-173).

This is the integration the Shadbala primitive unlocks: Sthira's starting rasi is the sign occupied
by the Brahma Graha, whose selection Parashara resolves partly by STRENGTH — which the engine now
has (partial Shadbala). So `sthira_for_chart` can finally run Sthira end-to-end from a chart.

Procedure (following Santhanam's step-by-step Notes at BPHS-46:170-173, which close the primary
sloka's rules):
  1. If the 8th lord occupies the 8th house -> it is the Brahma Graha.
  2. Else, among planets occupying the 8th house -> the one with the most degrees (ties: strength).
  3. Else (no planet in the 8th), among planets in ODD signs -> most degrees (ties: strength).
     ("in an odd sign within 6 houses of the Ascendant or the 7th" spans all houses between the two
      references, so it reduces to the odd-sign condition.)
  4. Fallback: the strongest among the lords of the 6th/8th/12th (the primary sloka's emphasis).

Strength is the partial Shadbala (Sthana+Dig+Naisargika+Kala:Paksha). Degrees use degree-within-sign
(Rahu/Ketu reversed, 30 - deg, per the nodes' retrograde reckoning the sloka begins to state).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.parashara.chart.cast import ParasharaChart
from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import SIGN_LORDS
from app.parashara.primitives.shadbala.total import partial_shadbala

SOURCE: Final[Citation] = Citation("BPHS-46", 4873)
_NODES = ("Rahu", "Ketu")


@dataclass(frozen=True)
class BrahmaGraha:
    planet: str
    sign: int           # 1..12 — the Sthira starting rasi
    reason: str


def _sign_of(lon: float) -> int:
    return int(lon % 360.0 // 30) + 1


def _house_of(sign: int, asc_sign: int) -> int:
    return ((sign - asc_sign) % 12) + 1


def _degrees_advanced(planet: str, lon: float) -> float:
    """Degrees traversed in the current sign; reversed for the nodes (they move retrograde)."""
    deg = lon % 30.0
    return (30.0 - deg) if planet in _NODES else deg


def _strength(planet: str, chart: ParasharaChart) -> float:
    """Partial-Shadbala virupas; nodes have no Shadbala, so they rank 0 on the strength tie-break."""
    if planet in _NODES:
        return 0.0
    return partial_shadbala(planet, chart.longitudes, asc_sign=chart.asc_sign,
                            asc_longitude=chart.asc_longitude, moon_waxing=chart.moon_waxing,
                            speed=chart.speeds.get(planet, 0.0), ayanamsa=chart.ayanamsa).virupas


def _pick(candidates: list[str], chart: ParasharaChart) -> str:
    """The candidate with the most degrees; ties broken by strength."""
    return max(candidates,
               key=lambda p: (_degrees_advanced(p, chart.longitudes[p]), _strength(p, chart)))


def brahma_graha(chart: ParasharaChart) -> BrahmaGraha:
    """Select the Brahma Graha for a chart (BPHS-46:170-173)."""
    eighth_sign = ((chart.asc_sign - 1 + 7) % 12) + 1
    eighth_lord = SIGN_LORDS[eighth_sign]

    # 1. 8th lord in the 8th.
    if eighth_lord in chart.longitudes and _sign_of(chart.longitudes[eighth_lord]) == eighth_sign:
        return BrahmaGraha(eighth_lord, eighth_sign, "the 8th lord occupies the 8th house")

    # 2. planets occupying the 8th house.
    in_eighth = [p for p, l in chart.longitudes.items() if _sign_of(l) == eighth_sign]
    if in_eighth:
        p = _pick(in_eighth, chart)
        return BrahmaGraha(p, _sign_of(chart.longitudes[p]),
                           "strongest/most-advanced planet in the 8th house")

    # 3. planets in odd signs.
    odd = [p for p, l in chart.longitudes.items() if _sign_of(l) % 2 == 1]
    if odd:
        p = _pick(odd, chart)
        return BrahmaGraha(p, _sign_of(chart.longitudes[p]),
                           "most-advanced planet in an odd sign")

    # 4. fallback: strongest of the 6/8/12 lords.
    dusthana_lords = {SIGN_LORDS[((chart.asc_sign - 1 + h - 1) % 12) + 1] for h in (6, 8, 12)}
    present = [p for p in dusthana_lords if p in chart.longitudes]
    p = max(present, key=lambda q: _strength(q, chart))
    return BrahmaGraha(p, _sign_of(chart.longitudes[p]),
                       "strongest of the 6th/8th/12th lords (fallback)")


def sthira_for_chart(chart: ParasharaChart):
    """The Sthira dasha timeline for a chart, seeded by its Brahma Graha (end-to-end)."""
    from app.parashara.primitives.sthira_dasha import sthira_timeline
    return sthira_timeline(brahma_graha(chart).sign)
