"""Saturn's transit clock from the Samudaya Shodhyapinda — Patel ch014, Slokas 37-38.

The instruction, verbatim (Ashtakavarga of Patel ch014:941-950):

    "To find the good or bad effects of a particular bhava at a particular period take the
     Shodhyapinda of the Samudayashtakavarga bindus. Multiply it by the corresponding figure
     for that particular bhava and divide the product by 27 to find the remainder. When Saturn
     passes through the asterism indicated by the remainder (counted from Aswini), there will
     be destruction of the effects of that bhava."

And the worked example that pins the arithmetic (ch014:951-960): Samudaya Shodhyapinda 324 ×
33 bindus in the 1st = 10692; ÷27 leaves 0 → "Revati, Aslesha and Jyeshta are the asterisms";
÷12 leaves 0 → "Meena, Kataka and Vrischika are the rasis". So the marker is a **triad** (the
star and its two trines), remainder 0 maps to the LAST element (Revati / Meena), and there is
a parallel rasi clock.

**This module was reviewed and its first version FAILED (bphs-doctrine-reviewer, 2026-08-07).**
Recorded so the error class stays visible:

* The formula was wrong — each planet's OWN bhinna pinda was reduced modulo 27, a computation
  in none of the cited texts. Patel's rule is the **Samudaya** (combined, post-Shodhana) pinda
  **multiplied by the bhava's own bindus**: a per-BHAVA marker, not a per-planet one.
* The triad (star + trines) and the rasi half were silently absent.
* The comparison used Saturn's NATAL nakshatra while the reader-facing string said "stands on"
  — the rule is a TRANSIT clock, and a natal coincidence is a permanently-true, weaker claim.
  The comparison is now against Saturn's transit position at the report's own reference date.

**What stays deliberately unencoded**, each with its reason:

* The LONGEVITY limb (per-planet pindas × 8th-house bindus ÷ 27, quotient as Ayus years —
  Patel ch015:138-144, and the x7/27 application in ASP-14). Raman's caveat is aimed exactly
  here: the Ashtakavarga method of longevity "does not seem to be quite reliable"
  (HTJAH-II:4453-4456, verbatim-verified). Adding it must be a deliberate act with its own
  doctrine review. A test asserts the arithmetic is absent.
* The REKHA half (Sloka 39, ch014:997-1003): the mirrored computation on rekhas for the GOOD
  effects of the bhava. Omitted for now and SAID here rather than left silent — encoding it
  needs the rekha-shodhana grids this module does not touch.
* Citation reach: BPHS vol2 ch071:40 attests the rekha-span LONGEVITY method only, not this
  transit rule; the timing rests on Patel ch014 alone.

AV band discipline: corroborative, never decisive (Raman's own rating of Ashtakavarga),
report-layer only, no verdict feed (PREC-10).

Usage:
    from app.raman_saab.doctrine.av_pinda_timing import bhava_saturn_markers
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Optional

from app.raman_saab.chart.model import RamanChart

#: The 27 nakshatras, Aswini first. Remainder r maps to index r-1; remainder 0 to the LAST
#: (Revati) — pinned by Patel's own worked example ("divided by 27 leaves remainder 0.
#: Revati…", ch014:951-953).
_NAK: Final[tuple[str, ...]] = (
    "Aswini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra", "Punarvasu", "Pushya",
    "Aslesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Visakha", "Anuradha", "Jyeshta", "Mula", "Purva Ashadha", "Uttara Ashadha", "Sravana",
    "Dhanishta", "Satabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)

_SIGNS: Final[tuple[str, ...]] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

#: The seven contributing grahas — the nodes have no Ashtakavarga of their own.
_GRAHAS: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                   "Venus", "Saturn")


@dataclass(frozen=True)
class BhavaSaturnMarker:
    """One bhava's Saturn-transit marker triad, per Patel ch014 sl.37-38."""

    house: int
    samudaya_pinda: int
    bhava_bindus: int              # the reduced samudaya bindus of the bhava's sign
    product: int
    nakshatras: tuple[str, ...]    # the remainder star and its two trines
    rasis: tuple[str, ...]         # the parallel ÷12 clock, same triad shape
    saturn_transit_nakshatra: Optional[str]
    saturn_transit_rasi: Optional[str]
    saturn_on_nakshatra: bool
    saturn_on_rasi: bool


