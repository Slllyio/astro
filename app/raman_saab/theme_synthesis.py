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
    dominant_planets: tuple[str, ...]
    links: tuple[ThemeEvidenceLink, ...]
    convergence: Convergence
    convergence_why: str
    contradictions: tuple[Contradiction, ...]
    activation_span: str            # period_pairing_clause — timed-indication idiom, never decree
    varga_relation: str             # confirms / strengthens / qualifies / modifies / contradicts / D9-only
    final_interpretation: str
    evidence_weight: float = 0.0    # for ranking only; NOT a probability or a verdict


@dataclass(frozen=True)
class ExecutivePortrait:
    """The two-page opening: if you read only this, what is this horoscope?"""
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
class ThemeSynthesis:
    """The whole integrated interpretation: ranked themes, the dominant-theme spine, and the
    executive portrait. Built last, re-read only."""
    themes: tuple[ThemeReading, ...]
    spine: tuple[str, ...]          # theme_ids of the 3-7 dominant themes
    frame: str
    portrait: ExecutivePortrait


# ─────────────────────────────────────────────────────────────────────────────
# the theme roster — engine-sourced, not hardcoded per chart
# ─────────────────────────────────────────────────────────────────────────────
# Each candidate life-theme names its PRIMARY dashboard matter (the engine's own authoritative
# matter), the varga whose domain (varga_domains.DOMAINS) supplies its houses+karakas, and any
# classically-connected SUPPORTING houses. Supporting houses are only KEPT when the graph shows
# the theme's driving planet actually touches them (pass 3) — so networks are DISCOVERED from the
# chart, never asserted. Themes whose matter the engine does not judge are dropped.
_THEME_ROSTER: tuple[tuple[str, str, str, int, tuple[int, ...]], ...] = (
    # theme_id,       display name,               dashboard matter, varga(for domain), candidate support houses
    ("wealth",        "Wealth & resources",       "wealth",         2,  (11, 8)),
    ("career",        "Career & public standing", "career",         10, (2, 6, 11)),
    ("marriage",      "Marriage & partnership",   "marriage",       9,  (2, 11)),
    ("children",      "Children & progeny",       "children",       7,  (9,)),
    ("home",          "Home & property",          "property",       4,  (2,)),
    ("mother",        "Mother",                   "mother",         12, (4,)),
    ("father",        "Father & fortune",         "father",         12, (10,)),
    ("learning",      "Learning & intellect",     "education",      24, (5, 3)),
    ("health",        "Health & vitality",        "health",         30, (1, 8)),
    ("spirituality",  "Spirituality & liberation", "spiritual",     20, (12, 5)),
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
    matters = {m.house: m for m in r.synthesis.matters}
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
    for theme_id, name, matter_key, varga_n, support in _THEME_ROSTER:
        entry = dash.get(matter_key)
        prim_house = dr._MATTER_HOUSE.get(matter_key)
        if entry is None or prim_house is None or prim_house not in proformas:
            continue                                # the engine does not judge this matter -> drop
        try:
            domain = vd.domain_for(varga_n)
        except ValueError:
            continue

        pf = proformas[prim_house]
        headline = pf.rollup                        # PASSTHROUGH — never recomputed
        driver = dr.rollup_driver(r.calibration.get(prim_house), headline) or matter_key

        # pass 2 + 3: gather evidence links and discover the network / dominant planets
        links: list[ThemeEvidenceLink] = []
        dom_planets = _dominant_planets(r, prim_house, domain, census, planet_houses)
        kept_support = _discover_support(prim_house, support, dom_planets, planet_houses)
        houses = (prim_house,) + kept_support

        links.extend(_verdict_links(r, prim_house, kept_support, proformas))
        links.extend(_dashboard_link(entry))
        links.extend(_varga_links(r, prim_house, matters, domain))
        links.extend(_yoga_links(r, houses, yoga_house_bearings))
        links.extend(_strength_state_links(r, prim_house, pf, dom_planets))
        links.extend(_dasha_links(r, houses))
        links.extend(_transit_links(r, houses))
        links.extend(_insight_links(r, houses))

        # pass 4: convergence (evidentiary count, both poles)
        convergence, why = _convergence(headline, links, r)
        # pass 5: contradictions (classified, PREC-cited)
        contradictions = _contradictions(r, prim_house, pf, headline, matters, name)

        activation = _safe(lambda: dr.period_pairing_clause(r, houses), "")
        varga_rel = _varga_relation(r, prim_house, matters, domain)
        final = _final_interpretation(name, headline, convergence, contradictions,
                                      activation, dom_planets)
        weight = _weight(convergence, links, r, houses)

        themes.append(ThemeReading(
            theme_id=theme_id, name=name, domain=domain.domain, houses=houses,
            karakas=domain.karakas, headline_verdict=headline, driver=driver,
            dominant_planets=dom_planets, links=tuple(links), convergence=convergence,
            convergence_why=why, contradictions=contradictions, activation_span=activation,
            varga_relation=varga_rel, final_interpretation=final, evidence_weight=weight))

    # pass 6: rank + spine + portrait
    themes.sort(key=lambda t: t.evidence_weight, reverse=True)
    spine = tuple(t.theme_id for t in themes[:_spine_size(themes)])
    frame = getattr(r.overview, "stronger_frame", "") or ""
    portrait = _portrait(r, themes, spine, frame)
    return ThemeSynthesis(themes=tuple(themes), spine=spine, frame=frame, portrait=portrait)


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


def _dominant_planets(r, prim_house, domain, census, planet_houses) -> tuple[str, ...]:
    """The planets that structurally drive this theme's primary house: its lagna-frame lord,
    its domain karakas, and any census-dominant graha that touches the house. The 'why' is the
    census breadth itself — no invented score. Deduped, order-stable, capped at 3."""
    out: list[str] = []
    # 1. the primary house's lagna-frame lord (frame-lord-trap-safe)
    from app.raman_saab import detailed_report as dr
    pf = next((p for p in r.proformas if p.house == prim_house), None)
    if pf is not None:
        out.append(pf.lord)
    # 2. domain karakas that the census confirms as participating
    for k in domain.karakas:
        if k not in out and (k in census or prim_house in planet_houses.get(k, set())):
            out.append(k)
    # 3. any planet the graph shows touching this house, ranked by census breadth
    touch = [(p, sum(census.get(p, {}).values())) for p, hs in planet_houses.items()
             if prim_house in hs and p not in out]
    for p, _ in sorted(touch, key=lambda x: x[1], reverse=True):
        out.append(p)
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


def _dashboard_link(entry) -> list[ThemeEvidenceLink]:
    from app.raman_saab.insight_digest import _lean_of
    return [ThemeEvidenceLink(
        "verdict", f"{entry.matter} ({entry.varga_name}) reader", entry.verdict,
        _lean_of(entry.verdict),
        "r.dashboard.entries[*].verdict @ matter_varga_dashboard.py:38", RAMAN_EXPLICIT)]


def _varga_links(r, prim_house, matters, domain) -> list[ThemeEvidenceLink]:
    m = matters.get(prim_house)
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


def _transit_links(r, houses) -> list[ThemeEvidenceLink]:
    """Transit as the SUBORDINATE modifier only — a dasha-x-transit confluence row whose
    period lord activates one of the theme's houses. Never an independent prediction."""
    hset = set(houses)
    out: list[ThemeEvidenceLink] = []
    for c in getattr(r, "dasha_transit", ()) or ():
        chouses = set(getattr(c, "houses", ()) or ())
        if chouses and (chouses & hset):
            lbl = getattr(c, "label", None) or getattr(c, "planet", "period lord")
            out.append(ThemeEvidenceLink(
                "transit", "Dasha x transit confluence", str(lbl), "neutral",
                "r.dasha_transit @ detailed_report.py:1506", RAMAN_GENERAL))
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


def _convergence(headline, links, r) -> tuple[Convergence, str]:
    """Count agreeing vs opposing DIRECTION-bearing axes; always report both poles."""
    from app.raman_saab.insight_digest import _lean_of
    head = _dir(_lean_of(headline))
    agree = oppose = 0
    for lk in links:
        if lk.axis not in ("verdict", "varga", "yoga"):
            continue                                # only direction-bearing axes count
        d = _dir(lk.lean)
        if d == 0 or head == 0:
            continue
        if d == head:
            agree += 1
        else:
            oppose += 1
    d9 = any(lk.axis == "varga" and _dir(lk.lean) == head and head != 0 for lk in links)
    active = any(lk.axis == "dasha" for lk in links)
    present = agree + oppose
    if present >= 5 and oppose == 0 and d9 and active:
        conv: Convergence = "VERY_HIGH"
    elif agree >= 4 and oppose <= 1:
        conv = "HIGH"
    elif oppose >= 1 and agree > oppose:
        conv = "MODERATE"
    elif present < 3:
        conv = "WEAK"
    else:
        conv = "MIXED"
    why = (f"{agree} of {present} direction-bearing axes agree with the headline "
           f"({'D9 confirms' if d9 else 'D9 neutral/absent'}; "
           f"{oppose} oppose; {'a running period activates it' if active else 'not currently lit'}). "
           f"Both poles are reported; this is evidentiary agreement, not a probability.")
    return conv, why


def _contradictions(r, prim_house, pf, headline, matters, theme_name) -> tuple[Contradiction, ...]:
    """Classify the apparent conflicts and cite the precedence rule that resolves each."""
    from app.raman_saab import detailed_report as dr
    from app.raman_saab.insight_digest import _lean_of
    out: list[Contradiction] = []

    # B. house-vs-dashboard grain (the archetypal 'H4 afflicted != mother afflicted') -> PREC-1
    conflicts = _safe(lambda: dr.house_dashboard_conflicts(r, prim_house), ()) or ()
    for c in conflicts:
        out.append(Contradiction(
            "different_grain (house vs matter)",
            (f"House {prim_house} rollup: {headline} @ house_template.py:236", str(c)),
            "PREC-1",
            "The house is graded by its weakest matter; the dashboard names one matter judged "
            "by its dedicated reader. Both are true at different grain."))

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
    m = matters.get(prim_house)
    if m is not None and _nav_lean(m.navamsa) != "neutral" and \
            _dir(_nav_lean(m.navamsa)) != _dir(_lean_of(headline)) and _dir(_lean_of(headline)) != 0:
        out.append(Contradiction(
            "natal vs divisional confirmation",
            (f"D1 rollup {headline}", f"D9 navamsa: {m.navamsa} @ synthesis.py:39"),
            "PREC-5",
            "The navamsa modulates confidence in the natal indication; it does not overturn "
            "the D1 verdict."))

    return tuple(out)


def _varga_relation(r, prim_house, matters, domain) -> str:
    m = matters.get(prim_house)
    if m is None or not m.navamsa:
        return "D9-only (no dedicated varga reader for this theme)"
    nl = _nav_lean(m.navamsa)
    if nl == "favourable":
        return "confirms"
    if nl == "adverse":
        return "qualifies (D9 weakens)"
    return "neutral (D9 neither confirms nor weakens)"


def _final_interpretation(name, headline, convergence, contradictions, activation, dom_planets) -> str:
    lead = dom_planets[0] if dom_planets else "the chart"
    parts = [f"{name} reads {headline}, carried chiefly by {lead}; "
             f"the independent readings show {convergence.replace('_', ' ').lower()} convergence."]
    if contradictions:
        parts.append(f" One tension is disclosed and resolved by {contradictions[0].governing}.")
    if activation:
        parts.append(f" {activation}")
    return "".join(parts)


def _weight(convergence, links, r, houses) -> float:
    base = {"VERY_HIGH": 5.0, "HIGH": 4.0, "MODERATE": 3.0, "MIXED": 2.0, "WEAK": 1.0}[convergence]
    axes = len({lk.axis for lk in links})
    # bump by digest priority if a digest item concerns any of the theme's houses
    prio = 0.0
    hset = set(houses)
    for i, it in enumerate(getattr(getattr(r, "digest", None), "items", ()) or ()):
        if set(getattr(it, "houses", ()) or ()) & hset:
            prio = max(prio, 1.0 - i * 0.1)
    return base + axes * 0.3 + prio


def _spine_size(themes) -> int:
    """3-7 dominant themes; fewer if the evidence does not support more (a big weight gap)."""
    if len(themes) <= 3:
        return len(themes)
    # take up to 7, but stop early where the weight drops off a cliff
    cap = min(7, len(themes))
    for i in range(3, cap):
        if themes[i - 1].evidence_weight - themes[i].evidence_weight > 1.0:
            return i
    return cap


def _portrait(r, themes, spine, frame) -> ExecutivePortrait:
    from app.raman_saab.insight_digest import _lean_of
    by_id = {t.theme_id: t for t in themes}
    spine_themes = [by_id[i] for i in spine if i in by_id]

    # temperament — Moon frame / lagna nature word from the overview, plus the dominant graha
    temperament = _safe(lambda: getattr(r.overview, "temperament", "") or "", "") or \
        (f"read chiefly from the {frame}" if frame else "")

    # dominant actors — census-ranked biographies (planet_bios[0] is dominant), why = census breadth
    actors: list[tuple[str, str]] = []
    for bio in (getattr(r, "planet_bios", ()) or ())[:3]:
        why = f"{bio.census_count} structural appearances (" + \
              ", ".join(f"{k} {v}" for k, v in (getattr(bio, 'census_by_relation', ()) or ())[:3]) + ")"
        actors.append((bio.planet, why))

    fav = [t.name for t in spine_themes if _lean_of(t.headline_verdict) == "favourable"]
    adv = [t.name for t in spine_themes if _lean_of(t.headline_verdict) == "adverse"]

    tensions = [c for t in themes for c in t.contradictions]
    principal = tensions[0].resolution if tensions else "No major cross-section contradiction is flagged."

    protective = _protective_factors(r)
    cur = _safe(lambda: f"{r.synthesis.running_md} MD / {r.synthesis.running_ad} AD", "")
    nxt = _next_chapter(r)
    honesty = _safe(lambda: r.info.sentence, "") or ""

    return ExecutivePortrait(
        temperament=temperament, frame=frame, dominant_actors=tuple(actors),
        strongest_domains=tuple(fav[:4]), weakest_domains=tuple(adv[:4]),
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
