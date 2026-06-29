"""Jaimini interpretation layer — reads the Karakamsa (Jaimini Sutras 1, pada-2).

ADDITIVE and PARALLEL to the Parashari house verdicts: it never alters them. Jaimini and Parashari
are parallel schools; letting Jaimini move the Parashari verdict would be the same distortion the
project rejects elsewhere. This layer is surfaced alongside the verdicts, as a separate reading.

The Karakamsa is the Atmakaraka's navamsa sign, read as a lagna in the D9. A planet OCCUPYING the
Karakamsa — its navamsa sign equals the AK's navamsa sign, i.e. it is conjunct the Atmakaraka in the
navamsa — colours the soul's profession / inclination per Jaimini Sutras 1.2 Su.14-22. (Rahu and
Ketu can OCCUPY the Karakamsa even though, per the locked 7-karaka rule, they can never BE the
Atmakaraka.)

Usage:
    from app.raman_saab.primitives import jaimini_reading as jr
    jr.karakamsa_indications(chart)   # [(planet, profession/inclination), ...]
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.special_points import atmakaraka

#: Jaimini Sutras 1.2 Su.14-22 — planet conjunct the Atmakaraka in the navamsa -> profession.
_KARAKAMSA_PROFESSION: Final[dict[str, str]] = {
    "Sun":     "public service / political life / authority (JS 1.2 Su.14)",
    "Moon":    "comforts & public/nurturing dealings; with Venus, wealth + a life of education (JS 1.2 Su.15)",
    "Mars":    "medicine & surgery, arms, fire-trades, engineering / alchemy (JS 1.2 Su.16)",
    "Mercury": "commerce, textiles & weaving, arts & crafts, social-political affairs (JS 1.2 Su.17)",
    "Jupiter": "Vedic / religious wisdom, Vedanta, teaching, priestly learning (JS 1.2 Su.18)",
    "Venus":   "high office / political life, refinement, long vitality (JS 1.2 Su.19)",
    "Saturn":  "fame & mastery in one's own established line of work (JS 1.2 Su.20)",
    "Rahu":    "weapons / machinery, poisons & medicine, metals, unconventional trades (JS 1.2 Su.21)",
    "Ketu":    "livestock / elephant trades, marginal or unconventional lines (JS 1.2 Su.22)",
}
_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def karakamsa_sign(chart: RamanChart) -> int:
    """The Karakamsa sign (1..12) — the Atmakaraka's navamsa sign."""
    return chart.planets[atmakaraka(chart)].navamsa_sign


def karakamsa_indications(chart: RamanChart) -> list[tuple[str, str]]:
    """(planet, profession/inclination) for each planet OCCUPYING the Karakamsa (navamsa-conjunct
    the Atmakaraka), in natural order. The Atmakaraka itself occupies the Karakamsa by definition,
    so its own nature is the primary reading."""
    ks = karakamsa_sign(chart)
    out: list[tuple[str, str]] = []
    for planet in _ORDER:
        p = chart.planets.get(planet)
        if p is not None and p.navamsa_sign == ks:
            out.append((planet, _KARAKAMSA_PROFESSION[planet]))
    return out
