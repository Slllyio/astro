"""Nisargayu — natural longevity (BPHS ch.43, slokas 16-17), with the exaltation scale (ch.3 sl.49-50).

The third of Parashara's three longevity methods (Pindayu, Amsayu, Nisargayu). The Raman engine
carries Pindayu + Amsayu but not Nisargayu — this fills that gap on the BPHS side.

    "Nisargayu: 1, 2, 9, 20, 18, 20 and 50 are the years allotted to the Moon, Mars, Mercury, Venus,
     Jupiter, the Sun and Saturn from the period of birth." (BPHS-43:551)

Those seven allotments sum to exactly **120 years** — the canonical full human lifespan — which is
the load-bearing constant here. The allotment is the FULL value "when they are in deep exaltation;
these are halved at deep debilitation" (BPHS-43 notes), scaling proportionally between the two:

    deep exaltation point (ch.3 sl.49-50): Sun Aries 10, Moon Taurus 3, Mars Capricorn 28,
    Mercury Virgo 15, Jupiter Cancer 5, Venus Pisces 27, Saturn Libra 20; debilitation is the 7th
    sign from exaltation at the same degree, i.e. exactly 180 deg away.

    scale = 1.0 at the exaltation point (distance 0), 0.5 at the debilitation point (distance 180),
    linear in the angular distance between — the classical Ayurdaya rasmi curve.

## Scope — what this module does and does NOT do
This is the DISTINCTIVE core of Nisargayu: the natural allotment and the exaltation scaling. The
"full" Nisargayu additionally applies the FOUR Pindayu reductions (the haranas — Chakrapata,
Astangata, etc.) and an Ascendant contribution "the same as in the Pindayu scheme" (BPHS-43:568).
Those reductions are a large shared method not yet built; `nisargayu_span` returns the pre-reduction
natural span and says so, so nothing is silently presented as the final figure.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.parashara.doctrine.sources import Citation
from app.parashara.primitives.relationships import EXALTATION

#: Full natural-lifespan allotment per graha, in years (BPHS-43:551). Nodes have no allotment.
NISARGAYU_YEARS: Final[Mapping[str, float]] = {
    "Moon": 1, "Mars": 2, "Mercury": 9, "Venus": 20, "Jupiter": 18, "Sun": 20, "Saturn": 50,
}
#: Full human lifespan = the allotments summed.
FULL_SPAN: Final[float] = 120.0

#: Deep-exaltation degree WITHIN the exaltation sign (BPHS-3:894). Sign comes from EXALTATION.
EXALT_DEGREE: Final[Mapping[str, float]] = {
    "Sun": 10, "Moon": 3, "Mars": 28, "Mercury": 15, "Jupiter": 5, "Venus": 27, "Saturn": 20,
}

YEARS_SOURCE: Final[Citation] = Citation("BPHS-43", 551)
EXALT_SOURCE: Final[Citation] = Citation("BPHS-3", 894)


def deep_exaltation_point(planet: str) -> float:
    """Absolute sidereal longitude (0..360) of `planet`'s deepest exaltation (ch.3 sl.49-50)."""
    if planet not in EXALT_DEGREE:
        raise ValueError(f"no exaltation defined for {planet!r}")
    return (EXALTATION[planet] - 1) * 30.0 + EXALT_DEGREE[planet]


def exaltation_scale(planet: str, longitude: float) -> float:
    """The Nisargayu scale factor at `longitude`: 1.0 at deep exaltation -> 0.5 at deep debilitation.

    Linear in the angular distance from the exaltation point (0 deg -> full, 180 deg -> half).
    """
    exalt = deep_exaltation_point(planet)
    diff = abs((longitude % 360.0) - exalt) % 360.0
    distance = min(diff, 360.0 - diff)          # 0..180, circular
    return 1.0 - 0.5 * (distance / 180.0)


@dataclass(frozen=True)
class NisargayuContribution:
    planet: str
    full_years: float           # the allotment before scaling
    scale: float                # exaltation scale factor 0.5..1.0
    years: float                # full_years * scale


def contribution(planet: str, longitude: float) -> NisargayuContribution:
    """One graha's Nisargayu contribution at its longitude (pre-reduction)."""
    if planet not in NISARGAYU_YEARS:
        raise ValueError(f"Nisargayu has no allotment for {planet!r} (nodes are excluded)")
    full = NISARGAYU_YEARS[planet]
    scale = exaltation_scale(planet, longitude)
    return NisargayuContribution(planet=planet, full_years=full, scale=scale, years=full * scale)


@dataclass(frozen=True)
class NisargayuSpan:
    per_planet: Mapping[str, NisargayuContribution]
    natural_years: float        # sum of scaled contributions, BEFORE the Pindayu reductions
    reductions_applied: bool    # always False here — see module docstring


def nisargayu_span(longitudes: Mapping[str, float]) -> NisargayuSpan:
    """The natural (pre-reduction) Nisargayu span from the seven grahas' longitudes.

    `reductions_applied=False` is stated on the result so this pre-reduction figure is never
    mistaken for the final longevity — the haranas + Ascendant contribution are a later tranche.
    """
    contribs = {p: contribution(p, longitudes[p]) for p in NISARGAYU_YEARS if p in longitudes}
    return NisargayuSpan(per_planet=contribs,
                         natural_years=sum(c.years for c in contribs.values()),
                         reductions_applied=False)
