"""The judgment graph (synthesis layer S1) — every computed judgment object as a node,
every already-computed relation as an edge.

PURE RE-READ (the PREC-10 rule): nothing here judges anything. The graph collects links
the report already computed — house lords/occupants/karakas from the proformas, whole-sign
drishti from the chart, MD chapters' lit houses from the timeline, fired insights' section
links, the maraka tiers, and the v18 interpretation-guide records — into one explicit
nodes/edges structure so downstream consumers (theme census, biographies, LLM grounding,
API users) can reason ACROSS sections instead of summarizing one at a time.

Relations are a CLOSED vocabulary: the v18 guide's five doctrine relations
(governs/corroborates/different_grain/re_read_of/parallel, carried on section->section
edges) plus the structural set below. `provenance` says which computed object asserted the
edge; `cite` carries a WORK:line token when the underlying object has one.

Known, honest limitation (recorded, not papered over): `FiredYoga` carries no participant
list structurally, so yoga nodes link only to their citation and the yogas section —
participant edges await a FiredYoga field, not a text-parse.

Usage:
    from app.raman_saab.judgment_graph import build_judgment_graph
    g = build_judgment_graph(report)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Optional

from app.raman_saab.interpretation_guide import INTERPRETATION_GUIDE

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

#: Structural relations, in addition to the v18 doctrine relations.
STRUCTURAL_RELATIONS: Final[frozenset[str]] = frozenset({
    "lord_of", "occupies", "aspects", "karaka_of", "timer_of", "rules_period",
    "participates_in", "maraka_tier", "links"})

#: S4 non-Raman tier (user decision 2026-08-03): modern cross-house groupings, carried in
#: the graph ONLY under this banner — never as bare doctrine, never in a verdict.
MODERN_PROVENANCE: Final[str] = ("MODERN_SYNTHESIS — no Raman citation, no demonstrated "
                                 "predictive weight")
NON_RAMAN_GROUPINGS: Final[dict[str, tuple[int, ...]]] = {
    "professional_income": (2, 10, 11),
    "family_support": (4, 9),
    "transformative_intelligence": (5, 8),
    "communication_and_trade": (3, 7, 11),
    "inner_life": (8, 12, 4),
}
RELATION_VOCABULARY: Final[frozenset[str]] = STRUCTURAL_RELATIONS | frozenset(
    INTERPRETATION_GUIDE["relation_vocabulary"])

_GRAHAS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


@dataclass(frozen=True)
class JudgmentNode:
    id: str                    # "house:10", "planet:Mercury", "yoga:<id>", ...
    kind: str                  # house | planet | yoga | insight | dasha_period | section
    label: str
    data: tuple[tuple[str, str], ...] = field(default_factory=tuple)  # key/value extras


@dataclass(frozen=True)
class JudgmentEdge:
    src: str
    dst: str
    relation: str
    provenance: str            # which computed object asserted this edge
    cite: Optional[str] = None


@dataclass(frozen=True)
class JudgmentGraph:
    nodes: tuple[JudgmentNode, ...]
    edges: tuple[JudgmentEdge, ...]

    def node_ids(self) -> frozenset[str]:
        return frozenset(n.id for n in self.nodes)


def build_judgment_graph(r: "DetailedReport") -> JudgmentGraph:
    """Assemble the graph from the report's already-computed objects. Deterministic:
    node and edge order follows the fixed iteration orders below."""
    from app.raman_saab.doctrine import drishti

    nodes: list[JudgmentNode] = []
    edges: list[JudgmentEdge] = []
    seen: set[str] = set()

    def add_node(nid: str, kind: str, label: str,
                 data: tuple[tuple[str, str], ...] = ()) -> None:
        if nid not in seen:
            seen.add(nid)
            nodes.append(JudgmentNode(nid, kind, label, data))

    # ── base nodes: 12 houses, 9 grahas, the contract sections ────────────────
    for h in range(1, 13):
        pf = r.proformas[h - 1] if len(r.proformas) >= h else None
        data = (("verdict", pf.rollup),) if pf is not None else ()
        add_node(f"house:{h}", "house", f"House {h}", data)
    for p in _GRAHAS:
        add_node(f"planet:{p}", "planet", p)
    from app.raman_saab.detailed_report import SECTION_CONTRACT
    for spec in SECTION_CONTRACT:
        add_node(f"section:{spec.section_id}", "section", spec.section_id)

    # ── structural edges from the proformas (lord / karaka per house) ─────────
    for h in range(1, 13):
        if len(r.proformas) < h:
            continue
        pf = r.proformas[h - 1]
        if pf.lord in _GRAHAS:
            edges.append(JudgmentEdge(f"planet:{pf.lord}", f"house:{h}", "lord_of",
                                      "HouseProforma.lord"))
        for sv in pf.significations:
            if sv.karaka in _GRAHAS:
                edges.append(JudgmentEdge(
                    f"planet:{sv.karaka}", f"house:{h}", "karaka_of",
                    f"SignificationVerdict[{sv.signification}].karaka"))

    # ── occupancy + whole-sign drishti from the chart ─────────────────────────
    for p in _GRAHAS:
        pl = r.chart.planets.get(p)
        if pl is None:
            continue
        edges.append(JudgmentEdge(f"planet:{p}", f"house:{pl.rasi_house}", "occupies",
                                  "chart.planets.rasi_house"))
    for h in range(1, 13):
        for p in drishti.aspecting_house(h, r.chart):
            if p in _GRAHAS:
                edges.append(JudgmentEdge(f"planet:{p}", f"house:{h}", "aspects",
                                          "drishti.aspecting_house"))

    # ── fired yogas (citation only — no participant field exists) ─────────────
    for y in r.yogas:
        yid = f"yoga:{y.id}"
        add_node(yid, "yoga", y.name, (("kind", str(y.kind)),))
        edges.append(JudgmentEdge(yid, "section:yogas", "links", "FiredYoga",
                                  cite=f"{y.source.work}:{y.source.line}"))

    # ── MD chapters: period nodes, ruling lord, lit houses ────────────────────
    for i, ch in enumerate(r.life_chapters.chapters):
        pid = f"dasha_period:{i}:{ch.maha}"
        add_node(pid, "dasha_period", f"{ch.maha} Mahadasha",
                 (("is_current", str(ch.is_current)),))
        if ch.maha in _GRAHAS:
            edges.append(JudgmentEdge(f"planet:{ch.maha}", pid, "rules_period",
                                      "LifeChapter.maha"))
        for entry in ch.houses_lit:
            house = entry[0] if isinstance(entry, tuple) else entry
            edges.append(JudgmentEdge(pid, f"house:{house}", "timer_of",
                                      "LifeChapter.houses_lit"))

    # ── maraka tiers ──────────────────────────────────────────────────────────
    mp = getattr(r.chart, "maraka_points", None)
    if mp is not None:
        for u in mp.units:
            if u.graha in _GRAHAS:
                edges.append(JudgmentEdge(f"planet:{u.graha}", "section:maraka",
                                          "maraka_tier", f"MarakaUnit.tier={u.tier}"))

    # ── fired insights: rule -> the sections it bridges ───────────────────────
    for fi in r.insights:
        iid = f"insight:{fi.rule.id}"
        cite = (f"{fi.rule.source.work}:{fi.rule.source.line}"
                if fi.rule.source is not None else None)
        add_node(iid, "insight", fi.rule.name)
        for link in getattr(fi.rule, "links", ()) or ():
            edges.append(JudgmentEdge(iid, f"section:{_slug(link)}", "links",
                                      "SynthesisRule.links", cite=cite))

    # ── S4 non-Raman groupings: matter nodes, BANNERED edges only ─────────────
    for name, houses in NON_RAMAN_GROUPINGS.items():
        mid = f"matter:{name}"
        add_node(mid, "matter", name.replace("_", " "),
                 (("provenance", MODERN_PROVENANCE),))
        for h in houses:
            edges.append(JudgmentEdge(f"house:{h}", mid, "participates_in",
                                      MODERN_PROVENANCE))

    # ── the v18 guide's doctrine relations, as section->section edges ─────────
    for prec in INTERPRETATION_GUIDE["precedence"]:
        if prec["governs"] and prec["subordinate"]:
            for g in prec["governs"]:
                for s in prec["subordinate"]:
                    edges.append(JudgmentEdge(f"section:{g}", f"section:{s}",
                                              prec["relation"],
                                              f"interpretation_guide.{prec['id']}"))
        else:
            secs = prec["sections"]
            for a, b in zip(secs, secs[1:]):
                edges.append(JudgmentEdge(f"section:{a}", f"section:{b}",
                                          prec["relation"],
                                          f"interpretation_guide.{prec['id']}"))
    for par in INTERPRETATION_GUIDE["parallel_lenses"]:
        secs = par["sections"]
        for a, b in zip(secs, secs[1:]):
            edges.append(JudgmentEdge(f"section:{a}", f"section:{b}", "parallel",
                                      f"interpretation_guide.{par['id']}"))

    known = {n.id for n in nodes}
    kept = tuple(e for e in edges if e.src in known and e.dst in known)
    return JudgmentGraph(nodes=tuple(nodes), edges=kept)


_SECTION_ALIASES: Final[dict[str, str]] = {
    # SynthesisRule.links carry display names; map to contract section ids.
    "life-narrative": "timeline", "chart signature": "chart_signature",
    "house strength cross-check": "house_strength",
}


def _slug(link: str) -> str:
    key = link.strip().lower()
    return _SECTION_ALIASES.get(key, key.replace(" ", "_").replace("-", "_"))
