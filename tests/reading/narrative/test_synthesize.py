"""Tests for `app.reading.narrative.synthesize`.

Locks the public NarrativeOutput contract and the dual LLM-available /
LLM-disabled paths:

- LLM-disabled path (client=None, OLLAMA_ENABLED=False default) returns
  deterministic skeletons verbatim.
- Mode "full" returns all 11 NARRATIVE_SECTIONS including the 6 domains.
- Mode "section" returns exactly the one requested section.
- Mode "summary" returns a non-empty chart-level summary.
- LLM path uses a StubClient (no network); output is the canned LLM text.
- Forbidden-word policy: if the LLM emits "will" / "guaranteed" /
  "definitely" / "certainly", synthesize falls back to the skeleton.
- Lazy-import discipline: importing `app.reading.narrative` MUST NOT pull
  in `sentence_transformers` at module top.
"""
from __future__ import annotations

import re
import sys

import pytest

from app.llm.client import StubClient
from app.reading.narrative import NarrativeOutput, narrate_reading
from app.reading.narrative.prompts import FORBIDDEN_WORDS
from app.reading.narrative.section_builders import (
    DOMAIN_SECTIONS,
    NARRATIVE_SECTIONS,
)


_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_WORDS) + r")\b",
    flags=re.IGNORECASE,
)


def _assert_safe_in_all_sections(out: NarrativeOutput) -> None:
    """No forbidden word may appear in the summary OR any section."""
    if out.summary:
        match = _FORBIDDEN_RE.search(out.summary)
        assert match is None, (
            f"forbidden word {match.group(0)!r} in summary: {out.summary!r}"
        )
    for name, text in out.sections.items():
        match = _FORBIDDEN_RE.search(text)
        assert match is None, (
            f"forbidden word {match.group(0)!r} in section {name!r}: {text!r}"
        )


# ---------------------------------------------------------------------------
# Mode + section validation
# ---------------------------------------------------------------------------


class TestArgumentValidation:
    """Argument validation is on the public entry point only."""

    def test_unknown_mode_raises(self, bangalore_reading):
        with pytest.raises(ValueError, match="unknown mode"):
            narrate_reading(bangalore_reading, mode="frobnicate")  # type: ignore[arg-type]

    def test_section_mode_requires_section(self, bangalore_reading):
        with pytest.raises(ValueError, match="section is required"):
            narrate_reading(bangalore_reading, mode="section")

    def test_section_must_be_known(self, bangalore_reading):
        with pytest.raises(ValueError, match="unknown section"):
            narrate_reading(bangalore_reading, mode="section", section="bogus")

    def test_section_must_be_none_in_summary_mode(self, bangalore_reading):
        with pytest.raises(ValueError, match="section must be None"):
            narrate_reading(
                bangalore_reading, mode="summary", section="career",
            )

    def test_reading_must_be_dict(self):
        with pytest.raises(TypeError):
            narrate_reading("not a dict", mode="full")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# LLM-disabled (deterministic) path
# ---------------------------------------------------------------------------


class TestLLMDisabledPath:
    """When client=None and OLLAMA_ENABLED is False (test default), the
    narrative is purely deterministic — skeleton text in, skeleton text out."""

    def test_full_mode_returns_all_sections(self, bangalore_reading):
        out = narrate_reading(bangalore_reading, mode="full", client=None)
        assert out.mode == "full"
        assert out.llm_used is False
        for name in NARRATIVE_SECTIONS:
            assert name in out.sections, f"missing section {name!r}"
            assert out.sections[name].strip()

    def test_full_mode_includes_all_six_domains(self, bangalore_reading):
        out = narrate_reading(bangalore_reading, mode="full", client=None)
        for domain in DOMAIN_SECTIONS:
            assert domain in out.sections
            assert domain.lower() in out.sections[domain].lower()

    def test_summary_mode_produces_non_empty_summary(self, bangalore_reading):
        out = narrate_reading(bangalore_reading, mode="summary", client=None)
        assert out.mode == "summary"
        assert out.summary.strip()
        assert out.llm_used is False

    def test_section_mode_returns_only_requested_section(self, bangalore_reading):
        out = narrate_reading(
            bangalore_reading, mode="section", section="current_mahadasha",
            client=None,
        )
        assert out.mode == "section"
        assert out.summary == ""
        assert set(out.sections.keys()) == {"current_mahadasha"}
        assert out.sections["current_mahadasha"].strip()
        assert out.llm_used is False

    def test_safe_language_holds_across_all_sections(self, bangalore_reading):
        """Regex-asserts the safe-language doctrine on a full narration."""
        out = narrate_reading(bangalore_reading, mode="full", client=None)
        _assert_safe_in_all_sections(out)


# ---------------------------------------------------------------------------
# LLM-available (stub) path
# ---------------------------------------------------------------------------


