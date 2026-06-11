"""H12 — Bandhana Yoga: mode of confinement keyed to the rising sign.

Raman (HTJAH-II:16429-16436): "Malefics in the 2nd, 5th, 9th and 12th houses
cause captivity, the exact nature of which is determined by the nature of the
sign rising on the Ascendant." Four modes over ten signs:

    Aries / Taurus / Sagittarius   -> bound by ropes
    Scorpio                        -> thrown into an underground cell
    Gemini / Libra / Virgo         -> put in fetters
    Pisces / Cancer / Capricorn    -> confined in a large protected building

Source fidelity note: the printed text names only 10 signs — **Leo and
Aquarius are absent** from the grid. ``confinement_mode`` returns ``None`` for
them (faithful gap, not an oversight).

Pure doctrine data returned as judge metadata — no scoring logic.

Data source: docs/raman_saab/methodology/house_12_vyaya.md (Group D, rows
D3a-D3d), verified against the corpus HTJAH-II:16429-16436.

Usage:
    from app.raman_saab.doctrine.lookups.confinement_modes import confinement_mode
    confinement_mode("Scorpio")   # -> "thrown into an underground cell"
    confinement_mode("Leo")       # -> None (source silent)
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping

from app.raman_saab.doctrine.sources import Citation


@dataclass(frozen=True)
class ConfinementMode:
    """Mode of captivity for one rising sign (Bandhana Yoga grid)."""
    lagna_sign: str
    mode: str
    sources: tuple[Citation, ...]


_ALL_SIGNS: Final[frozenset[str]] = frozenset((
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
))


def _ii(*lines: int) -> tuple[Citation, ...]:
    return tuple(Citation("HTJAH-II", ln) for ln in lines)


def _group(signs: tuple[str, ...], mode: str,
           *lines: int) -> list[tuple[str, ConfinementMode]]:
    return [(s, ConfinementMode(s, mode, _ii(*lines))) for s in signs]


# Rising sign -> mode of captivity (HTJAH-II:16429-16436). Leo and Aquarius
# are NOT printed in the source and are deliberately absent here.
CONFINEMENT_MODES: Final[Mapping[str, ConfinementMode]] = MappingProxyType(dict(
    _group(("Aries", "Taurus", "Sagittarius"),
           "bound by ropes", 16431, 16432)
    + _group(("Scorpio",),
             "thrown into an underground cell", 16433, 16434)
    + _group(("Gemini", "Libra", "Virgo"),
             "put in fetters", 16434, 16435)
    + _group(("Pisces", "Cancer", "Capricorn"),
             "confined in a large protected building", 16435, 16436)
))


def confinement_mode(lagna_sign: str) -> str | None:
    """Printed mode of captivity for the rising sign (HTJAH-II:16429-16436).

    Returns None for Leo/Aquarius (the source names only 10 signs); raises
    ValueError for anything that is not a zodiacal sign.
    """
    if lagna_sign not in _ALL_SIGNS:
        raise ValueError(f"unknown rising sign: {lagna_sign!r}")
    record = CONFINEMENT_MODES.get(lagna_sign)
    return record.mode if record is not None else None
