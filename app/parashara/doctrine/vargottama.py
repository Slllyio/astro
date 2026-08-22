"""Vargottama — a body in the same sign in the Rasi (D1) and Navamsa (D9).

A body whose navamsa sign equals its rasi sign is Vargottama ("best of the vargas") and is strong.
Saravali defines the vargottama navamsas positionally, and the definition is exactly "D9 sign = D1
sign":

    "The first Navamsa of a Movable Rasi, the 5th one in a Fixed Rasi and the 9th one in a Common
     (Dual) Rasi are called Vargottamamsa. Should the natal Lagna be in such Vargottama Navamsa, the
     native becomes an important person." (SARAVALI-3:66)

(Verified: the 1st/5th/9th navamsa of a movable/fixed/dual sign are precisely those that map back to
the same sign.) The navamsa arithmetic is stream-agnostic, taken from the shared varga substrate.
"""
from __future__ import annotations

from typing import Final, Mapping, Optional

from app.parashara.doctrine.sources import Citation
from app.raman_saab.chart import varga as _varga     # substrate: pure division arithmetic

SOURCE: Final[Citation] = Citation("SARAVALI-3", 66)


def is_vargottama(longitude: float) -> bool:
    """True if the longitude's D9 (navamsa) sign equals its D1 (rasi) sign (SARAVALI-3:66)."""
    lon = longitude % 360.0
    return _varga.varga_sign(lon, 1) == _varga.varga_sign(lon, 9)


def vargottama_bodies(longitudes: Mapping[str, float], *,
                      asc_longitude: Optional[float] = None) -> tuple[str, ...]:
    """Every graha that is Vargottama, plus "Lagna" if the ascendant longitude is given and qualifies.

    The ascendant is listed first when vargottama (Saravali singles out the lagna's case).
    """
    out: list[str] = []
    if asc_longitude is not None and is_vargottama(asc_longitude):
        out.append("Lagna")
    out.extend(p for p, lon in longitudes.items() if is_vargottama(lon))
    return tuple(out)
