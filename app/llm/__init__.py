"""LLM narrative layer — Ollama-backed natural-language interpretation of
Vedic charts. Optional: when OLLAMA_ENABLED is False (the default), the
interpreter falls back to a deterministic template renderer so the
/interpret endpoints never depend on an external service."""
