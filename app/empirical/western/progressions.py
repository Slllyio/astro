"""Secondary progressions and solar-arc directions.

Secondary progression is the "day for a year" convention: the chart cast for
the *n*-th day after birth is read as the chart for the *n*-th year of life.
The only free parameter is what "a year" means in days, and it is a real fork —
365.2422 (tropical) and 365.25 (Julian) differ by ~0.7 days of progressed
motion over an 85-year life, which is most of a degree of progressed Moon.

:data:`TROPICAL_YEAR_DAYS` is the default because Western progression is a
tropical-zodiac technique. Note this is **not** ``DAYS_PER_VEDIC_YEAR``
(365.2425): that constant is locked to Vimshottari math in ``CLAUDE.md`` and
must not leak across traditions. The value is a constructor argument precisely
so a tournament arm can register an alternative rather than edit it in place.

Usage:
    from app.empirical.western.progressions import secondary_progressed_jd, solar_arc
    pjd = secondary_progressed_jd(natal_jd, target_jd)
    directed = solar_arc_directed(natal_positions, arc)
"""

from __future__ import annotations

from typing import Final, Mapping

from app.empirical.western.angles import norm360
from app.empirical.western.tropical import Position, tropical_position

__all__ = [
    "TROPICAL_YEAR_DAYS",
    "JULIAN_YEAR_DAYS",
    "secondary_progressed_jd",
    "solar_arc",
    "solar_arc_directed",
]

#: Mean tropical year — the equinox-to-equinox year the tropical zodiac is
#: defined against. Default for secondary progressions.
TROPICAL_YEAR_DAYS: Final[float] = 365.242190

#: Julian year. Offered because some published progression tables use it;
#: selecting it is a pre-registration choice, not a default.
JULIAN_YEAR_DAYS: Final[float] = 365.25


def secondary_progressed_jd(
    natal_jd: float,
    target_jd: float,
    *,
    year_days: float = TROPICAL_YEAR_DAYS,
) -> float:
    """The Julian Day whose chart is the secondary-progressed chart for ``target_jd``.

    One day of ephemeris time represents one year of life, so elapsed years map
    to elapsed days one-for-one:

        progressed_jd = natal_jd + (target_jd - natal_jd) / year_days

    At ``target_jd == natal_jd`` this returns ``natal_jd`` exactly — the
    progressed chart at age zero is the natal chart, which is the property test
    this function is pinned by.

    Works for negative elapsed time (converse progressions) without special
    casing.
    """
    if year_days <= 0.0:
        raise ValueError(f"year_days must be positive, got {year_days}")
    return natal_jd + (target_jd - natal_jd) / year_days


def solar_arc(natal_sun_longitude: float, progressed_sun_longitude: float) -> float:
    """The solar arc: how far the progressed Sun has advanced from natal.

    Returned in ``[0, 360)`` rather than as a shortest-signed delta. The Sun
    never retrogrades, so its progressed motion is monotonically forward and
    the forward arc is the physically meaningful quantity — roughly 1° per year
    of life. A signed-shortest reading would wrap to negative past age ~180 and
    silently invert every directed position.
    """
    return norm360(progressed_sun_longitude - natal_sun_longitude)


def solar_arc_directed(
    natal_positions: Mapping[str, Position],
    arc: float,
) -> dict[str, float]:
    """Advance every natal body by the solar arc.

    Solar-arc direction moves the whole chart rigidly: each body's directed
    longitude is its natal longitude plus the arc. Returns longitudes only —
    a directed chart has no meaningful body speed of its own.
    """
    return {name: norm360(pos.longitude + arc) for name, pos in natal_positions.items()}


def progressed_solar_arc(
    natal_jd: float,
    target_jd: float,
    natal_sun_longitude: float,
    *,
    year_days: float = TROPICAL_YEAR_DAYS,
) -> float:
    """Convenience: compute the solar arc for a target date in one call.

    Casts the progressed Sun at the secondary-progressed instant and returns
    its arc from the natal Sun.
    """
    pjd = secondary_progressed_jd(natal_jd, target_jd, year_days=year_days)
    progressed_sun = tropical_position(pjd, "Sun")
    return solar_arc(natal_sun_longitude, progressed_sun.longitude)
