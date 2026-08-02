"""Reasoning-model support in `OllamaClient` — `app/llm/client.py`.

Found live 2026-08-03 while measuring whether a larger local model has better citation
discipline than the 1.5B student: `gemma4:12b` advertises `thinking` in its `/api/show`
capabilities, and on a ~3.1k-token evidence prompt it spent its ENTIRE token budget in the
thinking channel — `done_reason="length"`, `eval_count` 957 then 5053, and an EMPTY `response`
every single time. The client raises `OllamaUnavailable` on an empty response, so every answer
silently degraded to the deterministic fallback and the whole 35-minute run scored zero.

`think=False` fixed it outright: 252 tokens, `done_reason="stop"`, a clean grounded answer.
Both knobs stay OUT of the payload unless set, so non-reasoning models are untouched.
"""
from __future__ import annotations

import json

import httpx
import pytest

from app.llm.client import OllamaClient, OllamaUnavailable


class _Capture:
    """Records the JSON body of the last POST and replies with a canned generation."""

    def __init__(self, response: str = "ok"):
        self.body: dict = {}
        self._response = response

    def __call__(self, url, json=None, timeout=None):      # noqa: A002 — httpx's kwarg name
        self.body = json
        # `raise_for_status()` needs a bound request, so build a real one.
        return httpx.Response(200, json={"response": self._response},
                              request=httpx.Request("POST", url))


class TestThinkingOptions:
    def test_payload_is_unchanged_when_neither_option_is_set(self, monkeypatch):
        """A plain model must see exactly the payload it always saw."""
        cap = _Capture()
        monkeypatch.setattr(httpx, "post", cap)
        OllamaClient("http://x", "qwen2.5:1.5b").complete("hi")
        assert cap.body == {"model": "qwen2.5:1.5b", "prompt": "hi", "stream": False}

    def test_think_false_is_sent_for_reasoning_models(self, monkeypatch):
        cap = _Capture()
        monkeypatch.setattr(httpx, "post", cap)
        OllamaClient("http://x", "gemma4:12b", think=False).complete("hi")
        assert cap.body["think"] is False

    def test_num_ctx_rides_in_options(self, monkeypatch):
        """Evidence prompts run ~3.1k tokens; the 4k default leaves almost no room to answer."""
        cap = _Capture()
        monkeypatch.setattr(httpx, "post", cap)
        OllamaClient("http://x", "gemma4:12b", num_ctx=8192).complete("hi")
        assert cap.body["options"] == {"num_ctx": 8192}

    def test_empty_response_still_raises_so_the_caller_can_fall_back(self, monkeypatch):
        """The symptom that hid the thinking problem must remain loud, not silently empty."""
        monkeypatch.setattr(httpx, "post", _Capture(response="   "))
        with pytest.raises(OllamaUnavailable, match="empty response"):
            OllamaClient("http://x", "gemma4:12b").complete("hi")


class TestReportClientWiring:
    """The report's narrative surfaces must actually RECEIVE the reasoning-model settings —
    without them a 12B answers nothing and every response silently becomes engine prose."""

    def test_report_client_carries_model_num_ctx_and_think(self, monkeypatch):
        from app.api.report_routes import _make_client
        from app.core import config

        monkeypatch.setattr(config.settings, "REPORT_LLM_BACKEND", "ollama")
        monkeypatch.setattr(config.settings, "REPORT_LLM_MODEL", "gemma4:12b")
        monkeypatch.setattr(config.settings, "REPORT_LLM_NUM_CTX", 8192)
        monkeypatch.setattr(config.settings, "REPORT_LLM_THINK", False)
        inner = _make_client("SYSTEM").inner          # SystemPromptWrapper's wrapped client
        assert (inner.model, inner.num_ctx, inner.think) == ("gemma4:12b", 8192, False)

    def test_report_model_falls_through_to_the_fast_default_when_unset(self, monkeypatch):
        """Empty REPORT_LLM_MODEL keeps the prior behaviour — the global OLLAMA_MODEL."""
        from app.api.report_routes import _make_client
        from app.core import config

        monkeypatch.setattr(config.settings, "REPORT_LLM_BACKEND", "ollama")
        monkeypatch.setattr(config.settings, "REPORT_LLM_MODEL", "")
        monkeypatch.setattr(config.settings, "OLLAMA_MODEL", "qwen2.5:1.5b")
        assert _make_client("SYSTEM").inner.model == "qwen2.5:1.5b"
