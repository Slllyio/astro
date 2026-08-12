"""Midpoints — the Ebertin/Uranian layer.

A midpoint is the degree halfway between two bodies. Two such degrees exist on
a circle; this module uses the *near* midpoint (the one on the short arc),
which is the standard convention. The far midpoint is always exactly 180° away
and is available via :func:`opposite_midpoint` for callers that want the full
axis.

Pure arithmetic over longitudes — no ephemeris calls, so this module is exact
and fast enough to run over a whole corpus.

Usage:
    from app.empirical.western.midpoints import midpoint_tree, midpoints_near
    tree = midpoint_tree(positions)
    triggered = midpoints_near(tree, point=natal_sun_lon, orb=1.5)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from app.empirical.western.angles import circ_midpoint, norm360, separation
from app.empirical.western.tropical import Position

__all__ = [
    "MidpointHit",
    "midpoint",
    "opposite_midpoint",
    "midpoint_tree",
    "midpoints_near",
]


def midpoint(lon_a: float, lon_b: float) -> float:
    """Near midpoint of two longitudes. Symmetric; ``midpoint(a, a) == a``."""
    return circ_midpoint(lon_a, lon_b)


def opposite_midpoint(lon_a: float, lon_b: float) -> float:
    """The far midpoint — the near one's exact opposition."""
    return norm360(circ_midpoint(lon_a, lon_b) + 180.0)


def midpoint_tree(
    positions: Mapping[str, Position],
    bodies: Iterable[str] | None = None,
) -> dict[tuple[str, str], float]:
    """All pairwise near midpoints.

    Keys are ``(body_a, body_b)`` tuples in the iteration order given, each
    unordered pair appearing once. For *n* bodies this is *n(n-1)/2* entries —
    55 for the default eleven-body set.
    """
    names = list(bodies) if bodies is not None else list(positions)
    missing = [n for n in names if n not in positions]
    if missing:
        raise KeyError(f"bodies not in positions: {missing}")
    tree: dict[tuple[str, str], float] = {}
    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            tree[(name_a, name_b)] = midpoint(
                positions[name_a].longitude, positions[name_b].longitude
            )
    return tree


@dataclass(frozen=True, slots=True)
class MidpointHit:
    """A midpoint axis within orb of a point.

    Attributes:
      pair: The two bodies whose midpoint this is.
      midpoint_longitude: The near midpoint degree.
      point: The longitude tested against.
      orb: Angular distance from the point to the nearer end of the axis.
      on_far_side: True when the point sits on the *opposite* midpoint rather
        than the near one. Both ends of the axis count as activated in
        Ebertin's usage, so this records which end without discarding the hit.
    """

    pair: tuple[str, str]
    midpoint_longitude: float
    point: float
    orb: float
    on_far_side: bool


def midpoints_near(
    tree: Mapping[tuple[str, str], float],
    point: float,
    *,
    orb: float = 1.5,
) -> list[MidpointHit]:
    """Midpoint axes activated by a point, within ``orb``.

    Both ends of each axis are tested: a point conjunct the far midpoint sits
    on the same axis and is reported with ``on_far_side=True``.

    Returns:
      Hits sorted by orb ascending.
    """
    if orb <= 0.0:
        raise ValueError(f"orb must be positive, got {orb}")
    hits: list[MidpointHit] = []
    for pair, mid in tree.items():
        near = separation(point, mid)
        far = separation(point, norm360(mid + 180.0))
        best, on_far = (near, False) if near <= far else (far, True)
        if best <= orb:
            hits.append(
                MidpointHit(
                    pair=pair,
                    midpoint_longitude=mid,
                    point=norm360(point),
                    orb=best,
                    on_far_side=on_far,
                )
            )
    hits.sort(key=lambda h: (h.orb, h.pair))
    return hits
