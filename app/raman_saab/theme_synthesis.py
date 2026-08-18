"""The integrated-interpretation (theme-synthesis) layer — a READ-ONLY overlay.

The engine answers "what does each section say?" well; this layer answers "what does the
whole horoscope say when the sections are read together?". It is built LAST in
``build_detailed_report`` and consumes only finished ``DetailedReport`` fields — it never
re-judges a house, never re-runs Shadbala, never recomputes a dasha date. Every synthesized
claim is a re-read of an authoritative verdict or a corroborating measurement, and every
link carries the ``accessor`` (the field it came from) so the claim stays auditable.

Design contract (see docs/raman_saab/SYNTHESIS_LAYER_ARCHITECTURE.md):

- **The headline verdict is a passthrough.** ``ThemeReading.headline_verdict`` byte-equals
  the house rollup / dashboard verdict. Only ``axis=='verdict'`` links carry a direction;
  magnitude / state / varga / transit / yoga / statistical links carry ``lean`` as
  CORROBORATION only and can never flip a verdict. This is what keeps the golden ratchet
  (259/293) byte-identical — the layer imports nothing in the D1 verdict path.
- **Convergence is an evidentiary count, never a probability**, and it always reports the
  opposing pole too (the median chart carries both poles at all times, CLAUDE.md ★★).
- **Contradictions cite the governing precedence rule** (``INTERPRETATION_GUIDE``), never a
  fabricated resolution.
- **Provenance travels on every link** (RAMAN / CLASSICAL / STATISTICAL / MODERN_SYNTHESIS);
  the layer authors no ``WORK:line`` — a model-authored citation is treated as fabricated.

Usage:
    from app.raman_saab.theme_synthesis import build_theme_synthesis
    ts = build_theme_synthesis(report)      # report: DetailedReport
    for theme in ts.themes: ...
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Optional

import swisseph as swe

from app.raman_saab.doctrine import varga_domains as vd

if TYPE_CHECKING:                                   # avoid the build_detailed_report import cycle
    from app.raman_saab.detailed_report import DetailedReport

Axis = Literal["verdict", "magnitude", "state", "dasha", "varga", "transit", "yoga", "citation"]
Convergence = Literal["VERY_HIGH", "HIGH", "MODERATE", "MIXED", "WEAK"]

# provenance labels the layer may stamp (mirrors the existing Tagged/banner vocabulary)
RAMAN_EXPLICIT = "RAMAN_EXPLICIT"
RAMAN_GENERAL = "RAMAN_GENERAL_PRINCIPLE"
CLASSICAL_NONCITABLE = "CLASSICAL_NONCITABLE"
STATISTICAL = "STATISTICAL"
MODERN_SYNTHESIS = "MODERN_SYNTHESIS"


# ─────────────────────────────────────────────────────────────────────────────
# data model
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ThemeEvidenceLink:
    """One piece of evidence for a theme, on exactly one axis, fully traceable.

    ``value`` is the finding verbatim from the source object. ``lean`` is a coarse
    direction (favourable/adverse/neutral) used ONLY for corroboration counting — a link
    whose ``axis`` is not 'verdict' can never carry the theme's direction. ``accessor`` is
    the report field + file:line the value came from, so any sentence built on this link can
    answer "which finding produced you?"."""
    axis: Axis
    label: str
    value: str
    lean: str                       # 'favourable' | 'adverse' | 'neutral' | 'mixed'
    accessor: str
    provenance: str = MODERN_SYNTHESIS
    cite: Optional[object] = None   # a Citation object IF the source already carried one; never authored here


@dataclass(frozen=True)
class Contradiction:
    """Two findings that appear to conflict, classified and resolved by an existing
    precedence rule rather than forced to cancel."""
    kind: str                       # the taxonomy class (see _contradictions)
    poles: tuple[str, str]          # the two findings, each carrying its own accessor
    governing: str                  # the PREC-id (or doctrine tag) that resolves it
    resolution: str
    parties: tuple[str, ...] = ()   # the named participants (e.g. the facets that differ), as DATA
    #: `poles` is prose for the reader; `parties` carries the same names structurally so a
    #: renderer never has to parse the sentence back apart to recover them.


@dataclass(frozen=True)
class ThemeReading:
    """One life-theme, its evidence chain across every axis, its convergence and its
    contradictions — a re-read on top of the authoritative verdicts, judging nothing anew."""
    theme_id: str
    name: str
    domain: str
    houses: tuple[int, ...]
    karakas: tuple[str, ...]
    headline_verdict: str           # PASSTHROUGH of the primary house rollup — never recomputed
    driver: str
    sub_matters: tuple[tuple[str, str], ...]   # (matter, its own dashboard verdict) — the house's facets
    dominant_planets: tuple[str, ...]
    links: tuple[ThemeEvidenceLink, ...]
    convergence: Convergence
    convergence_label: str          # reader-facing phrase ('high convergence' / 'aligned, lightly evidenced')
    convergence_why: str
    contradictions: tuple[Contradiction, ...]
    activation_span: str            # period_pairing_clause — timed-indication idiom, never decree
    varga_relation: str             # confirms / strengthens / qualifies / modifies / contradicts / D9-only
    final_interpretation: str
    evidence_weight: float = 0.0    # for ranking only; NOT a probability or a verdict


@dataclass(frozen=True)
class ExecutivePortrait:
    """The two-page opening: if you read only this, what is this horoscope?"""
    identity: str                   # Lagna / lagna-lord / Atmakaraka / Karakamsa / Moon — who the chart is
    temperament: str
    frame: str
    dominant_actors: tuple[tuple[str, str], ...]    # (planet, why-dominant)
    strongest_domains: tuple[str, ...]
    weakest_domains: tuple[str, ...]
    principal_tension: str
    protective_factors: tuple[str, ...]
    current_chapter: str
    next_chapter: str
    honesty_note: str               # r.info.sentence — calibration, not validation


@dataclass(frozen=True)
class ThemeConnection:
    """Two themes discovered to share a mechanism — the same driving planet or a common house —
    so the reader sees the horoscope as one fabric, not independent modules."""
    theme_a: str
    theme_b: str
    shared: str                     # the planet(s)/house(s) they share
    note: str


@dataclass(frozen=True)
class DashaChapter:
    """One Mahadasha run and how the life-themes evolve across it — the horoscope's movement
    through time. A re-read of r.life_chapters (never new dasha math). A chapter foregrounds a
    theme when the Mahadasha lord is one of that theme's OWN driving planets — the differential
    signal (the Saturn period foregrounds what Saturn drives, not every house it happens to
    aspect). Split into those NEWLY emphasized in this chapter versus those CONTINUING from the
    previous one (Raman's item-9 evolution question)."""
    maha: str
    span: str                       # 'YYYY-YYYY' (JD arithmetic, GREG_CAL)
    is_current: bool
    lean: str                       # the MD Ishta/Kashta lean, re-read
    activates: tuple[str, ...]      # themes the MD lord actually drives (differential, not flooding)
    emerging: tuple[str, ...]       # newly emphasized vs the previous chapter
    continuing: tuple[str, ...]     # carried over from the previous chapter
    acts_through: tuple[str, ...] = ()   # for a NODE chapter: the planets it gives results for


@dataclass(frozen=True)
class ThemeSynthesis:
    """The whole integrated interpretation: ranked themes, the dominant-theme spine, the
    executive portrait, the cross-theme fabric, and the dasha evolution. Built last, re-read
    only."""
    themes: tuple[ThemeReading, ...]
    spine: tuple[str, ...]          # theme_ids of the 3-5 dominant themes (see _spine_size)
    frame: str
    portrait: ExecutivePortrait
    connections: tuple[ThemeConnection, ...] = ()
    dasha_evolution: tuple[DashaChapter, ...] = ()


# ─────────────────────────────────────────────────────────────────────────────
# the theme roster — engine-sourced, not hardcoded per chart
# ─────────────────────────────────────────────────────────────────────────────
# A theme is a BHAVA (or house-cluster), NOT a dashboard matter — several dashboard matters can
# share one house (mother/property/comforts/education all live in H4; father/dharma in H9), and
# treating each as its own theme produced clones that all inherited the same house verdict and the
# same tensions. So each theme names its PRIMARY house, the dashboard MATTERS that live there (its
# facets), the varga whose domain (varga_domains.DOMAINS) supplies karakas, and candidate SUPPORT
# houses (kept only when a driving planet actually touches them — pass 3). The headline is the
# primary house rollup; the facets carry each matter's own dashboard verdict, so a house that reads
# afflicted while its matters read favourable tells that story ONCE, inside the theme.
@dataclass(frozen=True)
class _PlainDomain:
    """The domain stand-in for a bhava with NO classical divisional chart of its own (H8, H12).
    Carries a plain description, no karakas and no citation — the engine must not imply Raman
    (or the Parashari scheme) assigned a varga where none is assigned. Such a theme is still read
    from the rasi, with the navamsa applying as the general strength check as it does everywhere."""
    domain: str
    karakas: tuple[str, ...] = ()
    source: Optional[object] = None


@dataclass(frozen=True)
class _ThemeSpec:
    """One roster entry. ``varga`` names the division whose domain (varga_domains.DOMAINS)
    supplies this theme's karakas and citation; ``None`` means no classical division covers this
    bhava, and ``domain_note`` describes it instead."""
    theme_id: str
    name: str
    primary_house: int
    matters: tuple[str, ...]        # dashboard matters that live in this house (its facets)
    varga: Optional[int]
    support: tuple[int, ...]        # CANDIDATE network houses, kept only when a driver touches one
    domain_note: str = ""           # used only when varga is None


_THEME_ROSTER: tuple[_ThemeSpec, ...] = (
    _ThemeSpec("wealth",      "Wealth & resources",         2,  ("wealth",),   2,  (11, 8)),
    _ThemeSpec("career",      "Career & public standing",   10, ("career",),   10, (2, 6, 11)),
    _ThemeSpec("marriage",    "Marriage & partnership",     7,  ("marriage",), 9,  ()),
    _ThemeSpec("children",    "Children & creativity",      5,  ("children",), 7,  (9,)),
    _ThemeSpec("foundations", "Home, mother & foundations", 4,
               ("mother", "property", "comforts", "education"), 4, (2,)),
    _ThemeSpec("fortune",     "Fortune, father & dharma",   9,  ("father", "spiritual"), 20, (5, 10)),
    _ThemeSpec("health",      "Health & vitality",          6,  ("health",),   30, (1, 8)),
    _ThemeSpec("siblings",    "Siblings & courage",         3,  ("siblings",), 3,  ()),
    # The four bhavas that carry no dashboard matter of their own. They were previously visible
    # only as SUPPORT houses inside other themes, so the reading never stated what the chart says
    # about the self, about gains, about crisis and longevity, or about loss and withdrawal — a
    # completeness gap. D1 covers the body explicitly; H8, H11 and H12 are assigned no division in
    # the domain table, so they carry a plain description and say so rather than borrowing one.
    _ThemeSpec("self",        "Self, body & constitution",  1,  (),            1,  (6, 8)),
    _ThemeSpec("gains",       "Gains, friends & fulfilment", 11, (),        None,  (2, 10),
               "income, gains, friendships and the fulfilment of desires — read from the rasi "
               "(no classical division is assigned to this bhava)"),
    # NB: a theme name must not START with a pinned "## <label>" section marker — a theme renders
    # as "#### <name>", which contains "## <name>", so such a name silently hijacks every
    # find("## <label>") / _section(md, "## <label>") lookup in the report tests. "Longevity, …"
    # did exactly that to the real "## Longevity" section. Guarded by
    # test_theme_names_cannot_hijack_a_pinned_section_marker.
    _ThemeSpec("longevity",   "Crisis, longevity & the hidden", 8, (),      None,  (1, 12),
               "longevity, upheaval and what is hidden — read from the rasi (no classical "
               "division is assigned to this bhava)"),
    _ThemeSpec("liberation",  "Loss, seclusion & liberation", 12, (),       None,  (4, 8),
               "expenditure, withdrawal and moksha — read from the rasi (no classical division "
               "is assigned to this bhava)"),
)


# ─────────────────────────────────────────────────────────────────────────────
# small direction helpers (reuse the engine's own lean vocabulary)
# ─────────────────────────────────────────────────────────────────────────────
def _dir(lean: str) -> int:
    """+1 favourable, -1 adverse, 0 neutral/mixed — for corroboration counting only."""
    return {"favourable": 1, "adverse": -1}.get(lean, 0)


def _nav_lean(navamsa: Optional[str]) -> str:
    """The D9 relation as a coarse lean (the only verdict-bearing varga signal)."""
    n = (navamsa or "").lower()
    if "confirm" in n or "delivered" in n or "support" in n:
        return "favourable"
    if "weaken" in n or "contradict" in n or "undercut" in n or "denies" in n:
        return "adverse"
    return "neutral"


# ─────────────────────────────────────────────────────────────────────────────
# the builder
# ─────────────────────────────────────────────────────────────────────────────
def build_theme_synthesis(r: "DetailedReport") -> ThemeSynthesis:
    """Assemble the integrated interpretation from an already-built ``DetailedReport``.

    Six deterministic passes: theme roster -> evidence gather -> dominant actors ->
    convergence -> contradictions -> ranking + portrait. Read-only throughout; the one
    permitted rebuild is ``build_judgment_graph(r)`` (a pure re-read of relations)."""
    # lazy imports — detailed_report has finished importing by the time this runs, so this
    # avoids the build_detailed_report <-> theme_synthesis cycle
    from app.raman_saab import detailed_report as dr
    from app.raman_saab.insight_digest import _lean_of
    from app.raman_saab.judgment_graph import build_judgment_graph
    from app.raman_saab.planet_biographies import planet_census
    from app.raman_saab.doctrine.synthesis_rules import yoga_house_bearings

    proformas = {pf.house: pf for pf in r.proformas}
    dash = {e.matter: e for e in r.dashboard.entries}

    # pass 3 inputs (structural graph, once) — tolerate a sparse/Track-B failure
    try:
        graph = build_judgment_graph(r)
        census = planet_census(graph)
    except Exception:
        census = {}
    # planet -> the houses it touches (lord/karaka/occupy/aspect), from the census breakdown
    planet_houses = _planet_house_map(r)

    themes: list[ThemeReading] = []
    for spec in _THEME_ROSTER:
        theme_id, name, prim_house = spec.theme_id, spec.name, spec.primary_house
        matters, support = spec.matters, spec.support
        if prim_house not in proformas:
            continue
        if spec.varga is None:                      # a bhava with no classical division
            domain = _PlainDomain(spec.domain_note or f"house {prim_house}")
        else:
            try:
                domain = vd.domain_for(spec.varga)
            except ValueError:
                continue

        pf = proformas[prim_house]
        headline = pf.rollup                        # PASSTHROUGH — never recomputed
        driver = dr.rollup_driver(r.calibration.get(prim_house), headline) or name.split()[0].lower()
        # the house's facets — each dashboard matter that lives here, with its OWN verdict
        facets = tuple((m, dash[m].verdict) for m in matters if m in dash)

        # pass 2 + 3: gather evidence links and discover the network / dominant planets
        links: list[ThemeEvidenceLink] = []
        dom_planets = _dominant_planets(r, prim_house, domain, census, planet_houses)
        kept_support = _discover_support(prim_house, support, dom_planets, planet_houses)
        houses = (prim_house,) + kept_support

        links.extend(_verdict_links(r, prim_house, kept_support, proformas))
        links.extend(_facet_links(facets))
        links.extend(_varga_links(r, prim_house, domain))
        links.extend(_yoga_links(r, houses, yoga_house_bearings))
        links.extend(_strength_state_links(r, prim_house, pf, dom_planets))
        links.extend(_dasha_links(r, houses))
        links.extend(_transit_links(r, houses, dom_planets, planet_houses))
        links.extend(_insight_links(r, houses))

        # pass 4: convergence (evidentiary count, both poles)
        convergence, conv_label, why = _convergence(headline, facets, links, r)
        # pass 5: contradictions — ONE consolidated statement per axis, not one per matter
        contradictions = _contradictions(r, prim_house, pf, headline, facets, name)

        activation = _theme_timing(r, name, prim_house, houses, dom_planets)
        varga_rel = _varga_relation(r, prim_house, domain)
        final = _final_interpretation(name, headline, convergence, conv_label, contradictions,
                                      activation, dom_planets, facets)
        weight = _weight(convergence, links, r, houses, dom_planets)

        themes.append(ThemeReading(
            theme_id=theme_id, name=name, domain=domain.domain, houses=houses,
            karakas=domain.karakas, headline_verdict=headline, driver=driver, sub_matters=facets,
            dominant_planets=dom_planets, links=tuple(links), convergence=convergence,
            convergence_label=conv_label, convergence_why=why, contradictions=contradictions,
            activation_span=activation, varga_relation=varga_rel, final_interpretation=final,
            evidence_weight=weight))

    # pass 6: rank + spine + portrait + the cross-theme fabric + dasha evolution
    themes.sort(key=lambda t: t.evidence_weight, reverse=True)
    spine = tuple(t.theme_id for t in themes[:_spine_size(themes)])
    frame = getattr(r.overview, "stronger_frame", "") or ""
    portrait = _portrait(r, themes, spine, frame)
    connections = _connections(themes)
    evolution = _dasha_evolution(r, themes)
    return ThemeSynthesis(themes=tuple(themes), spine=spine, frame=frame, portrait=portrait,
                          connections=connections, dasha_evolution=evolution)


# ─────────────────────────────────────────────────────────────────────────────
# pass helpers
# ─────────────────────────────────────────────────────────────────────────────
def _safe(fn, default):
    try:
        return fn()
    except Exception:
        return default


def _planet_house_map(r: "DetailedReport") -> dict[str, set[int]]:
    """planet -> the set of houses it influences (lord/karaka/helps/obstructs), from the
    already-built planet biographies. Pure re-read; empty on sparse charts."""
    out: dict[str, set[int]] = {}
    for bio in getattr(r, "planet_bios", ()) or ():
        hs: set[int] = set()
        hs.update(getattr(bio, "lord_of", ()) or ())
        hs.update(getattr(bio, "karaka_of", ()) or ())
        hs.update(getattr(bio, "helps", ()) or ())
        hs.update(getattr(bio, "obstructs", ()) or ())
        occ = getattr(bio, "occupies", 0) or 0
        if occ:
            hs.add(occ)
        out[bio.planet] = hs
    return out


def _matter_reading(r, house):
    """The MatterReading for a house (carries the D9 navamsa relation). None if absent."""
    return next((m for m in r.synthesis.matters if m.house == house), None)


def _dominant_planets(r, prim_house, domain, census, planet_houses) -> tuple[str, ...]:
    """The planets that STRUCTURALLY drive this theme's primary house — its lagna-frame lord and
    its domain karakas, in that order. A broad-census planet is added ONLY if it actually LORDS
    or is a KARAKA of the primary house (not merely aspects it) — so a weak, unrelated graha is
    never listed as a 'driver' just because it casts a distant aspect. Deduped, capped at 3."""
    out: list[str] = []
    # 1. the primary house's lagna-frame lord (frame-lord-trap-safe: HouseProforma.lord is the
    #    lagna-frame lord's name)
    pf = next((p for p in r.proformas if p.house == prim_house), None)
    if pf is not None and pf.lord:
        out.append(pf.lord)
    # 2. domain karakas the census confirms as participating
    for k in domain.karakas:
        if k not in out and (k in census or prim_house in planet_houses.get(k, set())):
            out.append(k)
    # 3. a further planet ONLY if it lords/karaka-s this very house (a real structural tie,
    #    not a distant aspect) — from the planet biographies' lord_of/karaka_of
    if len(out) < 3:
        for bio in getattr(r, "planet_bios", ()) or ():
            if bio.planet in out:
                continue
            if prim_house in (getattr(bio, "lord_of", ()) or ()) or \
                    prim_house in (getattr(bio, "karaka_of", ()) or ()):
                out.append(bio.planet)
            if len(out) >= 3:
                break
    return tuple(out[:3])


def _discover_support(prim_house, candidates, dom_planets, planet_houses) -> tuple[int, ...]:
    """Keep a candidate supporting house ONLY when a dominant planet actually touches it — the
    network is discovered from the graph, never asserted. Falls back to the classical candidates
    when the graph is empty (sparse chart), disclosed as such downstream."""
    if not planet_houses:
        return tuple(candidates)
    touched = set()
    for p in dom_planets:
        touched |= planet_houses.get(p, set())
    kept = tuple(h for h in candidates if h in touched and h != prim_house)
    return kept


def _verdict_links(r, prim_house, support, proformas) -> list[ThemeEvidenceLink]:
    from app.raman_saab import detailed_report as dr
    from app.raman_saab.insight_digest import _lean_of
    out: list[ThemeEvidenceLink] = []
    pf = proformas[prim_house]
    out.append(ThemeEvidenceLink(
        "verdict", f"House {prim_house} rollup", pf.rollup, _lean_of(pf.rollup),
        f"r.proformas[{prim_house-1}].rollup @ house_template.py:236", RAMAN_EXPLICIT))
    for h in support:
        spf = proformas.get(h)
        if spf is not None:
            out.append(ThemeEvidenceLink(
                "verdict", f"House {h} (network) rollup", spf.rollup, _lean_of(spf.rollup),
                f"r.proformas[{h-1}].rollup @ house_template.py:236", RAMAN_EXPLICIT))
    return out


def _facet_links(facets) -> list[ThemeEvidenceLink]:
    """One verdict link per dashboard matter that lives in this house (its facets) — each judged
    by its own dedicated reader. This is where a house-vs-matter grain difference shows up."""
    from app.raman_saab.insight_digest import _lean_of
    out: list[ThemeEvidenceLink] = []
    for matter, verdict in facets:
        out.append(ThemeEvidenceLink(
            "verdict", f"{matter} (dedicated reader)", verdict, _lean_of(verdict),
            "r.dashboard.entries[*].verdict @ matter_varga_dashboard.py:38", RAMAN_EXPLICIT))
    return out


def _varga_links(r, prim_house, domain) -> list[ThemeEvidenceLink]:
    m = _matter_reading(r, prim_house)
    if m is None or not m.navamsa:
        return []
    return [ThemeEvidenceLink(
        "varga", "D9 (navamsa) confirmation", m.navamsa, _nav_lean(m.navamsa),
        f"r.synthesis.matters[h={prim_house}].navamsa @ synthesis.py:39", RAMAN_EXPLICIT,
        cite=domain.source)]


def _yoga_links(r, houses, yoga_house_bearings) -> list[ThemeEvidenceLink]:
    from app.raman_saab import detailed_report as dr
    out: list[ThemeEvidenceLink] = []
    hset = set(houses)
    for y in getattr(r, "yogas", ()) or ():
        bearing = _safe(lambda: yoga_house_bearings(r.chart, y), None)
        if not bearing or not (bearing & hset):
            continue
        lean = _safe(lambda: dr._yoga_record_lean(y), "neutral") or "neutral"
        name = getattr(y, "name", getattr(y, "id", "yoga"))
        out.append(ThemeEvidenceLink(
            "yoga", f"{name} bears on {sorted(bearing & hset)}", name, lean,
            "yoga_house_bearings(r.chart, y) @ synthesis_rules.py:238",
            RAMAN_EXPLICIT, cite=getattr(y, "source", None)))
    return out


def _strength_state_links(r, prim_house, pf, dom_planets) -> list[ThemeEvidenceLink]:
    """Magnitude (Shadbala/Bhava Bala) and state (Deeptadi) as CORROBORATION only — never a
    direction. Uses the frame-lord-trap-safe lagna ledger for the strength readout."""
    from app.raman_saab import detailed_report as dr
    out: list[ThemeEvidenceLink] = []
    # Bhava Bala rank (magnitude) for the primary house
    row = next((hs for hs in getattr(r, "house_strength", ()) if getattr(hs, "house", None) == prim_house), None)
    if row is not None and getattr(row, "bhava_bala_rank", None) is not None:
        out.append(ThemeEvidenceLink(
            "magnitude", f"House {prim_house} Bhava Bala rank", f"rank {row.bhava_bala_rank}/12",
            "neutral", "r.house_strength[*].bhava_bala_rank @ detailed_report.py:1734",
            RAMAN_GENERAL))
    # the driving planet's Shadbala (magnitude)
    for p in dom_planets[:1]:
        pl = r.chart.planets.get(p)
        if pl is not None and getattr(pl, "shadbala_rupas", None) is not None:
            out.append(ThemeEvidenceLink(
                "magnitude", f"{p} Shadbala", f"{pl.shadbala_rupas.total/60.0:.2f} rupas",
                "neutral", "r.chart.planets[p].shadbala_rupas.total @ chart/model.py:26",
                RAMAN_GENERAL))
    # the driving planet's Deeptadi STATE (a distinct axis from magnitude/direction; HPA Ch.7,
    # verdict-invariant — testimony about the CONDITION the planet acts from, never a direction)
    from app.raman_saab.primitives import deeptadi as _deeptadi
    states = _safe(lambda: _deeptadi.chart_states(r.chart), {}) or {}
    for p in dom_planets[:1]:
        st = states.get(p)
        if st:
            out.append(ThemeEvidenceLink(
                "state", f"{p} Deeptadi state", f"{st[0]} ({st[1]})", "neutral",
                "deeptadi.chart_states(r.chart) @ deeptadi.py:100", RAMAN_EXPLICIT))
    return out


def _dasha_links(r, houses) -> list[ThemeEvidenceLink]:
    from app.raman_saab import detailed_report as dr
    tiers = _safe(lambda: dr.house_current_tiers(r), {}) or {}
    out: list[ThemeEvidenceLink] = []
    for h in houses:
        t = tiers.get(h)
        if t:
            out.append(ThemeEvidenceLink(
                "dasha", f"House {h} in the running period", t, "neutral",
                "house_current_tiers(r) @ detailed_report.py:1029", RAMAN_EXPLICIT))
    return out


def _transit_links(r, houses, dom_planets, planet_houses) -> list[ThemeEvidenceLink]:
    """Transit as the SUBORDINATE modifier only — a dasha-x-transit confluence whose period lord
    bears on this theme. Never an independent prediction (HTJAH-II:4679-4687: transits are
    catalytic, all conclusions drawn primarily on Dasa-vichara).

    ``ConfluenceWindow`` carries ``planet``/``role``/JD bounds — it has NO ``houses`` or ``label``
    field, so the earlier attribute probe silently matched nothing and this axis emitted zero
    links on every chart. The confluence is matched by its PLANET instead: it bears on the theme
    when that planet drives the theme or influences one of the theme's houses. One link per
    planet+role — ``r.dasha_transit`` holds a row per bhukti-and-segment overlap, so a single
    period lord otherwise repeats the identical row many times over."""
    hset = set(houses)
    drivers = set(dom_planets)
    out: list[ThemeEvidenceLink] = []
    seen: set[tuple[str, str]] = set()
    for c in getattr(r, "dasha_transit", ()) or ():
        planet = getattr(c, "planet", None)
        if not planet:
            continue
        if planet not in drivers and not (planet_houses.get(planet, set()) & hset):
            continue
        role = str(getattr(c, "role", "") or "")
        if (planet, role) in seen:
            continue
        seen.add((planet, role))
        out.append(ThemeEvidenceLink(
            "transit", "Dasha x transit confluence",
            f"{planet}{f' ({role})' if role else ''} well-placed by transit in its own period",
            "neutral", "r.dasha_transit[*].planet @ detailed_report.py:1526", RAMAN_GENERAL))
    return out


def _insight_links(r, houses) -> list[ThemeEvidenceLink]:
    """Fired cross-feature insights whose linked sections touch this theme — carrying the
    insight's own provenance band so a classical/AV insight never outranks a Raman one."""
    from app.raman_saab.insight_digest import _lean_of
    out: list[ThemeEvidenceLink] = []
    hset = set(houses)
    for fi in getattr(r, "insights", ()) or ():
        ih = set(getattr(fi.rule, "houses", ()) or ()) if hasattr(fi, "rule") else set()
        if ih and not (ih & hset):
            continue
        if not ih:
            continue
        band = getattr(fi.rule, "band", "") or ""
        prov = {"raman": RAMAN_EXPLICIT, "classical": CLASSICAL_NONCITABLE,
                "av": CLASSICAL_NONCITABLE}.get(str(band).lower(), MODERN_SYNTHESIS)
        out.append(ThemeEvidenceLink(
            "citation", f"Insight ({band})", fi.detail[:120], "neutral",
            "r.insights @ synthesis_rules.py:101", prov))
    return out


def _convergence(headline, facets, links, r) -> tuple[Convergence, str, str]:
    """Count agreeing vs opposing INDEPENDENT direction-bearing axes (the support-house verdicts,
    the facet dashboard verdicts, D9, and yoga leans — NOT the headline itself, which would
    trivially agree). Returns (tier, reader_label, why). Always reports both poles; convergence
    is evidentiary agreement, never a probability."""
    from app.raman_saab.insight_digest import _lean_of
    head = _dir(_lean_of(headline))
    agree = oppose = 0
    for lk in links:
        if lk.axis not in ("verdict", "varga", "yoga"):
            continue
        # the primary-house rollup IS the headline — don't count it as its own witness
        if lk.label.startswith("House ") and "rollup" in lk.label and "(network)" not in lk.label:
            continue
        d = _dir(lk.lean)
        if d == 0 or head == 0:
            continue
        agree += (d == head)
        oppose += (d != head)
    d9 = any(lk.axis == "varga" and _dir(lk.lean) == head and head != 0 for lk in links)
    active = any(lk.axis == "dasha" for lk in links)
    present = agree + oppose
    # a NON-DIRECTIONAL headline (a 'mixed' rollup) has nothing for an axis to agree or disagree
    # with, so the counting loop above skips every link. Reporting that as WEAK/'aligned' would
    # claim an alignment that was never tested — say plainly that the headline is undecided.
    if head == 0:
        conv: Convergence = "MIXED"
    elif present >= 5 and oppose == 0 and d9 and active:
        conv = "VERY_HIGH"
    elif agree >= 4 and oppose <= 1:
        conv = "HIGH"
    elif present >= 3 and agree > oppose:
        conv = "MODERATE"
    elif present < 3:
        conv = "WEAK"
    else:
        conv = "MIXED"
    # reader label — 'weak' when few axes AGREE is misleading; call that 'lightly evidenced'
    if head == 0:
        label = "the headline itself is undecided"
    elif conv == "WEAK":
        label = "aligned, but lightly evidenced" if oppose == 0 else "little agreement"
    elif conv == "MIXED":
        label = "the evidence splits both ways"
    else:
        label = conv.replace("_", " ").lower() + " convergence"
    counted = ("the headline is undecided, so no axis can agree or oppose it (0 agree, 0 oppose)"
               if head == 0 else
               f"{agree} of {present} independent axes agree with the headline and "
               f"{oppose} oppose it")
    why = (f"{counted} "
           f"({'the navamsa confirms' if d9 else 'the navamsa is neutral/absent'}; "
           f"{'the running period lights it' if active else 'not currently lit'}); "
           f"an evidentiary count, not a probability.")
    return conv, label, why


def _contradictions(r, prim_house, pf, headline, facets, theme_name) -> tuple[Contradiction, ...]:
    """Classify the apparent conflicts and cite the precedence rule that resolves each — ONE
    consolidated statement per axis, never one line per matter (the old per-matter loop printed
    the same H4 grain tension three times)."""
    from app.raman_saab import detailed_report as dr
    from app.raman_saab.insight_digest import _lean_of
    out: list[Contradiction] = []

    # B. house-vs-facet grain (the archetypal 'H4 afflicted but mother/comforts/schooling
    # favourable') -> PREC-1. Consolidated: name every facet whose own verdict differs from the
    # house rollup in ONE line.
    hlean = _dir(_lean_of(headline))
    differ = [m for m, v in facets if _dir(_lean_of(v)) != 0 and _dir(_lean_of(v)) != hlean]
    if differ and hlean != 0:
        other = "favourable" if hlean < 0 else "afflicted"
        out.append(Contradiction(
            "house vs its matters (different grain)",
            (f"House {prim_house} reads {headline} @ house_template.py:236",
             f"but {', '.join(differ)} each read {other} by their dedicated readers"),
            "PREC-1",
            f"The bhava is graded by its single weakest matter, so H{prim_house} reads "
            f"{headline}; each matter above is judged by its own dedicated reader. Both are "
            f"true at different grain — ask the matter for {', '.join(differ)}, the house for "
            f"the bhava as a whole.",
            parties=tuple(differ)))

    # D. split-status within the house -> PREC-3
    split = _safe(lambda: dr.signification_tenor_split(r.calibration.get(prim_house)), None)
    if split is not None and getattr(split, "majority", None) and \
            _dir(_lean_of(split.majority)) != 0 and _dir(_lean_of(split.majority)) != _dir(_lean_of(headline)):
        out.append(Contradiction(
            "house condition vs sub-matters",
            (f"Headline {headline} (weakest matter)",
             f"Majority of significations read {split.majority} "
             f"({split.favourable}F/{split.afflicted}A/{split.mixed}M) @ detailed_report.py:764"),
            "PREC-3",
            "The headline is the weakest decided matter, not the house's overall tenor; the "
            "split is disclosed, the verdict unchanged."))

    # E. strength vs beneficence -> GBB-9
    L = _safe(lambda: dr._lagna_ledger(pf.significations[0]) if pf.significations else None, None)
    if L is not None and (getattr(L, "bhava_bala_strong", None) or getattr(L, "lord_strong", None)) \
            and _lean_of(headline) == "adverse":
        out.append(Contradiction(
            "strength vs beneficence",
            (f"House {prim_house} is strong (Bhava Bala / lord) @ house_template.py:187",
             f"yet the verdict is {headline}"),
            "GBB-9",
            "A strong-but-afflicted house delivers its difficulty with unusual force; strength "
            "is magnitude, not direction (PREC-2)."))

    # F. general vs divisional (D9) -> PREC-5
    m = _matter_reading(r, prim_house)
    if m is not None and _nav_lean(m.navamsa) != "neutral" and \
            _dir(_nav_lean(m.navamsa)) != _dir(_lean_of(headline)) and _dir(_lean_of(headline)) != 0:
        out.append(Contradiction(
            "natal vs divisional confirmation",
            (f"D1 rollup {headline}", f"D9 navamsa: {m.navamsa} @ synthesis.py:39"),
            "PREC-5",
            "The navamsa modulates confidence in the natal indication; it does not overturn "
            "the D1 verdict."))

    return tuple(out)


def _varga_relation(r, prim_house, domain) -> str:
    m = _matter_reading(r, prim_house)
    if m is None or not m.navamsa:
        return "D9-only (no dedicated varga reader for this theme)"
    nl = _nav_lean(m.navamsa)
    if nl == "favourable":
        return "confirms"
    if nl == "adverse":
        return "qualifies (D9 weakens)"
    return "neutral (D9 neither confirms nor weakens)"


#: Raman's four fructification grades, strongest first (HTJAH-I:1592-1596, 1635-1640).
_TIER_ORDER = ("par excellence", "ordinary", "limited", "feeble")


def _theme_timing(r, name, prim_house, houses, dom_planets) -> str:
    """A DIFFERENTIAL, FORWARD-LOOKING timing note, graded by Raman's own fructification scheme.

    Scans the bhuktis ahead of ``ref_jd`` through the engine's shared ``graded_buckets`` (the ONE
    implementation of HTJAH-I:1592-1596 — par excellence / ordinary / limited / feeble) and names
    the window in which this theme's primary bhava is best supported. Three deliberate choices:

    - **Forward only.** A reader asks "when next", not "when was the high-water mark since birth";
      scanning the whole life also makes almost every house peak in the same early bhukti.
    - **Same-lord bhuktis are skipped.** When MD lord == AD lord the association test is trivially
      true, so that bhukti grades par excellence for nearly every house — a degenerate window that
      would drown the differential signal (measured: 11 of 12 houses on one chart).
    - **A theme that never reaches the top tier says so.** That is a real finding (a bhava the
      coming years support only weakly), not an absence to hide.

    Timed-indication idiom throughout — a window that supports an indication, never a decree that
    an event occurs. Silent (empty) when the timeline carries no forward bhukti for the house."""
    from app.raman_saab import detailed_report as dr
    ref = getattr(r, "ref_jd", 0.0)
    periods = getattr(getattr(r, "timeline", None), "periods", ()) or ()
    best: Optional[tuple[int, str, str, str, int, int]] = None
    for tp in periods:
        per = tp.period
        if getattr(per, "end_jd", 0.0) <= ref:          # already past
            continue
        if per.antar and per.maha == per.antar:         # degenerate same-lord bhukti
            continue
        _assoc, buckets = _safe(lambda: dr.graded_buckets(tp, r.chart), (False, {}))
        for tier, items in (buckets or {}).items():
            if not any(getattr(a, "house", None) == prim_house for a in items):
                continue
            rank = _TIER_ORDER.index(tier) if tier in _TIER_ORDER else len(_TIER_ORDER)
            if best is None or rank < best[0]:
                best = (rank, tier, per.maha, per.antar or "",
                        _year(per.start_jd), _year(per.end_jd))
    if best is None:
        return ""
    _rank, tier, maha, antar, y0, y1 = best
    bhukti = f"{maha}/{antar}" if antar else maha
    span = f"{y0}-{y1}" if y1 != y0 else str(y0)
    # both variants open on the same noun phrase so the clause reads correctly standalone AND
    # after the "In time, …" connector the final interpretation puts in front of it
    if tier == _TIER_ORDER[0]:
        return (f"the {bhukti} bhukti ({span}) is the window ahead that best supports it — "
                f"H{prim_house} grades {tier} there on Raman's fructification scheme "
                f"(HTJAH-I:1592-1596).")
    return (f"the {bhukti} bhukti ({span}) offers the strongest support ahead, and only at the "
            f"{tier} grade — H{prim_house} is not carried to the top tier in the years shown "
            f"(HTJAH-I:1592-1596).")


def _final_interpretation(name, headline, convergence, conv_label, contradictions, activation,
                          dom_planets, facets) -> str:
    """A single astrologer's sentence, not a template. Names the driving planet, the verdict, the
    convergence in words, and — where a house's matters read against its headline — that split as
    the theme's own story (not a bolted-on 'a tension is disclosed')."""
    lead = dom_planets[0] if dom_planets else "the chart"
    body = f"{name} reads {headline}, carried chiefly by {lead}"
    grain = next((c for c in contradictions if c.governing == "PREC-1"), None)
    if grain and grain.parties:
        # the house-vs-matters split IS the interpretation here. The differing facets come from
        # `parties` as data — recovering them by slicing the pole PROSE (as this once did) breaks
        # silently the moment the contradiction's wording changes.
        body += (f"; the bhava as a whole takes its tone from its weakest matter, though "
                 f"{', '.join(grain.parties)} read the other way")
    elif convergence in ("VERY_HIGH", "HIGH"):
        body += ", and the independent readings converge strongly"
    else:
        # the reader-facing label, so the sentence and the heading never disagree
        body += f" ({conv_label})"
    if activation:
        # the narrative sentence carries the clause without its citation — the Timing line
        # renders the same note in full, so traceability is not lost by shortening here
        body += ". In time, " + activation.split(" (HTJAH-")[0].rstrip(" .—-")
    return body.rstrip(".") + "."


def _weight(convergence, links, r, houses, dom_planets) -> float:
    """Ranking score for the spine — how load-bearing a theme is, NOT a probability or a verdict.

    Four terms, each of which actually varies across themes:

    - **convergence** — how well the independent readings agree (the dominant term).
    - **centrality** — whether the chart's own busiest grahas drive it (census-ranked biographies).
    - **network breadth** — how many support bhavas survived the evidence gate, i.e. how widely
      the theme is wired into the rest of the chart.
    - **digest salience** — the engine's own ranked digest already says what stands out.

    The previous version added ``len({axes}) * 0.3``, which measured nothing: every theme carries
    the same 5-6 axes, so it was a constant offset masquerading as a signal."""
    base = {"VERY_HIGH": 5.0, "HIGH": 4.0, "MODERATE": 3.0, "MIXED": 2.0, "WEAK": 1.0}[convergence]
    # centrality — the chart's top-3 census grahas that actually drive this theme
    top = [b.planet for b in (getattr(r, "planet_bios", ()) or ())[:3]]
    centrality = min(0.8, 0.4 * sum(1 for p in dom_planets if p in top))
    breadth = 0.25 * max(0, len(set(houses)) - 1)
    # digest salience — highest-ranked digest item touching any of the theme's houses
    prio = 0.0
    hset = set(houses)
    for i, it in enumerate(getattr(getattr(r, "digest", None), "items", ()) or ()):
        if set(getattr(it, "houses", ()) or ()) & hset:
            prio = max(prio, 1.0 - i * 0.1)
    return base + centrality + breadth + prio


def _connections(themes) -> tuple[ThemeConnection, ...]:
    """Discover a GENUINE shared mechanism between two themes — a strong tie, not a coincidence.
    A connection needs EITHER the same CHIEF driving planet (dom_planets[0] equal — the same graha
    leads both), OR one theme's PRIMARY house sitting inside the other's network (a real
    structural overlap). Merely sharing a broad karaka (Jupiter signifies half the chart) does
    NOT qualify — that produced the old 'everything connects to wealth' noise."""
    picks = list(themes)
    out: list[ThemeConnection] = []
    seen: set[frozenset] = set()
    for i, a in enumerate(picks):
        for b in picks[i + 1:]:
            key = frozenset((a.theme_id, b.theme_id))
            if key in seen:
                continue
            lead_a = a.dominant_planets[0] if a.dominant_planets else None
            lead_b = b.dominant_planets[0] if b.dominant_planets else None
            same_lead = lead_a and lead_a == lead_b
            prim_overlap = (a.houses and a.houses[0] in b.houses) or \
                           (b.houses and b.houses[0] in a.houses)
            if not same_lead and not prim_overlap:
                continue
            seen.add(key)
            if same_lead:
                shared = lead_a
                note = (f"{a.name} and {b.name} are both led by {lead_a} — one graha carries "
                        f"both, so they tend to ripen and strain together.")
            else:
                h = a.houses[0] if a.houses and a.houses[0] in b.houses else b.houses[0]
                shared = f"H{h}"
                note = (f"{a.name} and {b.name} overlap at H{h} — the same bhava participates in "
                        f"both, tying the two areas together.")
            out.append(ThemeConnection(a.name, b.name, shared, note))
    return tuple(out[:6])


def _year(jd: float) -> int:
    return int(swe.revjul(jd, swe.GREG_CAL)[0])


def _node_agents(r) -> dict[str, tuple[str, ...]]:
    """{node: the planets it acts for} — Rahu and Ketu carry no rulership of their own, so they
    give the results of the lord of the sign they occupy (their dispositor) and of any planet
    joined with them. Without this a node can NEVER appear among a theme's driving planets (it is
    never a sign-lord and never a domain karaka), so every Rahu/Ketu Mahadasha — a quarter of the
    120-year Vimshottari cycle — would foreground nothing at all.

    Conjunction is sign membership, per the project's locked drishti convention. Pure re-read of
    the cast chart; empty when a node is absent."""
    from app.raman_saab.chart.constants import SIGN_LORDS
    out: dict[str, tuple[str, ...]] = {}
    planets = getattr(getattr(r, "chart", None), "planets", {}) or {}
    for node in ("Rahu", "Ketu"):
        p = planets.get(node)
        if p is None:
            continue
        agents: list[str] = []
        disp = _safe(lambda: SIGN_LORDS[p.sign], None)
        if disp and disp not in agents:
            agents.append(disp)
        for other, op in planets.items():
            if other in ("Rahu", "Ketu") or other in agents:
                continue
            if getattr(op, "sign", None) == p.sign:      # joined with the node (same sign)
                agents.append(other)
        out[node] = tuple(agents)
    return out


def _dasha_evolution(r, themes) -> tuple[DashaChapter, ...]:
    """Which life-themes each Mahadasha FOREGROUNDS, chapter by chapter — the horoscope's
    evolution through time. Differential, not flooding: a theme is foregrounded by a chapter only
    when the Mahadasha lord is one of that theme's OWN driving planets (``dominant_planets``), so
    the Saturn period foregrounds career and foundations (which Saturn drives), not all nine
    themes at once. A pure re-read — the lord names and spans are the chapters' own; no new dasha
    math. When a chapter's lord drives none of the tracked themes that is stated as such (a fallow
    stretch), never padded with everything the lord distantly touches."""
    lc = getattr(r, "life_chapters", None)
    chapters = getattr(lc, "chapters", ()) if lc else ()
    if not chapters:
        return ()
    theme_drivers = [(t.name, set(t.dominant_planets)) for t in themes]
    agents = _node_agents(r)
    out: list[DashaChapter] = []
    prev: set[str] = set()
    for ch in chapters:
        lord = getattr(ch, "maha", "") or ""
        # a node rules nothing of its own — it foregrounds what its dispositor and its
        # co-tenants drive, and the routing is disclosed rather than silently assumed
        acts_through = agents.get(lord, ()) if lord in agents else ()
        keys = {lord} | set(acts_through)
        active = tuple(name for name, drv in theme_drivers if keys & drv)
        aset = set(active)
        emerging = tuple(n for n in active if n not in prev)
        continuing = tuple(n for n in active if n in prev)
        out.append(DashaChapter(
            maha=lord,
            span=f"{_year(ch.start_jd)}-{_year(ch.end_jd)}",
            is_current=bool(getattr(ch, "is_current", False)),
            lean=getattr(ch, "lean", None) or "neutral",
            activates=active, emerging=emerging, continuing=continuing,
            acts_through=acts_through))
        prev = aset
    return tuple(out)


def _spine_size(themes) -> int:
    """How many themes form the spine: 3-5, cut where the ranked weights actually fall away.

    A spine that names most of the roster names nothing. The old rule took up to SEVEN and only
    stopped on a drop greater than 1.0 — a threshold the distribution almost never crosses, so
    every chart returned the maximum (measured: 7 of 12 on all three test charts). Instead, choose
    among the allowed sizes the one that sits at the LARGEST drop in the ranking, so the cut lands
    on this chart's own break rather than on an absolute constant."""
    n = len(themes)
    if n <= 3:
        return n
    lo, hi = 3, min(5, n)
    best_size, best_gap = lo, -1.0
    for size in range(lo, hi + 1):
        if size >= n:
            break
        gap = themes[size - 1].evidence_weight - themes[size].evidence_weight
        if gap > best_gap:
            best_gap, best_size = gap, size
    return best_size


# plain-language names for the census relation keys (planet_biographies census_by_relation)
_REL_WORD = {
    "karaka_of": "as karaka", "lord_of": "as house-lord", "aspects": "by aspect",
    "occupies": "by occupation", "maraka_tier": "in a maraka role",
    "conjoins": "by conjunction", "helps": "as a helper", "obstructs": "as an obstructor",
}


def _identity_line(r) -> str:
    """Who the chart IS, in one line: Lagna and its lord, the Atmakaraka and its Karakamsa sign,
    and the Moon's nakshatra. Pure re-read of r.synthesis + r.chart; empty on a sparse chart."""
    from app.raman_saab.chart.constants import SIGN_LORDS
    from app.raman_saab.primitives import nakshatra_signature
    sy = getattr(r, "synthesis", None)
    if sy is None:
        return ""
    parts: list[str] = []
    lagna = getattr(sy, "lagna", "") or ""
    asc = getattr(getattr(r, "chart", None), "asc_sign", None)
    if lagna and asc is not None:
        lord = _safe(lambda: SIGN_LORDS[asc], "")
        parts.append(f"{lagna} lagna ruled by {lord}" if lord else f"{lagna} lagna")
    ak = getattr(sy, "atmakaraka", "") or ""
    km = getattr(sy, "karakamsa", "") or ""
    if ak:
        parts.append(f"Atmakaraka {ak}" + (f" with Karakamsa in {km}" if km else ""))
    moon = _safe(lambda: r.chart.planets.get("Moon"), None)
    if moon is not None:
        nk = _safe(lambda: nakshatra_signature.signature_for(moon.nakshatra), None)
        if nk is not None:
            pada = getattr(moon, "pada", None)
            parts.append(f"Moon in {nk.name}" + (f" (pada {pada})" if pada else ""))
    return "; ".join(parts) + "." if parts else ""


def _portrait(r, themes, spine, frame) -> ExecutivePortrait:
    from app.raman_saab.insight_digest import _lean_of
    by_id = {t.theme_id: t for t in themes}
    spine_themes = [by_id[i] for i in spine if i in by_id]

    identity = _identity_line(r)

    # temperament — Moon frame / lagna nature word from the overview, plus the dominant graha
    temperament = _safe(lambda: getattr(r.overview, "temperament", "") or "", "") or \
        (f"read chiefly from the {frame}" if frame else "")

    # dominant actors — census-ranked biographies (planet_bios[0] is dominant), why in plain words
    actors: list[tuple[str, str]] = []
    for i, bio in enumerate((getattr(r, "planet_bios", ()) or ())[:3]):
        breakdown = sorted((getattr(bio, 'census_by_relation', ()) or ()),
                           key=lambda kv: kv[1], reverse=True)
        roles = ", ".join(f"{v}x {_REL_WORD.get(k, k.replace('_', ' '))}" for k, v in breakdown[:4])
        lead = "the chart's busiest graha" if i == 0 else "also prominent"
        why = f"{lead} — {bio.census_count} structural roles" + (f" ({roles})" if roles else "")
        actors.append((bio.planet, why))

    fav = [t for t in spine_themes if _lean_of(t.headline_verdict) == "favourable"]
    adv = [t for t in spine_themes if _lean_of(t.headline_verdict) == "adverse"]

    # principal tension — the chart's REAL structural pull, not a method note: the strongest
    # favourable spine theme set against the strongest strained one (both already weight-sorted).
    # Falls back to the single most-load-bearing contradiction, then to an honest 'no dominant
    # tension' when the spine agrees in direction.
    tensions = [c for t in themes for c in t.contradictions]
    if fav and adv:
        a, b = fav[0], adv[0]
        al, bl = a.dominant_planets[0] if a.dominant_planets else "", \
            b.dominant_planets[0] if b.dominant_planets else ""
        principal = (f"the chart's centre of gravity is {a.name.lower()} "
                     f"({a.headline_verdict}"
                     + (f", carried by {al}" if al else "") + "), while "
                     f"{b.name.lower()} carries the countervailing strain "
                     f"({b.headline_verdict}"
                     + (f", on {bl}" if bl else "") + ") — the central negotiation of the life "
                     "runs between the two.")
    elif tensions:
        principal = tensions[0].resolution
    else:
        principal = ("No single structural tension dominates — the spine themes agree in "
                     "direction, so the chart reads as of a piece.")

    protective = _protective_factors(r)
    cur = _safe(lambda: f"{r.synthesis.running_md} MD / {r.synthesis.running_ad} AD", "")
    nxt = _next_chapter(r)
    honesty = _safe(lambda: r.info.sentence, "") or ""

    return ExecutivePortrait(
        identity=identity, temperament=temperament, frame=frame, dominant_actors=tuple(actors),
        strongest_domains=tuple(t.name for t in fav[:4]),
        weakest_domains=tuple(t.name for t in adv[:4]),
        principal_tension=principal, protective_factors=protective,
        current_chapter=cur, next_chapter=nxt, honesty_note=honesty)


def _protective_factors(r) -> tuple[str, ...]:
    """Bhanga / neecha-bhanga / benefic-relief already flagged on the report — never invented."""
    out: list[str] = []
    bal = getattr(r, "balarishta", None)
    if bal is not None and getattr(bal, "cancelled", False):
        out.append("Balarishta present but cancelled (bhanga)")
    # longevity band as a protective foundation (band word only, never a date)
    lc = getattr(r, "longevity_class", "") or ""
    if lc:
        out.append(f"longevity reads at the {lc} band")
    return tuple(out[:4])


def _next_chapter(r) -> str:
    """The next MD boundary and its lean, from the timeline — a timed indication, not a decree."""
    tl = getattr(r, "life_chapters", None)
    chapters = getattr(tl, "chapters", ()) if tl else ()
    ref = getattr(r, "ref_jd", 0.0)
    for ch in chapters:
        start = getattr(ch, "start_jd", None)
        if start is not None and start > ref:
            lord = getattr(ch, "lord", getattr(ch, "maha", "the next"))
            return f"the {lord} chapter follows"
    return ""
