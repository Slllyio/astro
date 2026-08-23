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


_ONE_NAVAMSA: Final[float] = 10.0 / 3.0        # 3 deg 20'

ASCENDANT_SOURCE: Final[Citation] = Citation("BPHS-43", 411)   # "years granted by the ascendant"


def _ascendant_years_rasi(asc_sign: int, asc_deg_in_rasi: float) -> float:
    """Ascendant-lord-stronger case (BPHS-43:411): signs from Aries to the sign before the
    ascendant + the ascendant degrees as year-fraction (30 deg = 1 year)."""
    return (asc_sign - 1) + (asc_deg_in_rasi / 30.0)


def _ascendant_years_navamsa(navamsa_lagna_sign: int, asc_deg_in_rasi: float) -> float:
    """Navamsa-lagna-lord-stronger case (BPHS-43:420): signs to the one before the Navamsa Lagna +
    the fraction of the current navamsa traversed (one navamsa = 3 deg 20' = 1 year). Verified
    against Parashara's worked nativity: Navamsa Lagna Cancer, asc 0-48-34 -> 3.2428 years."""
    frac = (asc_deg_in_rasi % _ONE_NAVAMSA) / _ONE_NAVAMSA
    return (navamsa_lagna_sign - 1) + frac


@dataclass(frozen=True)
class HaranaReducedSpan:
    per_planet: Mapping[str, "hr.HaranaResult"]
    contributions: Mapping[str, NisargayuContribution]  # the pre-reduction scaled allotments
    planetary_years: float       # sum of scaled allotments AFTER the four haranas
    ascendant_added: bool        # always False — the Ascendant contribution is a later tranche


