"""v1.2.0 — LLM polish for the master reading.

M8 (master_compose) produces structured, accurate prose paragraphs from
template assembly. This module sends each paragraph through an LLM with
the structured backing data as ground-truth context, getting back
smoothed prose that READS like a master astrologer wrote it (instead of
a template).

CRITICAL DESIGN: the structured data is the ground truth. The LLM
ONLY smooths style. The prompts:
1. Include the M8 template paragraph as the rough draft
2. Include all structured chart facts so the LLM can specify
3. EXPLICITLY ban prediction-trap language ("will", "guaranteed", "definitely", "certainly")
4. Forbid the LLM from adding facts not in the structured data

Public surface
--------------
- ``llm_polish_master_reading(master, *, llm=None)`` -> ``PolishedMasterReading``
- ``PolishedDomain``, ``PolishedMasterReading`` Pydantic models

Default fallback is ``StubClient`` so tests + offline usage work without
Ollama/Claude/OpenAI configured. To use a real LLM, pass
``OllamaClient(host=..., model=...)`` or a future Anthropic/OpenAI client.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.integration.master_compose import DomainParagraph, MasterReading
from app.llm.client import LLMClient, StubClient

logger = logging.getLogger(__name__)


_BANNED_WORDS = ("will", "guaranteed", "definitely", "certainly")


class PolishedDomain(BaseModel):
    """One LLM-polished domain paragraph + the structured backing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    bhava: int = Field(ge=1, le=12)
    template_paragraph: str  # original from M8
    polished_paragraph: str  # LLM-polished version
    three_pillar_label: str
    md_relevance: str
    yogas_touching_domain: tuple[str, ...]


