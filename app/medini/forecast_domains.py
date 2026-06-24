"""Mundane-domain attribution: which worldly affairs does each event touch?

In classical mundane astrology, each graha rules specific spheres of
collective life. Phaladeepika Ch.27 ("Predictions for the country and
king"), BPHS Ch.99 (Sun's apparent retrograde and effects), and Varahamihira's
Brihat Samhita all map planet -> mundane domain. We bundle a conservative
lookup keyed off those sources so each event in the forecast can be tagged
with the spheres it likely affects.

Sources for each mapping are noted inline as comments — these are the
classical anchors, not modern speculation. Edit cautiously; the table is
imported by the route layer and is part of the API contract.

Pure data + helpers; no IO, no DB.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MundaneDomain:
    """One sphere of worldly life affected by a planet's mundane signal."""
    key: str           # short id: 'finance', 'agriculture'
    label: str         # human-readable
    icon: str          # single emoji-free glyph for terminal display
    description: str   # one-line note explaining the linkage


# Domain catalog — keep keys stable; UIs will i18n the labels later.
DOMAINS: dict[str, MundaneDomain] = {
    "politics":      MundaneDomain("politics", "Politics & Government", "G",
                                   "Heads of state, governance, regime stability"),
    "military":      MundaneDomain("military", "Military & Conflict", "M",
                                   "Armies, war, accidents, violence, security"),
    "finance":       MundaneDomain("finance", "Finance & Trade", "F",
                                   "Markets, currency, commerce, wealth flows"),
    "religion":      MundaneDomain("religion", "Religion & Wisdom", "R",
                                   "Religious institutions, teachers, ethics, law"),
    "agriculture":   MundaneDomain("agriculture", "Agriculture & Land", "A",
                                   "Crops, harvest, land tenure, food supply"),
    "weather":       MundaneDomain("weather", "Weather & Climate", "W",
                                   "Rainfall, storms, droughts, seasonal shifts"),
    "public_health": MundaneDomain("public_health", "Public Health", "H",
                                   "Epidemics, hospitals, pandemics, well-being"),
    "communication": MundaneDomain("communication", "Communication & Transport", "C",
                                   "Trade routes, news, transit, intellectual life"),
    "arts":          MundaneDomain("arts", "Arts & Culture", "T",
                                   "Entertainment, fashion, women's affairs, luxury"),
    "labor":         MundaneDomain("labor", "Labor & Workers", "L",
                                   "Working class, mining, service economy, the poor"),
    "foreign":       MundaneDomain("foreign", "Foreign Affairs", "O",
                                   "External relations, immigration, diplomacy"),
    "masses":        MundaneDomain("masses", "Public Sentiment", "P",
                                   "Mood of the populace, mass psychology, water"),
    "tech_disruption": MundaneDomain("tech_disruption", "Technology & Disruption", "D",
                                     "Sudden technological shifts, novelty, scandal"),
}


# --------------------------------------------------------------------------- #
# Per-planet domain mappings                                                   #
# --------------------------------------------------------------------------- #
# Each tuple is ordered by significance (most central domain first). Sources:
# - Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn:
#       Phaladeepika Ch.27 (country/king prediction);
#       BPHS Ch.3 (planetary significations); Brihat Samhita Ch.16.
# - Rahu, Ketu: classical mundane Rahu = foreign/disruption/poisons,
#       Ketu = mysticism/sudden events/eclipses — KN Rao, Predictive
#       Astrology of the Hindus, and Brihat Samhita on grahana-yogas.
_PLANET_DOMAINS: dict[str, tuple[str, ...]] = {
    "Sun":      ("politics", "religion", "public_health"),
    "Moon":     ("masses", "agriculture", "weather", "public_health"),
    "Mars":     ("military", "labor", "agriculture"),
    "Mercury":  ("communication", "finance", "arts"),
    "Jupiter":  ("religion", "finance", "politics"),
    "Venus":    ("arts", "finance", "weather"),
    "Saturn":   ("labor", "agriculture", "politics", "masses"),
    "Rahu":     ("foreign", "tech_disruption", "public_health"),
    "Ketu":     ("religion", "tech_disruption", "public_health"),
}


def domains_for_planet(planet: str) -> tuple[str, ...]:
    """Return the domain keys ruled by ``planet`` (classical mundane only)."""
    return _PLANET_DOMAINS.get(planet, ())


def domains_for_event(event: dict[str, Any]) -> tuple[str, ...]:
    """Compute the union of domains affected by an event.

    * INGRESS / STATION / NEW_MOON / FULL_MOON: domains of the single planet.
    * CONJUNCTION: union of both planets' domains — joint mundane signal.
    * ECLIPSE: solar = Sun-domain union with Rahu-domain (eclipses are
      Rahu-Ketu-luminary phenomena); lunar = Moon + Rahu.
    """
    t = event.get("type")
    if t in {"INGRESS", "STATION", "NEW_MOON", "FULL_MOON"}:
        return domains_for_planet(event.get("planet", ""))

    if t == "CONJUNCTION":
        union: list[str] = []
        seen: set[str] = set()
        for p in (event.get("planet_a", ""), event.get("planet_b", "")):
            for d in domains_for_planet(p):
                if d not in seen:
                    union.append(d)
                    seen.add(d)
        return tuple(union)

    if t == "ECLIPSE":
        # Eclipses always carry node energy (Rahu/Ketu shadow); blend with
        # the luminary.
        family = event.get("family", "")
        union: list[str] = []
        seen: set[str] = set()
        if family == "SOLAR":
            sources = ("Sun", "Rahu")
        elif family == "LUNAR":
            sources = ("Moon", "Rahu")
        else:
            sources = ()
        for p in sources:
            for d in domains_for_planet(p):
                if d not in seen:
                    union.append(d)
                    seen.add(d)
        return tuple(union)

    return ()


def annotate_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Tag each event with its ``domains`` field (immutable copy).

    Returns new dicts so the annotator can be safely chained with severity
    annotation, citation enrichment, etc.
    """
    return [{**e, "domains": list(domains_for_event(e))} for e in events]


def describe_domain(key: str) -> dict[str, str] | None:
    """Look up a domain by key — used by the UI's hover-card tooltips."""
    d = DOMAINS.get(key)
    if d is None:
        return None
    return {"key": d.key, "label": d.label, "icon": d.icon, "description": d.description}
