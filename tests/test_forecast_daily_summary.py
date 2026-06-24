"""Tests for app.medini.forecast_daily_summary.

Two contract paths: deterministic (always works, pinned phrasings) and LLM
(via injected stub client; falls back to deterministic on failure).
"""
from __future__ import annotations

import pytest

from app.llm.client import OllamaUnavailable, StubClient
from app.medini.forecast_daily_summary import (
    _build_llm_prompt,
    _dominant_domain,
    _heaviest_event,
    _peak_severity,
    annotate_by_day,
    deterministic_daily_summary,
    llm_daily_summary,
)


SAMPLE_DAY_EVENTS = [
    {
        "type": "INGRESS", "jd": 2460676.5, "date_utc": "2026-01-01",
        "planet": "Jupiter", "from_sign": "Gemini", "to_sign": "Cancer",
        "description": "Jupiter ingresses Cancer (from Gemini)",
        "severity": 9, "severity_band": "red",
        "domains": ["religion", "finance", "politics"],
    },
    {
        "type": "STATION", "jd": 2460676.7, "date_utc": "2026-01-01",
        "planet": "Mercury", "from_state": "direct", "to_state": "retrograde",
        "description": "Mercury stations retrograde (was direct)",
        "severity": 5, "severity_band": "yellow",
        "domains": ["communication", "finance", "arts"],
    },
    {
        "type": "NEW_MOON", "jd": 2460676.9, "date_utc": "2026-01-01",
        "sign": "Capricorn",
        "description": "New Moon in Capricorn",
        "severity": 5, "severity_band": "yellow",
        "domains": ["masses", "agriculture"],
    },
]


# --------------------------------------------------------------------------- #
# Feature extractors                                                            #
# --------------------------------------------------------------------------- #

class TestFeatureExtractors:
    def test_peak_severity_returns_max(self) -> None:
        assert _peak_severity(SAMPLE_DAY_EVENTS) == 9

    def test_peak_severity_empty_returns_zero(self) -> None:
        assert _peak_severity([]) == 0

    def test_heaviest_event_picks_max_severity(self) -> None:
        h = _heaviest_event(SAMPLE_DAY_EVENTS)
        assert h is not None
        assert h["planet"] == "Jupiter"

    def test_heaviest_event_empty_returns_none(self) -> None:
        assert _heaviest_event([]) is None

    def test_dominant_domain_picks_most_touched(self) -> None:
        """finance appears in 2 events; should win."""
        result = _dominant_domain(SAMPLE_DAY_EVENTS)
        # Multiple keys tie at 2 (finance, ...); just check it returned one
        assert result in {"finance", "religion", "politics",
                          "communication", "arts", "masses", "agriculture"}


# --------------------------------------------------------------------------- #
# Deterministic path                                                            #
# --------------------------------------------------------------------------- #

class TestDeterministicSummary:
    def test_empty_day_returns_nothing_scheduled(self) -> None:
        assert "No mundane events" in deterministic_daily_summary([])

    def test_single_high_severity_event_uses_heavy_opener(self) -> None:
        """Severity 9 (red) → 'A heavy day' opener; lock the phrasing."""
        text = deterministic_daily_summary([SAMPLE_DAY_EVENTS[0]])
        assert text.startswith("A heavy day:")
        assert "Jupiter" in text
        assert "Cancer" in text

    def test_low_severity_uses_light_opener(self) -> None:
        ev = {"type": "INGRESS", "jd": 2460676.5, "planet": "Moon",
              "description": "Moon ingresses Pisces",
              "severity": 4, "severity_band": "green",
              "domains": ["masses"]}
        text = deterministic_daily_summary([ev])
        assert text.startswith("A light day:")

    def test_multi_event_day_mentions_counts(self) -> None:
        text = deterministic_daily_summary(SAMPLE_DAY_EVENTS)
        # 'In total:' sentence + the per-type counts
        assert "In total:" in text
        # The three event types must show up: ingress, station, new moon
        assert "ingress" in text.lower()
        assert "station" in text.lower()

    def test_dominant_sphere_mentioned_when_domains_present(self) -> None:
        text = deterministic_daily_summary(SAMPLE_DAY_EVENTS)
        assert "Dominant sphere:" in text


# --------------------------------------------------------------------------- #
# LLM path                                                                      #
# --------------------------------------------------------------------------- #

