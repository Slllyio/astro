"""Thin LLM client abstraction.

Single Protocol — `complete(prompt) -> str` — so the rest of the codebase
doesn't pin to a specific provider. Two concrete implementations:
  - OllamaClient: HTTP POST to a local /api/generate (no SDK dep)
  - StubClient:   returns canned text (used in tests + offline fallback)

Adding e.g. an OpenAI / Anthropic client later is a 30-line file that
implements the same Protocol; nothing else in the app changes.
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
