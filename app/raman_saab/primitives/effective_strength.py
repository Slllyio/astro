"""Effective strength of a graha — Shadbala read together with the placement facts Raman
treats as overriding it (DOCTRINE_BACKLOG B1).

Raw Shadbala is not the whole of a planet's power in Raman's own judgments. The decisive
case is HTJAH-I:3788, where a *strong* lord is nonetheless read as powerless:

    "Though the Karaka Mars is well disposed, the fact of the ruler of the third becoming
     combust and hence powerless, renders the third house weak. This stands against his
     having any brothers."

The engine's Shadbala pillar reads that lord strong, so any comparison built on
`is_powerful` alone contradicts Raman on his own worked chart. B1 records the requirement:
comparative weighing must fold "combustion / debilitation-uncancelled / dusthana" into a
factor's effective strength, not just total Shadbala.

**This module is a MEASURE, not a policy.** It reports the facts and the bands; it does not
decide a verdict, gate a yoga, or rank the three factors. That deliberate line exists because
the obvious shortcut — treating `is_powerful` as "powerful lord" — was tried and over-fires
badly (Shankha 102/164, Kahala 48/164 → four HPA-20 yogas deferred, yogas.py:922-933). A
consumer that wants to gate on this must measure its effect on the golden ratchet first.

No coefficient here is invented. The only numbers are Raman's own MIN_REQUIRED bars
(GBB-8:303-312) and the marginal band already shipped and tuned under B2
(house_template._MARGINAL_BAND, GBB-1:38-60 — strength scales continuously, there is no cliff).

Usage:
    from app.raman_saab.primitives.effective_strength import effective_strength
    es = effective_strength("Mercury", chart)
    if es.decisively_weak: ...        # Raman would not let this factor carry the matter
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives import relationships
from app.raman_saab.primitives.bhangas import neecha_bhanga
from app.raman_saab.primitives.combustion import combust_fraction
from app.raman_saab.primitives.shadbala.total import MIN_REQUIRED
from app.raman_saab.ordinals import ordinal

#: Rupas below MIN_REQUIRED still counted "not decisively weak" — the B2 band, already shipped
#: and golden-tuned in house_template._MARGINAL_BAND. Duplicated as a module constant rather
#: than imported so this primitive never depends on the judge layer (which imports primitives).
MARGINAL_BAND: Final[float] = 0.2

#: The dusthanas. Raman treats the 6th/8th/12th as houses of affliction throughout; a factor
#: sitting there is reported, never silently penalised — see `in_dusthana` below.
DUSTHANAS: Final[frozenset[int]] = frozenset({6, 8, 12})


@dataclass(frozen=True)
class EffectiveStrength:
    """One graha's strength picture: the Shadbala number plus the facts that override it.

    `band` is the Shadbala reading alone ("strong" / "marginal" / "weak" / "unknown" when the
    chart carries no Shadbala). `decisively_weak` is the B1 question — whether Raman would let
    this factor carry a matter — and is True when the Shadbala band is weak OR a hard
    placement fact makes it powerless regardless of the number.
    """

    planet: str
    rupas: float | None
    band: str
    combust: float                    # 0.0 free .. 1.0 exact conjunction with the Sun
    debilitated_uncancelled: bool
    in_dusthana: bool
    reasons: tuple[str, ...]

    @property
    def decisively_weak(self) -> bool:
        """True when this factor cannot be read as carrying its matter.

        Combustion and uncancelled debilitation are HARD: HTJAH-I:3788 reads a combust lord
        "powerless" while its Shadbala is strong, so the number cannot outvote them. A
        dusthana placement is reported but is NOT hard on its own — Raman's dusthana readings
        are matter-specific (a strong dusthana lord *feeds* an affliction rather than curing
        it, detailed_report clause-1.5), so folding it in here would double-count."""
        return bool(self.band == "weak" or self.combust > 0.0
                    or self.debilitated_uncancelled)


def effective_strength(planet: str, chart: RamanChart) -> EffectiveStrength:
    """Read `planet`'s Shadbala together with the placement facts that override it."""
    p = chart.planets.get(planet)
    if p is None:
        return EffectiveStrength(planet, None, "unknown", 0.0, False, False,
                                 ("not present on this chart",))

    rupas = p.shadbala_rupas.total / 60.0 if p.shadbala_rupas is not None else None
    bar = MIN_REQUIRED.get(planet)
    reasons: list[str] = []

    if rupas is None or bar is None:
        band = "unknown"                      # Rahu/Ketu carry no Shadbala (GBB-3, 7 grahas)
    elif rupas >= bar:
        band = "strong"
    elif rupas >= bar - MARGINAL_BAND:
        band = "marginal"
        reasons.append(f"Shadbala {rupas:.2f} is within {MARGINAL_BAND} rupa of the "
                       f"{bar} bar (GBB-8:303-312; marginal band GBB-1:38-60)")
    else:
        band = "weak"
        reasons.append(f"Shadbala {rupas:.2f} is below the {bar}-rupa bar (GBB-8:303-312)")

    combust = combust_fraction(planet, chart)
    if combust > 0.0:
        reasons.append(f"combust ({combust:.2f} of the orb) — Raman reads a combust ruler "
                       f"'powerless' even when otherwise well disposed (HTJAH-I:3788)")

    # DEBILITATION maps planet -> (sign, deep-fall degree); only the sign matters here.
    _deb = relationships.DEBILITATION.get(planet)
    debilitated = bool(_deb is not None and _deb[0] == p.sign)
    deb_uncancelled = bool(debilitated and not neecha_bhanga(planet, chart))
    if debilitated:
        reasons.append("debilitated, cancellation NOT established (HPA-33:308)"
                       if deb_uncancelled else "debilitated but cancelled (neecha-bhanga)")

    in_dusthana = p.bhava in DUSTHANAS
    if in_dusthana:
        reasons.append(f"placed in the {ordinal(p.bhava)}, a dusthana (reported, not penalised here)")

    return EffectiveStrength(planet, rupas, band, combust, deb_uncancelled, in_dusthana,
                             tuple(reasons))
