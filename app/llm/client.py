"""Thin LLM client abstraction.

Single Protocol — `complete(prompt) -> str` — so the rest of the codebase
doesn't pin to a specific provider. Three concrete implementations:
  - OllamaClient:    HTTP POST to a local /api/generate (no SDK dep)
  - AnthropicClient: Claude via the official `anthropic` SDK
  - StubClient:      returns canned text (used in tests + offline fallback)

Adding e.g. an OpenAI client later is a 30-line file that implements the
same Protocol; nothing else in the app changes.
"""
from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

import httpx

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMClient(Protocol):
    """Anything with a sync `complete(prompt) -> str` is an LLM client.

    `runtime_checkable` lets tests do `isinstance(client, LLMClient)` for
    sanity, without forcing concrete implementations into a class hierarchy.
    """

    def complete(self, prompt: str) -> str: ...


class OllamaClient:
    """Calls Ollama's local HTTP API. Synchronous (the route layer offloads
    to a thread). Doesn't pull in the `ollama` Python SDK — a single
    `httpx.post` is enough and keeps the dependency surface minimal.
    """

    def __init__(
        self,
        host: str,
        model: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete(self, prompt: str) -> str:
        """Send a single non-streaming generation request.

        Ollama's /api/generate accepts {model, prompt, stream}. With stream=False
        the response is one JSON object whose `response` field is the full text.
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        try:
            r = httpx.post(url, json=payload, timeout=self.timeout_seconds)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            # Don't crash the request; let the caller decide whether to
            # surface this or render a fallback.
            logger.warning("Ollama request failed: %s", exc)
            raise OllamaUnavailable(str(exc)) from exc

        data = r.json()
        text = data.get("response", "").strip()
        if not text:
            raise OllamaUnavailable("Ollama returned an empty response")
        return text


class OllamaUnavailable(Exception):
    """Raised when the Ollama daemon is unreachable or returns nothing.

    Distinct from a generic exception so the route layer can choose to
    fall back to the deterministic template renderer rather than 500.
    """


class AnthropicUnavailable(Exception):
    """Raised when the Anthropic API is unreachable, returns empty, or the
    API key is missing. Mirrors OllamaUnavailable so route layers can apply
    the same fallback policy regardless of LLM provider."""


class AnthropicClient:
    """Calls Anthropic's Messages API via the official ``anthropic`` SDK.

    Default model is the locked project choice (Sonnet 4.6) per CLAUDE.md
    2026-06-01. The pandit synthesis pipeline expects long context windows
    (~30-50K input tokens) carrying 40-60 retrieved corpus passages, so
    ``max_tokens`` defaults to 8192 to allow narrative-grade output.

    System prompt lives on the constructor because it's per-pipeline, not
    per-call — the LLMClient Protocol stays minimal.

    API key is sourced from ``ANTHROPIC_API_KEY`` environment variable
    (the SDK's default behaviour). Missing key surfaces as
    AnthropicUnavailable rather than crashing import.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        system: str | None = None,
        max_tokens: int = 8192,
        timeout_seconds: float = 120.0,
    ) -> None:
        try:
            import anthropic
        except ImportError as exc:
            raise AnthropicUnavailable(
                "anthropic SDK not installed; pip install anthropic>=0.40"
            ) from exc
        self._anthropic_module = anthropic
        self.model = model
        self.system = system
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        # Lazy-init the client so __init__ doesn't fail when the env var
        # is unset (tests that never call complete() still construct).
        self._client: object | None = None

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        try:
            self._client = self._anthropic_module.Anthropic(
                timeout=self.timeout_seconds,
            )
        except Exception as exc:
            raise AnthropicUnavailable(
                f"Could not initialise Anthropic client: {exc}"
            ) from exc

    def complete(self, prompt: str) -> str:
        """Send a single non-streaming Messages request and return the text.

        The LLMClient Protocol is sync; the FastAPI route layer is expected
        to wrap calls in ``asyncio.to_thread`` (the same pattern the project
        already applies to ephemeris calls).
        """
        self._ensure_client()
        kwargs: dict[str, object] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if self.system:
            kwargs["system"] = self.system
        try:
            response = self._client.messages.create(**kwargs)  # type: ignore[attr-defined]
        except Exception as exc:
            logger.warning("Anthropic request failed: %s", exc)
            raise AnthropicUnavailable(str(exc)) from exc

        # The Messages API returns a list of content blocks; concatenate
        # all text blocks. Non-text blocks (tool_use, etc.) aren't expected
        # for plain completion, so we ignore them defensively.
        text_parts = [
            block.text for block in response.content  # type: ignore[attr-defined]
            if getattr(block, "type", None) == "text"
        ]
        text = "".join(text_parts).strip()
        if not text:
            raise AnthropicUnavailable("Anthropic returned empty text")
        return text


class StubClient:
    """Returns a canned reply for every prompt. Used by tests and as the
    default when OLLAMA_ENABLED is False — combined with the fallback
    template renderer, the /interpret endpoints stay functional even
    without Ollama installed.
    """

    def __init__(self, canned_response: str = "(stub LLM response)") -> None:
        self.canned_response = canned_response
        self.last_prompt: str | None = None  # tests inspect this

    def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.canned_response
