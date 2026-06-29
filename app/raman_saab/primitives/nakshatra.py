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


_PADA: Final[float] = 30.0 / 9.0                    # one nakshatra-pada = 3 deg 20'
#: the three water->fire sign junctions (Cancer/Leo, Scorpio/Sagittarius, Pisces/Aries).
_GANDANTA_JUNCTIONS: Final[tuple[float, ...]] = (120.0, 240.0, 360.0)


def is_gandanta(lon: float) -> bool:
    """True if the longitude is within one pada (3 deg 20') of a water/fire sign junction — the
    gandanta sandhi (Revati-Ashwini, Ashlesha-Magha, Jyeshtha-Mula): the last pada of the water-sign
    nakshatra or the first pada of the next fire-sign nakshatra. A sensitive/inauspicious zone."""
    lon = lon % 360.0
    for j in _GANDANTA_JUNCTIONS:
        if j == 360.0:                              # 356d40'..360 or 0..3d20'
            if lon >= 360.0 - _PADA or lon <= _PADA:
                return True
        elif j - _PADA <= lon <= j + _PADA:
            return True
    return False


def gandanta_grahas(chart: RamanChart) -> list[str]:
    """Planets (and 'Lagna') sitting in a gandanta zone."""
    out = [n for n, p in chart.planets.items() if is_gandanta(p.lon)]
    if is_gandanta(chart.asc_lon):
        out.append("Lagna")
    return out
