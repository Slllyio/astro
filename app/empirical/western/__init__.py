"""Phase 2 — the Western/modern toolkit.

Real tropical computation over pyswisseph, replacing the
``sidereal + 24° ayanamsa`` approximation in
``app/medini/ml/cross_tradition.py`` (whose own docstring concedes it drifts
~50″/year and uses whole-sign houses for both traditions "to remove 95% of the
engineering cost").

The mathematics is a thin shell over Swiss Ephemeris; the tests are the work.
Every module is pinned either to an externally-published astronomical fact
(equinox instants, the repo's externally-verified canonical chart) or to a
structural property that must hold by construction (harmonic 1 = radix,
progressed age 0 = natal, return longitude = natal longitude).

Modules:
  angles       circular arithmetic shared by everything here
  tropical     ayanamsa-free body positions
  houses       Placidus/Koch/whole-sign — explicit NULL where undefined
  aspects      configurable, fingerprintable orb table + applying/separating
  progressions secondary (day-for-year) and solar arc
  returns      solar/lunar returns by longitude root-find
  transits     exact hits with orb entry/exit windows
  midpoints    Ebertin-style midpoint tree
  harmonics    Addey ``longitude × n``
"""

from __future__ import annotations

__all__ = [
    "angles",
    "aspects",
    "harmonics",
    "houses",
    "midpoints",
    "progressions",
    "returns",
    "transits",
    "tropical",
]