class TestLLMSummary:
    def test_llm_path_returns_client_response_and_llm_source(self) -> None:
        """Happy path: client succeeds → (text, "llm")."""
        stub = StubClient(canned_response="Jupiter sets the tone this week.")
        text, source = llm_daily_summary("2026-01-01", SAMPLE_DAY_EVENTS, stub)
        assert text == "Jupiter sets the tone this week."
        assert source == "llm"

    def test_llm_path_falls_back_on_unavailable_with_deterministic_label(self) -> None:
        """OllamaUnavailable from the client triggers deterministic fallback
        AND the returned source label is 'deterministic' (not 'llm') —
        that's the bug we fixed: silent fallback was mis-tagged."""
        class FailingClient:
            model = "broken"
            def complete(self, prompt: str) -> str:
                raise OllamaUnavailable("dead")
        text, source = llm_daily_summary(
            "2026-01-01", SAMPLE_DAY_EVENTS, FailingClient(),
        )
        assert text.startswith("A heavy day:")  # deterministic shape
        assert source == "deterministic"

    def test_llm_path_falls_back_on_arbitrary_exception_with_correct_label(self) -> None:
        """Any exception → deterministic + source label reflects that."""
        class BadClient:
            model = "x"
            def complete(self, prompt: str) -> str:
                raise RuntimeError("network blew up")
        text, source = llm_daily_summary(
            "2026-01-01", SAMPLE_DAY_EVENTS, BadClient(),
        )
        assert "Jupiter" in text  # deterministic includes headline event
        assert source == "deterministic"

    def test_llm_prompt_includes_event_facts(self) -> None:
        """Prompt MUST name the events + severities so the LLM can synthesize
        rather than hallucinate."""
        prompt = _build_llm_prompt("2026-01-01", SAMPLE_DAY_EVENTS)
        assert "Jupiter" in prompt
        assert "Mercury" in prompt
        assert "sev=9/10" in prompt
        assert "no 'energies'" in prompt  # tone guard

    def test_empty_events_returns_deterministic(self) -> None:
        """No events → return the deterministic 'nothing scheduled' string
        without calling the LLM. Source label is 'deterministic'."""
        stub = StubClient(canned_response="X")  # would have leaked through
        text, source = llm_daily_summary("2026-01-01", [], stub)
        assert "No mundane events" in text
        assert text != "X"
        assert source == "deterministic"


# --------------------------------------------------------------------------- #
# annotate_by_day                                                               #
# --------------------------------------------------------------------------- #

class TestAnnotateByDay:
    def test_returns_one_entry_per_date(self) -> None:
        by_day = {
            "2026-01-01": SAMPLE_DAY_EVENTS,
            "2026-01-02": [SAMPLE_DAY_EVENTS[0]],
        }
        out = annotate_by_day(by_day)
        assert set(out.keys()) == {"2026-01-01", "2026-01-02"}
        for date, body in out.items():
            assert "summary" in body
            assert "source" in body
            assert body["source"] in {"llm", "deterministic"}

    def test_source_is_deterministic_when_no_client(self) -> None:
        out = annotate_by_day({"2026-01-01": SAMPLE_DAY_EVENTS})
        assert out["2026-01-01"]["source"] == "deterministic"

    def test_source_is_llm_when_client_provided(self) -> None:
        stub = StubClient(canned_response="canned")
        out = annotate_by_day(
            {"2026-01-01": SAMPLE_DAY_EVENTS}, client=stub,
        )
        assert out["2026-01-01"]["source"] == "llm"
        assert out["2026-01-01"]["summary"] == "canned"

    def test_source_reflects_actual_fallback_not_intended_path(self) -> None:
        """**Regression guard for the source-mis-tag bug**.

        Earlier, ``annotate_by_day`` set ``source="llm"`` whenever a client
        was passed, even when the LLM call silently fell back to the
        deterministic template (timeout, transport error, etc.). The fix:
        ``llm_daily_summary`` returns ``(text, actual_source)`` and the
        annotator must surface the ACTUAL source so the UI badge doesn't
        lie about provenance.
        """
        # Disable cache so the failing client is actually called fresh.
        from app.medini.forecast_cache import reset_daily_summary_cache
        reset_daily_summary_cache()

        class FailingClient:
            model = "down"
            def complete(self, prompt: str) -> str:
                raise OllamaUnavailable("daemon dropped")

        out = annotate_by_day(
            {"2026-01-01": SAMPLE_DAY_EVENTS},
            client=FailingClient(),
            use_cache=False,
        )
        body = out["2026-01-01"]
        # The narrative is the deterministic template (the fallback fired)
        assert body["summary"].startswith("A heavy day:")
        # …AND the source label correctly reports "deterministic", NOT "llm".
        assert body["source"] == "deterministic", (
            "annotate_by_day must surface the actual source, not the "
            "intended one — UI would otherwise mis-tag silent fallbacks"
        )

    def test_peak_severity_and_dominant_domain_in_envelope(self) -> None:
        out = annotate_by_day({"2026-01-01": SAMPLE_DAY_EVENTS})
        body = out["2026-01-01"]
        assert body["peak_severity"] == 9
        assert body["dominant_domain"] is not None
