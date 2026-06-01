"""Tier-3 RAG enrichment: per-finding doctrine citation gatherer.

Annotates each high-confidence ``promise`` / ``yoga`` / ``trigger`` Finding
with up to ``k`` ``Citation`` objects pulled from the doctrine knowledge
library via ``app.medini.services.knowledge_search.KnowledgeSearchService``.

The module is the ONE Tier-3 module that talks to the RAG index for
per-finding doctrine support. Two sibling modules (``consensus_scoring``,
``dispute_surfacing``) consume the citations this module produces.

Methodology:
    Type: descriptive
    Inputs to retrieval/scoring: rule_slug + structural_slots only
        (specifically ``Finding.rule + Finding.classification``)
        — NEVER ``Finding.verdict`` text.
    Explicitly NOT used: ``Finding.verdict`` free-text — banned per
        anti-confirmation-bias commitment. Surfacing passages by free-text
        verdict would let the engine ratify whatever it already said
        ("Einstein had X, so X must be true"), which is the exact
        confirmation-bias failure mode the v1 design is built to avoid.
    Thresholds & their source: eligibility floor (band in very_strong / medium / high
        AND classification in promise / yoga / trigger) is a Spec Section 14
        engineering threshold meant to cap retrieval cost — NOT fitted
        against any historical-outcome corpus.
    Famous-chart anti-contamination: biographical passages mentioning
        any of {Einstein, Gandhi, Steve Jobs, Ramana, Kalam, Obama,
        Nehru} are filtered out of the citation pool because those
        figures' charts were used in our famous-chart fixture pinning;
        retrieving biographies of them would create a circular
        confirmation pathway. Anti-contamination check is a simple
        substring scan against ``Citation.passage`` lowercased.
    Null-baseline test required: N/A — this module is a retrieval
        wrapper, not a scoring model. There is no chart-corpus fitting
        and therefore no outcome-shuffled control to apply.
    Prediction-trap declaration: "This module does NOT predict outcomes.
        It retrieves pre-existing computed findings' supporting doctrine
        passages. No fitting against any chart corpus with outcome
        labels."

Doctrine source: spec Section 14, Tier-3 methodology commitments;
    embeddings produced by ``app.medini.ml.build_rag_index``.
"""
from __future__ import annotations

import logging
from typing import Any

from app.reading.schema import Citation, Finding

logger = logging.getLogger(__name__)

# Eligibility gates — keep retrieval cost bounded, see Methodology block.
_ELIGIBLE_BANDS: frozenset[str] = frozenset({"very_strong", "medium", "high"})
_ELIGIBLE_CLASSIFICATIONS: frozenset[str] = frozenset({"promise", "yoga", "trigger"})

# Famous-chart fixture names used in our test pinning. Biographical passages
# naming these figures are filtered to prevent a circular confirmation pathway.
# Substring-matched against ``passage.lower()`` — see Methodology block above.
_FAMOUS_CHART_NAMES: frozenset[str] = frozenset(
    {
        "einstein",
        "gandhi",
        "steve jobs",
        "ramana",
        "kalam",
        "obama",
        "nehru",
    }
)

# Citation.passage is truncated to this many chars before construction so a
# very long matched passage doesn't bloat the JSON envelope.
_PASSAGE_MAX_CHARS: int = 500


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _build_query_from_rule_slot(finding: Finding) -> str:
    """Construct the retrieval query from rule + structural slot ONLY.

    The query is `{rule_name} {classification}`. The verdict text is NEVER
    incorporated — see the module's Methodology block for the
    anti-confirmation-bias rationale.

    Returns a single string suitable for sentence-transformers ``encode``.
    """
    return f"{finding.rule} {finding.classification}"


def _is_biographical_about_famous_chart(text: str) -> bool:
    """Return True iff the passage mentions a famous-chart fixture name.

    Substring-match against the lowercased passage. False-positive risk is
    accepted: the failure mode of erroneously filtering a doctrine passage
    that happens to use the surname is preferable to the failure mode of
    citing a famous-chart biography against the very chart the fixture pins.
    """
    lower = (text or "").lower()
    return any(name in lower for name in _FAMOUS_CHART_NAMES)


