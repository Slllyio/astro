"""Unit tests for app.medini.forecast_event_text.

Validates the per-event LLM-synthesis layer: prompt construction, gating
on (citations present, client provided), silent failure on LLM error, and
cache integration.
"""
from __future__ import annotations

import pytest

from app.llm.client import OllamaUnavailable, StubClient
from app.medini.forecast_event_text import (
    _build_prompt,
    _event_text_key,
    _parse_mode_marker,
    annotate_events,
    event_text,
    get_event_text_cache,
    reset_event_text_cache,
)


EVENT_WITH_CITATIONS = {
    "type": "INGRESS", "jd": 2460676.5, "date_utc": "2026-01-01",
    "planet": "Jupiter", "to_sign": "Cancer",
    "description": "Jupiter ingresses Cancer (from Gemini)",
    "severity": 9, "domains": ["religion", "finance", "politics"],
    "citations": [
        {"source": "bphs", "title": "BPHS Ch.X",
         "snippet": "Jupiter in Cancer is exalted, bringing prosperity."},
        {"source": "phaladeepika", "title": "Phaladeepika 27",
         "snippet": "When Jupiter enters Cancer..."},
    ],
}

EVENT_WITHOUT_CITATIONS = {
    "type": "STATION", "jd": 2460676.5, "date_utc": "2026-01-01",
    "planet": "Mercury", "to_state": "retrograde",
    "description": "Mercury stations retrograde",
    "severity": 5, "domains": ["communication"],
    "citations": [],
}


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_event_text_cache()
    yield
    reset_event_text_cache()


# --------------------------------------------------------------------------- #
# Prompt construction                                                          #
# --------------------------------------------------------------------------- #

class TestPromptConstruction:
    def test_prompt_names_event_and_severity(self) -> None:
        p = _build_prompt(EVENT_WITH_CITATIONS)
        assert "Jupiter" in p
        assert "Cancer" in p
        assert "9/10" in p

    def test_prompt_includes_verbatim_citation_snippets(self) -> None:
        """The LLM grounds on the snippets — they MUST appear in the prompt."""
        p = _build_prompt(EVENT_WITH_CITATIONS)
        assert "Jupiter in Cancer is exalted" in p
        assert "BPHS Ch.X" in p

    def test_prompt_signals_no_citations_when_empty(self) -> None:
        """When citations are empty, prompt still works; signal explicitly."""
        ev = {**EVENT_WITH_CITATIONS, "citations": []}
        p = _build_prompt(ev)
        assert "CITED DOCTRINE: (none available)" in p

    def test_prompt_tone_guard_present(self) -> None:
        """Lock the tone-guard phrasing — it's what keeps the LLM from
        inventing astrological 'energies' jargon."""
        p = _build_prompt(EVENT_WITH_CITATIONS)
        assert "'energies'" in p
        assert "disclaimers" in p

    def test_prompt_forbids_unsupported_classical_claims(self) -> None:
        """v1 hallucinated 'Moon exalted in Virgo' (wrong — exalted in
        Taurus). The new prompt MUST contain an explicit constraint
        against making exaltation/debilitation/dignity claims without
        a citation backing them — that's the structural fix."""
        p = _build_prompt(EVENT_WITH_CITATIONS)
        for term in ("exaltation", "debilitation", "dignity",
                     "moolatrikona", "rulership"):
            assert term in p.lower(), (
                f"prompt missing constraint against unsupported '{term}' claims"
            )

    def test_prompt_demands_numbered_citation_attribution(self) -> None:
        """LLM is told to anchor each claim with [N] — pin the instruction
        so a future prompt edit can't quietly drop this."""
        p = _build_prompt(EVENT_WITH_CITATIONS)
        # Both the numbered citations themselves and the [N] attribution
        # instruction must be present.
        assert "[1]" in p
        assert "[N]" in p

    def test_prompt_exposes_event_facts_atomically(self) -> None:
        """Event details (type, planet, signs, date) must appear as discrete
        labeled fields, not just embedded in a free-form description.
        This is what stops the LLM from re-interpreting the description."""
        p = _build_prompt(EVENT_WITH_CITATIONS)
        assert "type: INGRESS" in p
        assert "planet: Jupiter" in p
        assert "to_sign: Cancer" in p
        assert "date: 2026-01-01" in p


