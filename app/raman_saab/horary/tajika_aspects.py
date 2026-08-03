"""Tajika aspects and yogas — exactly the set Raman's Prasna Tantra defines.

Aspect set (PRASNA-2:258-262): conjunction 0, sextile 60, square 90, trine 120,
opposition 180. "An aspect by itself has no orb. But planets have orbs of operation
(deepthamsas): the Sun 15, the Moon 12, Mars 7, Mercury 7, Jupiter 9, Venus 7 and
Saturn 9" (PRASNA-2:262-264, AS PRINTED). Square/opposition generally inauspicious;
trine/sextile auspicious (PRASNA-2:266-270).

Orb rule (VARSHA-7:43-47, where Raman himself sends the reader — PRASNA-4:1080-1083): "If
the Deepthamsas of a slow-moving planet mix with those of a faster-moving planet this yoga
is caused. For instance ... Guru's deepthamsas are 9 and Sukra's 7. If Guru and Sukra are
within 7 degrees from each other this yoga is produced" — i.e. the orbs must MUTUALLY
mingle, so the SMALLER of the two deeptamsas governs. (PRASNA-4's own worked figure is
OCR-damaged at the digit; the VARSHA micro-example is unambiguous and is the rule encoded.)

Speed order (PRASNA-4:1085-1088): "The speed becomes faster in the order of Saturn,
Jupiter, Mars, the Sun, Venus, Mercury and the Moon."

Yogas (PRASNA-4):
- Ithasala/Muthaseela (stanzas 54-55, :1068-1119): the faster planet, at lesser longitude,
  is BEHIND the slower — an applying aspect within orb. Within one degree of exactness (or
  exact) it is Poorna (complete).
- Easarapha/Musaripha (stanza 56, :1122-1148): the faster planet AHEAD of the slower — a
  separating aspect; unfavourable.
- Naktha (stanza 57, :1151-1161): two planets in no mutual aspect; a planet FASTER than
  both, in aspect with both, transfers the light between them.
- Yamaya (stanza 60, :1218-1253): two lords in no mutual aspect; a planet SLOWER than both,
  in aspect with both, transfers the light.
- Kamboola (stanza 61, :1255-1330): an Ithasala pair with the Moon also in Ithasala with
  either — graded "par excellence, medium or ordinary according to the strength the Moon
  and the other two planets become endowed with" (the full Uttamottama..Adhama ladder cites
  Varshaphal ch. III's panchadhikara; the three printed grades are what this module returns).

Usage:
    from app.raman_saab.horary.tajika_aspects import ithasala, easarapha, naktha, yamaya
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.doctrine.sources import Citation

TAJIKA_ASPECT_ANGLES: Final[tuple[int, ...]] = (0, 60, 90, 120, 180)
#: PRASNA-2:262-264, as printed.
DEEPTAMSA: Final[dict[str, int]] = {
    "Sun": 15, "Moon": 12, "Mars": 7, "Mercury": 7, "Jupiter": 9, "Venus": 7, "Saturn": 9}
#: PRASNA-4:1085-1088 — slowest first.
SPEED_ORDER: Final[tuple[str, ...]] = (
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon")

_POORNA_ORB: Final[float] = 1.0        # PRASNA-4:1116-1119


@dataclass(frozen=True)
class TajikaYoga:
    yoga: str                  # Ithasala | Poorna Ithasala | Easarapha | Naktha | Yamaya | Kamboola
    planets: tuple[str, ...]
    aspect_angle: int
    gap_degrees: float         # distance from exactness
    favourable: bool
    source: Citation


def speed_rank(planet: str) -> int:
    """0 = slowest (Saturn) .. 6 = fastest (Moon)."""
    return SPEED_ORDER.index(planet)


def _orb(p1: str, p2: str) -> float:
    return float(min(DEEPTAMSA[p1], DEEPTAMSA[p2]))


#: Exactness targets in the DIRECTED separation space sep = (slower - faster) mod 360,
#: which strictly DECREASES as the faster planet gains: each tajika angle A is exact at
#: sep = A and sep = 360 - A.
_TARGETS: Final[tuple[int, ...]] = (0, 60, 90, 120, 180, 240, 270, 300, 360)


def _directed(p1: str, lon1: float, p2: str, lon2: float) -> tuple[str, str, float, int, float]:
    """(faster, slower, sep, aspect angle, signed gap). gap > 0 means sep is still above the
    target and shrinking toward it — APPLYING; gap < 0 means the exactness has passed —
    SEPARATING."""
    faster, slower = (p1, p2) if speed_rank(p1) > speed_rank(p2) else (p2, p1)
    f_lon = lon1 if faster == p1 else lon2
    s_lon = lon2 if faster == p1 else lon1
    sep = (s_lon - f_lon) % 360.0
    target = min(_TARGETS, key=lambda t: abs(sep - t))
    angle = target if target <= 180 else 360 - target
    return faster, slower, sep, angle, sep - target


def in_aspect(p1: str, lon1: float, p2: str, lon2: float) -> bool:
    """True when the two planets stand within orb of any tajika aspect."""
    *_, gap = _directed(p1, lon1, p2, lon2)
    return abs(gap) <= _orb(p1, p2)


def ithasala(p1: str, lon1: float, p2: str, lon2: float) -> Optional[TajikaYoga]:
    """Ithasala between two planets, else None. The faster planet must be APPLYING to the
    exact aspect (PRASNA-4 stanzas 54-55): the directed separation still shrinks toward
    exactness."""
    faster, slower, _sep, angle, gap = _directed(p1, lon1, p2, lon2)
    if abs(gap) > _orb(p1, p2) or gap < -1e-9:
        return None
    name = "Poorna Ithasala" if abs(gap) <= _POORNA_ORB else "Ithasala"
    return TajikaYoga(name, (faster, slower), angle, abs(gap), True,
                      Citation("PRASNA-4", 1068))


def easarapha(p1: str, lon1: float, p2: str, lon2: float) -> Optional[TajikaYoga]:
    """Easarapha (Musaripha): the faster planet has passed the exact aspect and separates
    (PRASNA-4 stanza 56). Unfavourable."""
    faster, slower, _sep, angle, gap = _directed(p1, lon1, p2, lon2)
    if abs(gap) > _orb(p1, p2) or gap >= -1e-9:
        return None
    return TajikaYoga("Easarapha", (faster, slower), angle, abs(gap), False,
                      Citation("PRASNA-4", 1122))


def naktha(pa: str, lon_a: float, pb: str, lon_b: float,
           pc: str, lon_c: float) -> Optional[TajikaYoga]:
    """Naktha (PRASNA-4 stanza 57): `pa` and `pb` share no aspect; `pc`, FASTER than both
    and in aspect with both, transfers the light."""
    if in_aspect(pa, lon_a, pb, lon_b):
        return None
    if speed_rank(pc) <= max(speed_rank(pa), speed_rank(pb)):
        return None
    if in_aspect(pc, lon_c, pa, lon_a) and in_aspect(pc, lon_c, pb, lon_b):
        return TajikaYoga("Naktha", (pa, pb, pc), 0, 0.0, True, Citation("PRASNA-4", 1151))
    return None


def yamaya(pa: str, lon_a: float, pb: str, lon_b: float,
           pc: str, lon_c: float) -> Optional[TajikaYoga]:
    """Yamaya (PRASNA-4 stanza 60): the two lords share no aspect; `pc`, SLOWER than both
    and in aspect with both, transfers the light."""
    if in_aspect(pa, lon_a, pb, lon_b):
        return None
    if speed_rank(pc) >= min(speed_rank(pa), speed_rank(pb)):
        return None
    if in_aspect(pc, lon_c, pa, lon_a) and in_aspect(pc, lon_c, pb, lon_b):
        return TajikaYoga("Yamaya", (pa, pb, pc), 0, 0.0, True, Citation("PRASNA-4", 1218))
    return None


def kamboola(p1: str, lon1: float, p2: str, lon2: float,
             moon_lon: float) -> Optional[TajikaYoga]:
    """Kamboola (PRASNA-4 stanza 61): Ithasala between the two planets, with the Moon also
    in Ithasala with either of them."""
    pair = ithasala(p1, lon1, p2, lon2)
    if pair is None or "Moon" in (p1, p2):
        return None
    if (ithasala("Moon", moon_lon, p1, lon1) is not None
            or ithasala("Moon", moon_lon, p2, lon2) is not None):
        return TajikaYoga("Kamboola", (p1, p2, "Moon"), pair.aspect_angle,
                          pair.gap_degrees, True, Citation("PRASNA-4", 1255))
    return None