def _is_eligible(finding: Finding) -> bool:
    """Return True iff a finding should be passed to the RAG retrieval step.

    See module Methodology block for the eligibility-floor rationale.
    """
    return (
        finding.classification in _ELIGIBLE_CLASSIFICATIONS
        and finding.confidence.band in _ELIGIBLE_BANDS
    )


def _coerce_result_to_citation(result: Any) -> Citation | None:
    """Map a retrieval-service result object to a Citation, filtering as needed.

    The retrieval backend returns either a real ``SearchResult`` from
    ``app.medini.services.knowledge_search`` or a duck-typed result with the
    same ``source / text / score / artefact_id`` attributes.

    Returns None if the passage is filtered by famous-chart contamination.
    """
    text = getattr(result, "text", None)
    if text is None:
        # Some backends use ``snippet`` instead — fall through to that name.
        text = getattr(result, "snippet", "")
    text = text or ""
    if _is_biographical_about_famous_chart(text):
        return None
    return Citation(
        source=str(getattr(result, "source", "") or ""),
        passage=text[:_PASSAGE_MAX_CHARS],
        relevance=float(getattr(result, "score", 0.0) or 0.0),
        knowledge_doc_id=str(getattr(result, "artefact_id", "") or ""),
    )


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #


def attach_citations(findings: list[Finding], k: int = 3) -> list[Finding]:
    """Return a new list of findings with ``citations`` populated where eligible.

    Performance discipline (spec Section 9): ALL eligible queries are
    batch-encoded in a single ``encode`` call to avoid paying the
    sentence-transformer-per-finding cost.

    Lazy-import discipline (Phase 6 Task 6.0): ``sentence_transformers``,
    ``torch`` and ``knowledge_search`` are imported here inside the function
    body — never at module top. Calling ``attach_citations`` with an empty
    list of eligible findings should NOT trigger the heavy model load,
    because the lazy ``ensure_loaded()`` is only invoked when there is real
    work to do.

    Parameters
    ----------
    findings:
        The full list of Findings emitted by upstream tiers. Findings whose
        classification or confidence band falls outside the eligibility
        floor (see ``_is_eligible``) are returned unchanged.
    k:
        Maximum number of Citation objects per Finding. Defaults to 3.

    Returns
    -------
    list[Finding]
        A new list (same length as ``findings``) where eligible findings
        have their ``citations`` field populated. The non-eligible findings
        are returned first in the list, followed by the enriched ones.
        Downstream code must not depend on positional indexing.
    """
    # Lazy import — never at module top. The Phase 6 Task 6.0 regression test
    # asserts that the --no-enrich CLI path never loads sentence_transformers,
    # which means this import must remain inside the function body.
    from app.medini.services.knowledge_search import get_default_service

    eligible_by_id: dict[str, Finding] = {
        f.id: f for f in findings if _is_eligible(f)
    }
    non_eligible = [f for f in findings if f.id not in eligible_by_id]

    if not eligible_by_id:
        # No work to do — return findings unchanged. Skipping the service
        # init here protects the --no-enrich + empty-eligibility paths.
        return list(findings)

    # Build queries deterministically — order matches eligible_by_id insertion.
    eligible_list = list(eligible_by_id.values())
    queries = [_build_query_from_rule_slot(f) for f in eligible_list]

    svc = get_default_service()
    try:
        svc.ensure_loaded()
    except Exception as exc:  # IndexUnavailable, FileNotFound, ...
        # Index missing in this deployment: leave findings unenriched and
        # surface the diagnostic in logs. Keeps the engine usable when the
        # knowledge_library has not been built.
        logger.warning(
            "RAG index unavailable; skipping citation enrichment: %s", exc,
        )
        return list(findings)

    # Batch-encode all queries in ONE model call (perf discipline).
    embeddings = svc._model.encode(queries, normalize_embeddings=True)

    enriched: list[Finding] = []
    for finding, query_vec in zip(eligible_list, embeddings):
        try:
            raw_results = svc.retrieve(query_vec, k=k)
        except Exception as exc:
            logger.warning(
                "RAG retrieve failed for finding %s: %s", finding.id, exc,
            )
            raw_results = ()
        citations: list[Citation] = []
        for r in raw_results:
            citation = _coerce_result_to_citation(r)
            if citation is not None:
                citations.append(citation)
        enriched.append(finding.model_copy(update={"citations": citations}))

    return non_eligible + enriched
