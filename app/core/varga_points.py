"""Sensitive varga points: khara (22nd) drekkana and the 64th navamsa.

Both are classical mrityu-bhaga-class sensitive points Raman's longevity
doctrine references (HPA Ch. XIV context; the v2 encoder covered every
NH-tagged timing mechanism EXCEPT drekkana_22 — this module closes that
gap for the doctrine engine).

Definitions (standard, consistent with whole-sign counting used repo-wide):

* **Khara / 22nd drekkana**: drekkanas are 10° arcs. Counting the drekkana
  occupied by the lagna as the 1st, the 22nd falls 21 arcs = 210° further
  along the zodiac — the middle drekkana family of the 8th sign from the
  lagna's. Its D3 sign lord is the khara-drekkana lord (a maraka agent).

* **64th navamsa**: navamsas are 3°20' arcs. Counting the navamsa occupied
  by the Moon (or, secondarily, the lagna) as the 1st, the 64th falls
  63 arcs = 210° further — the 4th navamsa family of the 8th sign. Its D9
  lord is the chidra graha.

Both points are therefore ``reference longitude + 210°``; the varga sign is
read with the same divisional mapping the rest of the repo uses
(``compute_divisional_longitude``).
"""
from __future__ import annotations

import dataclasses

from app.core.dignity import SIGN_RULERS
from app.core.shodashavarga import compute_divisional_longitude

_ARC = 210.0  # 21 drekkanas == 63 navamsas == 210 degrees


@dataclasses.dataclass(frozen=True)
class VargaPoint:
    longitude: float   # zodiacal longitude of the sensitive point, 0..360
    sign: int          # rasi (1..12) holding the point
    varga_sign: int    # D3 sign for khara drekkana / D9 sign for 64th navamsa
    lord: str          # ruler of varga_sign


def _point(reference_lon: float, divisor: int) -> VargaPoint:
    lon = (float(reference_lon) + _ARC) % 360.0
    varga_lon = compute_divisional_longitude(lon, divisor)
    varga_sign = int(varga_lon % 360.0 // 30) + 1
    return VargaPoint(
        longitude=lon,
        sign=int(lon // 30) + 1,
        varga_sign=varga_sign,
        lord=SIGN_RULERS[varga_sign],
    )


def khara_drekkana(lagna_lon: float) -> VargaPoint:
    """22nd drekkana from the lagna's drekkana (khara). Lord is a maraka agent."""
    return _point(lagna_lon, 3)


def navamsa_64th(reference_lon: float) -> VargaPoint:
    """64th navamsa from the reference point's navamsa (usually the Moon).

    The lord of this navamsa is the chidra graha of longevity doctrine.
    """
    return _point(reference_lon, 9)


def occupies_point(planet_lon: float, point: VargaPoint, orb: float = 5.0) -> bool:
    """True when a planet stands within ``orb`` degrees of the sensitive point."""
    delta = abs((float(planet_lon) - point.longitude + 180.0) % 360.0 - 180.0)
    return delta <= orb