# --------------------------------------------------------------------------- #
# event_text                                                                   #
# --------------------------------------------------------------------------- #

class TestEventText:
    def test_returns_none_when_no_citations(self) -> None:
        stub = StubClient(canned_response="never reached")
        result = event_text(EVENT_WITHOUT_CITATIONS, stub)
        assert result is None

    def test_returns_grounded_text_with_marker(self) -> None:
        """LLM returns the [GROUNDED]: prefix → event_text strips it and
        returns (text, True)."""
        stub = StubClient(canned_response="[GROUNDED]: Jupiter ingresses Cancer [1].")
        result = event_text(EVENT_WITH_CITATIONS, stub)
        assert result == ("Jupiter ingresses Cancer [1].", True)

    def test_returns_general_text_when_citations_off_topic(self) -> None:
        """[GENERAL]: prefix → event_text returns (text, False) so the UI
        can render the synthesis with a 'not-directly-cited' style."""
        stub = StubClient(
            canned_response="[GENERAL]: Moon ingress to Virgo broadly "
                            "affects public sentiment and agriculture.",
        )
        result = event_text(EVENT_WITH_CITATIONS, stub)
        assert result == (
            "Moon ingress to Virgo broadly affects public sentiment and agriculture.",
            False,
        )

    def test_returns_text_with_unknown_marker_as_none_grounded(self) -> None:
        """Older models or prompt drift may omit the marker; surface the
        text but with grounded=None so the UI can dispatch."""
        stub = StubClient(canned_response="No marker just prose text.")
        result = event_text(EVENT_WITH_CITATIONS, stub)
        assert result == ("No marker just prose text.", None)

    def test_returns_none_when_marker_present_but_no_content(self) -> None:
        """A response of only '[GROUNDED]:' (nothing after) is a malformed
        synthesis — treat as failure, return None."""
        stub = StubClient(canned_response="[GROUNDED]:")
        result = event_text(EVENT_WITH_CITATIONS, stub)
        assert result is None

    def test_returns_none_on_ollama_unavailable(self) -> None:
        class FailingClient:
            model = "broken"
            def complete(self, prompt: str) -> str:
                raise OllamaUnavailable("daemon down")
        result = event_text(EVENT_WITH_CITATIONS, FailingClient())
        assert result is None

    def test_returns_none_on_arbitrary_exception(self) -> None:
        """Any exception — network, parse, timeout — must NOT raise. Returns
        None so the route can omit the field cleanly."""
        class BadClient:
            model = "x"
            def complete(self, prompt: str) -> str:
                raise RuntimeError("everything broke")
        result = event_text(EVENT_WITH_CITATIONS, BadClient())
        assert result is None


# --------------------------------------------------------------------------- #
# annotate_events                                                              #
# --------------------------------------------------------------------------- #