def nisargayu_after_haranas(chart) -> HaranaReducedSpan:
    """Nisargayu's seven planetary contributions after the four haranas (BPHS-43:567).

    Applies Astangata / Satru Kshetra / Vyayadi / Kroorodaya per graha, takes only the highest per
    graha (BPHS-43:392), and honours Vyayadi's "only the strongest of planets sharing a bhava loses"
    (BPHS-43:429) using the partial Shadbala. The Ascendant's own contribution (BPHS-43:569) forks on
    a navamsa-lord strength comparison and is DEFERRED — `ascendant_added=False` says so, so this
    harana-reduced planetary span is never mistaken for the final longevity.
    """
    from app.parashara.primitives import haranas as hr
    from app.parashara.primitives import graha_drishti as gd
    from app.parashara.primitives.relationships import SIGN_LORDS, naisargika
    from app.parashara.primitives.combustion import is_combust
    from app.parashara.primitives.shadbala.total import partial_shadbala

    lons = chart.longitudes
    sun = lons["Sun"]
    present = [p for p in NISARGAYU_YEARS if p in lons]
    signs = {p: int(lons[p] % 360.0 // 30) + 1 for p in present}
    all_signs = {p: int(l % 360.0 // 30) + 1 for p, l in lons.items()}
    contribs = {p: contribution(p, lons[p]) for p in present}

    # a benefic aspecting the lagna halves Kroorodaya (BPHS-43:381)
    lagna_aspecters = gd.planets_aspecting_sign(chart.asc_sign, all_signs)
    benefic_aspects_lagna = any(hr.is_longevity_benefic(q) for q in lagna_aspecters)

    frac: dict[str, list[float]] = {}
    for p in present:
        sign = signs[p]
        lord = SIGN_LORDS[sign]
        house = ((sign - chart.asc_sign) % 12) + 1
        retro = chart.speeds.get(p, 0.0) < 0.0
        frac[p] = [
            hr.astangata_fraction(p, combust=is_combust(p, lons[p], sun, retrograde=retro)),
            hr.satru_kshetra_fraction(
                in_enemy_sign=(p != lord and naisargika(p, lord) == "shatru"), retrograde=retro),
            hr.vyayadi_fraction(house, is_benefic=hr.is_longevity_benefic(p)),
            hr.kroorodaya_fraction(p, in_lagna=(house == 1), asc_longitude=chart.asc_longitude,
                                   benefic_aspect=benefic_aspects_lagna),
        ]

    # Vyayadi: when several grahas share a bhava, only the STRONGEST loses (BPHS-43:429).
    by_house: dict[int, list[str]] = {}
    for p in present:
        house = ((signs[p] - chart.asc_sign) % 12) + 1
        if house in hr._VYAYADI:
            by_house.setdefault(house, []).append(p)
    for plist in by_house.values():
        if len(plist) > 1:
            strength = {q: partial_shadbala(
                q, lons, asc_sign=chart.asc_sign, asc_longitude=chart.asc_longitude,
                moon_waxing=chart.moon_waxing, speed=chart.speeds.get(q, 0.0),
                ayanamsa=chart.ayanamsa, kala_ctx=chart.kala).virupas for q in plist}
            strongest = max(plist, key=lambda q: strength[q])
            for q in plist:
                if q != strongest:
                    frac[q][2] = 0.0

    _NAMES = ("Astangata", "Satru Kshetra", "Vyayadi", "Kroorodaya")
    results: dict[str, "hr.HaranaResult"] = {}
    total = 0.0
    for p in present:
        a, s, v, k = frac[p]
        net = hr.net_fraction(a, s, v, k)
        reason = "none" if net == 0.0 else _NAMES[[a, s, v, k].index(net)]
        results[p] = hr.HaranaResult(planet=p, astangata=a, satru_kshetra=s, vyayadi=v,
                                     kroorodaya=k, net=net, reason=reason)
        total += contribs[p].years * (1.0 - net)
    return HaranaReducedSpan(per_planet=results, contributions=contribs,
                             planetary_years=total, ascendant_added=False)


@dataclass(frozen=True)
class NisargayuFull:
    planetary_years: float       # harana-reduced planetary contributions
    ascendant_years: float       # the Ascendant's own contribution (BPHS-43:411)
    ascendant_method: str        # "rasi" (asc lord stronger) | "navamsa" (navamsa-lagna lord stronger)
    total_years: float           # the complete Nisargayu span
    haranas: HaranaReducedSpan


def ascendant_contribution(chart) -> tuple[float, str]:
    """The Ascendant's Nisargayu years and which method applied, by the stronger of the ascendant
    lord vs the navamsa-lagna lord (BPHS-43:411-431). Undergoes no harana check."""
    from app.raman_saab.chart import varga as _v
    from app.parashara.primitives.relationships import SIGN_LORDS
    from app.parashara.primitives.shadbala.total import partial_shadbala

    asc_deg_in_rasi = chart.asc_longitude % 30.0
    navamsa_lagna = _v.navamsa_sign(chart.asc_longitude % 360.0)
    asc_lord = SIGN_LORDS[chart.asc_sign]
    nav_lord = SIGN_LORDS[navamsa_lagna]

    def strength(p: str) -> float:
        if p not in chart.longitudes:
            return 0.0
        return partial_shadbala(
            p, chart.longitudes, asc_sign=chart.asc_sign, asc_longitude=chart.asc_longitude,
            moon_waxing=chart.moon_waxing, speed=chart.speeds.get(p, 0.0),
            ayanamsa=chart.ayanamsa, kala_ctx=chart.kala).virupas

    if strength(nav_lord) > strength(asc_lord):
        return _ascendant_years_navamsa(navamsa_lagna, asc_deg_in_rasi), "navamsa"
    return _ascendant_years_rasi(chart.asc_sign, asc_deg_in_rasi), "rasi"


def nisargayu_full(chart) -> NisargayuFull:
    """The complete Nisargayu span: harana-reduced planetary contributions + the Ascendant's own
    contribution (BPHS-43). This is the final figure the pre-reduction `nisargayu_span` deferred."""
    hs = nisargayu_after_haranas(chart)
    asc_years, method = ascendant_contribution(chart)
    return NisargayuFull(planetary_years=hs.planetary_years, ascendant_years=asc_years,
                         ascendant_method=method, total_years=hs.planetary_years + asc_years,
                         haranas=hs)
