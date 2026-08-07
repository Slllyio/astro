"""Shodhya Pinda → nakshatra, and where Saturn stands against it.

    "Longevity summed from bindu-spans across the eight Ashtakavargas, and bhava-destruction
     timed by Saturn's transit over the Shodhyapinda-derived nakshatra"
     (BPHS vol2 ch071:40; Patel ch014:941-1027, ch015:132-674)

`SYN_N10` carried the note "(Shodhyapinda not computed; on record only.)" That note is STALE —
`primitives/ashtakavarga_pinda` computes it, and has since the ASP corpus correction of
2026-08-03: `PindaBreakdown.total` is Rasi Pinda + Graha Pinda, which is what the wider
literature calls the Shodhya Pinda ("The sum of the Rasi figures (Rasi Pinda) and Planetary
figures (Graha Pinda) will be the Sodya Pinda for each planet", ASP-14:196-198). The rule's
blocker was removed and nobody updated the rule.

**Only the TIMING half is encoded here, and that is a doctrinal decision, not an omission.**
The rule has two limbs:

* *bhava-destruction timed by Saturn over the Shodhyapinda nakshatra* — precise, mechanical,
  and encoded: the Pinda reduced modulo 27 names a nakshatra, and Saturn either transits it or
  does not.
* *longevity summed from bindu-spans* — NOT encoded. Raman's own caveat is aimed exactly and
  only here: the Ashtakavarga method of longevity "does not seem to be quite reliable"
  (HTJAH-II:4453-4456). The x7/27 Ayurdaya application is described in the pinda module's
  docstring and deliberately left unimplemented. Encoding a lifespan from a method its own
  authority distrusts would be the opposite of this project's rule.

So this reports a MARKER the classical method uses, never an outcome. Nothing here times a
death, and nothing here touches a verdict — AV band, corroborative, PREC-10.

Usage:
    from app.raman_saab.doctrine.av_pinda_timing import pinda_nakshatras
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.model import RamanChart

#: The 27 nakshatras, Aswini first — the frame the Pinda residue is counted in.
_NAK: Final[tuple[str, ...]] = (
    "Aswini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra", "Punarvasu", "Pushya",
    "Aslesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Visakha", "Anuradha", "Jyeshta", "Mula", "Purva Ashadha", "Uttara Ashadha", "Sravana",
    "Dhanishta", "Satabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)

#: Saturn's own Ashtakavarga is the frame the classical timing uses; the seven visible grahas
#: carry a Shodhya Pinda, the nodes do not (they contribute no Ashtakavarga of their own).
PINDA_PLANETS: Final[tuple[str, ...]] = ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                         "Venus", "Saturn")


@dataclass(frozen=True)
class PindaNakshatra:
    planet: str
    pinda: int
    index: int                 # 0-based into _NAK
    nakshatra: str
    saturn_is_there: bool      # Saturn's NATAL nakshatra coincides with this marker


def pinda_nakshatras(chart: RamanChart) -> tuple[PindaNakshatra, ...]:
    """Each planet's Shodhya Pinda and the nakshatra its residue names.

    A pure read: the Pinda is already computed, and this only counts it into a frame. The
    residue is taken modulo 27 — a Pinda is a bindu-count, not a longitude, so this is a
    COUNTED position in the nakshatra sequence and not a zodiacal one.
    """
    from app.raman_saab.primitives.ashtakavarga_pinda import ashtakavarga_pinda

    # `PlanetPos.nakshatra` is a 1-BASED INDEX (1..27), not a name — comparing it to a name
    # made this flag silently False on every chart, which is the shape of failure this project
    # keeps meeting: a check that runs, returns, and can never be true.
    saturn = chart.planets.get("Saturn")
    saturn_idx = getattr(saturn, "nakshatra", None)
    saturn_idx = (int(saturn_idx) - 1) if saturn_idx else None

    out: list[PindaNakshatra] = []
    for p in PINDA_PLANETS:
        if p not in chart.planets:
            continue
        try:
            total = ashtakavarga_pinda(chart, p).total
        except Exception:                                          # noqa: BLE001
            continue
        idx = (total - 1) % 27 if total else 0
        name = _NAK[idx]
        out.append(PindaNakshatra(planet=p, pinda=total, index=idx, nakshatra=name,
                                  saturn_is_there=saturn_idx is not None and saturn_idx == idx))
    return tuple(out)
