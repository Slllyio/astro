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
  - the CROSS-category sequence (governing factor -> foundation -> convergence -> current
    period -> insights -> tension -> distinctive) is a fixed editorial template in
    `build_insight_digest` below — a deterministic choice, not a number the engine emitted,
    and not the model's. The head of the sequence is Raman's own opening order (Wave-2,
    2026-08-17): name the ruler of the nativity first (HTJAH-I:16001-16002), ground on the
    longevity foundation next, then weigh the bhavas.
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
_SEC_RULER = "Ruler of the nativity"
_SEC_LONGEVITY = "Longevity"
_SEC_ARISHTA = "Arishta & Bhanga"

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
    kind: str                      # governing_factor | foundation | dominant_theme | convergence
                                   #   | tension | distinctive | timing
    title: str
    detail: str
    lean: str                      # "favourable" | "adverse" | "mixed" | "neutral"
    houses: tuple[int, ...]        # bhavas this item concerns (for click-to-highlight)
    sections: tuple[str, ...]      # report sections it bridges (for click-to-jump)
    cites: tuple[str, ...]         # WORK:line tokens already attached to the findings (may be empty)
    priority: int                  # 0 = most important; the engine's rank, not the LLM's


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


def _bhava_bala_clause(report: "DetailedReport", house: int) -> str:
    """The house's Bhava-Bala rank as one clause — Raman states HOW strong relative to the
    rest (ranking only, no cutoff: GBB-9:332, the same re-read the House strength
    cross-check renders). Magnitude, never direction; "" when the rank is unavailable."""
    hs = next((row for row in report.house_strength if row.house == house), None)
    if hs is None or hs.bhava_bala_rank is None:
        return ""
    return (f" By Bhava Bala this house ranks {hs.bhava_bala_rank} of 12 — magnitude, "
            f"not direction (GBB-9:332).")


def _governing_item(report: "DetailedReport", priority: int) -> DigestItem | None:
    """Rank-0 (Wave-2, 2026-08-17): the governing factor — Raman's own opening move, "in
    order to obtain a first impression we must first of all consider the ruler of the
    nativity" (HTJAH-I:16001-16002, the citation the Ruler card already carries). A pure
    re-read of the already-built `report.ruler`."""
    ru = report.ruler
    if not ru.lagna_lord:
        return None
    if ru.strongest is None:
        detail = (f"{ru.lagna_lord} rules the nativity as Lagna lord; no Shadbala is "
                  f"available on this chart, so the strongest planet is not determined — "
                  f"nothing is guessed in its place.")
        lean = "neutral"
    elif ru.coincide:
        detail = (f"{ru.lagna_lord} rules the nativity AND is the strongest planet by "
                  f"Shadbala ({ru.strongest_rupas:.1f} rupas) — the two governing factors "
                  f"coincide: \"the foundation is quite sound\" (HTJAH-I:3880-3882).")
        lean = "favourable"
    else:
        detail = (f"{ru.lagna_lord} rules the nativity as Lagna lord, while the strongest "
                  f"planet by Shadbala is {ru.strongest} ({ru.strongest_rupas:.1f} rupas) "
                  f"— two distinct first-impression factors, read together in the Ruler "
                  f"card; they do not coincide here.")
        lean = "neutral"
    return DigestItem(
        kind="governing_factor",
        title=f"The governing factor: {ru.lagna_lord} rules the nativity",
        detail=detail, lean=lean, houses=(1,),
        sections=(_SEC_RULER,),
        cites=("HTJAH-I:16001-16002",) + (("HTJAH-I:3880-3882",) if ru.coincide else ()),
        priority=priority,
    )


def _foundation_item(report: "DetailedReport", priority: int) -> DigestItem | None:
    """Rank-1 (Wave-2, 2026-08-17): the foundation — the longevity band and the
    Balarishta/bhanga status, the classical precondition to everything else the digest
    ranks. Pure re-read of `longevity_class` + `balarishta` + the already-fired
    "Strength lifts the longevity band" insight (HTJAH-I:11703)."""
    band = report.longevity_class
    if not band:
        return None
    bal = report.balarishta
    if bal is None:
        bal_bit = "no Balarishta screen is available on this chart"
    elif bal.applies and not bal.cancelled:
        bal_bit = "the Balarishta screen applies and is not cancelled"
    elif bal.cancelled:
        bal_bit = "the Balarishta screen is cancelled by the classical antidotes"
    else:
        bal_bit = "no Balarishta combination applies"
    lift = next((ins for ins in report.insights
                 if ins.rule.id == "SYN_R10_STRENGTH_OVERRIDES_ARISHTA"), None)
    lift_bit = (f" Strength lifts the band on this chart: {lift.detail.rstrip('.')}."
                if lift is not None else "")
    lean = {"purna": "favourable", "alpa": "adverse"}.get(band, "neutral")
    cites = (((f"{lift.rule.source.work}:{lift.rule.source.line}",)
              if lift is not None and lift.rule.source is not None else ()))
    return DigestItem(
        kind="foundation",
        title=f"The foundation: longevity reads at the {band} band",
        detail=(f"The classical order ascertains the span before judging the bhavas; "
                f"this chart's Ayurdaya band is {band}, and {bal_bit}.{lift_bit} A band "
                f"of the method, never a date."),
        lean=lean, houses=(8,),
        sections=(_SEC_LONGEVITY, _SEC_ARISHTA),
        cites=cites, priority=priority,
    )


