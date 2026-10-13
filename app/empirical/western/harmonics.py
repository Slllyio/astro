"""Harmonic charts — Addey's ``longitude × n`` transform.

The *n*-th harmonic multiplies every longitude by *n* and re-wraps to the
circle. Its point is that an aspect of ``360/n`` degrees in the radix becomes a
conjunction in the harmonic, so harmonic conjunctions are a compact encoding of
a whole aspect family. That makes harmonics cheap, high-yield features — and
also a multiplicity hazard, since each harmonic tested is another family member.

Pure arithmetic; no ephemeris calls.

Usage:
    from app.empirical.western.harmonics import harmonic_chart
    h5 = harmonic_chart(positions, 5)
"""

from __future__ import annotations

from typing import Iterable, Mapping

from app.empirical.western.angles import norm360, separation
from app.empirical.western.tropical import Position

__all__ = ["harmonic", "harmonic_chart", "harmonic_conjunctions"]


def harmonic(longitude: float, n: int) -> float:
    """The *n*-th harmonic of a longitude.

    ``harmonic(x, 1) == norm360(x)`` — the first harmonic is the radix itself,
    which is the property this function is pinned by.
    """
    if n < 1:
        raise ValueError(f"harmonic number must be >= 1, got {n}")
    return norm360(longitude * n)


def harmonic_chart(
    positions: Mapping[str, Position],
    n: int,
    bodies: Iterable[str] | None = None,
) -> dict[str, float]:
    """Every body's *n*-th harmonic longitude.

    Returns longitudes only: harmonic motion is not physical motion, so
    carrying a "speed" through the transform would invite it to be read as one.
    """
    names = list(bodies) if bodies is not None else list(positions)
    missing = [nm for nm in names if nm not in positions]
    if missing:
        raise KeyError(f"bodies not in positions: {missing}")
    return {name: harmonic(positions[name].longitude, n) for name in names}


def harmonic_conjunctions(
    chart: Mapping[str, float],
    *,
    orb: float = 6.0,
) -> list[tuple[str, str, float]]:
    """Pairs conjunct within ``orb`` in a harmonic chart.

    In the *n*-th harmonic a conjunction corresponds to a radix aspect of
    ``360/n`` (or a multiple), so this is the standard way harmonic charts are
    read.

    Returns:
      ``(body_a, body_b, orb)`` triples, tightest first.
    """
    if orb <= 0.0:
        raise ValueError(f"orb must be positive, got {orb}")
    names = list(chart)
    out: list[tuple[str, str, float]] = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            sep = separation(chart[a], chart[b])
            if sep <= orb:
                out.append((a, b, sep))
    out.sort(key=lambda t: (t[2], t[0], t[1]))
    return out
