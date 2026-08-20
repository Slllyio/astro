"""The Yoga deep-read (section v21) — every fired yoga as a complete study.

Per fired yoga: Raman's definition QUOTED verbatim around its 3HC/HPA citation
(`sources.passage`; where the corpus is not mounted an honest absence line plus the
record's paraphrase is rendered — never an empty quotation), the exact computation (the
condition tree rendered readable), why it qualifies (each participant's chart facts),
MEASURED strength (Shadbala rupas + bhanga-aware effective dignity — deliberately no
invented percentage: numeric weighting is measured-null in this project and Raman states
no such figure), cancellation state (only the ENCODED bhangas Raman states — neecha
bhanga via `bhangas.effective_dignity`; Kemadruma already folds its own bhanga into
firing; dusthana-formation nullification and Raja-Yoga Bhanga are disclosed as
not-graded), modifying planets (aspect edges from the judgment graph), operating periods
(the existing `yoga_timing` rows, quality rendered as prose), and historical importance
(Notable Horoscopes mentions, cited). Closes with a comparison ranking the chart's fired
yogas by their participants' measured strength.

Participants are resolved SEMANTICALLY via `synthesis_rules._yoga_planets` — the same
resolver the Yoga×Dasha timing section uses — so a flank yoga names the planet actually
occupying the flank, not every candidate its condition tree enumerates. The syntactic
graha-name scan (`participants`) remains only as a last-resort fallback; where neither
resolves (the Nabhasa whole-chart patterns, multi-arm lordship yogas) the read says so
plainly instead of claiming the chart lacks Shadbala.

PURE RE-READ (PREC-10): nothing here re-decides whether a yoga fires.

Usage:
    from app.raman_saab.yoga_deep_read import build_yoga_deep_reads
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.sources import passage
from app.raman_saab.judgment_graph import JudgmentGraph

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport

_GRAHAS: Final[frozenset[str]] = frozenset({
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"})

#: Notable Horoscopes mentions per yoga-name fragment (mined 2026-08-03; the passage
#: around each line names the nativity — Nero, Akbar, et al.).
NH_EXAMPLES: Final[dict[str, tuple[str, ...]]] = {
    "Gajakesari": ("NH:1181", "NH:1189", "NH:1778", "NH:1993"),
    "Hamsa": ("NH:1330", "NH:1346", "NH:1441", "NH:1778", "NH:2580"),
    "Adhi": ("NH:1369", "NH:1442"),
    "Anapha": ("NH:2484",),
    "Malavya": ("NH:2580", "NH:2626", "NH:3099"),
    "Sasa": ("NH:3099",),
    "Ruchaka": ("NH:3099",),
}


def describe(cond: C.Condition) -> str:
    """Render a condition tree as readable text — the yoga's exact computation."""
    if isinstance(cond, C.And):
        return "(" + " AND ".join(describe(c) for c in cond.conds) + ")"
    if isinstance(cond, C.Or):
        return "(" + " OR ".join(describe(c) for c in cond.conds) + ")"
    if isinstance(cond, C.Not):
        return f"NOT {describe(cond.cond)}"
    if isinstance(cond, C.AtLeastN):
        return (f"at least {cond.n} of (" + "; ".join(describe(c) for c in cond.conds)
                + ")")
    name = type(cond).__name__
    attrs = {k: v for k, v in vars(cond).items() if not k.startswith("_")}
    inner = ", ".join(f"{k}={_describe_value(v)}" for k, v in attrs.items())
    return f"{name}({inner})"


def _describe_value(v: object) -> str:
    """Render one condition argument DETERMINISTICALLY.

    A bare f-string on a `set`/`frozenset` renders it in iteration order, which follows the
    interpreter's per-process string hash — so the same chart produced
    ``states={'moolatrikona', 'own'}`` in one process and ``states={'own', 'moolatrikona'}`` in
    the next. One line of an otherwise byte-stable report changing between runs is a real
    defect: it breaks output diffing, which is how a refactor is proven not to have moved a
    verdict (this was found by exactly such a diff). Sets are sorted; everything else is
    unchanged.
    """
    if isinstance(v, (set, frozenset)):
        return "{" + ", ".join(repr(x) for x in sorted(v, key=repr)) + "}"
    return str(v)


