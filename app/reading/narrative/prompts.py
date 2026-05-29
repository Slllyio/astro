"""LLM prompt templates for narrative elaboration.

The narrative layer hands the LLM a deterministic skeleton plus the
structured findings JSON and asks for a prose elaboration that preserves
the project's locked safe-language conventions.

Discipline:
- The forbidden-word list is repeated in the prompt as a hard CONSTRAINT.
  We also enforce it post-hoc with a regex in `synthesize.py`: if the LLM
  output still contains any forbidden word, we fall back to the
  deterministic skeleton (no silent rule-breaking).
- We pass the FINDINGS JSON truncated, so even ultra-long readings stay
  within Ollama's default context.
- We never ask the LLM to invent new facts; the deterministic skeleton is
  the floor.
"""
from __future__ import annotations

import json
from typing import Any

# Words that must NEVER appear in narrative prose. The regex test in
# tests/reading/narrative/test_synthesize.py asserts this for every output.
FORBIDDEN_WORDS: tuple[str, ...] = (
    "will",
    "guaranteed",
    "definitely",
    "certainly",
)


_SYSTEM = (
    "You are interpreting a Vedic kundli reading for a thoughtful adult who "
    "wants insight, not prediction. Speak warmly and plainly. Do not "
    "disclaim astrology. Cite specifics from the FINDINGS; never invent "
    "placements."
)


NARRATIVE_PROMPT_TEMPLATE = """{system}

CONSTRAINTS (HARD):
- Use "indicates", "suggests", "may", "favors", "tends to", "points toward"
- NEVER use: "will", "guaranteed", "definitely", "certainly", "always"
- Cite doctrine sources from the FINDINGS when relevant
- Keep response to 4-6 sentences
- Do not invent facts — only use what is in the STRUCTURED FINDINGS below

SECTION: {section_name}

STRUCTURED FINDINGS (JSON):
{findings_json}

DETERMINISTIC SKELETON (starting point — preserve every factual claim):
{skeleton}

Write a prose elaboration of the section. Keep every fact from the skeleton.
Return only the prose, no preamble or headers."""


SUMMARY_PROMPT_TEMPLATE = """{system}

CONSTRAINTS (HARD):
- Use "indicates", "suggests", "may", "favors", "tends to", "points toward"
- NEVER use: "will", "guaranteed", "definitely", "certainly", "always"
- One short paragraph (4-6 sentences)
- Tone: warm, grounded, constructive
- End with one constructive note for the current mahadasha period

SECTION SKELETONS (use as the factual floor):
{skeleton_bundle}

Write a single short paragraph that synthesizes the headline themes across
the chart, mentioning the ascendant, the current mahadasha, and one or two
notable findings (a strong yoga, an active domain, a flagged contradiction).
Return only the prose, no preamble or headers."""


def _truncate_findings_for_prompt(findings: Any, *, max_chars: int = 4000) -> str:
    """Serialize a findings slice to JSON for the prompt, capped in length.

    Ollama's default context is small; ML readings can have 80+ findings.
    We truncate the JSON string defensively rather than risk a prompt that
    blows the window and gets silently rejected.
    """
    try:
        payload = json.dumps(findings, default=str, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return "(findings could not be serialized)"
    if len(payload) <= max_chars:
        return payload
    return payload[:max_chars] + "\n... (truncated)"


def build_section_prompt(
    section_name: str,
    findings: Any,
    skeleton: str,
) -> str:
    """Build the LLM prompt for a single section.

    Args:
        section_name: Canonical section name (e.g. "current_mahadasha").
        findings: The relevant slice of ReadingOutput as a JSON-serializable
            object (dict, list, or None).
        skeleton: The deterministic prose skeleton returned by the matching
            builder in `section_builders.py`.
    """
    return NARRATIVE_PROMPT_TEMPLATE.format(
        system=_SYSTEM,
        section_name=section_name,
        findings_json=_truncate_findings_for_prompt(findings),
        skeleton=skeleton.strip(),
    )


def build_summary_prompt(skeleton_bundle: dict[str, str]) -> str:
    """Build the LLM prompt for the chart-level summary.

    The summary is rendered from the union of all section skeletons; this
    keeps the model factually anchored without re-passing the full
    findings JSON (which is too large for one prompt).
    """
    bundle = "\n\n".join(
        f"[{name}]\n{text.strip()}" for name, text in skeleton_bundle.items()
    )
    return SUMMARY_PROMPT_TEMPLATE.format(
        system=_SYSTEM,
        skeleton_bundle=bundle,
    )
