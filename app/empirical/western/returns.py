"""Solar and lunar returns, by longitude root-find.

A return is the instant a body regains its exact natal longitude. This module
finds it numerically rather than by table interpolation: bracket the crossing
on a coarse scan, then bisect to sub-arcsecond precision. The pinned property
is that at the returned instant the body's longitude equals the natal
longitude to better than 1″ — a return that is merely "the right day" is not a
return chart, because the ascendant moves 15° per hour.

Sun and Moon never retrograde, so their longitude is monotonically increasing
and each cycle contains exactly one crossing. That is what makes a simple
bracket-and-bisect correct here; it would not be for a planet with retrograde
loops, so :func:`find_return` is deliberately restricted to bodies whose
synodic motion is monotonic.

Usage:
    from app.empirical.western.returns import solar_return, lunar_return
    jd = solar_return(natal_sun_longitude, search_from_jd)
"""

from __future__ import annotations

from typing import Final

from app.empirical.western.angles import norm360, signed_delta
from app.empirical.western.tropical import tropical_position

__all__ = [
    "PERIOD_DAYS",
    "ReturnNotFoundError",
    "find_return",
    "solar_return",
    "lunar_return",
]

#: Mean return periods, used only to size the coarse scan.
PERIOD_DAYS: Final[dict[str, float]] = {
    "Sun": 365.242190,
    "Moon": 27.321582,
}

#: Bodies whose ecliptic longitude never decreases, so exactly one crossing
#: occurs per cycle. Restricting to these keeps the bracket logic sound.
_MONOTONIC: Final[frozenset[str]] = frozenset(PERIOD_DAYS)

# Bisect until the longitude residual is this small. 1e-7° ≈ 0.00036″, three
# orders of magnitude inside the 1″ property the tests assert.
_TOL_DEG: Final[float] = 1e-7
_MAX_BISECT: Final[int] = 200


class ReturnNotFoundError(RuntimeError):
    """No crossing found inside the searched span."""


def _residual(jd: float, body: str, target_lon: float) -> float:
    """Signed angle from the target longitude to the body, in ``[-180, 180)``.

    Crosses zero from negative to positive exactly when the body passes the
    target going forward.
    """
    return signed_delta(target_lon, tropical_position(jd, body).longitude)


def find_return(
    target_longitude: float,
    search_from_jd: float,
    body: str,
    *,
    max_cycles: float = 1.5,
) -> float:
    """Julian Day of the first time ``body`` reaches ``target_longitude`` at or
    after ``search_from_jd``.

    Args:
      target_longitude: The natal longitude to return to.
      search_from_jd: Start of the search.
      body: ``"Sun"`` or ``"Moon"``.
      max_cycles: How many mean periods to scan before giving up.

    Raises:
      KeyError: body is not one with monotonic longitude.
      ReturnNotFoundError: no crossing inside the scanned span.
    """
    if body not in _MONOTONIC:
        raise KeyError(
            f"find_return supports only monotonic-longitude bodies {sorted(_MONOTONIC)}; got {body!r}. "
            "Retrograding bodies can cross a longitude three times and need a different search."
        )
    period = PERIOD_DAYS[body]
    target = norm360(target_longitude)

    # Coarse scan at 1/40 of a period: fine enough that the Moon (~13.2°/day)
    # advances only ~9° per step, so no crossing can hide between samples.
    step = period / 40.0
    span = period * max_cycles

    jd_lo = search_from_jd
    f_lo = _residual(jd_lo, body, target)
    if f_lo == 0.0:
        return jd_lo

    steps = int(span / step) + 1
    for i in range(1, steps + 1):
        jd_hi = search_from_jd + i * step
        f_hi = _residual(jd_hi, body, target)
        # A genuine forward crossing goes negative → non-negative with a small
        # jump. The ±180 seam also flips sign, but with a ~360° jump; excluding
        # large jumps rejects it.
        if f_lo < 0.0 <= f_hi and (f_hi - f_lo) < 180.0:
            return _bisect(jd_lo, jd_hi, body, target)
        jd_lo, f_lo = jd_hi, f_hi

    raise ReturnNotFoundError(
        f"no {body} return to {target_longitude:.6f}° within {span:.1f} days of JD {search_from_jd}"
    )


def _bisect(jd_lo: float, jd_hi: float, body: str, target: float) -> float:
    """Bisect a bracketed crossing to :data:`_TOL_DEG`."""
    for _ in range(_MAX_BISECT):
        jd_mid = (jd_lo + jd_hi) / 2.0
        f_mid = _residual(jd_mid, body, target)
        if abs(f_mid) < _TOL_DEG:
            return jd_mid
        if f_mid < 0.0:
            jd_lo = jd_mid
        else:
            jd_hi = jd_mid
    return (jd_lo + jd_hi) / 2.0


def solar_return(natal_sun_longitude: float, search_from_jd: float) -> float:
    """The next solar return on or after ``search_from_jd``."""
    return find_return(natal_sun_longitude, search_from_jd, "Sun")


def lunar_return(natal_moon_longitude: float, search_from_jd: float) -> float:
    """The next lunar return on or after ``search_from_jd``."""
    return find_return(natal_moon_longitude, search_from_jd, "Moon")
