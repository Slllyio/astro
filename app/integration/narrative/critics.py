"""4-critic adversarial verification for narrative claims.

Each critic takes a domain narrative paragraph + the structured findings
that back it, and emits a verdict ("confirm" / "refute" / "uncertain")
with a reason. Critics run in parallel via ``concurrent.futures``.

The 4 critic angles:

1. **BPHS purist** — does this narrative align with canonical BPHS doctrine?
   Refute if it makes claims contradicting Parashara's classical rules.

2. **Skeptic** — is this claim plausible-but-wrong? Refute if the narrative
   sounds confident but isn't grounded in the cited findings.

3. **Modern translator** — does this apply to 2026 life context (career =
   not just king/minister; marriage = not just arranged; etc.)? Refute if
   the narrative is anachronistic.

4. **Contradiction hunter** — does this contradict another claim in the
   same reading? Refute if cross-domain contradiction surfaces.

The 4 critics use the same LLMClient as the composer. Outputs are
structured (small JSON shapes) so the synthesizer can mechanically count
confirmations.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.llm.client import LLMClient, StubClient


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

class CriticVerdict(BaseModel):
    """One critic's verdict on one narrative claim."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    critic_angle: str  # "bphs_purist" / "skeptic" / "modern_translator" / "contradiction_hunter"
    domain: str  # which domain's narrative was reviewed
    verdict: str  # "confirm" / "refute" / "uncertain"
    reason: str
    suggested_revision: str | None = None


