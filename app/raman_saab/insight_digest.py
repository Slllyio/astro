"""The Insight Digest — the engine's own ranked "what matters most" for a chart.

The detailed report is faithful but SILOED: 21 sections, each judged on its own axis. A reader
cannot see that (say) three independent testimonies converge on the same house, or which of the
chart's many readings actually distinguishes it. This module assembles that view — but it is a
pure RE-READ and TRANSPOSITION of fields the engine has already computed; it recomputes no
verdict, so it can never move the golden ratchet.

Crucially, **the ranking is deterministic engine code, not an LLM's.** Deciding what matters most
is itself an astrological judgment, so it must never be delegated to the model. Two things set the
order, both in Python here:
  - the WITHIN-category order is the engine's own already-computed ranking — the
    `PreponderanceReading.most_corroborated_favourable / _afflicted / most_contested` picks, the
    band-precedence order of `insights` (raman > classical > av), and the rarity-sorted
    `distinctive` entries (furthest from the population midpoint);
  - the CROSS-category sequence (convergence -> current period -> insights -> tension ->
    distinctive) is a fixed editorial template in `build_insight_digest` below — a deterministic
    choice, not a number the engine emitted, and not the model's.
The grounded LLM layer (`report_explainer`) then only NARRATES this pre-ranked digest into plain
language; it never re-orders or re-weighs it.

Each item carries the citations already attached to its underlying findings (yoga citations, the
testimony-ledger line), so the frontend can click-to-source and the LLM can anchor. Population
readings (`distinctive`) carry no Raman citation by design — they are information content
(EMPIRICAL_ASTRODATABANK provenance), never doctrine.

Usage:
    from app.raman_saab.insight_digest import build_insight_digest
    digest = build_insight_digest(report)      # report: DetailedReport
    for item in digest.items:
        print(item.priority, item.kind, item.title, item.cites)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.raman_saab.doctrine.synthesis_rules import yoga_house_bearings

if TYPE_CHECKING:                                   # runtime import would be circular
    from app.raman_saab.detailed_report import DetailedReport

#: Raman's "judgment is the summing up of the influence of planets" — the per-house testimony
#: ledger line (the same citation the explainer stamps on a house's preponderance count).
_LEDGER_CITE = "HTJAH-I:8870"

#: Frontend section headings (must match the titles `report.html` renders, so a digest item's
#: `sections` can be turned into click-to-jump links). Used for the house-derived items.
_SEC_PREPONDERANCE = "Preponderance of testimonies"
_SEC_HOUSES = "House-by-house"
_SEC_YOGAS = "Yogas"
_SEC_STANDS_OUT = "What stands out"
_SEC_INFO = "Information content of this reading"
_SEC_TIMELINE = "Life-narrative (Vimshottari)"
_SEC_CHAPTERS = "Life-chapters"

#: Plain-language label for each bhava, for readable item titles (standard significations, matching
#: the report's own usage — not a re-judgment).
_HOUSE_LABEL: dict[int, str] = {
    1: "self & body", 2: "wealth & speech", 3: "siblings & courage", 4: "home & mother",
    5: "children & intellect", 6: "health & adversaries", 7: "marriage & partnership",
    8: "longevity & upheaval", 9: "fortune & father", 10: "career & status",
    11: "gains & fulfilment", 12: "loss & liberation",
}


@dataclass(frozen=True)
class DigestItem:
    """One ranked finding in the digest. Every field is a restatement of already-computed engine
    output — `lean` is the direction the underlying finding already carries, never a new verdict."""
    kind: str                      # first_impression | dominant_theme | convergence |
                                   # tension | distinctive | timing
    title: str
    detail: str
    lean: str                      # "favourable" | "adverse" | "mixed" | "neutral"
    houses: tuple[int, ...]        # bhavas this item concerns (for click-to-highlight)
    sections: tuple[str, ...]      # report sections it bridges (for click-to-jump)
    cites: tuple[str, ...]         # WORK:line tokens already attached to the findings (may be empty)
    priority: int                  # 0 = most important; the engine's rank, not the LLM's
    #: the same finding said about the PERSON rather than the chart (v35). Empty when there is
    #: nothing plain to say. ADDS to `detail`, never replaces it — the technical text stays.
    plain: str = ""


@dataclass(frozen=True)
class InsightDigest:
    """The whole-chart ranked digest. `headline` is the honesty frame (information content of the
    reading); `items` are the ranked findings, most important first."""
    headline: str
    items: tuple[DigestItem, ...]


# ─── lean inference (read the direction the finding already carries) ─────────────

def _lean_of(verdict: str) -> str:
    """Map an already-decided verdict string to a coarse direction — a re-READING of the engine's
    own word, not a re-judgment. Adverse keywords are tested BEFORE favourable ones so that a
    compound like "strongly afflicted" (were the vocabulary ever to drift to include degree words)
    can never be mislabelled favourable by matching "strong" first — the safe failure is toward
    caution, never a silent direction reversal."""
    v = (verdict or "").lower()
    if any(w in v for w in ("mixed", "contest", "split", "even")):
        return "mixed"
    if any(w in v for w in ("afflict", "advers", "malefic", "weak", "bad", "poor", "danger")):
        return "adverse"
    if any(w in v for w in ("favour", "favor", "good", "benefic", "strong", "auspicious")):
        return "favourable"
    return "neutral"


# ─── house-level helpers ────────────────────────────────────────────────────────

def _house_label(house: int) -> str:
    return _HOUSE_LABEL.get(house, f"house {house}")


def _testimonies_for(report: "DetailedReport", house: int):
    return next((h for h in report.preponderance.houses if h.house == house), None)


def _yogas_on_house(report: "DetailedReport", house: int):
    """The fired yogas whose constituent planets bear on `house` (own/occupy/aspect) — reusing the
    locked `yoga_house_bearings` operationalization. Whole-chart pattern yogas (no constituent
    identity) return None and are skipped."""
    hits = []
    for y in report.yogas:
        bearings = yoga_house_bearings(report.chart, y)
        if bearings and house in bearings:
            hits.append(y)
    return hits


def _yoga_cite(y) -> str:
    return f"{y.source.work}:{y.source.line}"


def _convergence_item(report: "DetailedReport", house: int, favourable: bool,
                      priority: int) -> DigestItem | None:
    """The most-corroborated house (its own witnesses most agree with its headline) + the yogas
    that bear on it — the "N independent testimonies converge here" finding."""
    ht = _testimonies_for(report, house)
    if ht is None:
        return None
    agree = ht.favourable if favourable else ht.adverse
    yogas = _yogas_on_house(report, house)
    cites = [_LEDGER_CITE] + [_yoga_cite(y) for y in yogas]
    sections = [_SEC_PREPONDERANCE, _SEC_HOUSES] + ([_SEC_YOGAS] if yogas else [])
    side = "favourable" if favourable else "afflicted"
    yoga_clause = ""
    if yogas:
        names = ", ".join(y.name for y in yogas[:3])
        yoga_clause = f" The yoga(s) {names} also bear on this house."
    return DigestItem(
        kind="convergence",
        title=f"House {house} ({_house_label(house)}) is the most strongly corroborated "
              f"{side} area",
        detail=f"Its headline reads {ht.verdict}; {agree} of its independent witnesses lean the "
               f"same way ({ht.status}, {ht.preponderance}).{yoga_clause}",
        lean="favourable" if favourable else "adverse",
        houses=(house,),
        sections=tuple(sections),
        cites=tuple(dict.fromkeys(cites)),          # de-dup, keep order
        priority=priority,
    )


def _tension_item(report: "DetailedReport", house: int, priority: int) -> DigestItem | None:
    """The most-contested house — where the headline stands but the witnesses pull against it."""
    ht = _testimonies_for(report, house)
    if ht is None:
        return None

    # Name WHICH matter set the headline. Without it a reader meets "7 favourable, 0 adverse"
    # over a headline of "afflicted" and can only read it as broken. The rule is Raman's
    # (PREC-1: a house follows its weakest DECIDED matter, not its majority) and the engine
    # already knows the answer — the Nichod states it — the digest simply never did.
    pf = next((p for p in report.proformas if p.house == house), None)
    driver = ""
    if pf is not None and pf.significations:
        odd = [s for s in pf.significations if str(s.verdict) == str(pf.rollup)]
        rest = [s for s in pf.significations if str(s.verdict) != str(pf.rollup)]
        if odd and rest and len(odd) < len(rest):
            names = ", ".join(s.signification.replace("_", " ") for s in odd)
            driver = (f" The headline follows {names} — the one matter reading "
                      f"{pf.rollup} — while the other {len(rest)} read otherwise; a house "
                      f"takes its weakest decided matter, not its majority.")

    return DigestItem(
        kind="tension",
        title=f"House {house} ({_house_label(house)}) is the most contested area",
        detail=f"Its headline reads {ht.verdict}, yet its own witnesses are divided "
               f"({ht.favourable} favourable, {ht.adverse} adverse, {ht.neutral} neutral — "
               f"{ht.status}).{driver} The engine records the tension rather than resolving it.",
        lean="mixed",
        houses=(house,),
        sections=(_SEC_PREPONDERANCE, _SEC_HOUSES),
        cites=(_LEDGER_CITE,),
        priority=priority,
    )


def _insight_item(fired, priority: int) -> DigestItem:
    """A fired cross-feature synthesis rule — an insight that CONNECTS report sections."""
    rule = fired.rule
    cite = (f"{rule.source.work}:{rule.source.line}",) if rule.source is not None else ()
    return DigestItem(
        kind="dominant_theme",
        title=rule.name,
        detail=f"{rule.simple_meaning} In this chart: {fired.detail}",
        lean="neutral",                              # insights are connective, not directional
        houses=(),
        sections=tuple(rule.links),
        cites=cite,
        priority=priority,
    )


def _distinctive_item(house: int, entry, priority: int) -> DigestItem:
    """A reading that most distinguishes this chart from the population — pure information content,
    no Raman citation (EMPIRICAL provenance)."""
    share = (f"only {entry.band_share:.0%} of charts share this exact reading"
             if entry.band_share is not None else "an uncommon reading")
    inv = (" This channel is one the project's validation program proved runs BACKWARDS in real "
           "cases — treat it with maximal skepticism." if entry.inverted_warning else "")
    return DigestItem(
        kind="distinctive",
        title=f"House {house} — {entry.signification}: {entry.verdict} ({entry.degree})",
        detail=f"{share} ({entry.rarity}).{inv} This is a statement about the reading's information "
               f"content, not a prediction about a life.",
        lean=_lean_of(entry.verdict),
        houses=(house,),
        sections=(_SEC_STANDS_OUT, _SEC_INFO),
        cites=(),
        priority=priority,
    )


def _timing_item(report: "DetailedReport", priority: int) -> DigestItem | None:
    """The Mahadasha the person is currently living — the woven Life-chapter for the running run."""
    cur = next((c for c in report.life_chapters.chapters if c.is_current), None)
    if cur is None:
        return None
    lean = (cur.lean or "").lower()
    lean_word = ("favourable" if "ishta" in lean or "good" in lean
                 else "adverse" if "kashta" in lean or "hard" in lean
                 else "neutral")
    # a compact slice of the chapter's own narrative — first sentence, the engine's words
    first = cur.narrative.split(". ", 1)[0].strip()
    if first and not first.endswith("."):
        first += "."
    return DigestItem(
        kind="timing",
        title=f"You are currently in the {cur.maha} Mahadasha",
        detail=first or f"The running {cur.maha} Mahadasha shapes the present chapter.",
        lean=lean_word,
        houses=tuple(h for h, _t, _v in cur.houses_lit),
        sections=(_SEC_TIMELINE, _SEC_CHAPTERS),
        cites=(),
        priority=priority,
    )


# ─── the assembler ──────────────────────────────────────────────────────────────

def _ruler_item(report: "DetailedReport", priority: int) -> DigestItem | None:
    """The first impression — the Lagna and its lord.

    Added after measuring: the digest named houses 4, 5, 8, 10, 12 for one chart and 2, 3, 4, 9
    for another, and **the Lagna in neither**. Raman opens every reading on it ("the first
    impression", HTJAH-I:16001-16002), and it is the house he emphasises most across his own
    worked readings, so a "what matters most" that never mentions it is missing his first move.
    """
    ru = getattr(report, "ruler", None)
    lord = getattr(ru, "lagna_lord", None)
    if ru is None or not lord:
        return None
    strongest = getattr(ru, "strongest", None)
    house = getattr(ru, "lagna_lord_house", None)
    detail = f"{lord} rules the ascendant"
    if house:
        detail += f" and sits in house {house}"
    if strongest and strongest != lord:
        detail += f"; {strongest} carries the greatest strength in the chart"
    elif strongest:
        detail += " and also carries the greatest strength"
    temperament = getattr(ru, "temperament", None)
    if temperament:
        detail += f". {str(temperament).rstrip('.')}."
    return DigestItem(
        kind="first_impression",
        title=f"The chart is ruled by {lord}",
        detail=detail + " Raman reads the rising sign and its lord first, before any other "
                        "matter is judged.",
        lean="neutral",
        houses=(1,),
        sections=("ruler", "chart_signature"),
        cites=("HTJAH-I:16001-16002",),
        priority=priority,
    )


def build_insight_digest(report: "DetailedReport",
                         *, max_insights: int = 3, max_distinctive: int = 3) -> InsightDigest:
    """Rank the chart's most important findings from already-computed structures. Pure re-read;
    no verdict is recomputed. Items are returned most-important-first, with `priority` = position."""
    items: list[DigestItem] = []
    pp = report.preponderance

    # 0. the first impression — the Lagna and its lord (HTJAH-I:16001). Without this the digest
    #    never mentions the ascendant at all, which was measurably the case before it was added.
    ruler = _ruler_item(report, priority=len(items))
    if ruler is not None:
        items.append(ruler)

    # 1-2. the strongest agreements (favourable then afflicted convergence)
    if pp.most_corroborated_favourable is not None:
        it = _convergence_item(report, pp.most_corroborated_favourable, favourable=True,
                               priority=len(items))
        if it is not None:
            items.append(it)
    if pp.most_corroborated_afflicted is not None:
        it = _convergence_item(report, pp.most_corroborated_afflicted, favourable=False,
                               priority=len(items))
        if it is not None:
            items.append(it)

    # 3. the chapter the person is living now
    timing = _timing_item(report, priority=len(items))
    if timing is not None:
        items.append(timing)

    # 4. the top cross-feature insights (already band-sorted raman > classical > av)
    for fired in report.insights[:max_insights]:
        items.append(_insight_item(fired, priority=len(items)))

    # 5. the sharpest tension (a house whose witnesses pull against its headline)
    if pp.most_contested is not None:
        it = _tension_item(report, pp.most_contested, priority=len(items))
        if it is not None:
            items.append(it)

    # 6. what most distinguishes this chart from the population (rare-first)
    for house, entry in report.distinctive[:max_distinctive]:
        items.append(_distinctive_item(house, entry, priority=len(items)))

    return InsightDigest(headline=report.info.sentence,
                         items=_ordered_by_salience(report, items))


def _ordered_by_salience(report: "DetailedReport",
                         items: list[DigestItem]) -> tuple[DigestItem, ...]:
    """Re-order the SAME items by how much each one's houses deserve attention.

    The slots above are the order the sections were BUILT in, and measuring it exposed what
    that costs: scored against the houses Raman actually emphasised in his own worked readings,
    the built order ranked WORSE than simply naming the Lagna, then the 10th, then the 7th
    (p@1 0.286 vs 0.643 — `docs/raman_saab/SALIENCE_BASELINE.md`). The reason is structural.
    Slots 1-2 lead with CORROBORATION, which is population-typical by construction — the median
    chart carries 19 afflicted and 31 favourable significations — and "what most distinguishes
    this chart" is built last, so the one item carrying chart-specific information arrives last.

    Re-ordering by the doctrinal salience of each item's houses beat the built order on
    held-out charts: p@3 +0.143 [+0.024, +0.238], r@3 +0.262 [+0.083, +0.464],
    MRR +0.302 [+0.083, +0.503].

    REPORT COMPLETENESS: this REORDERS, it never drops. Every item built above is returned.
    An item with no house (the running-period note) is neutral-scored so it neither floats to
    the top nor sinks — it is orientation, not a finding.
    """
    from dataclasses import replace

    from app.raman_saab.salience import house_salience

    try:
        scored = house_salience(report)
    except Exception:                                              # noqa: BLE001
        return tuple(items)                                        # never lose the digest

    neutral = (sum(s.score for s in scored.values()) / len(scored)) if scored else 0.0

    # An item naming most of the chart selects nothing — the running-period note lists every
    # house its dasha touches, and scoring it by its best house floated it straight to the top
    # on the strength of the Lagna it happened to include. Same abundance fallacy the whole
    # programme keeps meeting: what is true of every house distinguishes none of them.
    _UNSELECTIVE = 6

    def key(entry: tuple[int, DigestItem]) -> tuple[float, int]:
        idx, item = entry
        if not item.houses or len(item.houses) > _UNSELECTIVE:
            return (-neutral, idx)
        best = max((scored[h].score for h in item.houses if h in scored), default=neutral)
        return (-best, idx)                                        # idx keeps the sort stable

    # Order ACROSS kinds by salience, but never WITHIN one. Two invariants depend on the
    # within-kind order and both are real: distinctive items must stay in the engine's own
    # rare-first ranking (the digest re-reads that ranking, it does not re-derive it — PREC-10),
    # and the dominant-theme items must stay in band precedence, raman > classical > av, which
    # is doctrine. Clamping each item's score to at most its predecessor OF THE SAME KIND makes
    # every kind's sequence non-increasing, so a stable sort cannot reshuffle it.
    scores = [(-key((i, it))[0], it) for i, it in enumerate(items)]
    last_of_kind: dict[str, float] = {}
    clamped: list[float] = []
    for value, item in scores:
        prev = last_of_kind.get(item.kind)
        value = value if prev is None else min(value, prev)
        last_of_kind[item.kind] = value
        clamped.append(value)

    ordered = [it for _s, _i, it in
               sorted(((-clamped[i], i, it) for i, it in enumerate(items)))]

    # v35 — give each finding its person-facing voice. Failure here must cost the reader the
    # sentence, never the finding.
    def _plain(it: DigestItem) -> str:
        try:
            from app.raman_saab.plainspoken import plain_for_item
            return plain_for_item(report, it)
        except Exception:                                          # noqa: BLE001
            return ""

    return tuple(replace(it, priority=i, plain=_plain(it))
                 for i, it in enumerate(ordered))