def participants(cond: C.Condition) -> tuple[str, ...]:
    """Every graha the condition tree names, in first-appearance order."""
    seen: list[str] = []

    def walk(c: C.Condition) -> None:
        for k, v in vars(c).items():
            if k.startswith("_"):
                continue
            if isinstance(v, str) and v in _GRAHAS and v not in seen:
                seen.append(v)
            elif isinstance(v, C.Condition):
                walk(v)
            elif isinstance(v, (tuple, list)):
                for item in v:
                    if isinstance(item, C.Condition):
                        walk(item)
                    elif isinstance(item, str) and item in _GRAHAS and item not in seen:
                        seen.append(item)
    walk(cond)
    return tuple(seen)


@dataclass(frozen=True)
class ParticipantFacts:
    planet: str
    house: int
    sign: int
    dignity: str
    effective_dignity: str      # bhanga-aware (bhangas.effective_dignity)
    rupas: Optional[float]      # Shadbala; None on Track-B
    strong: Optional[bool]
    # Wave-2 enrichment (2026-08-18, append-only): the 3HC remarks' standard strength
    # qualifiers, labelled from values the read already holds — the participant's
    # kendra/trikona/dusthana placement class (from `house`) and its functional nature
    # for THIS Lagna (primitives.functional_nature, HTJAH-I:523-604). Labels only;
    # nothing re-judged.
    placement: str = ""         # "kendra-trikona (Lagna)" | "kendra" | "trikona" | "dusthana" | "other"
    functional: str = ""        # "benefic" | "malefic" | "neutral" | "yogakaraka" | ""


@dataclass(frozen=True)
class YogaDeepRead:
    id: str
    name: str
    kind: str
    effect: str
    cite: str
    definition_quote: str               # verbatim passage around the citation
    computation: str                    # describe(condition)
    participants: tuple[ParticipantFacts, ...]
    strength_note: str                  # measured values, never a percentage
    cancellation_note: str
    modifiers: tuple[str, ...]          # planets aspecting the participants (graph)
    periods: tuple[str, ...]            # yoga_timing windows, pre-formatted
    nh_examples: tuple[str, ...]
    comparison_rank: int                # 1 = strongest participants among fired yogas
    # Wave-2 enrichment (2026-08-18, append-only): SYN_R1 applied to THIS yoga's own
    # resolved participants — "of the planets forming a yoga, the stronger delivers
    # most of it, in his own periods" (3HC:1359). Empty when fewer than two
    # participants carry Shadbala (a single-causer yoga has no stronger-of-two).
    syn_r1_line: str = ""


def _quality_prose(q) -> str:
    """A `vimshottari.LordQuality` as reader prose — never the dataclass repr.

    e.g. "well - friend, strong" / "poorly - combust, though vargottama (HTJAH-I:5372)".
    The vargottama reconciliation clause (with Raman's vargottama-doubling citation,
    HTJAH-I:5372) appears only when the flag is True yet the delivery tag reads
    poorly/mixed — the case a reader would otherwise find contradictory. ASCII-safe.
    """
    bits: list[str] = []
    if q.dignity and q.dignity not in ("neutral", "unknown"):
        bits.append(q.dignity)
    if q.combust:
        bits.append("combust")
    if q.strong is True:
        bits.append("strong")
    elif q.strong is False:
        bits.append("weak")
    if q.vargottama and q.tag not in ("poorly", "mixed"):
        bits.append("vargottama")
    prose = q.tag + (" - " + ", ".join(bits) if bits else "")
    if q.vargottama and q.tag in ("poorly", "mixed"):
        prose += ", though vargottama (HTJAH-I:5372)"
    return prose


#: Disclosure appended when no encoded cancellation applies — the two Raman-stated
#: formation-strength modifiers the engine does NOT grade (citations already on record in
#: `synthesis_rules.yoga_house_bearings`; never invented here).
_CANCEL_NOT_GRADED: Final[str] = (
    "none of the encoded Raman-stated cancellations applies; not graded here: "
    "dusthana-formation nullification (HTJAH-I:2948-2956), Raja-Yoga Bhanga "
    "(HTJAH-I:15903)")


def placement_tag(house: int) -> str:
    """The kendra/trikona/dusthana class of a rasi house (1..12) — the standard strength
    qualifier 3HC's remarks apply to a yoga-causer's seat. House 1 is BOTH a kendra and a
    trikona and is labelled as such; 2/3/11 fall in none of the three classes."""
    if house == 1:
        return "kendra-trikona (Lagna)"
    if house in (4, 7, 10):
        return "kendra"
    if house in (5, 9):
        return "trikona"
    if house in (6, 8, 12):
        return "dusthana"
    return "other"


