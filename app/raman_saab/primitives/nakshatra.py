from __future__ import annotations
from typing import Final
from app.raman_saab.chart.model import RamanChart

_NAK_LORDS: Final[tuple[str, ...]] = (
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
_TARA_NAMES: Final[tuple[str, ...]] = (
    "janma", "sampat", "vipat", "kshema", "pratyak", "sadhaka", "naidhana", "mitra", "param_mitra")


def nakshatra_lord(nak: int) -> str:
    """Vimshottari dasha lord for nakshatra number 1..27 (Ketu..Mercury cycle)."""
    return _NAK_LORDS[(int(nak) - 1) % 9]


def tara_position(planet: str, chart: RamanChart) -> int:
    """1..9 tara of `planet`'s nakshatra counted from the Janma (natal Moon) nakshatra."""
    janma = chart.planets["Moon"].nakshatra
    nak = chart.planets[planet].nakshatra
    return ((nak - janma) % 27) % 9 + 1


def tara_of(planet: str, chart: RamanChart) -> str:
    """Named tara (janma/sampat/vipat/kshema/pratyak/sadhaka/naidhana/mitra/param_mitra)."""
    return _TARA_NAMES[tara_position(planet, chart) - 1]
