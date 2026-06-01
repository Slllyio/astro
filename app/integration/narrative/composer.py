"""LLM-driven narrative composer for the integrated reading.

Reads a Track-A reading (optionally enhanced via dkp_enhancer +
modulator + gap annotator) and emits one narrative paragraph per domain
plus an overall summary. Uses ``app.llm.client.LLMClient`` Protocol so
the consumer can plug in Ollama, OpenAI, Anthropic, or a stub.

The composer's job is PRESENTATION — turn structured findings into a
readable paragraph with citations. Verification (refuting bad claims) is
done by ``critics.py`` in a separate pass.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.llm.client import LLMClient, StubClient

# The 6 domain names Track A emits.
DOMAINS: tuple[str, ...] = (
    "career", "marriage", "children", "wealth", "health", "education",
)

# Bhava map for narrative context (matches dkp_modulator_adapter).
_DOMAIN_BHAVA: dict[str, int] = {
    "career": 10, "marriage": 7, "children": 5,
    "wealth": 2, "health": 6, "education": 4,
}


class DomainNarrative(BaseModel):
    """One LLM-composed narrative paragraph for one domain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    bhava: int
    overall_direction: str  # positive / negative / neutral / mixed
    paragraph: str
    cited_findings: list[str]  # Finding rule IDs the LLM was told to ground in
    cited_translations: list[str]  # DKP TranslationRecord keys cited
    confidence_band: str | None = None