def kemadruma_cancellation_branch(chart) -> Optional[str]:
    """Which bhanga branch cancels this chart's Kemadruma geometry — a DISCLOSURE re-read
    of :func:`app.raman_saab.primitives.bhangas.kemadruma_bhanga`, naming the FIRST branch
    that fires in that primitive's own evaluation order (3HC:2182-2185 branches a/b/c,
    then the extended benefic-drishti branch the primitive documents as Phase-2 backfill,
    not 3HC). Returns None when no branch fires — by construction, non-None here iff
    `kemadruma_bhanga(chart)` is True (paired test pins the equivalence). Nothing is
    re-judged: the record `Y.KEMADRUMA` still decides firing on its own."""
    from app.raman_saab.doctrine import drishti
    from app.raman_saab.primitives.bhangas import _KENDRA, _in_kendra_from
    from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS
    if "Moon" not in chart.planets:
        return None
    moon_h = chart.planets["Moon"].rasi_house
    if moon_h in _KENDRA:
        return "the Moon itself in a kendra from the Lagna (3HC:2182-2185)"
    for name, pl in chart.planets.items():
        if name in ("Moon", "Rahu", "Ketu"):
            continue
        if pl.rasi_house in _KENDRA:
            return f"{name} in a kendra from the Lagna (3HC:2182-2185)"
        if _in_kendra_from(name, moon_h, chart):
            return f"{name} in a kendra from the Moon (3HC:2182-2185)"
        if pl.rasi_house == moon_h:
            return f"the Moon in conjunction with {name} (3HC:2182-2185)"
    for name in NATURAL_BENEFICS:
        if name != "Moon" and drishti.aspects_planet(name, "Moon", chart):
            return (f"benefic {name} aspecting the Moon (extended bhanga - "
                    f"standard doctrine, not 3HC:2182-2185)")
    return None


def _syn_r1_line(parts: tuple[ParticipantFacts, ...]) -> str:
    """SYN_R1 (3HC:1359) applied to this yoga's own resolved participants: name the
    strongest-by-Shadbala as delivering the larger part in its own periods. Empty unless
    two-plus participants carry rupas and the extremes are distinct planets — the same
    guards `synthesis_rules._chk_r1` applies chart-wide."""
    scored = [f for f in parts if f.rupas is not None]
    if len(scored) < 2:
        return ""
    scored.sort(key=lambda f: -f.rupas)
    lead, sub = scored[0], scored[-1]
    if lead.planet == sub.planet:
        return ""
    of = "pair" if len(scored) == 2 else f"{len(scored)} participants"
    return (f"of the {of}, {lead.planet} at {lead.rupas:.2f} rupas delivers the larger "
            f"part of this yoga's indications, in its own periods; {sub.planet} "
            f"({sub.rupas:.2f}) acts as sub-lord to a lesser extent (3HC:1359)")