class TestLLMAvailablePath:
    """When a client is passed, synthesize must call it and surface output."""

    def test_section_uses_llm_when_client_passed(self, bangalore_reading):
        """Stub returns canned text — synthesize must surface it, not skeleton."""
        stub = StubClient(canned_response="The chart suggests warm prospects.")
        out = narrate_reading(
            bangalore_reading, mode="section", section="career", client=stub,
        )
        assert out.llm_used is True
        assert out.sections["career"] == "The chart suggests warm prospects."

    def test_full_mode_uses_llm_for_all_sections(self, bangalore_reading):
        """Full mode calls the LLM for every section + summary."""
        stub = StubClient(canned_response="Indicates a thoughtful chapter.")
        out = narrate_reading(
            bangalore_reading, mode="full", client=stub,
        )
        assert out.llm_used is True
        for name in NARRATIVE_SECTIONS:
            assert out.sections[name] == "Indicates a thoughtful chapter."
        # And the summary uses the LLM too.
        assert out.summary == "Indicates a thoughtful chapter."

    def test_summary_mode_uses_llm_for_summary_only(self, bangalore_reading):
        """Summary mode does NOT elaborate per-section, but does elaborate summary."""
        stub = StubClient(canned_response="A grounded year may suggest growth.")
        out = narrate_reading(
            bangalore_reading, mode="summary", client=stub,
        )
        assert out.summary == "A grounded year may suggest growth."
        # Section bodies stay as raw skeletons in summary mode.
        for name in NARRATIVE_SECTIONS:
            # Skeletons exist and are non-empty.
            assert out.sections[name].strip()
        # But the LLM was used (for summary) → llm_used flag set.
        assert out.llm_used is True


# ---------------------------------------------------------------------------
# Safe-language enforcement on LLM output
# ---------------------------------------------------------------------------


class TestForbiddenWordRejection:
    """If the LLM emits a forbidden word, synthesize falls back to skeleton."""

    def test_rejects_will(self, bangalore_reading):
        stub = StubClient(canned_response="This will definitely happen tomorrow.")
        out = narrate_reading(
            bangalore_reading, mode="section", section="career", client=stub,
        )
        # Forbidden word rejected → skeleton served → llm_used=False.
        assert out.llm_used is False
        # Skeleton mentions the domain.
        assert "career" in out.sections["career"].lower()

    def test_rejects_guaranteed(self, bangalore_reading):
        stub = StubClient(canned_response="A guaranteed outcome in your marriage.")
        out = narrate_reading(
            bangalore_reading, mode="section", section="marriage", client=stub,
        )
        assert out.llm_used is False

    def test_rejects_certainly(self, bangalore_reading):
        stub = StubClient(canned_response="You certainly find prosperity.")
        out = narrate_reading(
            bangalore_reading, mode="section", section="wealth", client=stub,
        )
        assert out.llm_used is False

    def test_accepts_safe_language(self, bangalore_reading):
        """Safe wording must NOT be rejected."""
        stub = StubClient(
            canned_response="The chart suggests opportunities and may favor growth."
        )
        out = narrate_reading(
            bangalore_reading, mode="section", section="career", client=stub,
        )
        assert out.llm_used is True

    def test_word_boundary_does_not_match_substrings(self, bangalore_reading):
        """`willingness` should NOT match `will` (word-boundary regex)."""
        stub = StubClient(
            canned_response=(
                "A willingness to grow indicates fertile ground for the period."
            )
        )
        out = narrate_reading(
            bangalore_reading, mode="section", section="education", client=stub,
        )
        assert out.llm_used is True


# ---------------------------------------------------------------------------
# Robustness: LLM client exceptions
# ---------------------------------------------------------------------------


class _BoomClient:
    """Test double whose `complete` always raises."""

    def complete(self, prompt: str) -> str:  # noqa: ARG002
        raise RuntimeError("simulated transport failure")


class TestLLMClientFailureFallback:
    """A client that raises must NOT crash the narration."""

    def test_section_falls_back_to_skeleton(self, bangalore_reading):
        out = narrate_reading(
            bangalore_reading,
            mode="section",
            section="current_mahadasha",
            client=_BoomClient(),
        )
        assert out.llm_used is False
        assert out.sections["current_mahadasha"].strip()

    def test_full_mode_falls_back_for_every_section(self, bangalore_reading):
        out = narrate_reading(
            bangalore_reading, mode="full", client=_BoomClient(),
        )
        assert out.llm_used is False
        for name in NARRATIVE_SECTIONS:
            assert out.sections[name].strip()


# ---------------------------------------------------------------------------
# Lazy-import discipline
# ---------------------------------------------------------------------------


class TestLazyImportDiscipline:
    """sentence_transformers must NOT be loaded by importing the narrative
    module. RAG citations are read from the already-enriched Finding blocks."""

    def test_sentence_transformers_not_loaded(self):
        """Re-importing app.reading.narrative does not load heavy deps."""
        # Pop any prior import of sentence_transformers from sys.modules to
        # be certain the assertion below isn't trivially satisfied.
        sys.modules.pop("sentence_transformers", None)

        # Force reload of the narrative package.
        for mod in list(sys.modules):
            if mod.startswith("app.reading.narrative"):
                sys.modules.pop(mod, None)

        import app.reading.narrative  # noqa: F401

        assert "sentence_transformers" not in sys.modules, (
            "narrative module must not load sentence_transformers at import"
        )
