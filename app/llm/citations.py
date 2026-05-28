"""Citation gathering for chart interpretations.

Given a chart payload and an interpretation mode/section, queries the
knowledge-library RAG index for the top-N most relevant doctrine passages
and returns them as ``Citation`` objects. The interpreter attaches these to
its ``Interpretation`` result so a UI can show grounding evidence next to
the LLM narrative.

Query construction is **chart-aware**: a `mahadasha` interpretation gets a
query mentioning the actual MD lord ("Mercury mahadasha results"), not a
generic "mahadasha" stub. This means citations are tied to the specific
chart, not to the section name in the abstract.

Failure modes are intentionally silent: any error from the RAG service
(missing index, model load failure, runtime exception) is logged and
returns an empty citation tuple. The chart interpretation MUST succeed even
when citations are unavailable — that's the whole point of decoupling
interpretation from grounding.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.medini.services.knowledge_search import (
    KnowledgeSearchService,
    SearchResult,
    get_default_service,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Citation:
    """One supporting passage attached to an interpretation.

    Lighter than ``SearchResult`` — drops fields the UI doesn't display
    (artefact_id, n_tokens) and keeps the snippet shorter (~300 chars vs
    400) since citations sit alongside narrative text and the page must
    stay scannable.
    """
    source: str
    title: str
    snippet: str
    source_url: str | None
    local_path: str | None
    score: float


def _result_to_citation(r: SearchResult, snippet_chars: int = 300) -> Citation:
    """Trim a SearchResult into a UI-friendly Citation."""
    snippet = r.snippet
    if len(snippet) > snippet_chars:
        snippet = snippet[:snippet_chars].rstrip() + "..."
    return Citation(
        source=r.source,
        title=r.title,
        snippet=snippet,
        source_url=r.source_url,
        local_path=r.local_path,
        score=r.score,
    )


# --------------------------------------------------------------------------- #
# Query construction: chart-aware queries per section                          #
# --------------------------------------------------------------------------- #

def _summary_query(chart: dict[str, Any]) -> tuple[str, str | None]:
    """Generic chart-summary query: anchor on Ascendant + current MD lord.

    Returns (query, topic_filter or None). For a Virgo asc with Mercury MD
    we get "Virgo ascendant Mercury mahadasha effects" which surfaces both
    Lagna chapters and dasha-result chapters — good general grounding.
    """
    asc = chart.get("ascendant") or {}
    md = chart.get("current_mahadasha") or {}
    asc_sign = asc.get("sign_name") or ""
    md_lord = md.get("mahadasha_lord") or ""
    parts = []
    if asc_sign:
        parts.append(f"{asc_sign} ascendant lagna")
    if md_lord:
        parts.append(f"{md_lord} mahadasha effects")
    if not parts:
        return ("Vedic astrology chart interpretation", None)
    return (" ".join(parts), None)


def _section_query(chart: dict[str, Any], section: str) -> tuple[str, str | None]:
    """Build a chart-aware query for a section drill-down.

    Returns (query, topic_filter or None). Topic filters narrow the search
    to the relevant taxonomy branch so e.g. `yogas` doesn't return dasha
    chapters even if their cosine score happens to be high.
    """
    asc = chart.get("ascendant") or {}
    md = chart.get("current_mahadasha") or {}
    asc_sign = (asc.get("sign_name") or "").strip()
    md_lord = (md.get("mahadasha_lord") or "").strip()

    if section == "ascendant":
        q = f"{asc_sign} ascendant lagna characteristics personality" if asc_sign \
            else "ascendant lagna effects"
        return (q, "primitives.houses")

    if section == "mahadasha":
        q = f"{md_lord} mahadasha results effects" if md_lord \
            else "mahadasha vimshottari results"
        return (q, "dasha.vimshottari")

    if section == "yogas":
        yogas = chart.get("yogas") or []
        names = " ".join(y.get("name", "") for y in yogas[:5])
        q = f"{names} yoga effects" if names \
            else "raja yoga dhana yoga panchamahapurusha effects"
        return (q, None)  # yogas span multiple topic leaves; don't over-filter

    if section == "panchanga":
        return ("tithi vara yoga karana panchanga muhurta", "primitives.panchanga")

    if section == "planetary":
        # Pick the strongest contextual planet — MD lord if present, else Sun
        focus = md_lord or "Sun"
        return (
            f"{focus} planet effects houses occupation aspects",
            "primitives.planets",
        )

    if section == "ashtakavarga":
        return ("ashtakavarga bhinna sarva bindus", "techniques.ashtakavarga")

    # Unknown section: fall back to a generic query so the route still gets
    # something useful to cite rather than nothing.
    return (f"{section} vedic astrology", None)


# --------------------------------------------------------------------------- #
# Public entry                                                                 #
# --------------------------------------------------------------------------- #

def gather_citations(
    chart: dict[str, Any],
    *,
    mode: str,
    section: str | None,
    top: int = 3,
    service: KnowledgeSearchService | None = None,
) -> tuple[Citation, ...]:
    """Return top-N doctrine passages relevant to this interpretation.

    Never raises — any failure (index missing, model load error, etc.) is
    logged and returns ``()`` so the caller doesn't have to wrap this in a
    try-block of its own. Pass an explicit ``service`` in tests to avoid
    touching the process-wide singleton.
    """
    if service is None:
        service = get_default_service()

    if mode == "summary":
        query, topic = _summary_query(chart)
    elif mode == "section" and section:
        query, topic = _section_query(chart, section)
    else:
        # mode == 'section' with no section name is a programmer error
        # upstream; degrade silently.
        logger.warning("gather_citations called with mode=%r section=%r",
                       mode, section)
        return ()

    try:
        results = service.search(
            query, mode="hybrid", topic=topic, top=top, min_tokens=50,
        )
    except Exception as exc:  # noqa: BLE001 - intentional swallow at boundary
        # Index unavailable or any runtime issue: chart interpretation must
        # still work. Log + return empty so the route's response body keeps
        # the narrative even if grounding is broken.
        logger.warning("citation gather failed (mode=%s section=%s): %s",
                       mode, section, exc)
        return ()

    return tuple(_result_to_citation(r) for r in results)