def _participant_facts(planet: str, r: "DetailedReport") -> Optional[ParticipantFacts]:
    from app.raman_saab.doctrine.synthesis_rules import _rupas, _strong
    from app.raman_saab.primitives.bhangas import effective_dignity
    from app.raman_saab.primitives.dignity import dignity as _dignity
    from app.raman_saab.primitives.functional_nature import functional_nature
    p = r.chart.planets.get(planet)
    if p is None:
        return None
    rupas = _rupas(r.chart, planet)
    strong = _strong(r.chart, planet)
    try:
        dig = _dignity(planet, r.chart)
    except Exception:  # noqa: BLE001
        dig = "unknown"
    try:
        eff = effective_dignity(planet, r.chart)
    except Exception:  # noqa: BLE001
        eff = dig
    try:
        func = str(functional_nature(planet, r.chart))
    except Exception:  # noqa: BLE001
        func = ""
    return ParticipantFacts(planet=planet, house=p.rasi_house,
                            sign=int(p.lon % 360.0 // 30.0) + 1, dignity=dig,
                            effective_dignity=eff,
                            rupas=round(rupas, 2) if rupas is not None else None,
                            strong=strong,
                            placement=placement_tag(p.rasi_house),
                            functional=func)


def build_yoga_deep_reads(r: "DetailedReport", graph: JudgmentGraph
                          ) -> tuple[YogaDeepRead, ...]:
    """One deep-read per FIRED yoga, comparison-ranked by mean participant rupas.

    Participants come from the semantic resolver `synthesis_rules._yoga_planets` (the
    planets that actually CAUSE the yoga on this chart — the same resolver the
    Yoga×Dasha timing section uses); the syntactic `participants` scan is only a
    last-resort fallback. A yoga with resolvable participants always ranks above one
    without — an unresolvable yoga is a disclosed coverage gap, not a weak yoga.
    """
    from app.raman_saab.doctrine.synthesis_rules import _yoga_planets
    from app.raman_saab.doctrine.yogas import YOGAS
    from app.raman_saab.render import _jd_to_date

    by_id = {y.id: y for y in YOGAS}
    rows: list[dict] = []
    for fy in r.yogas:
        rec = by_id.get(fy.id)
        if rec is None:
            continue
        cite = f"{fy.source.work}:{fy.source.line}"
        quote = passage(cite, context=3)
        qtext = (quote or {}).get("text", "").replace("\n", " ").strip()
        if not qtext:
            # Honest absence — never an empty string rendered as a quotation.
            qtext = (f"Definition at {cite} - source corpus not mounted on this "
                     f"machine; paraphrase (from the engine's yoga record): {fy.effect}")
        names = _yoga_planets(r.chart, fy) or participants(rec.condition)
        parts = tuple(f for p in names
                      if (f := _participant_facts(p, r)) is not None)
        mean_rupas = (sum(f.rupas for f in parts if f.rupas is not None)
                      / max(1, sum(1 for f in parts if f.rupas is not None))
                      if any(f.rupas is not None for f in parts) else None)
        cancels = [f"{f.planet}: debilitation cancelled (neecha bhanga) — effective "
                   f"dignity {f.effective_dignity}"
                   for f in parts if f.dignity != f.effective_dignity]
        cancel_note = "; ".join(cancels) if cancels else _CANCEL_NOT_GRADED
        mods: list[str] = []
        part_names = {f.planet for f in parts}
        for e in graph.edges:
            if (e.relation == "aspects" and e.dst.startswith("house:")
                    and e.src.startswith("planet:")):
                src = e.src.split(":", 1)[1]
                if src not in part_names and any(
                        int(e.dst.split(":", 1)[1]) == f.house for f in parts):
                    if src not in mods:
                        mods.append(src)
        periods = tuple(
            f"{t.planet} {t.role}: {_jd_to_date(t.period_start_jd)} to "
            f"{_jd_to_date(t.period_end_jd)} (delivers {_quality_prose(t.quality)})"
            for t in r.yoga_timing if t.yoga_id == fy.id)
        nh = next((v for k, v in NH_EXAMPLES.items() if k.lower() in fy.name.lower()),
                  ())
        if not parts:
            strength = ("participants could not be resolved for this yoga's pattern "
                        "(a whole-chart or multi-arm rule with no single causer) — no "
                        "Shadbala mean is claimed; Raman assigns no percentage and none "
                        "is invented")
        else:
            strength = ("participants' Shadbala mean "
                        + (f"{mean_rupas:.2f} rupas" if mean_rupas is not None
                           else "unavailable (no Shadbala on this chart)")
                        + " — measured values; Raman assigns no percentage and none is "
                          "invented")
        rows.append(dict(fy=fy, rec=rec, cite=cite, qtext=qtext, parts=parts,
                         mean=mean_rupas if mean_rupas is not None else -1.0,
                         cancel=cancel_note, mods=tuple(mods), periods=periods, nh=nh,
                         strength=strength, syn_r1=_syn_r1_line(parts)))
    # Resolvable participants always outrank unresolvable ones; within each group,
    # higher mean rupas first (the -1.0 sentinel never sinks a RESOLVED yoga).
    rows.sort(key=lambda d: (0 if d["parts"] else 1, -d["mean"]))
    out: list[YogaDeepRead] = []
    for rank, d in enumerate(rows, 1):
        fy, rec = d["fy"], d["rec"]
        out.append(YogaDeepRead(
            id=fy.id, name=fy.name, kind=str(fy.kind), effect=fy.effect, cite=d["cite"],
            definition_quote=d["qtext"], computation=describe(rec.condition),
            participants=d["parts"], strength_note=d["strength"],
            cancellation_note=d["cancel"], modifiers=d["mods"], periods=d["periods"],
            nh_examples=d["nh"], comparison_rank=rank, syn_r1_line=d["syn_r1"]))
    return tuple(out)
