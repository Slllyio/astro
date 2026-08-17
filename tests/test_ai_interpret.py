"""Tests for the walled AI-interpretation layer (labeled LLM speculation, NOT the engine).

Pins the three contract points: the disclaimer ships on every response, the harmful-category
exclusion is enforced in CODE on the model's output (and scrubbed from its input), and the
panel reports itself unavailable — never engine-authored speculation — when the model is off.
"""
from __future__ import annotations

import pytest

from app.llm.ai_interpret import (
    AI_INTERP_SYSTEM,
    DISCLAIMER,
    TOPIC_DEFERRAL,
    build_interp_prompt,
    excluded_topic,
)
from app.llm.report_explainer import Evidence, Fact

_BIRTH = {
    "year": 1990, "month": 7, "day": 15, "hour": 12, "minute": 0,
    "latitude": 12.97, "longitude": 77.59, "tz_offset": 5.5, "ayanamsa": "lahiri",
}


def _ev(*texts: str) -> Evidence:
    return Evidence(scope="digest",
                    facts=tuple(Fact(n=i + 1, text=t) for i, t in enumerate(texts)))


class TestExcludedTopics:
    def test_selfharm_illness_and_decree_death_are_caught(self):
        """The retained exclusions (2026-08-17 prediction-unblock, user decision):
        self-harm and serious-illness vocabulary, plus decree-voiced death timing.
        Death/lifespan/maraka in the classical indication idiom was LIFTED."""
        for bad in ("Your death around 62 approaches.",
                    "thoughts of suicide",
                    "a terminal illness shadow"):
            assert excluded_topic(bad) is not None, f"missed: {bad}"

    def test_lifted_indication_idiom_passes(self):
        """Span-band and maraka vocabulary in indication idiom no longer defers
        (2026-08-17 user decision — the assistant's contrary recommendation and the
        user's override are recorded in DOCTRINE_BACKLOG 'prediction unblock')."""
        for ok in ("This speaks to a long LIFESPAN.",
                   "the maraka planets gather",
                   "the span reads at the purna band"):
            assert excluded_topic(ok) is None, f"over-blocked: {ok}"

    def test_chart_vocabulary_is_not_a_false_positive(self):
        """Cancer the rasi and the 8th house are legitimate chart words — never filtered."""
        for ok in ("The Moon in Cancer inclines you toward home.",
                   "The 8th house speaks of transformation and depth.",
                   "A season of upheaval invites resilience."):
            assert excluded_topic(ok) is None, f"false positive: {ok}"

    def test_prompt_input_is_scrubbed(self):
        """House 8's standard label is relabeled and longevity facts are dropped from the
        model's input, so the model is never fed the vocabulary the output filter rejects."""
        ev = _ev("House 8 (longevity & upheaval) is contested.",
                 "Longevity class: madhya (33-66 years).",
                 "House 10 (career & status) is favourable.")
        prompt = build_interp_prompt(ev, "gentle")
        assert "transformation & upheaval" in prompt
        # 2026-08-17 unblock: longevity facts are no longer dropped from the input —
        # the panel may reflect on span in indication idiom.
        assert "madhya" in prompt
        assert "career & status" in prompt

    def test_system_prompt_carries_the_hard_limits(self):
        """The wall is stated in the prompt too (defence in depth with the code filter)."""
        low = AI_INTERP_SYSTEM.lower()
        assert "never address serious" in low
        assert "suicide" in low and "self" in low
        assert "never as a decree of a dated death" in low
        assert "not the engine" in low.replace("\\\n", "")


class TestAiInterpretRoute:
    async def test_disabled_model_reports_unavailable_with_disclaimer(self, client):
        """LLM off: the panel says unavailable — the engine never authors speculation."""
        resp = await client.post("/report/ai-interpret", json=_BIRTH)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["unavailable"] is True and body["text"] is None
        assert body["disclaimer"] == DISCLAIMER

    async def test_served_interpretation_carries_disclaimer(self, client, monkeypatch):
        """A clean model answer is served verbatim WITH the disclaimer field."""
        import app.api.report_routes as rr
        from app.core.config import settings
        from app.llm.client import StubClient
        monkeypatch.setattr(settings, "REPORT_LLM_ENABLED", True)
        monkeypatch.setattr(rr, "_make_client",
                            lambda system, **kwargs: StubClient("A reflective chart reading."))
        resp = await client.post("/report/ai-interpret", json={**_BIRTH, "register": "bold"})
        body = resp.json()
        assert resp.status_code == 200
        assert body["text"] == "A reflective chart reading."
        assert body["register"] == "bold"
        assert body["disclaimer"] == DISCLAIMER

    async def test_excluded_topic_in_output_is_replaced_whole(self, client, monkeypatch):
        """A model answer touching death/lifespan is REPLACED by the fixed deferral — the
        code wall, not the prompt, is the guarantee."""
        import app.api.report_routes as rr
        from app.core.config import settings
        from app.llm.client import StubClient
        monkeypatch.setattr(settings, "REPORT_LLM_ENABLED", True)
        monkeypatch.setattr(rr, "_make_client",
                            lambda system, **kwargs: StubClient("Wealth flows, but death around 60 looms."))
        resp = await client.post("/report/ai-interpret", json=_BIRTH)
        body = resp.json()
        assert body["deferred"] is True
        assert body["text"] == TOPIC_DEFERRAL
        assert "looms" not in body["text"]              # none of the model's text survives

    async def test_register_is_validated(self, client):
        resp = await client.post("/report/ai-interpret",
                                 json={**_BIRTH, "register": "prophetic"})
        assert resp.status_code == 422
