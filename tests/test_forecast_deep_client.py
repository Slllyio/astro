"""Tests for the OLLAMA_MODEL_DEEP fallthrough logic.

The forecast route splits LLM workload between a "fast" model (daily
summary, called many times) and a "deep" model (event_text, called fewer
times but benefits from better reasoning). When OLLAMA_MODEL_DEEP is
empty, the deep client must collapse to the fast client so single-model
deployments work without config changes.
"""
from __future__ import annotations

import pytest

from app.api.forecast_routes import _deep_client_or
from app.core import config
from app.llm.client import OllamaClient


def _make_client(model: str = "qwen2.5:latest") -> OllamaClient:
    return OllamaClient(
        host="http://localhost:11434", model=model, timeout_seconds=30.0,
    )


class TestDeepClientFallthrough:
    def test_none_fast_client_returns_none(self) -> None:
        """If LLM is disabled (fast client is None), deep is also None.
        Caller doesn't need to special-case this."""
        assert _deep_client_or(None) is None

    def test_empty_deep_model_returns_same_fast_client(
        self, monkeypatch,
    ) -> None:
        """Default config has OLLAMA_MODEL_DEEP='' → no model split → deep
        client IS the fast client (no extra object allocation)."""
        monkeypatch.setattr(config.settings, "OLLAMA_MODEL_DEEP", "")
        fast = _make_client()
        deep = _deep_client_or(fast)
        assert deep is fast

    def test_whitespace_only_deep_model_treated_as_empty(
        self, monkeypatch,
    ) -> None:
        """A misconfigured `OLLAMA_MODEL_DEEP="   "` (e.g. from a .env
        file) must not produce a separate broken client. Trim and treat
        as empty."""
        monkeypatch.setattr(config.settings, "OLLAMA_MODEL_DEEP", "   ")
        fast = _make_client()
        deep = _deep_client_or(fast)
        assert deep is fast

    def test_deep_model_equal_to_fast_returns_same_client(
        self, monkeypatch,
    ) -> None:
        """If a deployer sets both to the same value (redundant but valid),
        reuse the fast client rather than spinning up a duplicate."""
        monkeypatch.setattr(config.settings, "OLLAMA_MODEL", "qwen2.5:latest")
        monkeypatch.setattr(config.settings, "OLLAMA_MODEL_DEEP", "qwen2.5:latest")
        fast = _make_client("qwen2.5:latest")
        deep = _deep_client_or(fast)
        assert deep is fast

    def test_distinct_deep_model_builds_new_client(
        self, monkeypatch,
    ) -> None:
        """Different model name → new OllamaClient with the deep model
        and the longer (DEEP_TIMEOUT) timeout."""
        monkeypatch.setattr(config.settings, "OLLAMA_MODEL", "qwen2.5:latest")
        monkeypatch.setattr(config.settings, "OLLAMA_MODEL_DEEP", "gemma4:31b")
        monkeypatch.setattr(config.settings, "OLLAMA_DEEP_TIMEOUT_SECONDS", 180.0)
        fast = _make_client("qwen2.5:latest")
        deep = _deep_client_or(fast)
        assert deep is not fast
        assert deep is not None
        assert deep.model == "gemma4:31b"
        # Deep client must use the deep timeout, not the fast one
        assert deep.timeout_seconds == 180.0