class TestAnnotateEvents:
    def test_no_client_returns_events_unchanged(self) -> None:
        """No LLM client → no-op. Don't crash; just pass through."""
        out = annotate_events([EVENT_WITH_CITATIONS], client=None)
        assert out[0] is EVENT_WITH_CITATIONS  # exact identity preserved

    def test_event_with_citations_gets_event_text_and_grounded_flag(self) -> None:
        stub = StubClient(canned_response="[GROUNDED]: synth claim [1]")
        out = annotate_events([EVENT_WITH_CITATIONS], client=stub)
        assert out[0]["event_text"] == "synth claim [1]"
        assert out[0]["event_text_grounded"] is True

    def test_general_principles_path_sets_grounded_false(self) -> None:
        stub = StubClient(canned_response="[GENERAL]: broad strokes synthesis.")
        out = annotate_events([EVENT_WITH_CITATIONS], client=stub)
        assert out[0]["event_text"] == "broad strokes synthesis."
        assert out[0]["event_text_grounded"] is False

    def test_event_without_citations_left_alone(self) -> None:
        """Per UI dispatch contract: events without citations don't get the
        event_text field added (NOT set to empty string)."""
        stub = StubClient(canned_response="should not be added")
        out = annotate_events([EVENT_WITHOUT_CITATIONS], client=stub)
        assert "event_text" not in out[0]

    def test_does_not_mutate_input_event(self) -> None:
        """Immutability: returned events are new dicts."""
        stub = StubClient(canned_response="synth")
        annotate_events([EVENT_WITH_CITATIONS], client=stub)
        assert "event_text" not in EVENT_WITH_CITATIONS

    def test_cache_speeds_up_repeated_calls(self) -> None:
        """Second annotate of the same events hits the cache."""
        cache = get_event_text_cache()
        stub = StubClient(canned_response="X")
        annotate_events([EVENT_WITH_CITATIONS], client=stub)
        before_misses = cache.misses
        annotate_events([EVENT_WITH_CITATIONS], client=stub)
        # No additional miss on the second pass
        assert cache.misses == before_misses

    def test_cache_disabled_via_kwarg(self) -> None:
        cache = get_event_text_cache()
        stub = StubClient(canned_response="X")
        annotate_events([EVENT_WITH_CITATIONS], client=stub, use_cache=False)
        annotate_events([EVENT_WITH_CITATIONS], client=stub, use_cache=False)
        assert cache.hits == 0
        assert cache.misses == 0


# --------------------------------------------------------------------------- #
# _event_text_key                                                              #
# --------------------------------------------------------------------------- #

class TestParseModeMarker:
    """Marker parser must handle the LLM's expected outputs + drift."""

    def test_grounded_prefix_canonical(self) -> None:
        text, grounded = _parse_mode_marker("[GROUNDED]: synthesis claim.")
        assert text == "synthesis claim."
        assert grounded is True

    def test_general_prefix_canonical(self) -> None:
        text, grounded = _parse_mode_marker("[GENERAL]: broad principles.")
        assert text == "broad principles."
        assert grounded is False

    def test_marker_case_insensitive(self) -> None:
        """Models may emit '[grounded]:' instead of '[GROUNDED]:'."""
        text, grounded = _parse_mode_marker("[grounded]: text")
        assert grounded is True
        text, grounded = _parse_mode_marker("[General]: text")
        assert grounded is False

    def test_missing_colon_still_parsed(self) -> None:
        """Some models drop the colon; we tolerate it."""
        text, grounded = _parse_mode_marker("[GROUNDED] just the body")
        assert grounded is True
        assert text == "just the body"

    def test_no_marker_returns_none_grounded(self) -> None:
        text, grounded = _parse_mode_marker("plain text without marker")
        assert text == "plain text without marker"
        assert grounded is None

    def test_marker_with_leading_whitespace(self) -> None:
        """LLMs sometimes add a newline before the marker — strip + match."""
        text, grounded = _parse_mode_marker("\n  [GROUNDED]: claim")
        assert grounded is True
        assert text == "claim"


class TestKey:
    def test_same_event_and_citations_produce_same_key(self) -> None:
        a = _event_text_key(EVENT_WITH_CITATIONS)
        b = _event_text_key(EVENT_WITH_CITATIONS)
        assert a == b

    def test_citation_reordering_does_not_change_key(self) -> None:
        """Top-N citations from RAG may shuffle slightly between runs; key
        sorts before hashing so cache hits are stable."""
        original = EVENT_WITH_CITATIONS
        reordered = {**original, "citations": list(reversed(original["citations"]))}
        assert _event_text_key(original) == _event_text_key(reordered)

    def test_different_citations_change_key(self) -> None:
        """Re-tagging the corpus that produces different top citations
        MUST invalidate — we want fresh synthesis when evidence changes."""
        modified = {
            **EVENT_WITH_CITATIONS,
            "citations": [
                {"source": "different", "title": "X",
                 "snippet": "completely different passage"},
            ],
        }
        assert _event_text_key(EVENT_WITH_CITATIONS) != _event_text_key(modified)
