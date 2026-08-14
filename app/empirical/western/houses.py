"""Tropical house systems — Placidus, Koch, whole-sign, and friends.

**The design point of this module is the NULL.** Placidus and Koch are
undefined beyond the polar circles: the house circles they are built from never
intersect the horizon, so there is no cusp to compute. Swiss Ephemeris responds
by *silently substituting Porphyry* and flagging an error — ``houses_ex2``
reports the substitution verbatim as ``"within polar circle, switched to
Porphyry"``. A caller that ignores that flag gets twelve plausible-looking
floats that are not Placidus cusps at all.

Feeding those into a feature bank would be worse than useless: they would be
systematically wrong for exactly the high-latitude subset of the corpus, which
correlates with birth geography, which is already the strongest chartless
predictor we have (lat/lon/date alone scores AUC 0.744 on marriage). So
:func:`house_cusps` returns ``None`` rather than a fallback, and it is the
caller's job to record the miss.

Usage:
    from app.empirical.western.houses import house_cusps, house_of
    cusps = house_cusps(jd_ut, lat=12.97, lon=77.59, system="placidus")
    if cusps is None:
        ...  # undefined at this latitude — record, do not substitute
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Sequence

import swisseph as swe

from app.empirical.western.angles import in_arc, norm360

logger = logging.getLogger(__name__)

__all__ = [
    "HouseCusps",
    "HOUSE_SYSTEMS",
    "QUADRANT_SYSTEMS",
    "house_cusps",
    "house_of",
]

#: Public name → Swiss Ephemeris single-letter code.
HOUSE_SYSTEMS: Final[dict[str, bytes]] = {
    "placidus": b"P",
    "koch": b"K",
    "whole_sign": b"W",
    "equal": b"A",
    "porphyry": b"O",
    "regiomontanus": b"R",
    "campanus": b"C",
}

#: Systems that are undefined inside the polar circles. The sign-based and
#: ecliptic-division systems (whole-sign, equal, Porphyry) stay defined
#: everywhere because they never reference the horizon's diurnal circles.
QUADRANT_SYSTEMS: Final[frozenset[str]] = frozenset({"placidus", "koch", "regiomontanus", "campanus"})


@dataclass(frozen=True, slots=True)
class HouseCusps:
    """Twelve tropical house cusps plus the four angles.

    Attributes:
      system: The requested system name (never a substituted one).
      cusps: 12 longitudes; ``cusps[0]`` starts house 1.
      ascendant: Rising degree.
      midheaven: MC.
      armc: Right ascension of the MC.
      vertex: The vertex point.
    """

    system: str
    cusps: tuple[float, ...]
    ascendant: float
    midheaven: float
    armc: float
    vertex: float

    def __post_init__(self) -> None:
        if len(self.cusps) != 12:
            raise ValueError(f"expected 12 cusps, got {len(self.cusps)}")


def house_cusps(
    jd_ut: float,
    lat: float,
    lon: float,
    system: str = "placidus",
) -> HouseCusps | None:
    """Tropical house cusps, or ``None`` where the system is undefined.

    Args:
      jd_ut: Julian Day in UT.
      lat: Geographic latitude, degrees north positive.
      lon: Geographic longitude, degrees east positive.
      system: Key of :data:`HOUSE_SYSTEMS`.

    Returns:
      A :class:`HouseCusps`, or ``None`` when Swiss Ephemeris reports the
      system is undefined at this latitude (quadrant systems inside the polar
      circles). Never returns a silently-substituted system.

    Raises:
      KeyError: unknown system name.
    """
    if system not in HOUSE_SYSTEMS:
        raise KeyError(f"unknown house system {system!r}; expected one of {sorted(HOUSE_SYSTEMS)}")
    code = HOUSE_SYSTEMS[system]

    # No FLG_SIDEREAL and no set_sid_mode: these are tropical cusps.
    try:
        result = swe.houses_ex2(jd_ut, lat, lon, code)
    except swe.Error as exc:
        # houses_ex2 raises with the substitution reason, e.g.
        # "within polar circle, switched to Porphyry". That is precisely the
        # case we must not paper over.
        logger.info("house system %s undefined at lat=%.4f (%s) — returning NULL", system, lat, exc)
        return None
    except AttributeError:  # pragma: no cover - older pyswisseph without houses_ex2
        try:
            result = swe.houses_ex(jd_ut, lat, lon, code)
        except swe.Error as exc:
            logger.info("house system %s undefined at lat=%.4f (%s) — returning NULL", system, lat, exc)
            return None

    raw_cusps, ascmc = result[0], result[1]

    # Swiss Ephemeris returns 12 cusps for every system this module exposes;
    # anything else means the API contract shifted under us and the values
    # cannot be trusted positionally.
    if len(raw_cusps) != 12:  # pragma: no cover - defensive
        logger.warning("unexpected cusp count %d for system %s — returning NULL", len(raw_cusps), system)
        return None

    return HouseCusps(
        system=system,
        cusps=tuple(norm360(c) for c in raw_cusps),
        ascendant=norm360(ascmc[0]),
        midheaven=norm360(ascmc[1]),
        armc=norm360(ascmc[2]),
        vertex=norm360(ascmc[3]),
    )


def house_of(longitude: float, cusps: Sequence[float]) -> int:
    """Which house (1..12) a longitude falls in.

    Uses arc containment rather than subtraction so that houses spanning 0°
    Aries are handled correctly. Quadrant houses are unequal, so the arc
    between consecutive cusps — not a fixed 30° — defines membership.
    """
    if len(cusps) != 12:
        raise ValueError(f"expected 12 cusps, got {len(cusps)}")
    target = norm360(longitude)
    for i in range(12):
        if in_arc(target, norm360(cusps[i]), norm360(cusps[(i + 1) % 12])):
            return i + 1
    # Unreachable for 12 cusps that partition the circle.
    raise ValueError(f"longitude {longitude} matched no house — cusps are not a partition")