def _convergence_item(report: "DetailedReport", house: int, favourable: bool,
                      priority: int) -> DigestItem | None:
    """The most-corroborated house (its own witnesses most agree with its headline) + the yogas
    that bear on it — the "N independent testimonies converge here" finding."""
    ht = _testimonies_for(report, house)
    if ht is None:
        return None
    agree = ht.favourable if favourable else ht.adverse
    yogas = _yogas_on_house(report, house)
    bb_clause = _bhava_bala_clause(report, house)
    cites = [_LEDGER_CITE] + [_yoga_cite(y) for y in yogas] + (
        ["GBB-9:332"] if bb_clause else [])
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
               f"same way ({ht.status}, {ht.preponderance}).{yoga_clause}{bb_clause}",
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
    bb_clause = _bhava_bala_clause(report, house)
    return DigestItem(
        kind="tension",
        title=f"House {house} ({_house_label(house)}) is the most contested area",
        detail=f"Its headline reads {ht.verdict}, yet its own witnesses are divided "
               f"({ht.favourable} favourable, {ht.adverse} adverse, {ht.neutral} neutral — "
               f"{ht.status}). The engine records the tension rather than resolving it."
               f"{bb_clause}",
        lean="mixed",
        houses=(house,),
        sections=(_SEC_PREPONDERANCE, _SEC_HOUSES),
        cites=(_LEDGER_CITE,) + (("GBB-9:332",) if bb_clause else ()),
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
    # Wave-2 (2026-08-17, coherence fix): the running SUB-period's four-tier grade sits
    # beside the Ishta/Kashta lean so the two axes cannot read as a self-contradiction —
    # the same graded_buckets re-read the Nichod's "Running now" line already makes
    # (HTJAH-I:1592-1596, the locked uniform four-tier scheme).
    tier_clause = ""
    tier_cites: tuple[str, ...] = ()
    cur_tp = next((tp for tp in report.timeline.periods
                   if tp.period.start_jd <= report.ref_jd < tp.period.end_jd), None)
    if cur_tp is not None:
        from app.raman_saab.detailed_report import graded_buckets
        associated, _buckets = graded_buckets(cur_tp, report.chart)
        tier = "par excellence" if associated else "ordinary"
        assoc_word = "associated" if associated else "not associated"
        ad = cur_tp.period.antar or cur_tp.period.maha
        tier_clause = (f" The running {cur.maha}/{ad} sub-period grades {tier} by Raman's "
                       f"four-tier scheme (lords {assoc_word}); that grade and the lean "
                       f"above are different axes, not a contradiction.")
        tier_cites = ("HTJAH-I:1592-1596",)
    return DigestItem(
        kind="timing",
        title=f"You are currently in the {cur.maha} Mahadasha",
        detail=(first or f"The running {cur.maha} Mahadasha shapes the present chapter.")
               + tier_clause,
        lean=lean_word,
        houses=tuple(h for h, _t, _v in cur.houses_lit),
        sections=(_SEC_TIMELINE, _SEC_CHAPTERS),
        cites=tier_cites,
        priority=priority,
    )


# ─── the assembler ──────────────────────────────────────────────────────────────

def build_insight_digest(report: "DetailedReport",
                         *, max_insights: int = 3, max_distinctive: int = 3) -> InsightDigest:
    """Rank the chart's most important findings from already-computed structures. Pure re-read;
    no verdict is recomputed. Items are returned most-important-first, with `priority` = position."""
    items: list[DigestItem] = []
    pp = report.preponderance

    # 0. the governing factor — Raman opens by naming the ruler of the nativity
    # (HTJAH-I:16001-16002); Wave-2 2026-08-17, inserted BEFORE every other item.
    gov = _governing_item(report, priority=len(items))
    if gov is not None:
        items.append(gov)

    # 0b. the foundation — longevity band + Balarishta status, the classical
    # precondition to everything ranked below (HTJAH-I:11703 when the lift fired).
    fnd = _foundation_item(report, priority=len(items))
    if fnd is not None:
        items.append(fnd)

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

    return InsightDigest(headline=report.info.sentence, items=tuple(items))