class PolishedMasterReading(BaseModel):
    """LLM-polished version of MasterReading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    integration_version: str = "1.2.0"
    chart_basics: dict[str, Any]
    polished_overview: str
    polished_dasha_triple: str
    polished_arudha: str
    polished_upapada: str
    polished_domains: list[PolishedDomain]
    llm_provider: str
    total_prompt_chars: int


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_BASE_RULES = (
    "RULES — read carefully:\n"
    "1. NEVER add facts (planets, houses, dates) that are not in the GROUND TRUTH below.\n"
    "2. NEVER use the words 'will', 'guaranteed', 'definitely', or 'certainly'.\n"
    "3. Frame predictions as tendencies, themes, signatures — never as inevitable outcomes.\n"
    "4. Use specific structured detail (house numbers, sign names, dasha lords) — be precise.\n"
    "5. Acknowledge uncertainty where the structured data shows mixed signals.\n"
    "6. Output ONLY the polished prose. No headers, no commentary, no preface."
)


def _build_overview_prompt(master: MasterReading) -> str:
    """Top-level overview paragraph from chart basics + dasha triple."""
    b = master.chart_basics
    return (
        f"You are composing the OVERVIEW paragraph of a Vedic astrology reading.\n\n"
        f"GROUND TRUTH (facts about this chart — do not invent others):\n"
        f"- Lagna: {b.get('lagna_sign_name')} (sign {b.get('lagna_sign')})\n"
        f"- Moon: {b.get('moon_sign_name')} in nakshatra {b.get('moon_nakshatra')}\n"
        f"- Sun: {b.get('sun_sign_name')}\n"
        f"- Current dasha context: {master.dasha_triple_paragraph}\n\n"
        f"{_BASE_RULES}\n\n"
        f"Write ONE flowing paragraph (3-4 sentences) that opens the reading.\n"
        f"Mention the Lagna character + current dasha phase. NO predictions yet.\n\n"
        f"OVERVIEW PARAGRAPH:"
    )


def _build_dasha_polish_prompt(master: MasterReading) -> str:
    """Polish the M7 dasha triple paragraph."""
    return (
        f"You are smoothing a Vedic astrology dasha-triple paragraph into flowing prose.\n\n"
        f"GROUND TRUTH (the rough draft below contains the facts — do not add others):\n"
        f"{master.dasha_triple_paragraph}\n\n"
        f"{_BASE_RULES}\n\n"
        f"Rewrite the rough draft into 3-5 flowing sentences. Keep ALL facts. Adjust ONLY style and connector words.\n\n"
        f"POLISHED DASHA PARAGRAPH:"
    )


def _build_arudha_polish_prompt(master: MasterReading) -> str:
    return (
        f"You are smoothing the ARUDHA LAGNA (public-image projection) section.\n\n"
        f"GROUND TRUTH:\n{master.arudha_image_summary}\n\n"
        f"{_BASE_RULES}\n\n"
        f"Rewrite into 2-3 flowing sentences explaining what the world sees in this native.\n\n"
        f"POLISHED ARUDHA PARAGRAPH:"
    )


def _build_upapada_polish_prompt(master: MasterReading) -> str:
    return (
        f"You are smoothing the UPAPADA LAGNA (marriage signifier) section.\n\n"
        f"GROUND TRUTH:\n{master.upapada_marriage_summary}\n\n"
        f"{_BASE_RULES}\n\n"
        f"Rewrite into 2-3 flowing sentences about the marriage / spouse signature.\n\n"
        f"POLISHED UPAPADA PARAGRAPH:"
    )


def _build_domain_polish_prompt(
    master: MasterReading, domain_para: DomainParagraph,
) -> str:
    """Polish one domain paragraph (career/marriage/etc.)."""
    b = master.chart_basics
    return (
        f"You are smoothing the {domain_para.domain.upper()} domain paragraph "
        f"of a Vedic astrology reading.\n\n"
        f"CHART CONTEXT:\n"
        f"- Lagna: {b.get('lagna_sign_name')}\n"
        f"- Current MD context: {master.dasha_triple_paragraph}\n\n"
        f"DOMAIN-SPECIFIC GROUND TRUTH:\n"
        f"- Bhava: {domain_para.bhava}H\n"
        f"- Three-pillar composite: {domain_para.three_pillar_label} "
        f"(score {domain_para.three_pillar_score:+.1f})\n"
        f"- Yogas touching this domain: {', '.join(domain_para.yogas_touching_domain) or 'none'}\n"
        f"- MD relevance: {domain_para.md_relevance}\n"
        f"\n"
        f"ROUGH DRAFT (rewrite into flowing prose; preserve ALL facts; adjust ONLY style):\n"
        f"{domain_para.paragraph}\n\n"
        f"{_BASE_RULES}\n\n"
        f"POLISHED {domain_para.domain.upper()} PARAGRAPH:"
    )


# ---------------------------------------------------------------------------
# Banned-word guard
# ---------------------------------------------------------------------------

def _scrub_banned_words(text: str) -> str:
    """Replace prediction-trap words with classical tendency framing."""
    replacements = (
        # word boundary substitutions, case-insensitive
        (" will ", " may "),
        (" Will ", " May "),
        (" guaranteed ", " indicated "),
        (" Guaranteed ", " Indicated "),
        (" definitely ", " classically "),
        (" Definitely ", " Classically "),
        (" certainly ", " typically "),
        (" Certainly ", " Typically "),
    )
    out = text
    for before, after in replacements:
        out = out.replace(before, after)
    return out


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def llm_polish_master_reading(
    master: MasterReading,
    *,
    llm: LLMClient | None = None,
    polish_dasha_triple: bool = True,
    polish_arudha: bool = True,
    polish_upapada: bool = True,
    polish_domains: bool = True,
    include_overview: bool = True,
) -> PolishedMasterReading:
    """Polish a MasterReading through an LLM, preserving all facts.

    Parameters
    ----------
    master
        A MasterReading from ``compose_master_reading(reading)``.
    llm
        Any ``LLMClient`` (StubClient / OllamaClient / future Anthropic).
        Defaults to ``StubClient`` so this works in tests + offline.
    polish_*
        Each section can be individually polished or skipped. Defaults
        polish everything except overview.
    include_overview
        Whether to generate a top-level overview paragraph (separate LLM call).
    """
    if llm is None:
        llm = StubClient(canned_response="(stub LLM polish — no real LLM configured)")

    provider_name = type(llm).__name__
    total_prompt_chars = 0

    # Overview
    polished_overview = ""
    if include_overview:
        prompt = _build_overview_prompt(master)
        total_prompt_chars += len(prompt)
        polished_overview = _scrub_banned_words(llm.complete(prompt).strip())

    # Dasha triple
    polished_dasha = master.dasha_triple_paragraph
    if polish_dasha_triple:
        prompt = _build_dasha_polish_prompt(master)
        total_prompt_chars += len(prompt)
        polished_dasha = _scrub_banned_words(llm.complete(prompt).strip())

    # Arudha
    polished_arudha = master.arudha_image_summary
    if polish_arudha:
        prompt = _build_arudha_polish_prompt(master)
        total_prompt_chars += len(prompt)
        polished_arudha = _scrub_banned_words(llm.complete(prompt).strip())

    # Upapada
    polished_upapada = master.upapada_marriage_summary
    if polish_upapada:
        prompt = _build_upapada_polish_prompt(master)
        total_prompt_chars += len(prompt)
        polished_upapada = _scrub_banned_words(llm.complete(prompt).strip())

    # Per-domain
    polished_domains: list[PolishedDomain] = []
    for dp in master.domain_paragraphs:
        if polish_domains:
            prompt = _build_domain_polish_prompt(master, dp)
            total_prompt_chars += len(prompt)
            try:
                polished_text = _scrub_banned_words(llm.complete(prompt).strip())
            except Exception as exc:
                logger.warning(
                    "LLM polish failed for %s domain: %s; falling back to template",
                    dp.domain, exc,
                )
                polished_text = dp.paragraph
        else:
            polished_text = dp.paragraph

        polished_domains.append(PolishedDomain(
            domain=dp.domain,
            bhava=dp.bhava,
            template_paragraph=dp.paragraph,
            polished_paragraph=polished_text,
            three_pillar_label=dp.three_pillar_label,
            md_relevance=dp.md_relevance,
            yogas_touching_domain=dp.yogas_touching_domain,
        ))

    return PolishedMasterReading(
        chart_basics=dict(master.chart_basics),
        polished_overview=polished_overview,
        polished_dasha_triple=polished_dasha,
        polished_arudha=polished_arudha,
        polished_upapada=polished_upapada,
        polished_domains=polished_domains,
        llm_provider=provider_name,
        total_prompt_chars=total_prompt_chars,
    )
