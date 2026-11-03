"""KP significators: which houses each planet signifies, and at what level.

Krishnamurti's ladder (KPR3-LADDER, stated for houses 2/6/10/11 and applied
by him to every house) ranks a house's significators:

  A  planets in the constellation (star) of the occupants of the house
  B  the occupants
  C  planets in the constellation of the lord of the house
  D  the lord
  E  planets conjoined with or aspected by them   <- opt-in only (rulings R8, R8a)

"Tenant is stronger than owner" (KPR3-TENANT), so A > B > C > D. The planet's
side of the same fact: a planet offers the results of the house occupied by
its star lord (KPR3-STAR-OCCUPIED) and of the houses its star lord owns
(KPR3-STARLORD-HOUSES).

Nodes own no sign. A node is an agent: it "will give the results of the
planets with which it is conjoined then those of the planet which aspects
them. Lastly, those of the lord of the sign" (KPR3-NODE-AGENT). The engine
encodes conjunction (same sign, ruling R6) and the sign lord; the aspect step
is not encoded (ruling R8). The node's agent houses count as its "owned"
houses at levels C/D, tagged ``agent`` so the reader can see where they came
from. Those agent houses belong to the node alone: a planet in a node's star
takes only the house the node occupies (ruling R6a, Krishnamurti's own
significator table for the Alibag chart, KPR5 pp.154-156).

Usage:
    from app.kp.significators import planet_significations, house_significators
    planet_significations(chart)["Venus"]   # tuple[Signification, ...]
    house_significators(chart, 7)           # ordered A..D
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kp.chart import NODES, KPChart, sign_index

LEVELS: Final[tuple[str, ...]] = ("A", "B", "C", "D", "E")
LEVEL_TEXT: Final[dict[str, str]] = {
    "A": "in the star of an occupant",
    "B": "occupant",
    "C": "in the star of the lord",
    "D": "lord",
    "E": "conjoined with or aspected by a significator",
}
LEVEL_CITE: Final[dict[str, str]] = {
    "A": "KPR3-LADDER", "B": "KPR3-LADDER", "C": "KPR3-LADDER-C", "D": "KPR3-LADDER-D",
    "E": "KPR5-LEVEL-E",
}

#: Hindu sign aspects (drishti), counted inclusively: every planet the 7th; Mars also 4 and 8;
#: Jupiter 5 and 9; Saturn 3 and 10. Reader 6 uses them by name ("Jupiter ... aspects Moon by
#: its 5th aspect", "Saturn ... by its 10th aspect", KPR6-DRISHTI). Nodes cast none (ruling R8a).
DRISHTI: Final[dict[str, tuple[int, ...]]] = {
    "Sun": (7,), "Moon": (7,), "Mercury": (7,), "Venus": (7,),
    "Mars": (4, 7, 8), "Jupiter": (5, 7, 9), "Saturn": (3, 7, 10),
}


@dataclass(frozen=True, slots=True)
class Signification:
    """``planet`` signifies ``house`` at ``level``; ``via`` names the planet that carries it."""

    planet: str
    house: int
    level: str
    via: str
    agent: bool = False

    def explain(self) -> str:
        """One-line reason, e.g. ``Venus signifies 7: in the star of Moon, occupant of 7``."""
        if self.level == "B":
            how = f"occupies {self.house}"
        elif self.level == "D":
            how = f"owns {self.house}" if not self.agent else f"represents {self.via}, lord of {self.house}"
        elif self.level == "E":
            how = f"conjoined with or aspected by {self.via}, a significator of {self.house}"
        elif self.level == "A":
            how = f"in the star of {self.via}, which occupies {self.house}"
        else:
            how = f"in the star of {self.via}, lord of {self.house}" + (" (as agent)" if self.agent else "")
        return f"{self.planet} signifies {self.house} [{self.level}]: {how}"


def node_represents(chart: KPChart, node: str) -> tuple[str, ...]:
    """Planets a node stands for: conjoined planets (same sign) first, then its sign lord."""
    s = sign_index(chart.planets[node].longitude)
    conj = tuple(
        p for p, pt in chart.planets.items()
        if p not in NODES and sign_index(pt.longitude) == s
    )
    lord = chart.planets[node].sign_lord
    return conj + ((lord,) if lord not in conj else ())


def _own_levels(chart: KPChart, planet: str) -> list[tuple[int, str, str, bool]]:
    """Houses a planet carries by itself: (house, 'occupied'|'owned', via, agent)."""
    out = [(chart.planets[planet].bhava, "occupied", planet, False)]
    if planet in NODES:
        for rep in node_represents(chart, planet):
            for h in chart.owned_houses(rep):
                out.append((h, "owned", rep, True))
            out.append((chart.planets[rep].bhava, "owned", rep, True))
    else:
        out.extend((h, "owned", planet, False) for h in chart.owned_houses(planet))
    return out


def _aspects(chart: KPChart, a: str, b: str) -> bool:
    """Does ``a`` cast a Hindu sign aspect on ``b``?"""
    if a not in DRISHTI:
        return False
    d = (sign_index(chart.planets[b].longitude) - sign_index(chart.planets[a].longitude)) % 12 + 1
    return d in DRISHTI[a]


def planet_significations(chart: KPChart, *, level_e: bool = False) -> dict[str, tuple[Signification, ...]]:
    """Every planet's significations, strongest level first, deduplicated per (house, level).

    ``level_e=True`` adds the ladder's last level (ruling R8a, off by default):
    a planet conjoined with (same sign) or aspected by (Hindu drishti) a
    significator of a house signifies that house at level E.
    """
    result: dict[str, tuple[Signification, ...]] = {}
    for p, pt in chart.planets.items():
        rows: list[Signification] = []
        star = pt.star_lord
        for h, kind, via, agent in _own_levels(chart, star):
            if agent:
                # Ruling R6a (KPR5 pp.154-156): a planet in a node's star takes the house
                # the node occupies; the node's agent houses stay with the node itself.
                continue
            level = "A" if kind == "occupied" else "C"
            rows.append(Signification(p, h, level, star, agent))
        for h, kind, via, agent in _own_levels(chart, p):
            level = "B" if kind == "occupied" else "D"
            rows.append(Signification(p, h, level, via, agent))
        seen: set[tuple[int, str]] = set()
        uniq = []
        for r in sorted(rows, key=lambda r: (LEVELS.index(r.level), r.house)):
            if (r.house, r.level) not in seen:
                seen.add((r.house, r.level))
                uniq.append(r)
        result[p] = tuple(uniq)
    if not level_e:
        return result
    extra: dict[str, list[Signification]] = {p: [] for p in result}
    for src, rows in result.items():
        houses = {r.house for r in rows}
        s_sign = sign_index(chart.planets[src].longitude)
        for x in chart.planets:
            if x == src:
                continue
            if sign_index(chart.planets[x].longitude) == s_sign or _aspects(chart, src, x):
                extra[x] += [Signification(x, h, "E", src) for h in sorted(houses)]
    out = {}
    for p, rows in result.items():
        have = {r.house for r in rows}
        seen: set[int] = set()
        add = []
        for r in extra[p]:
            if r.house not in have and r.house not in seen:
                seen.add(r.house)
                add.append(r)
        out[p] = rows + tuple(add)
    return out


def houses_signified(chart: KPChart, planet: str, sigs: dict[str, tuple[Signification, ...]] | None = None) -> frozenset[int]:
    """All houses ``planet`` signifies in ``sigs`` (levels A-D unless built with ``level_e``)."""
    sigs = sigs or planet_significations(chart)
    return frozenset(s.house for s in sigs[planet])


def house_significators(chart: KPChart, house: int) -> tuple[Signification, ...]:
    """Significators of ``house`` in ladder order A, B, C, D (nodes listed before planets per level).

    Ordering nodes first within a level follows "nodes are stronger than
    planets" (KPR3-NODES-STRONGER).
    """
    sigs = planet_significations(chart)
    rows = [s for v in sigs.values() for s in v if s.house == house]
    return tuple(sorted(rows, key=lambda s: (LEVELS.index(s.level), s.planet not in NODES, s.planet)))


__all__ = [
    "LEVELS", "LEVEL_TEXT", "LEVEL_CITE", "Signification", "node_represents",
    "planet_significations", "houses_signified", "house_significators",
]
