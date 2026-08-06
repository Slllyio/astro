"""The reading arc (v33) — the 53 contracted sections grouped into seven movements.

For 32 versions the report's section order was governed by an append-only contract, so every
new section landed where the CONTRACT allowed rather than where it READS best: the life
matters a person actually asks about (career, wealth, marriage, children) sat after the
Ashtakavarga tables, and four separate summaries bookended the document instead of framing
it. The order was a build log.

This module is the single source of truth for the reading sequence. ``SECTION_CONTRACT`` and
``HTML_SECTION_ORDER`` are asserted equal to :func:`flattened_order`, so the arc lives here
and the renderers merely walk it. The section SET remains frozen and append-only — nothing is
ever removed or hidden (REPORT COMPLETENESS); only the sequence is a design decision.

The connective passages are composed deterministically from :mod:`raman_style`, which encodes
Raman's own compositional habits (cause before result, evidence before verdict, close each
unit). They are a pure re-read in the sense of PREC-10 — every fact quoted has already been
judged by a section on one side of the boundary or the other, and nothing here re-judges
anything. No model is called, so a passage reads the same on every run.

Usage:
    from app.raman_saab.report_movements import MOVEMENTS, flattened_order, movement_passage
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

from app.raman_saab.raman_style import because, conclusion, weighed

if TYPE_CHECKING:  # pragma: no cover — import only for the annotation, never at runtime
    from app.raman_saab.detailed_report import DetailedReport


@dataclass(frozen=True)
class Movement:
    """One movement of the reading: a roman numeral, a title, and the sections it carries."""

    numeral: str
    title: str
    section_ids: tuple[str, ...]


#: The reading arc. The ruler opens (Raman's own first-impression move, HTJAH-I:16001); the
#: honesty frame lands BEFORE any life claim rather than after it; the instrument is shown
#: before it is used; the twelve fields precede the matters they govern; the matters precede
#: the timing that qualifies them; the summing up closes with `nichod` last.
#:
#: `title`, `plain_reading` and `chart_signature` must stay adjacent, in that order: in the
#: HTML they are one `<header>` element and are emitted as a single chunk.
MOVEMENTS: Final[tuple[Movement, ...]] = (
    Movement("I", "Who this is", (
        "title", "plain_reading", "chart_signature", "now_box",
        "ruler", "planet_bios", "psych",
    )),
    Movement("II", "How to read it honestly", (
        "info_content", "interpretation_guide", "judgment_graph",
        "stands_out", "digest", "dashboard",
    )),
    Movement("III", "The instrument", (
        "chart_grids", "positions", "rect_confidence", "shadbala",
        "ashtakavarga", "divisional",
    )),
    Movement("IV", "The twelve fields", (
        "houses", "house_strength", "preponderance",
        # v34 — what governs a contested house, then how firmly each house stands. They sit
        # here because they are about the twelve fields, and after preponderance because both
        # re-read its ledger.
        "dominance", "restraint",
        "yogas", "yoga_deep", "deeptadi",
    )),
    Movement("V", "The matters of life", (
        "career", "profession", "wealth", "marriage", "children",
        "health_readout", "arishta", "longevity", "maraka", "maraka_saturn",
    )),
    Movement("VI", "In time", (
        "timeline", "yoga_timing", "ishta_kashta", "md_condition", "av_dasha_seat",
        "dasa_kakshya", "life_chapters", "decades", "gochara", "dasha_transit",
    )),
    Movement("VII", "The summing up", (
        "karakamsa", "soul", "karmic", "pitru",
        # v34 — which of Raman's own charts this one recalls: a stepping-back recognition,
        # so it belongs with the summing up rather than among the house readings.
        "analogy",
        "synthesis", "life_synthesis", "glossary", "nichod",
    )),
)


def flattened_order() -> tuple[str, ...]:
    """Every section id in reading order — the sequence both renderers walk."""
    return tuple(sid for mv in MOVEMENTS for sid in mv.section_ids)


def movement_of(section_id: str) -> Optional[Movement]:
    """The movement a section belongs to, or None if it is not placed in the arc."""
    return next((mv for mv in MOVEMENTS if section_id in mv.section_ids), None)


def movement_index(section_id: str) -> Optional[int]:
    """Index of the movement carrying ``section_id`` — for renderers emitting headers."""
    return next((i for i, mv in enumerate(MOVEMENTS) if section_id in mv.section_ids), None)


def _ruler_names(r: "DetailedReport") -> tuple[str, str]:
    """(lagna lord, strongest planet) — ``r.ruler`` is a dataclass, never a bare string."""
    ru = getattr(r, "ruler", None)
    lord = getattr(ru, "lagna_lord", None) or "the ascendant lord"
    strongest = getattr(ru, "strongest", None) or "the strongest planet"
    return str(lord), str(strongest)


def movement_passage(r: "DetailedReport", index: int) -> str:
    """The connective sentence that opens movement ``index``.

    Each passage names a fact the previous movement established and says what the next one
    does with it, so the document hands off rather than restarting. Every value is read
    defensively: a sparse chart falls back to a generic phrasing rather than raising, but a
    fully-populated report yields a non-empty passage at every one of the seven movements
    (pinned by test, so the fallbacks can never quietly become the norm).
    """
    if not 0 <= index < len(MOVEMENTS):
        return ""

    if index == 0:
        lord, strongest = _ruler_names(r)
        if lord == strongest:
            return because(
                f"{lord} both rules the ascendant and carries the greatest strength",
                "this opening states who the chart describes, in one voice, before any "
                "technical section qualifies it")
        return because(
            f"{lord} rules the ascendant while {strongest} carries the greatest strength",
            "this opening states who the chart describes before any technical section "
            "qualifies it")

    if index == 1:
        info = getattr(r, "info", None)
        total = getattr(info, "total", None)
        modal = getattr(info, "modal_verdict", None)
        count = getattr(info, "modal_count", None)
        if total and modal and count:
            return weighed(
                f"{total} computed significations, of which {count} read {modal}",
                "the frame for reading them is set out before the readings themselves — how "
                "much of this is particular to the chart, and how much any chart would show")
        return weighed(
            "how much of this reading is particular to the chart",
            "the frame for reading it is set out before the readings themselves")

    if index == 2:
        return because(
            "every verdict that follows rests on the placements just summarised",
            "the instrument itself is shown here in full — positions, strengths, the "
            "divisional charts, and how far the birth time may move before a pillar changes "
            "— so each later judgement can be checked against it")

    if index == 3:
        return because(
            "the instrument stands as measured",
            "the twelve houses are read in turn, each with the testimonies for and against "
            "it named rather than summarised away")

    if index == 4:
        pp = getattr(r, "preponderance", None)
        best = getattr(pp, "most_corroborated_favourable", None)
        contested = getattr(pp, "most_contested", None)
        if best and contested:
            return weighed(
                f"house {best} carrying the most corroborated favourable testimony and "
                f"house {contested} the most divided",
                "the matters a person actually asks about are taken next, each by "
                "its own dedicated reader rather than by the house rollup")
        return weighed(
            "the testimonies gathered house by house",
            "the matters a person actually asks about are taken next, each by its "
            "own dedicated reader")

    if index == 5:
        syn = getattr(r, "synthesis", None)
        md = getattr(syn, "running_md", None)
        ad = getattr(syn, "running_ad", None)
        if md and ad:
            return because(
                f"{md} is the running Mahadasha with {ad} as bhukti",
                "the same verdicts are now placed in time — the periods are a lens over "
                "readings that do not themselves change")
        return because(
            "the readings above are fixed by the chart, not by the calendar",
            "the periods that follow are a lens over them, never a revision of them")

    return conclusion(
        "what follows gathers the reading — the soul-level frame, the cross-feature "
        "synthesis and the closing Nichod — re-reading the sections above without "
        "re-judging any of them")
