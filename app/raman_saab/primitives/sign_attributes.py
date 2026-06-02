from __future__ import annotations
from typing import Final

# sign 1..12 = Aries..Pisces.


def element(sign: int | str) -> str:
    """Fire / Earth / Air / Water, repeating for signs 1..12."""
    return ("fire", "earth", "air", "water")[(int(sign) - 1) % 4]


def modality(sign: int) -> str:
    """Movable / Fixed / Common (Cardinal/Fixed/Mutable), repeating for signs 1..12."""
    return ("movable", "fixed", "common")[(int(sign) - 1) % 3]


def parity(sign: int) -> str:
    """Odd (1,3,5,...) or even (2,4,6,...) sign."""
    return "odd" if int(sign) % 2 == 1 else "even"


def sign_gender(sign: int) -> str:
    """Masculine for odd signs, feminine for even signs."""
    return "masculine" if parity(sign) == "odd" else "feminine"


_PLANET_GENDER: Final[dict[str, str]] = {
    "Sun": "masculine", "Mars": "masculine", "Jupiter": "masculine",
    "Moon": "feminine", "Venus": "feminine",
    "Mercury": "neuter", "Saturn": "neuter", "Rahu": "neuter", "Ketu": "neuter",
}


def planet_gender(planet: str) -> str:
    """Naisargika gender of a graha."""
    return _PLANET_GENDER[planet]


_KEETA: Final[frozenset[int]] = frozenset({4, 8, 12})   # Cancer, Scorpio, Pisces


def is_keeta(sign: int) -> bool:
    """True for watery/insect signs: Cancer (4), Scorpio (8), Pisces (12)."""
    return int(sign) in _KEETA


_SEERSHODAYA: Final[frozenset[int]] = frozenset({3, 5, 6, 7, 8, 11})  # head-rising


def rise_type(sign: int) -> str:
    """Seershodaya / Prushtodaya / Ubhayodaya (Pisces) rise classification."""
    if int(sign) == 12:
        return "ubhayodaya"
    return "seershodaya" if int(sign) in _SEERSHODAYA else "prushtodaya"


_SUSHKA: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn"})  # dry planets


def is_sushka(planet: str) -> bool:
    """True for dry (fiery/airy) planets: Sun, Mars, Saturn."""
    return planet in _SUSHKA
