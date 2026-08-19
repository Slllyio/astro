"""Dignity-strength multiplier for the s6 scorer variant.

Reconstructed from its contract (imported by ``dasha_doctrine_structural.py``
as ``dignity_strength(lord, sign) -> float``). The original module was never
committed; this restores the documented behaviour.

The multiplier scales a lord's doctrine relevance by its natal sign dignity:
exalted planets act strongly, debilitated planets weakly. Signs are 1..12
(Aries..Pisces). ``None`` / unknown sign → neutral 1.0. Rahu/Ketu use the
commonly-cited (Rath / PVR) exaltation signs and are handled gracefully.
"""
from __future__ import annotations

from typing import Final

# Sign numbering: 1 Aries … 12 Pisces.
_EXALTATION: Final[dict[str, int]] = {
    "Sun": 1, "Moon": 2, "Mars": 10, "Mercury": 6, "Jupiter": 4,
    "Venus": 12, "Saturn": 7, "Rahu": 2, "Ketu": 8,
}
# Own signs (rulership). Sun/Moon rule one sign; the rest two.
_OWN_SIGNS: Final[dict[str, frozenset[int]]] = {
    "Sun": frozenset({5}),
    "Moon": frozenset({4}),
    "Mars": frozenset({1, 8}),
    "Mercury": frozenset({3, 6}),
    "Jupiter": frozenset({9, 12}),
    "Venus": frozenset({2, 7}),
    "Saturn": frozenset({10, 11}),
    # Nodes have no rulership in classical doctrine.
    "Rahu": frozenset(),
    "Ketu": frozenset(),
}

_EXALTED: Final[float] = 1.5
_OWN: Final[float] = 1.25
_DEBILITATED: Final[float] = 0.5
_NEUTRAL: Final[float] = 1.0


def _debilitation_sign(exalt_sign: int) -> int:
    """Debilitation is the 7th sign from exaltation (opposite)."""
    return ((exalt_sign - 1 + 6) % 12) + 1


def dignity_strength(lord: str, sign: object) -> float:
    """Return the dignity multiplier for ``lord`` placed in ``sign`` (1..12).

    Exalted → 1.5, own sign → 1.25, debilitated → 0.5, otherwise 1.0.
    Unknown / missing sign → 1.0 (neutral).
    """
    try:
        s = int(sign)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return _NEUTRAL
    if not 1 <= s <= 12:
        return _NEUTRAL
    exalt = _EXALTATION.get(lord)
    if exalt is not None:
        if s == exalt:
            return _EXALTED
        if s == _debilitation_sign(exalt):
            return _DEBILITATED
    if s in _OWN_SIGNS.get(lord, frozenset()):
        return _OWN
    return _NEUTRAL
