"""Synthesize a ReadingOutput dict into prose sections.

Public API:
    narrate_reading(reading, *, mode="full", section=None, client=None)
        -> NarrativeOutput

Two paths per section:
  1. Build a deterministic skeleton from the structured findings using
     `section_builders.py`. This is the factual floor.
  2. If `client` is provided (or a default Ollama client is built from
     settings when OLLAMA_ENABLED is True), prompt the LLM to elaborate.
     If the LLM is down OR returns prose containing a forbidden word
     ("will", "guaranteed", "definitely", "certainly"), fall back to the
     skeleton — never serve rule-violating prose.

Mode semantics:
  - "summary"  : run all skeleton builders, then produce a single short
                 chart-level paragraph from their union.
  - "full"     : run all skeleton builders AND a chart-level summary.
  - "section"  : produce a single named section only.

This module deliberately does NOT import `sentence_transformers`. RAG
citations are already inlined into Finding.citations by the Tier-3
enrichment in `app.reading.proforma`; we just thread them through.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from app.reading.narrative.prompts import (
    FORBIDDEN_WORDS,
    build_section_prompt,
    build_summary_prompt,
)
from app.reading.narrative.section_builders import (
    DOMAIN_SECTIONS,
    NARRATIVE_SECTIONS,
    build_chart_overview,
    build_contradictions_section,
    build_current_antardasha,
    build_current_mahadasha,
    build_domain_section,
    build_yogas_section,
)

logger = logging.getLogger(__name__)

NarrativeMode = Literal["summary", "full", "section"]


# Build a regex once at module load. Word-boundary anchors so
# "willingness" and "willing" do NOT match "will".
_FORBIDDEN_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_WORDS) + r")\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class NarrativeOutput:
    """The narrated reading.

    Attributes:
        summary: Chart-level paragraph. Empty in "section" mode.
        sections: Dict of section_name -> prose. In "section" mode contains
            exactly the requested section. In "summary" mode contains all
            section skeletons. In "full" mode contains both.
        mode: The mode that was run.
        llm_used: True iff at least one section was successfully elaborated
            by the LLM (and passed the forbidden-word check).
    """

    summary: str
    sections: dict[str, str]
    mode: str
    llm_used: bool = False
    forbidden_word_rejections: int = field(default=0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_default_client() -> Any | None:
    """Build the default LLM client from settings, or None if disabled.

    Lazy-imports `app.llm.client` so the narrative module's import cost
    stays minimal when narration is not used.
    """
    try:
        from app.core.config import settings
    except Exception:  # pragma: no cover - settings always importable in app
        return None
    if not getattr(settings, "OLLAMA_ENABLED", False):
        return None
    try:
        from app.llm.client import OllamaClient

        return OllamaClient(
            host=settings.OLLAMA_HOST,
            model=settings.OLLAMA_MODEL,
            timeout_seconds=settings.OLLAMA_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # pragma: no cover - import failure unusual
        logger.warning("Could not build default Ollama client: %s", exc)
        return None


def _passes_safe_language(text: str) -> bool:
    """True iff `text` contains none of the forbidden predictive words."""
    return _FORBIDDEN_PATTERN.search(text) is None


def _elaborate_or_fallback(
    *,
    client: Any | None,
    section_name: str,
    findings_slice: Any,
    skeleton: str,
) -> tuple[str, bool]:
    """Try the LLM; fall back to skeleton on failure or rule violation.

    Returns (text, used_llm).
    """
    if client is None:
        return skeleton, False

    prompt = build_section_prompt(section_name, findings_slice, skeleton)
    try:
        text = client.complete(prompt)
    except Exception as exc:  # noqa: BLE001 - any client error → fallback
        logger.warning(
            "LLM elaboration failed for %s; using skeleton (%s)",
            section_name, exc,
        )
        return skeleton, False

    text = (text or "").strip()
    if not text:
        return skeleton, False

    if not _passes_safe_language(text):
        logger.info(
            "LLM output for %s contained a forbidden word; using skeleton",
            section_name,
        )
        return skeleton, False

    return text, True


def _build_all_skeletons(reading: dict[str, Any]) -> dict[str, str]:
    """Run every deterministic builder against the reading dict.

    Returns the full skeleton map keyed by `NARRATIVE_SECTIONS`.
    """
    chart_block = reading.get("chart") or {}
    primitives = reading.get("primitives") or {}
    sequences = reading.get("sequences") or {}
    practitioner = reading.get("practitioner") or {}
    domains = reading.get("domains") or {}
    contradictions = reading.get("contradictions") or []

    skeletons: dict[str, str] = {
        "chart_overview": build_chart_overview(chart_block, primitives),
        "current_mahadasha": build_current_mahadasha(sequences),
        "current_antardasha": build_current_antardasha(sequences),
        "yogas": build_yogas_section(practitioner.get("findings") or []),
        "contradictions": build_contradictions_section(contradictions),
    }
    for name in DOMAIN_SECTIONS:
        skeletons[name] = build_domain_section(name, domains.get(name))
    return skeletons


def _findings_slice_for(reading: dict[str, Any], section: str) -> Any:
    """Return a focused JSON slice of the reading to ground the LLM.

    Keeping each slice small keeps the prompt context bounded and gives
    the LLM the minimum it needs to elaborate without inventing.
    """
    if section == "chart_overview":
        chart_block = reading.get("chart") or {}
        return {
            "cusps": chart_block.get("cusps"),
            "extras": {
                k: chart_block.get("extras", {}).get(k)
                for k in ("is_daytime", "panchanga", "current_mahadasha")
            },
        }
    if section == "current_mahadasha":
        mds = (reading.get("sequences") or {}).get("md_judgments") or []
        return next((m for m in mds if m.get("is_current")), None)
    if section == "current_antardasha":
        ads = (reading.get("sequences") or {}).get("ad_judgments") or []
        return next((a for a in ads if a.get("is_current")), None)
    if section == "yogas":
        findings = (reading.get("practitioner") or {}).get("findings") or []
        return [f for f in findings if f.get("classification") == "yoga"][:10]
    if section == "contradictions":
        return reading.get("contradictions") or []
    if section in DOMAIN_SECTIONS:
        return (reading.get("domains") or {}).get(section)
    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def narrate_reading(
    reading: dict[str, Any],
    *,
    mode: NarrativeMode = "full",
    section: str | None = None,
    client: Any | None = None,
) -> NarrativeOutput:
    """Turn a ReadingOutput dict into prose.

    Args:
        reading: A ReadingOutput-shaped dict (as produced by
            `app.reading.proforma.compute`).
        mode: One of "summary", "full", "section".
        section: Required when mode == "section"; must be a member of
            `NARRATIVE_SECTIONS`. Must be None otherwise.
        client: Optional explicit LLM client. When None, an Ollama client
            is built from settings if OLLAMA_ENABLED; otherwise the
            deterministic skeletons are returned as-is.

    Returns:
        NarrativeOutput. Always usable (never raises on LLM failure).

    Raises:
        ValueError: on invalid mode/section combinations only.
        TypeError: if `reading` is not a dict.
    """
    if not isinstance(reading, dict):
        raise TypeError("reading must be a dict matching ReadingOutput shape")

    if mode not in ("summary", "full", "section"):
        raise ValueError(
            f"unknown mode {mode!r}; expected 'summary', 'full', or 'section'"
        )

    if mode == "section":
        if section is None:
            raise ValueError("section is required when mode='section'")
        if section not in NARRATIVE_SECTIONS:
            raise ValueError(
                f"unknown section {section!r}; allowed: {NARRATIVE_SECTIONS}"
            )
    elif section is not None:
        raise ValueError("section must be None unless mode='section'")

    effective_client = client if client is not None else _resolve_default_client()

    # ---- Section mode: single named section ----
    if mode == "section":
        # Mypy: narrowed by the validation above.
        assert section is not None
        skeletons = _build_all_skeletons(reading)
        skeleton = skeletons[section]
        findings = _findings_slice_for(reading, section)
        text, used = _elaborate_or_fallback(
            client=effective_client,
            section_name=section,
            findings_slice=findings,
            skeleton=skeleton,
        )
        return NarrativeOutput(
            summary="",
            sections={section: text},
            mode=mode,
            llm_used=used,
        )

    # ---- Summary + Full mode: all sections + chart-level summary ----
    skeletons = _build_all_skeletons(reading)
    elaborated: dict[str, str] = {}
    llm_used_any = False
    if mode == "full":
        for name, sk in skeletons.items():
            findings = _findings_slice_for(reading, name)
            text, used = _elaborate_or_fallback(
                client=effective_client,
                section_name=name,
                findings_slice=findings,
                skeleton=sk,
            )
            elaborated[name] = text
            llm_used_any = llm_used_any or used
    else:
        # mode == "summary": keep the section skeletons untouched.
        elaborated = dict(skeletons)

    # Chart-level summary
    if effective_client is not None:
        prompt = build_summary_prompt(skeletons)
        try:
            raw = effective_client.complete(prompt)
            raw = (raw or "").strip()
            if raw and _passes_safe_language(raw):
                summary_text = raw
                llm_used_any = True
            else:
                summary_text = _deterministic_summary(skeletons)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM summary failed; using deterministic (%s)", exc)
            summary_text = _deterministic_summary(skeletons)
    else:
        summary_text = _deterministic_summary(skeletons)

    return NarrativeOutput(
        summary=summary_text,
        sections=elaborated,
        mode=mode,
        llm_used=llm_used_any,
    )


def _deterministic_summary(skeletons: dict[str, str]) -> str:
    """Compose a chart-level summary from the section skeletons.

    Picks the 3 most chart-relevant skeletons (overview + current MD + a
    domain) and concatenates them into one paragraph. Safe-language by
    construction since each skeleton is safe.
    """
    parts: list[str] = []
    overview = skeletons.get("chart_overview", "").strip()
    if overview:
        parts.append(overview)
    md = skeletons.get("current_mahadasha", "").strip()
    if md:
        parts.append(md)
    # Pick the first domain whose skeleton is non-trivial.
    for d in DOMAIN_SECTIONS:
        s = skeletons.get(d, "").strip()
        if s and "No domain reading is available" not in s:
            parts.append(s)
            break
    return " ".join(parts) or "No narrative content available for this chart."
