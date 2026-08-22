"""Vimsopaka over a real chart — joins the division maths to Parashara's relationship doctrine.

`primitives/vimsopaka.py` scores a planet given its Varga Viswa per division; `primitives/
relationships.py` decides those Viswa keys. This module supplies the missing input: **which sign
the planet actually occupies in each division**, computed from its longitude.

The varga arithmetic itself is stream-agnostic — the D9 of a longitude is the same number in every
tradition, and re-deriving it here would be duplication for its own sake. So this imports the
shared sign-functions (`app.raman_saab.chart.varga`, explicitly on the substrate allowlist in
`tests/parashara/test_engine_isolation.py`). What is NOT shared is the judgment applied to those
signs: the weights, the Viswa scale and the bands are all Parashara's, from BPHS ch.7.

A note on the temporary relationship: sloka 56 counts house-distance **between the two planets in
the birth chart** (a chart-specific fact), not within the division. So the compound relationship
uses each planet's RASI position, while the sign whose lord is being related to comes from the
DIVISION. Mixing those up is the easy error here — it would make the temporary component
meaningless.

Usage:
    from app.parashara.chart.vimsopaka_chart import vimsopaka_for
    r = vimsopaka_for("Jupiter", {"Jupiter": 125.4, "Saturn": 310.2, ...}, scheme="saptavarga")
"""
from __future__ import annotations

from typing import Mapping

from app.parashara.primitives import relationships as rel
from app.parashara.primitives.vimsopaka import SCHEMES, VimsopakaScore, vimsopaka
from app.raman_saab.chart import varga as _varga     # substrate: pure division arithmetic


def _division_number(tag: str) -> int:
    """'D9' -> 9."""
    return int(tag[1:])


def viswa_by_varga(planet: str, longitudes: Mapping[str, float], *,
                   scheme: str = "shodasavarga") -> dict[str, str]:
    """The Varga Viswa key for `planet` in every division the scheme names.

    Args:
        planet: the graha being weighed (one of `relationships.GRAHAS`).
        longitudes: sidereal longitude in degrees for every graha in the chart. The subject
            planet must be present; the other grahas are needed only to find sign lords'
            positions for the temporary relationship.
        scheme: which Vimsopaka scheme's divisions to cover.
    """
    if planet not in longitudes:
        raise ValueError(f"{planet} has no longitude in the chart")
    try:
        divisions = SCHEMES[scheme]
    except KeyError:
        raise ValueError(f"unknown Vimsopaka scheme {scheme!r}") from None

    subject_sign = int(longitudes[planet] % 360.0 // 30) + 1
    out: dict[str, str] = {}
    for tag in divisions:
        vsign = _varga.varga_sign(longitudes[planet] % 360.0, _division_number(tag))
        lord = rel.SIGN_LORDS[vsign]
        if lord == planet:
            out[tag] = "own"
            continue
        if lord not in longitudes:
            # Cannot compute the temporary half without the lord's own position. Parashara's
            # compound needs both halves, so refuse rather than silently fall back to naisargika.
            raise ValueError(
                f"{tag}: {planet} sits in {lord}'s sign, but {lord} has no longitude in the chart")
        # Sloka 56 counts the distance in the BIRTH chart, not inside the division.
        lord_sign = int(longitudes[lord] % 360.0 // 30) + 1
        distance = ((lord_sign - subject_sign) % 12) + 1
        out[tag] = rel.compound(planet, lord, house_distance=distance)
    return out


def vimsopaka_for(planet: str, longitudes: Mapping[str, float], *,
                  scheme: str = "shodasavarga") -> VimsopakaScore:
    """Vimsopaka bala for one planet in a real chart — the end-to-end entry point."""
    return vimsopaka(planet, viswa_by_varga(planet, longitudes, scheme=scheme), scheme=scheme)


def vimsopaka_all(longitudes: Mapping[str, float], *,
                  scheme: str = "shodasavarga") -> dict[str, VimsopakaScore]:
    """Vimsopaka for each of the seven grahas present in the chart.

    Rahu/Ketu are skipped: Parashara's relationship formula has no moolatrikona or exaltation
    lordship for the nodes, so a Viswa for them would be invented rather than derived.
    """
    return {g: vimsopaka_for(g, longitudes, scheme=scheme)
            for g in rel.GRAHAS if g in longitudes}
