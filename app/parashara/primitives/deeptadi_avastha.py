"""Deeptadi avasthas — a planet's dignity/placement state (BPHS ch.45, sl.8-10).

    "If a planet is in its exaltation sign it is in Deeptavastha, in own sign Swastha, in [a great]
     friend's sign Pramudita, in a friendly sign Santa, in a neutral's sign Deena, in the company of
     a malefic Vikala, in an enemy's sign Khala, and in being eclipsed by the Sun — Kopa. Depending
     on such a state ... the house occupied by it will obtain corresponding effects." (BPHS-45:113)

Six of these are mutually exclusive (a planet has one relationship to its sign's lord): exaltation ->
Deepta, own -> Swastha, great-friend -> Pramudita, friend -> Santa, neutral -> Deena, enemy -> Khala.
The other two are additional conditions that can co-occur with any of the six: a malefic sharing the
sign (Vikala) and combustion (Kopa). So this returns the dignity state PLUS those two flags, rather
than forcing an unstated precedence — faithful to the text listing eight conditions, not one ladder.

The third avastha layer, alongside Baladi (age-state by degree) and Jagradadi (awake/dreaming/
sleeping by dignity).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping, Optional

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.combustion import is_combust
from app.parashara.primitives.relationships import EXALTATION, SIGN_LORDS, compound, naisargika

SOURCE: Final[Citation] = Citation("BPHS-45", 113)   # sl.8-10
#: Natural malefics whose company puts a planet in Vikala (the fixed malefics; nodes included).
_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
#: compound relationship -> the Deeptadi dignity state it yields (BPHS-45:113).
_REL_STATE: Final[Mapping[str, str]] = {
    "adhi_mitra": "Pramudita", "mitra": "Santa", "sama": "Deena",
    "shatru": "Khala", "adhi_shatru": "Khala"}


@dataclass(frozen=True)
class DeeptadiAvastha:
    """A planet's Deeptadi state: the dignity state, plus the two co-occurring conditions."""
    state: str               # Deepta | Swastha | Pramudita | Santa | Deena | Khala
    vikala: bool             # shares its sign with a malefic
    kopa: bool               # combust (eclipsed by the Sun)


def _sign_of(lon: float) -> int:
    return int(lon % 360.0 // 30) + 1


def deeptadi(planet: str, longitudes: Mapping[str, float], *,
             speeds: Optional[Mapping[str, float]] = None) -> DeeptadiAvastha:
    """The Deeptadi avastha of `planet` (BPHS-45:113). `speeds` (deg/day; <0 retrograde) selects the
    combustion orb where available; omit to use the direct orb."""
    lon = longitudes[planet]
    sign = _sign_of(lon)
    if sign == EXALTATION.get(planet):
        state = "Deepta"
    elif SIGN_LORDS[sign] == planet:
        state = "Swastha"
    else:
        lord = SIGN_LORDS[sign]
        lord_lon = longitudes.get(lord)
        if lord_lon is not None:
            dist = ((_sign_of(lord_lon) - sign) % 12) + 1
            rel = compound(planet, lord, house_distance=dist)
        else:                                # lord absent -> natural relationship only (binary)
            rel = naisargika(planet, lord)
        state = _REL_STATE.get(rel, "Deena")
    vikala = any(p in _MALEFICS and p != planet and _sign_of(l) == sign
                 for p, l in longitudes.items())
    sun = longitudes.get("Sun")
    retro = bool(speeds and speeds.get(planet, 0.0) < 0.0)
    kopa = is_combust(planet, lon, sun, retrograde=retro) if sun is not None else False
    return DeeptadiAvastha(state=state, vikala=vikala, kopa=kopa)
