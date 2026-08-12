"""Circular-angle arithmetic shared by the Western toolkit.

Every helper here treats longitudes as points on a circle. The repo-wide trap
this avoids is naive ``abs(a - b)``, which silently reports 357° of separation
for two bodies 3° apart across the Pisces/Aries cusp (``CLAUDE.md`` § locked
conventions). All functions are pure and total.
"""

from __future__ import annotations

__all__ = [
    "norm360",
    "signed_delta",
    "separation",
    "circ_midpoint",
    "in_arc",
]


def norm360(angle: float) -> float:
    """Normalize an angle to ``[0, 360)``."""
    return angle % 360.0


def signed_delta(frm: float, to: float) -> float:
    """Shortest signed angle from ``frm`` to ``to``, in ``[-180, 180)``.

    Positive means ``to`` lies counter-clockwise (increasing longitude) of
    ``frm``. This is the primitive every applying/separating and root-finding
    decision in this package is built on.
    """
    return (to - frm + 180.0) % 360.0 - 180.0


def separation(a: float, b: float) -> float:
    """Unsigned angular separation in ``[0, 180]``."""
    return abs(signed_delta(a, b))


def circ_midpoint(a: float, b: float) -> float:
    """Midpoint of the *short* arc between two longitudes.

    Two midpoints exist on a circle; this returns the near one, which is the
    convention Ebertin-style midpoint work uses. ``circ_midpoint(a, a) == a``.
    """
    return norm360(a + signed_delta(a, b) / 2.0)


def in_arc(x: float, start: float, end: float) -> bool:
    """True when ``x`` lies in the counter-clockwise arc ``[start, end)``."""
    span = (end - start) % 360.0
    off = (x - start) % 360.0
    # A zero-width span means start == end; treat as the full circle.
    if span == 0.0:
        return True
    return off < span
