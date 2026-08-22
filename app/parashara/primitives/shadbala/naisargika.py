"""Naisargika bala — natural strength by luminosity (BPHS ch.27, sloka 14).

    "Divide one Rupa (60 Virupas) by 7 and multiply by 1 to 7 separately for Saturn, Mars, Mercury,
     Jupiter, Venus, the Moon and the Sun respectively." (BPHS-27:1406)

Fixed per planet — the brightest (Sun) gets the most. So Sun 7/7, Moon 6/7, Venus 5/7, Jupiter
4/7, Mercury 3/7, Mars 2/7, Saturn 1/7 of a rupa.
"""
from __future__ import annotations

from typing import Final

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.shadbala import VIRUPAS_PER_RUPA

SOURCE: Final[Citation] = Citation("BPHS-27", 1406)

#: multiplier k (planet gets k/7 of a rupa), BPHS-27:1406.
_SEVENTHS: Final[dict[str, int]] = {
    "Sun": 7, "Moon": 6, "Venus": 5, "Jupiter": 4, "Mercury": 3, "Mars": 2, "Saturn": 1,
}

#: Naisargika bala in VIRUPAS, per planet.
NAISARGIKA_VIRUPAS: Final[dict[str, float]] = {
    p: VIRUPAS_PER_RUPA * k / 7.0 for p, k in _SEVENTHS.items()
}


def naisargika_bala(planet: str) -> float:
    """Natural strength of `planet` in virupas (fixed)."""
    try:
        return NAISARGIKA_VIRUPAS[planet]
    except KeyError:
        raise ValueError(f"Naisargika bala is defined for the seven grahas, not {planet!r}") from None
