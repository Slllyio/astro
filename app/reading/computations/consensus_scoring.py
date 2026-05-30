"""Tier-3 enrichment: cross-source doctrine consensus scoring.

For each Finding that has had ``citations`` populated by ``rag_citations``,
computes the fraction of citations whose passages assert the
**rule-applicability** of the finding (e.g. "this configuration is *called*
Gajakesari Yoga"). Citations whose passages instead make **outcome claims**
("Gajakesari produces wealth and fame") are counted toward the denominator
but NOT toward the agreeing-numerator: by v1 design, outcome claims are
not in our evidence base.

The output ``ConsensusScore`` carries:

* ``score``               — agreeing / total in [0.0, 1.0]
* ``sources_agreeing``    — count of citations whose passage asserts the
                            rule applies to this configuration
* ``sources_total``       — count of citations attached to the finding
* ``low_consensus_flag``  — True iff score < 0.5

Methodology:
    Type: descriptive
    Inputs to retrieval/scoring: ``finding.rule`` (the rule name) +
        the already-attached ``finding.citations``. NEVER
        ``finding.verdict`` free-text — would re-introduce the
        confirmation-bias trap that ``rag_citations`` was designed to
        avoid.
    Explicitly NOT used: ``Finding.verdict`` free-text. Banned per
        anti-confirmation-bias commitment (a verdict-driven consensus
        score would inflate self-agreement).
    Thresholds & their source: ``low_consensus_flag`` is True at
        ``score < 0.5`` — chosen because below half-agreement we cannot
        in good faith say the doctrine corpus speaks with one voice.
        NOT calibrated against any historical-outcome corpus.
    Famous-chart anti-contamination: not re-applied here; citations
        arriving from ``rag_citations`` have already been filtered for
        famous-chart biographical contamination. If a downstream test
        bypasses ``rag_citations`` and attaches a contaminated
        citation, that citation will be counted; the design depends on
        the upstream filter doing its job.
    Null-baseline test required: N/A — pure aggregation, no model fit.
    Prediction-trap declaration: "This module does NOT predict outcomes.
        It scores cross-source agreement on PRE-EXISTING attached
        citations. No fitting against any chart corpus with outcome
        labels."

Doctrine source: spec Section 14, Tier-3 methodology commitments. The
    "rule-applicability vs outcome-claim" scope distinction is the
    central anti-confirmation-bias safeguard.
"""
from __future__ import annotations

import logging

from app.reading.schema import ConsensusScore, Finding

logger = logging.getLogger(__name__)


# Phrases that mark a passage as a rule-applicability statement (positive
# signal). These are intentionally narrow: any added phrase widens the
# numerator and weakens the anti-confirmation-bias guarantee.
_APPLICABILITY_PHRASES: tuple[str, ...] = (
    "is called",
    "is termed",
    "is known as",
    "is named",
    "is referred to as",
    "called the",
    "termed the",
    "known as the",
)

# Eligible classifications for consensus scoring. Primitives & afflictions
# are bookkeeping and outcome-flag respectively; we don't compute consensus
# on them in v1.
_ELIGIBLE_CLASSIFICATIONS: frozenset[str] = frozenset({"promise", "yoga", "trigger"})

# Boundary at which low_consensus_flag fires. Strict less-than (< 0.5);
# 0.5 itself is the "balanced" boundary and is not flagged.
_LOW_CONSENSUS_THRESHOLD: float = 0.5


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _extract_rule_keyword(rule_name: str) -> str:
    """Pull the most distinctive lowercased word out of the rule name.

    The first space-delimited token of the rule (e.g. "Gajakesari" out of
    "Gajakesari Yoga") is treated as the keyword. This keeps the
    rule-applicability check tight: a passage must mention the keyword
    AND an applicability phrase to count.
    """
    parts = (rule_name or "").strip().split()
    return parts[0].lower() if parts else ""


def _is_rule_applicability_statement(passage: str, rule_name: str) -> bool:
    """Return True iff the passage asserts that the rule applies (vs. predicting).

    The check has two AND-gates:

    1. The rule's keyword must appear in the lowercased passage.
    2. An applicability phrase (``is called``, ``is termed``, ...) must
       also appear.

    Both must be satisfied; either alone is insufficient. This is the
    central anti-confirmation-bias gate — see module Methodology block.
    """
    if not passage or not rule_name:
        return False
    lower = passage.lower()
    keyword = _extract_rule_keyword(rule_name)
    if not keyword or keyword not in lower:
        return False
    return any(phrase in lower for phrase in _APPLICABILITY_PHRASES)


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #


def score_consensus(findings: list[Finding]) -> list[Finding]:
    """Return a new list with ``consensus`` and ``consensus_status`` populated.

    Operation per finding:

    * If the finding's classification is not in
      ``_ELIGIBLE_CLASSIFICATIONS``, return it unchanged. Primitives and
      afflictions do not get consensus scoring in v1.
    * If the eligible finding has zero citations, return with
      ``consensus = None`` and ``consensus_status = "no_agreement"``.
      A zero-citation finding does NOT get a fabricated zero score.
    * Otherwise, compute ``ConsensusScore`` over the attached citations
      and set ``consensus_status = "computed"``.
    """
    out: list[Finding] = []
    for finding in findings:
        if finding.classification not in _ELIGIBLE_CLASSIFICATIONS:
            out.append(finding)
            continue

        if not finding.citations:
            # Eligible but no citations attached (perhaps RAG was unavailable).
            # Refuse to fabricate a zero score — surface no_agreement instead.
            out.append(
                finding.model_copy(
                    update={
                        "consensus": None,
                        "consensus_status": "no_agreement",
                    }
                )
            )
            continue

        total = len(finding.citations)
        agreeing = sum(
            1
            for c in finding.citations
            if _is_rule_applicability_statement(c.passage, finding.rule)
        )
        score = agreeing / total if total else 0.0
        consensus = ConsensusScore(
            score=score,
            sources_agreeing=agreeing,
            sources_total=total,
            low_consensus_flag=score < _LOW_CONSENSUS_THRESHOLD,
        )
        out.append(
            finding.model_copy(
                update={
                    "consensus": consensus,
                    "consensus_status": "computed",
                }
            )
        )
    return out
