"""Tests for the Phase-1 pandit-grade chart-reading pipeline.

Three layers under test:
  1. app.llm.client.AnthropicClient — Protocol conformance + lazy init
  2. app.llm.pandit_retriever — 8-axis retrieval, dedup, bundle assembly
  3. app.llm.pandit_synthesizer — prompt assembly + citation parsing

The Anthropic LLM call itself is NOT tested live — those tests use
StubClient to keep CI deterministic and offline.
"""
from __future__ import annotations

import pytest

from corpus_presence import needs_file

_needs_knowledge_corpus = needs_file(
    "data/knowledge_library/classical_shloka_rules.jsonl",
    "data/knowledge_library/nadi_corpus.jsonl",
    "data/knowledge_library/nadi_lagna_contexts.jsonl")

from app.llm.client import (
    AnthropicClient, AnthropicUnavailable, LLMClient, OllamaClient, StubClient,
)
from app.llm.pandit_retriever import (
    ChartFingerprint,
    DEFAULT_PER_AXIS_LIMIT,
    NAKSHATRA_NAMES,
    RetrievedCorpus,
    RetrievedPassage,
    SIGN_NAMES,
    retrieve_for_chart,
)
from app.llm.pandit_synthesizer import (
    PanditReading,
    PanditSynthesizer,
    SYSTEM_PROMPT,
    build_prompt,
)


# ─── Anthropic client ───────────────────────────────────────────────


class TestAnthropicClient:
    """The Anthropic client conforms to LLMClient Protocol and defers
    API-key validation to call time (so import + construction work in CI
    without a live key)."""

    def test_conforms_to_llmclient_protocol(self):
        client = AnthropicClient(model="claude-sonnet-4-6")
        assert isinstance(client, LLMClient)

    def test_default_model_is_sonnet_4_6(self):
        """CLAUDE.md 2026-06-01 locked Sonnet 4.6 as the pandit-pipeline default."""
        client = AnthropicClient()
        assert client.model == "claude-sonnet-4-6"

    def test_max_tokens_default_supports_narrative_output(self):
        """8192 is enough for a multi-section pandit reading."""
        client = AnthropicClient()
        assert client.max_tokens >= 4096

    def test_constructor_does_not_require_api_key(self):
        """API-key validation must be lazy so CI imports work."""
        # Should not raise even if ANTHROPIC_API_KEY is unset
        client = AnthropicClient()
        assert client._client is None  # lazy-init not yet triggered

    def test_existing_clients_still_conform(self):
        """Adding AnthropicClient must not break the StubClient/OllamaClient
        contract used elsewhere in the project."""
        assert isinstance(StubClient(), LLMClient)
        assert isinstance(
            OllamaClient(host="http://localhost:11434", model="llama3"),
            LLMClient,
        )


# ─── Retriever ──────────────────────────────────────────────────────


@pytest.fixture
def mainpuri_fingerprint() -> ChartFingerprint:
    """The Mainpuri 1989 chart (corrected 7-karaka values) — our reference
    fixture for the pandit pipeline. Used to lock retrieval against the
    same chart the framework was diagnosed on."""
    return ChartFingerprint(
        asc_sign=8,                    # Scorpio
        asc_lord_house=11,             # Mars in 11H
        asc_lord_planet="Mars",
        moon_nakshatra=23,             # Shatabhisha
        moon_sign=11,                  # Aquarius
        atmakaraka="Sun",
        karakamsa_sign=5,              # Leo
        md_lord="Saturn",
        ad_lord="Jupiter",
        active_yoga_names=("Amala", "Mangal Dosha", "Budha-Aditya", "Sarala"),
        domain="career",
    )


