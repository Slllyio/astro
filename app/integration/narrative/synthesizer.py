"""Synthesise narrative + critic verdicts into a verified output.

Takes a ``NarrativeOutput`` + ``CriticReview`` and produces a
``VerifiedNarrative`` where each domain claim has its surviving status
(>= 3 of 4 critics confirmed → kept; else flagged or rejected).

The default kept-threshold is 3/4 confirmations. The synthesizer also
exposes ``narrate_and_verify()`` — a one-call function that composes the
narrative AND runs critics in one shot, returning the verified output.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.integration.narrative.composer import (
    DomainNarrative,
    NarrativeOutput,
    compose_narrative,
)
from app.integration.narrative.critics import (
    CriticReview,
    CriticVerdict,
    run_critics,
)
from app.llm.client import LLMClient


# Threshold: claim survives if at least N of 4 critics confirm.
_DEFAULT_SURVIVAL_THRESHOLD = 3


class VerifiedClaim(BaseModel):
    """One domain narrative + the 4 critic verdicts + survival status."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    narrative: DomainNarrative
    critic_verdicts: list[CriticVerdict]
    confirm_count: int
    refute_count: int
    uncertain_count: int
    survives: bool  # confirm_count >= threshold
    status: str  # "shipped" / "flagged" / "rejected"


class VerifiedNarrative(BaseModel):
    """Top-level envelope from ``narrate_and_verify``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "0.5.0"
    overall_summary: str
    llm_provider: str
    survival_threshold: int
    per_domain: list[VerifiedClaim]
    domains_shipped: list[str]
    domains_flagged: list[str]
    domains_rejected: list[str]
    total_prompt_chars: int


def _classify_status(survives: bool, refute_count: int) -> str:
    if survives:
        return "shipped"
    if refute_count >= 3:
        return "rejected"
    return "flagged"


def narrate_and_verify(
    reading: dict[str, Any],
    *,
    llm: LLMClient | None = None,
    integrated: dict[str, Any] | None = None,
    survival_threshold: int = _DEFAULT_SURVIVAL_THRESHOLD,
) -> VerifiedNarrative:
    """Compose narrative + run critics + synthesise the verified output.

    Single-call entry point that does:
    1. ``compose_narrative(reading, llm=llm, integrated=integrated)``
    2. ``run_critics(narrative, reading, llm=llm)``
    3. Group verdicts per domain, apply survival threshold, classify status.

    Parameters
    ----------
    reading
        Track-A ReadingOutput dict.
    llm
        LLMClient (Ollama / OpenAI / Anthropic / Stub). If None, StubClient.
    integrated
        Optional IntegratedReadingOutput dict — provides DKP translations
        for the composer's domain prompts.
    survival_threshold
        Number of confirmations needed (out of 4) for a claim to ship.
        Default is 3. Lower for permissive mode (e.g. 2), higher for strict.

    Returns
    -------
    VerifiedNarrative
        Per-domain claims partitioned into shipped/flagged/rejected.
    """
    narrative = compose_narrative(reading, llm=llm, integrated=integrated)
    review = run_critics(narrative, reading, llm=llm)

    # Group verdicts by domain.
    by_domain: dict[str, list[CriticVerdict]] = {}
    for v in review.per_claim:
        by_domain.setdefault(v.domain, []).append(v)

    per_domain: list[VerifiedClaim] = []
    shipped: list[str] = []
    flagged: list[str] = []
    rejected: list[str] = []

    for narr in narrative.per_domain:
        verdicts = by_domain.get(narr.domain, [])
        confirms = sum(1 for v in verdicts if v.verdict == "confirm")
        refutes = sum(1 for v in verdicts if v.verdict == "refute")
        uncerts = sum(1 for v in verdicts if v.verdict == "uncertain")
        survives = confirms >= survival_threshold
        status = _classify_status(survives, refutes)
        if status == "shipped":
            shipped.append(narr.domain)
        elif status == "rejected":
            rejected.append(narr.domain)
        else:
            flagged.append(narr.domain)

        per_domain.append(VerifiedClaim(
            domain=narr.domain,
            narrative=narr,
            critic_verdicts=verdicts,
            confirm_count=confirms,
            refute_count=refutes,
            uncertain_count=uncerts,
            survives=survives,
            status=status,
        ))

    return VerifiedNarrative(
        overall_summary=narrative.overall_summary,
        llm_provider=narrative.llm_provider,
        survival_threshold=survival_threshold,
        per_domain=per_domain,
        domains_shipped=shipped,
        domains_flagged=flagged,
        domains_rejected=rejected,
        total_prompt_chars=narrative.prompt_chars,
    )