class CriticReview(BaseModel):
    """Aggregate 4-critic review for one narrative output."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    per_claim: list[CriticVerdict]  # 4 verdicts per domain claim
    domains_reviewed: list[str]
    total_verdicts: int


# ---------------------------------------------------------------------------
# Critic prompt templates
# ---------------------------------------------------------------------------

_CRITIC_PROMPTS = {
    "bphs_purist": (
        "You are a strict BPHS-purist Vedic astrology reviewer. Read the "
        "{domain} narrative below. Does it align with classical BPHS / "
        "Parashara doctrine? If it contradicts canonical doctrine, "
        "REFUTE. If it's grounded in classical rules, CONFIRM. "
        "If you cannot tell, UNCERTAIN.\n\n"
        "NARRATIVE:\n{paragraph}\n\n"
        "BACKING FINDINGS:\n{findings_summary}\n\n"
        "Output JSON only (no markdown), exactly:\n"
        '{{"verdict": "confirm|refute|uncertain", "reason": "<one sentence>"}}\n'
    ),
    "skeptic": (
        "You are a skeptical Vedic astrology reviewer. Read the {domain} "
        "narrative below. Default to REFUTE unless the claim is clearly "
        "supported by the cited findings. Be harsh on hand-waving or "
        "overclaiming. CONFIRM only when the paragraph stays within what "
        "the findings actually support.\n\n"
        "NARRATIVE:\n{paragraph}\n\n"
        "BACKING FINDINGS:\n{findings_summary}\n\n"
        "Output JSON only (no markdown), exactly:\n"
        '{{"verdict": "confirm|refute|uncertain", "reason": "<one sentence>"}}\n'
    ),
    "modern_translator": (
        "You translate ancient Vedic doctrine into modern 2026 life context. "
        "Read the {domain} narrative below. If it remains anchored in pre-"
        "modern social structures (e.g. talks of 'king' for career, 'arranged "
        "alliance' for marriage as if the only option), REFUTE. If it "
        "translates the doctrine sensibly into modern terms, CONFIRM.\n\n"
        "NARRATIVE:\n{paragraph}\n\n"
        "Output JSON only (no markdown), exactly:\n"
        '{{"verdict": "confirm|refute|uncertain", "reason": "<one sentence>"}}\n'
    ),
    "contradiction_hunter": (
        "You hunt for contradictions across a reading's narratives. Below is "
        "the {domain} narrative and excerpts of the OTHER domain narratives. "
        "If the {domain} paragraph contradicts any of the others (e.g. claims "
        "wealth is afflicted while wealth's own paragraph says it's strong), "
        "REFUTE. If it's coherent with the others, CONFIRM.\n\n"
        "DOMAIN NARRATIVE:\n{paragraph}\n\n"
        "OTHER DOMAIN NARRATIVES (excerpts):\n{other_narratives}\n\n"
        "Output JSON only (no markdown), exactly:\n"
        '{{"verdict": "confirm|refute|uncertain", "reason": "<one sentence>"}}\n'
    ),
}


# ---------------------------------------------------------------------------
# LLM output parser
# ---------------------------------------------------------------------------

_JSON_PATTERN = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _parse_verdict_json(text: str) -> tuple[str, str]:
    """Extract the first JSON-shaped object from LLM output and return
    (verdict, reason). Falls back to UNCERTAIN if parsing fails."""
    if not text:
        return "uncertain", "(empty LLM output)"
    match = _JSON_PATTERN.search(text)
    if not match:
        return "uncertain", "(no JSON in LLM output)"
    try:
        parsed = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return "uncertain", "(malformed JSON in LLM output)"
    verdict = str(parsed.get("verdict", "uncertain")).lower().strip()
    if verdict not in ("confirm", "refute", "uncertain"):
        verdict = "uncertain"
    reason = str(parsed.get("reason", ""))[:300]
    return verdict, reason


# ---------------------------------------------------------------------------
# Per-critic runner
# ---------------------------------------------------------------------------

def _findings_summary_for_domain(reading: dict, domain: str) -> str:
    """Compact backing-findings summary."""
    block = (reading.get("domains") or {}).get(domain) or {}
    parts: list[str] = []
    for key in ("promise", "overall_verdict"):
        f = block.get(key)
        if isinstance(f, dict):
            parts.append(f"{key}: [{f.get('direction', '?')}] {f.get('verdict', '')[:120]}")
    afflictions = block.get("afflictions") or []
    if afflictions:
        parts.append(f"afflictions: {len(afflictions)} findings")
    return "\n".join(parts) if parts else "(no backing findings)"


def _other_narratives_excerpt(
    narratives: list, current_domain: str,
) -> str:
    """Build the other-domain excerpts for the contradiction-hunter prompt."""
    lines: list[str] = []
    for n in narratives:
        if n.domain == current_domain:
            continue
        lines.append(f"- {n.domain} ({n.overall_direction}): {n.paragraph[:160]}")
    return "\n".join(lines) if lines else "(no other narratives)"


def _run_one_critic(
    *,
    angle: str,
    paragraph_text: str,
    domain: str,
    reading: dict,
    other_narratives_excerpt: str,
    llm: LLMClient,
) -> CriticVerdict:
    """Execute one critic-prompt and return the structured verdict."""
    template = _CRITIC_PROMPTS[angle]
    prompt = template.format(
        domain=domain,
        paragraph=paragraph_text,
        findings_summary=_findings_summary_for_domain(reading, domain),
        other_narratives=other_narratives_excerpt,
    )
    response = llm.complete(prompt)
    verdict, reason = _parse_verdict_json(response)
    return CriticVerdict(
        critic_angle=angle,
        domain=domain,
        verdict=verdict,
        reason=reason,
        suggested_revision=None,
    )


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def run_critics(
    narrative_output: Any,  # NarrativeOutput, but avoid circular import
    reading: dict[str, Any],
    *,
    llm: LLMClient | None = None,
    max_workers: int = 4,
) -> CriticReview:
    """Run all 4 critics on every domain narrative.

    Returns a ``CriticReview`` with 4 verdicts per domain claim. Critics
    are executed in parallel via ``ThreadPoolExecutor`` since the LLM
    client interface is sync."""
    if llm is None:
        llm = StubClient(canned_response='{"verdict": "uncertain", "reason": "stub LLM"}')

    angles = list(_CRITIC_PROMPTS.keys())
    narratives = list(narrative_output.per_domain)

    work_items: list[tuple[str, str, str, str]] = []  # (angle, domain, paragraph, others_excerpt)
    for n in narratives:
        others_excerpt = _other_narratives_excerpt(narratives, n.domain)
        for angle in angles:
            work_items.append((angle, n.domain, n.paragraph, others_excerpt))

    verdicts: list[CriticVerdict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(
                _run_one_critic,
                angle=angle, paragraph_text=para, domain=domain,
                reading=reading, other_narratives_excerpt=others, llm=llm,
            )
            for angle, domain, para, others in work_items
        ]
        for fut in concurrent.futures.as_completed(futures):
            verdicts.append(fut.result())

    domains_reviewed = sorted({v.domain for v in verdicts})

    return CriticReview(
        per_claim=verdicts,
        domains_reviewed=domains_reviewed,
        total_verdicts=len(verdicts),
    )