class NarrativeOutput(BaseModel):
    """Composer output — one paragraph per non-null domain + overall."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "0.5.0"
    overall_summary: str
    per_domain: list[DomainNarrative]
    llm_provider: str
    prompt_chars: int  # total chars sent to LLM (for budget tracking)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _format_findings(findings: list[dict]) -> str:
    """Compact representation of a finding list for the prompt."""
    if not findings:
        return "(none)"
    lines = []
    for f in findings[:6]:  # cap to keep prompt small
        rule = f.get("rule", "")
        direction = f.get("direction", "?")
        verdict = (f.get("verdict") or "")[:140]
        lines.append(f"- [{direction}] {rule}: {verdict}")
    if len(findings) > 6:
        lines.append(f"- ... and {len(findings) - 6} more")
    return "\n".join(lines)


def _format_translations(translations: list[dict]) -> str:
    """Compact representation of DKP translations for the prompt."""
    if not translations:
        return "(none)"
    lines = []
    for t in translations[:4]:
        key = t.get("key", "")
        shloka = (t.get("shloka") or "")[:120]
        modern = (t.get("modern_manifestation") or "")[:120]
        lines.append(f"- {key}: SHLOKA: {shloka} | MODERN: {modern}")
    if len(translations) > 4:
        lines.append(f"- ... and {len(translations) - 4} more")
    return "\n".join(lines)


def _build_domain_prompt(
    domain: str,
    domain_block: dict,
    relevant_translations: list[dict],
) -> str:
    """Build the LLM prompt for one domain narrative."""
    bhava = _DOMAIN_BHAVA.get(domain, 0)
    overall = domain_block.get("overall_verdict") or {}
    direction = overall.get("direction", "neutral")
    promise = domain_block.get("promise") or {}
    afflictions = domain_block.get("afflictions") or []
    cross_checks = domain_block.get("cross_checks") or []

    return (
        f"You are composing a Vedic astrology reading for the {domain} domain "
        f"(bhava {bhava}). Write ONE paragraph (3-5 sentences) describing "
        f"what the chart says about this domain. Be specific and grounded in "
        f"the findings below.\n\n"
        f"OVERALL DIRECTION: {direction}\n\n"
        f"PROMISE FINDING:\n- {promise.get('verdict', '(none)')}\n\n"
        f"AFFLICTIONS:\n{_format_findings(afflictions)}\n\n"
        f"CROSS-CHECKS:\n{_format_findings(cross_checks)}\n\n"
        f"RELEVANT CLASSICAL DOCTRINE:\n{_format_translations(relevant_translations)}\n\n"
        f"RULES:\n"
        f"- NEVER use 'will', 'guaranteed', 'definitely', or 'certainly'\n"
        f"- Cite at least one finding by its rule ID in your paragraph\n"
        f"- Cite at least one classical doctrine reference if available\n"
        f"- Acknowledge uncertainty where the findings conflict\n"
        f"\nNARRATIVE PARAGRAPH:"
    )


def _build_summary_prompt(per_domain: list[DomainNarrative]) -> str:
    """Build the prompt for the overall-summary paragraph."""
    lines = ["Overall summary of a Vedic astrology reading. Below are the "
             "six per-domain conclusions. Write ONE paragraph (3-4 sentences) "
             "that synthesises them. NEVER use 'will' / 'guaranteed'.\n"]
    for dn in per_domain:
        lines.append(f"- {dn.domain.upper()} ({dn.overall_direction}): {dn.paragraph[:200]}")
    lines.append("\nOVERALL SUMMARY PARAGRAPH:")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def compose_narrative(
    reading: dict[str, Any],
    *,
    llm: LLMClient | None = None,
    integrated: dict[str, Any] | None = None,
) -> NarrativeOutput:
    """Compose narrative paragraphs for each non-null domain.

    Parameters
    ----------
    reading
        A Track-A ReadingOutput-shaped dict.
    llm
        An ``LLMClient`` (Ollama/Anthropic/OpenAI/Stub). If None, a
        ``StubClient`` is used — useful for tests and offline composition.
    integrated
        Optional ``IntegratedReadingOutput.model_dump()`` dict. If provided,
        the composer pulls cited DKP translations from
        ``integrated.dkp_translations_summary``.

    Returns
    -------
    NarrativeOutput
        One ``DomainNarrative`` per non-null domain + overall summary.
    """
    if llm is None:
        llm = StubClient(canned_response="(stub narrative — no LLM configured)")

    summary_block = (
        ((integrated or {}).get("dkp_translations_summary") or {})
        if integrated is not None
        else {}
    )
    translation_records = (summary_block.get("records") or {})

    domains_block = reading.get("domains") or {}
    per_domain_results: list[DomainNarrative] = []
    total_prompt_chars = 0

    for domain in DOMAINS:
        block = domains_block.get(domain)
        if not block:
            continue

        # Find translation records cited by this domain's findings.
        finding_ids: list[str] = []
        cited_translation_keys: list[str] = []
        for finding_key in ("promise", "overall_verdict"):
            f = block.get(finding_key)
            if isinstance(f, dict) and f.get("rule"):
                finding_ids.append(f["rule"])
        for sub_list_key in ("afflictions", "cross_checks", "triggers"):
            for f in block.get(sub_list_key) or []:
                if isinstance(f, dict) and f.get("rule"):
                    finding_ids.append(f["rule"])

        # Translation records that mention this bhava or any of these finding rules.
        bhava = _DOMAIN_BHAVA.get(domain, 0)
        relevant: list[dict] = []
        for rec_key, rec in translation_records.items():
            if not isinstance(rec, dict):
                continue
            rec_text = (rec.get("modern_manifestation", "") + " " +
                        rec.get("ancient_manifestation", ""))
            if f"bhava {bhava}" in rec_text.lower() or f"{bhava}h" in rec_text.lower():
                relevant.append(rec)
                cited_translation_keys.append(rec_key)

        prompt = _build_domain_prompt(domain, block, relevant)
        total_prompt_chars += len(prompt)
        paragraph = llm.complete(prompt)

        overall = block.get("overall_verdict") or {}
        confidence = block.get("confidence") or {}
        per_domain_results.append(DomainNarrative(
            domain=domain,
            bhava=_DOMAIN_BHAVA.get(domain, 0),
            overall_direction=overall.get("direction", "neutral"),
            paragraph=paragraph.strip(),
            cited_findings=sorted(set(finding_ids)),
            cited_translations=sorted(set(cited_translation_keys)),
            confidence_band=confidence.get("band"),
        ))

    # Summary paragraph
    if per_domain_results:
        summary_prompt = _build_summary_prompt(per_domain_results)
        total_prompt_chars += len(summary_prompt)
        overall_summary = llm.complete(summary_prompt).strip()
    else:
        overall_summary = "(no domains populated)"

    return NarrativeOutput(
        overall_summary=overall_summary,
        per_domain=per_domain_results,
        llm_provider=type(llm).__name__,
        prompt_chars=total_prompt_chars,
    )
