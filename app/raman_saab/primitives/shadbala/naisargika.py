"""Naisargika Bala — natural (fixed) strength component of Shadbala.

Usage:
    from app.raman_saab.primitives.shadbala.naisargika import naisargika_bala
    sh = naisargika_bala("Sun")   # -> 60.0 Shashtiamsas

Reference: B.V. Raman, *Graha & Bhava Balas* (GBB-7), §5 / pp. 44-63.
Returns Shashtiamsas (float). 1 Rupa = 60 Shashtiamsas.
Rahu and Ketu receive 0 (nodes have no Shadbala).
"""
from __future__ import annotations

from typing import Final

# Fixed 60/7 ladder (Shashtiamsas), GBB-7:44-63. Saturn rank 1 (weakest) .. Sun rank 7 (strongest).
_RANK: Final[dict[str, int]] = {
    "Saturn": 1,
    "Mars": 2,
    "Mercury": 3,
    "Jupiter": 4,
    "Venus": 5,
    "Moon": 6,
    "Sun": 7,
}


def naisargika_bala(planet: str) -> float:
    """Natural strength in Shashtiamsas (fixed per planet). Returns 0.0 for nodes."""
    rank = _RANK.get(planet)
    return round(rank * 60.0 / 7.0, 2) if rank else 0.0