def _triad_27(remainder: int) -> tuple[str, ...]:
    """The asterism for a ÷27 remainder plus its two trines (9 apart), remainder 0 = Revati."""
    idx = (remainder - 1) % 27
    return tuple(_NAK[(idx - 9 * k) % 27] for k in range(3))


def _triad_12(remainder: int) -> tuple[str, ...]:
    """The rasi for a ÷12 remainder plus its two trines (4 apart), remainder 0 = Pisces."""
    idx = (remainder - 1) % 12
    return tuple(_SIGNS[(idx - 4 * k) % 12] for k in range(3))


def samudaya_shodhya_pinda(chart: RamanChart) -> tuple[int, dict[int, int]]:
    """The Samudaya (combined, post-Shodhana) grid and its Shodhyapinda.

    The grid is the per-sign sum of every graha's REDUCED bhinnashtakavarga — the table Patel
    prints as "Samudayashtakavarga — Trikona and Ekadhipatya Shodhana of bindus" (ch014). The
    pinda applies the same two Gunakaras HPA-26 defines, to that combined grid.
    """
    from app.raman_saab.primitives.ashtakavarga_pinda import graha_gunakara, rasi_gunakara
    from app.raman_saab.primitives.ashtakavarga_reduction import reduced_bhinnashtakavarga

    grid: dict[int, int] = {s: 0 for s in range(1, 13)}
    for g in _GRAHAS:
        reduced = reduced_bhinnashtakavarga(chart, g)
        for s in range(1, 13):
            grid[s] += reduced.get(s, 0)
    occupancy = {g: chart.planets[g].sign for g in _GRAHAS if g in chart.planets}
    pinda = rasi_gunakara(grid) + graha_gunakara(grid, occupancy)
    return pinda, grid


def bhava_saturn_markers(chart: RamanChart, ref_jd: float) -> tuple[BhavaSaturnMarker, ...]:
    """Every bhava's marker triads, and where TRANSIT Saturn stands at `ref_jd`.

    Pure read on the natal side; the one computation is Saturn's transit position at the
    report's own reference date — the same date every other "now" in the report uses.
    """
    import swisseph as swe

    pinda, grid = samudaya_shodhya_pinda(chart)

    # transit Saturn at ref_jd, sidereal per the chart's own ayanamsa (Lahiri lock)
    sat_nak: Optional[str] = None
    sat_rasi: Optional[str] = None
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        lon = swe.calc_ut(ref_jd, swe.SATURN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0] % 360.0
        sat_nak = _NAK[int(lon // (360.0 / 27))]
        sat_rasi = _SIGNS[int(lon // 30.0)]
    except Exception:                                              # noqa: BLE001
        pass

    out: list[BhavaSaturnMarker] = []
    for house in range(1, 13):
        sign = ((chart.asc_sign - 1) + (house - 1)) % 12 + 1
        bindus = grid.get(sign, 0)
        product = pinda * bindus
        if product <= 0:
            continue                       # a zero product names no asterism — no marker
        naks = _triad_27(product % 27)
        rasis = _triad_12(product % 12)
        out.append(BhavaSaturnMarker(
            house=house, samudaya_pinda=pinda, bhava_bindus=bindus, product=product,
            nakshatras=naks, rasis=rasis,
            saturn_transit_nakshatra=sat_nak, saturn_transit_rasi=sat_rasi,
            saturn_on_nakshatra=sat_nak is not None and sat_nak in naks,
            saturn_on_rasi=sat_rasi is not None and sat_rasi in rasis))
    return tuple(out)
