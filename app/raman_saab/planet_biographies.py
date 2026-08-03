"""Planet biographies (synthesis layer S2, report section v20) — the dominant grahas told
as one story each: role, strength, where they help, where they obstruct, when they run.

PURE RE-READ (PREC-10): every field selects from the judgment graph and already-computed
report objects; nothing is re-judged. The census is a deterministic degree-count over the
graph's structural edges — the "Mercury appears 14 times" number, with its edge kinds as
receipts.

Theme words come in two tiers (user decision 2026-08-03):
- Raman tier: `TRADE_BY_NAVAMSA_DISPOSITOR` (HTJAH-II:10249-10274) — his own planet ->
  vocation table, already encoded in `primitives/career.py`.
- Modern tier: `NON_RAMAN_THEMES` below — the contemporary keyword vocabulary, ALWAYS
  rendered under the provenance banner (the pitru precedent), never as bare doctrine.

Prose follows the Raman style rules (proposal phase 10, bounded by the LLM guard):
cause before result, decisive-but-descriptive idiom only, and each biography ends with a
"Conclusion:" sentence. Every sentence is guard-safe by test (`_FORBIDDEN_RE`).

Usage:
    from app.raman_saab.planet_biographies import build_planet_biographies
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

from app.raman_saab.judgment_graph import JudgmentGraph
from app.raman_saab.primitives.career import TRADE_BY_NAVAMSA_DISPOSITOR

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

#: The provenance banner every modern-tier theme carries (user-approved labeled layer).
MODERN_BANNER: Final[str] = ("MODERN_SYNTHESIS — no Raman citation, no demonstrated "
                             "predictive weight")

#: Modern keyword vocabulary per graha — BANNERED, never bare doctrine.
NON_RAMAN_THEMES: Final[dict[str, tuple[str, ...]]] = {
    "Sun": ("authority", "visibility", "vitality"),
    "Moon": ("emotional rhythm", "public connection", "nurture"),
    "Mars": ("drive", "competition", "engineering"),
    "Mercury": ("administration", "learning", "communication", "networking"),
    "Jupiter": ("guidance", "expansion", "principled growth"),
    "Venus": ("aesthetics", "relationship", "comfort"),
    "Saturn": ("discipline", "endurance", "structural work"),
    "Rahu": ("unconventional ambition", "amplification"),
    "Ketu": ("detachment", "specialisation"),
}

_CENSUS_RELATIONS: Final[frozenset[str]] = frozenset({
    "lord_of", "occupies", "aspects", "karaka_of", "rules_period", "maraka_tier"})

_VISIBLE: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


@dataclass(frozen=True)
class PlanetBiography:
    planet: str
    census_count: int
    census_by_relation: tuple[tuple[str, int], ...]
    lord_of: tuple[int, ...]
    karaka_of: tuple[int, ...]
    occupies: int                       # 0 when unplaced (Track-B sparse)
    dignity: str
    avastha: str
    helps: tuple[int, ...]              # favourable houses this planet influences
    obstructs: tuple[int, ...]          # afflicted houses this planet influences
    md_windows: tuple[tuple[float, float], ...]   # its own Mahadasha [start, end) JDs
    themes_raman: str                   # HTJAH-II:10249-10274 vocation words
    themes_modern: tuple[str, ...]      # NON_RAMAN_THEMES, bannered at render
    prose: str                          # cause-first narrative ending with "Conclusion:"
    # ── graha-chapter fields (2026-08-03, append-only): Raman's OWN paragraphs, pulled
    # verbatim by frozen line range (doctrine/lookups/graha_chapters). Each is
    # (text, "WORK:line") or None — None is an honest absence, never a guess. ──────────
    house_text: Optional[tuple[str, str]] = None      # HPA-21, its occupied house
    sign_text: Optional[tuple[str, str]] = None       # HPA-22, its sign (nodes: None)
    disease_text: Optional[tuple[str, str]] = None    # disease_map organs/tridosha
    family_role: str = ""                             # karaka-duty houses, named
    md_result_now: Optional[tuple[str, str]] = None   # HPA-24 per-sign text (if MD lord now)
    ad_result_now: Optional[tuple[str, str]] = None   # HPA-24 bhukti text (if in the pair)
    transit_text: Optional[tuple[str, str]] = None    # HPA-34 Gocharaphala section


def planet_census(graph: JudgmentGraph) -> dict[str, dict[str, int]]:
    """Deterministic degree-count per planet over the structural relations."""
    out: dict[str, dict[str, int]] = {}
    for e in graph.edges:
        if e.relation in _CENSUS_RELATIONS and e.src.startswith("planet:"):
            p = e.src.split(":", 1)[1]
            out.setdefault(p, {})
            out[p][e.relation] = out[p].get(e.relation, 0) + 1
    return out


def _house_verdict(r: "DetailedReport", house: int) -> str:
    return r.proformas[house - 1].rollup if len(r.proformas) >= house else ""


def _influenced_houses(graph: JudgmentGraph, planet: str) -> tuple[int, ...]:
    seen: list[int] = []
    for e in graph.edges:
        if (e.src == f"planet:{planet}" and e.dst.startswith("house:")
                and e.relation in ("lord_of", "occupies", "aspects")):
            h = int(e.dst.split(":", 1)[1])
            if h not in seen:
                seen.append(h)
    return tuple(seen)


def _compose_prose(b: "PlanetBiography") -> str:
    """The Raman Style Writer applied (raman_style): first impression opens, cause before
    result, no bare lists, a Conclusion ends the unit — descriptive idiom only."""
    from app.raman_saab.raman_style import because, conclusion

    bits: list[str] = []
    roles = []
    if b.lord_of:
        roles.append("rules house" + ("s " if len(b.lord_of) > 1 else " ")
                     + " and ".join(str(h) for h in b.lord_of))
    if b.occupies:
        roles.append(f"stands in house {b.occupies}")
    if b.karaka_of:
        roles.append("serves as karaka for house"
                     + ("s " if len(b.karaka_of) > 1 else " ")
                     + " and ".join(str(h) for h in b.karaka_of))
    if roles:
        bits.append(f"{b.planet} {', '.join(roles)}, in {b.dignity} dignity"
                    + (f" and {b.avastha} avastha" if b.avastha else "") + ".")
    if b.helps:
        bits.append(because(
            "its lordship and aspects reach " + ", ".join(f"house {h}" for h in b.helps),
            "the favourable readings there carry its signature"))
    if b.obstructs:
        bits.append(because(
            "it also touches " + ", ".join(f"house {h}" for h in b.obstructs),
            "the afflicted readings there trace back to it as well"))
    if b.md_windows:
        bits.append("Its own Mahadasha marks the years when these indications are "
                    "read most directly.")
    if b.themes_raman:
        bits.append(conclusion(
            f"this chart reads {b.planet} chiefly through {b.themes_raman} "
            f"(HTJAH-II:10249) — a description of the method's emphasis, never a "
            f"prediction"))
    else:
        bits.append(conclusion(
            f"{b.planet} is a chayagraha — Raman's vocation table names no trade for it "
            f"(an honest absence), and its influence is read through its placement and "
            f"periods above"))
    return " ".join(bits)


def build_planet_biographies(r: "DetailedReport", graph: JudgmentGraph,
                             *, top_n: int = 9) -> tuple[PlanetBiography, ...]:
    """Every graha as a CHAPTER (census-ranked, dominant first). The nodes are included —
    their HPA-21 house paragraphs and HPA-24 dasha paragraphs exist; where a table
    excludes them (HPA-22 signs, the HTJAH-II vocation rows) the field is an honest
    absence, never a guess."""
    from app.raman_saab.doctrine.lookups import graha_chapters as gc
    from app.raman_saab.doctrine.lookups.disease_map import (PLANET_ORGANS,
                                                             PLANET_TRIDOSHAS)
    from app.raman_saab.primitives.deeptadi import state as _avastha_state
    from app.raman_saab.primitives.dignity import dignity as _dignity

    census = planet_census(graph)
    all_grahas = (*_VISIBLE, "Rahu", "Ketu")
    ranked = sorted(all_grahas, key=lambda p: -sum(census.get(p, {}).values()))
    running_md = getattr(r.synthesis, "running_md", None)
    running_ad = getattr(r.synthesis, "running_ad", None)
    out: list[PlanetBiography] = []
    for p in ranked[:top_n]:
        by_rel = census.get(p, {})
        lord_of = tuple(sorted(int(e.dst.split(":", 1)[1]) for e in graph.edges
                               if e.src == f"planet:{p}" and e.relation == "lord_of"))
        karaka_of = tuple(sorted({int(e.dst.split(":", 1)[1]) for e in graph.edges
                                  if e.src == f"planet:{p}" and e.relation == "karaka_of"}))
        pl = r.chart.planets.get(p)
        occupies = pl.rasi_house if pl is not None else 0
        try:
            dig = _dignity(p, r.chart)
        except Exception:  # noqa: BLE001 — Track-B sparse chart
            dig = "unknown"
        try:
            av = _avastha_state(p, r.chart)
        except Exception:  # noqa: BLE001
            av = ""
        influenced = _influenced_houses(graph, p)
        helps = tuple(h for h in influenced if _house_verdict(r, h) == "favourable")
        obstructs = tuple(h for h in influenced if _house_verdict(r, h) == "afflicted")
        md_windows = tuple((tp.period.start_jd, tp.period.end_jd)
                           for tp in r.timeline.periods
                           if tp.period.maha == p and tp.period.antar is None)
        sign = int(pl.lon % 360.0 // 30.0) + 1 if pl is not None else 0
        organs = PLANET_ORGANS.get(p)
        disease = None
        if organs is not None:
            tri = PLANET_TRIDOSHAS.get(p)
            dtxt = (f"governs the {organs.organ}"
                    + (f"; tridosha: {tri.tridosha}" if tri is not None else ""))
            cite = organs.sources[0]
            disease = (dtxt, f"{cite.work}:{cite.line}")
        family = ", ".join(
            f"house {h}" for h in karaka_of) and (
            "karaka for " + ", ".join(f"house {h}" for h in karaka_of))
        md_now = (gc.md_sign_result(p, sign)
                  if running_md == p and sign else None)
        ad_now = (gc.ad_result(running_md, p)
                  if running_ad == p and running_md else None)
        bio = PlanetBiography(
            planet=p, census_count=sum(by_rel.values()),
            census_by_relation=tuple(sorted(by_rel.items())),
            lord_of=lord_of, karaka_of=karaka_of, occupies=occupies,
            dignity=dig, avastha=av, helps=helps, obstructs=obstructs,
            md_windows=md_windows,
            themes_raman=TRADE_BY_NAVAMSA_DISPOSITOR.get(p, ""),
            themes_modern=NON_RAMAN_THEMES.get(p, ()),
            prose="",
            house_text=gc.house_result(p, occupies) if occupies else None,
            sign_text=gc.sign_result(p, sign) if sign else None,
            disease_text=disease, family_role=family,
            md_result_now=md_now, ad_result_now=ad_now,
            transit_text=gc.transit_result(p))
        out.append(PlanetBiography(**{**bio.__dict__, "prose": _compose_prose(bio)}))
    return tuple(out)
