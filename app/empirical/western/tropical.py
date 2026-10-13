"""Direct tropical (ayanamsa-free) body positions.

This module replaces the ``sidereal + 24° approximation`` used by
``app/medini/ml/cross_tradition.py``, whose own docstring concedes it is "an
approximation" that drifts ~50″/year against the true Lahiri value. Nothing
here round-trips through a sidereal cast: ``swe.calc_ut`` is called *without*
``FLG_SIDEREAL``, which is what tropical means.

**Global-state contract.** This module never calls ``swe.set_sid_mode``.
swisseph's sidereal mode is process-global; the Vedic engine re-asserts Lahiri
on every call, but a tropical layer that flipped the mode would corrupt any
concurrently-cast Vedic chart. Tropical needs no ayanamsa, so the safe move is
to touch nothing. Enforced by ``tests/empirical/test_western_tropical.py``.

**Ephemeris backend.** ``swe.set_ephe_path(None)`` selects the built-in
Moshier ephemeris (matching ``app/core/ephemeris_engine.py``). Moshier covers
the Sun through Pluto plus the lunar nodes and mean apogee to sub-arcsecond
agreement with the Swiss files for modern dates, but it carries **no asteroid
data** — Chiron and friends raise unless real ``.se1`` files are installed.
:data:`DEFAULT_BODIES` is therefore the Moshier-safe set.

Usage:
    from app.empirical.western.tropical import julian_day_ut, tropical_positions
    jd = julian_day_ut(1990, 7, 15, 6.5)          # 12:00 IST == 06:30 UT
    pos = tropical_positions(jd)
    pos["Sun"].longitude
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Iterable, Mapping

import swisseph as swe

from app.empirical.western.angles import norm360

logger = logging.getLogger(__name__)

__all__ = [
    "Position",
    "BODY_IDS",
    "DEFAULT_BODIES",
    "EXTENDED_BODIES",
    "BodyUnavailableError",
    "julian_day_ut",
    "tropical_position",
    "tropical_positions",
    "south_node_longitude",
]

# Match app/core/ephemeris_engine.py: built-in Moshier, no external files.
swe.set_ephe_path(None)

# Tropical flags. FLG_SIDEREAL is deliberately absent — that absence *is* the
# tropical zodiac. FLG_SPEED is required for retrograde and applying/separating.
_FLAGS: Final[int] = swe.FLG_SWIEPH | swe.FLG_SPEED

BODY_IDS: Final[dict[str, int]] = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "TrueNode": swe.TRUE_NODE,
    "MeanNode": swe.MEAN_NODE,
    "Lilith": swe.MEAN_APOG,
    "Chiron": swe.CHIRON,
}

#: Bodies computable on the built-in Moshier ephemeris — the safe default.
DEFAULT_BODIES: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "TrueNode",
)

#: Everything :data:`BODY_IDS` knows. ``Chiron`` needs real ``.se1`` files.
EXTENDED_BODIES: Final[tuple[str, ...]] = tuple(BODY_IDS)


class BodyUnavailableError(RuntimeError):
    """Raised when the active ephemeris cannot compute a requested body.

    Never swallowed into a silent drop: a feature bank that quietly loses a
    column would corrupt every downstream tournament comparison.
    """


@dataclass(frozen=True, slots=True)
class Position:
    """One body's tropical position at one instant.

    Attributes:
      body: Key from :data:`BODY_IDS`.
      longitude: Tropical ecliptic longitude, degrees in ``[0, 360)``.
      latitude: Ecliptic latitude, degrees (positive north).
      distance_au: Distance from Earth in AU.
      speed_longitude: Degrees/day; negative means retrograde.
      speed_latitude: Degrees/day.
    """

    body: str
    longitude: float
    latitude: float
    distance_au: float
    speed_longitude: float
    speed_latitude: float

    @property
    def is_retrograde(self) -> bool:
        """True when apparent longitude is decreasing."""
        return self.speed_longitude < 0.0

    @property
    def sign_index(self) -> int:
        """0-based tropical sign (0 = Aries), by floor division.

        Floor division, not ``int(x / 30)``, so an exact 60.0° lands in Gemini
        rather than drifting on the cusp (``CLAUDE.md`` § locked conventions).
        """
        return int(self.longitude // 30.0)

    @property
    def degree_in_sign(self) -> float:
        """Degrees elapsed within the current sign, ``[0, 30)``."""
        return self.longitude % 30.0


def julian_day_ut(year: int, month: int, day: int, hour_ut: float) -> float:
    """Gregorian calendar date + decimal UT hour → Julian Day (UT).

    ``hour_ut`` must already be UT. Convert from local clock time by
    subtracting the zone offset, exactly as
    ``app/core/ephemeris_engine.calculate_jd`` does.
    """
    return swe.julday(year, month, day, hour_ut, swe.GREG_CAL)


def tropical_position(jd_ut: float, body: str) -> Position:
    """Tropical position of one body.

    Raises:
      KeyError: unknown body name.
      BodyUnavailableError: the active ephemeris lacks data for this body
        (typically Chiron on the Moshier fallback).
    """
    if body not in BODY_IDS:
        raise KeyError(f"unknown body {body!r}; expected one of {sorted(BODY_IDS)}")
    try:
        xx, _retflag = swe.calc_ut(jd_ut, BODY_IDS[body], _FLAGS)
    except swe.Error as exc:  # pragma: no cover - depends on installed ephemeris
        raise BodyUnavailableError(f"{body} unavailable on the active ephemeris: {exc}") from exc
    return Position(
        body=body,
        longitude=norm360(xx[0]),
        latitude=xx[1],
        distance_au=xx[2],
        speed_longitude=xx[3],
        speed_latitude=xx[4],
    )


def tropical_positions(
    jd_ut: float,
    bodies: Iterable[str] = DEFAULT_BODIES,
) -> dict[str, Position]:
    """Tropical positions for several bodies at one instant."""
    return {body: tropical_position(jd_ut, body) for body in bodies}


def south_node_longitude(positions: Mapping[str, Position]) -> float:
    """South node, derived as the true node's exact opposition.

    Swiss Ephemeris exposes only the north node; the south node is definitionally
    180° away, so deriving it is exact rather than approximate.
    """
    if "TrueNode" not in positions:
        raise KeyError("south_node_longitude needs 'TrueNode' in positions")
    return norm360(positions["TrueNode"].longitude + 180.0)