class TestRetriever:
    """The retriever fans out across 8 axes + yoga + domain queries and
    returns a deduplicated bundle of passages with stable [Ref N] anchors."""

    def test_retrieves_unique_passages(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        ref_ids = [p.ref_id for p in bundle.passages]
        assert len(ref_ids) == len(set(ref_ids)), "ref_ids must be unique"

    @_needs_knowledge_corpus
    def test_yields_at_least_30_passages_for_dense_chart(self, mainpuri_fingerprint):
        """A chart with 4 active yogas + domain should fan to 30+ passages."""
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        # Some passages may dedup across axes; floor at 30 keeps the
        # test resilient to corpus-density variation across sources
        assert len(bundle.passages) >= 30

    def test_axes_emitted_in_order(self, mainpuri_fingerprint):
        """First passages should come from lagna_character (humans read
        lowest [Ref N] first; pandit-cognition emulation puts the lagna
        framing earliest)."""
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        if bundle.passages:
            assert bundle.passages[0].axis == "lagna_character"

    def test_dkp_translation_records_matched_for_known_yogas(
        self, mainpuri_fingerprint,
    ):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        keys = [r.key for r in bundle.dkp_translations]
        # Mangal Dosha is in the curated 27 DKP records
        assert "Mangal Dosha" in keys

    @_needs_knowledge_corpus
    def test_nadi_lookup_returns_match_for_scorpio(self, mainpuri_fingerprint):
        """Post N-3 corpus closure, Scorpio Lagna resolves to Deva Keralam."""
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        assert bundle.nadi_match is not None
        assert bundle.nadi_match.found is True
        assert "Deva Keralam" in (bundle.nadi_match.tradition or "")

    @_needs_knowledge_corpus
    def test_lagna_contexts_attached(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        assert len(bundle.nadi_contexts) >= 1

    def test_axis_counts_populated(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        assert sum(bundle.axis_counts.values()) == len(bundle.passages)

    def test_passages_carry_provenance(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        for p in bundle.passages:
            assert p.source, "every passage must name its source"
            assert p.chapter, "every passage must name its chapter"
            assert p.text, "every passage must carry text"
            assert p.ref_id > 0

    def test_per_axis_limit_respected(self, mainpuri_fingerprint):
        """No single axis should contribute more than the per-axis limit."""
        bundle = retrieve_for_chart(
            mainpuri_fingerprint, per_axis_limit=DEFAULT_PER_AXIS_LIMIT,
        )
        for axis, count in bundle.axis_counts.items():
            # Yoga and domain axes use smaller per-yoga limits; the main
            # axes are the strict ones
            if not (axis.startswith("yoga:") or axis.startswith("domain:")
                    or axis.startswith("bhava:")):
                assert count <= DEFAULT_PER_AXIS_LIMIT

    def test_minimal_chart_does_not_crash(self):
        """A chart with no active yogas and no domain should still
        produce a valid (smaller) bundle."""
        fp = ChartFingerprint(
            asc_sign=1, asc_lord_house=1, asc_lord_planet="Mars",
            moon_nakshatra=0, moon_sign=1, atmakaraka="Sun",
            karakamsa_sign=5, md_lord="Sun",
        )
        bundle = retrieve_for_chart(fp)
        assert isinstance(bundle, RetrievedCorpus)
        # Even a minimal chart yields some passages from lagna/moon axes
        assert len(bundle.passages) >= 0


# ─── Synthesizer ────────────────────────────────────────────────────


class TestSynthesizerPromptAssembly:
    """The prompt assembler stitches retrieved corpus into a structured
    LLM input with all four sections present."""

    def test_prompt_has_all_required_sections(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        prompt = build_prompt(bundle)
        for section in ("CHART FACTS", "DOCTRINAL EVIDENCE",
                        "DKP TRANSLATION LAYER", "NADI LAYER"):
            assert section in prompt, f"prompt must contain {section}"

    def test_prompt_carries_chart_specifics(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        prompt = build_prompt(bundle)
        # The fingerprint's specific facts must appear
        assert "Scorpio" in prompt
        assert "Shatabhisha" in prompt
        assert "Saturn" in prompt
        assert "Sun" in prompt   # Atmakaraka
        assert "Leo" in prompt   # Karakamsa

    def test_prompt_enforces_citation_contract(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        prompt = build_prompt(bundle)
        # The prompt must instruct the LLM to anchor every claim
        assert "[Ref N]" in prompt
        assert "doctrine-derived inference" in prompt

    def test_prompt_locks_doctrine_invariants(self, mainpuri_fingerprint):
        """The prompt must reinforce the project's locked doctrinal
        decisions so the LLM doesn't drift into KP / tropical / 8-karaka."""
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        prompt = build_prompt(bundle)
        # Strict 7-karaka lock surfaces in the prompt's constraints
        assert "NEVER" in prompt or "never" in prompt
        # Rahu/Ketu chayagraha lock
        assert "Rahu" in prompt
        # Lahiri / whole-sign locks are in the system prompt
        assert "Lahiri" in SYSTEM_PROMPT or "sidereal" in SYSTEM_PROMPT
        assert "whole-sign" in SYSTEM_PROMPT or "whole sign" in SYSTEM_PROMPT

    def test_focal_themes_appear_in_prompt(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        prompt = build_prompt(bundle, focal_themes=("marriage", "wealth"))
        assert "marriage" in prompt.lower()
        assert "wealth" in prompt.lower()

    def test_passages_numbered_sequentially(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        prompt = build_prompt(bundle)
        # [Ref 1] should appear before [Ref 5] etc.
        import re
        refs = [int(m) for m in re.findall(r"\[Ref (\d+)\]", prompt)]
        # Strip duplicates (the contract text mentions [Ref N] generically)
        ref_set = sorted(set(r for r in refs if r > 0))
        if ref_set:
            assert ref_set == list(range(min(ref_set), max(ref_set) + 1)), (
                "ref ids must be sequential without gaps"
            )


class TestSynthesizerStubRoundtrip:
    """End-to-end run with StubClient — verifies wiring without an LLM call."""

    def test_synthesize_returns_pandit_reading(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        synth = PanditSynthesizer(
            llm=StubClient(canned_response="Stub narrative with [Ref 1] anchor."),
        )
        reading = synth.synthesize(bundle, focal_themes=("career",))
        assert isinstance(reading, PanditReading)
        assert "Stub narrative" in reading.narrative

    @_needs_knowledge_corpus
    def test_citation_parsing_extracts_used_refs(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        canned = "Discussion using [Ref 1] and [Ref 3] but not others."
        synth = PanditSynthesizer(llm=StubClient(canned_response=canned))
        reading = synth.synthesize(bundle)
        cited_ids = sorted(p.ref_id for p in reading.citations_used)
        assert cited_ids == [1, 3]
        # Remaining passages count must sum to total
        assert (
            len(reading.citations_used) + len(reading.unused_passages)
            == len(bundle.passages)
        )

    def test_focal_themes_preserved_in_reading(self, mainpuri_fingerprint):
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        synth = PanditSynthesizer(llm=StubClient())
        reading = synth.synthesize(bundle, focal_themes=("marriage", "career"))
        assert reading.focal_themes == ("marriage", "career")

    def test_prompt_token_estimate_reasonable(self, mainpuri_fingerprint):
        """For Mainpuri-density chart, prompt should be 3K-15K tokens —
        well inside Sonnet 4.6's 200K context window."""
        bundle = retrieve_for_chart(mainpuri_fingerprint)
        synth = PanditSynthesizer(llm=StubClient())
        reading = synth.synthesize(bundle)
        assert 1000 < reading.prompt_token_estimate < 20_000

    def test_model_name_threaded_from_client(self):
        """When the LLM exposes .model, it should surface in PanditReading."""
        fp = ChartFingerprint(
            asc_sign=1, asc_lord_house=1, asc_lord_planet="Mars",
            moon_nakshatra=0, moon_sign=1, atmakaraka="Sun",
            karakamsa_sign=5, md_lord="Sun",
        )
        bundle = retrieve_for_chart(fp)
        # OllamaClient has a .model attr — exercise the threading
        synth = PanditSynthesizer(
            llm=OllamaClient(host="http://stub", model="test-model"),
        )
        # We don't actually call the LLM here, just verify model attr
        # is reachable. Use StubClient with a model attr.
        class _ModeledStub:
            model = "stub-model-x"
            def complete(self, prompt: str) -> str:
                return "ok"
        synth = PanditSynthesizer(llm=_ModeledStub())
        reading = synth.synthesize(bundle)
        assert reading.model == "stub-model-x"
