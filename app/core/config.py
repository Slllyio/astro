from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Placeholder SECRET_KEY shipped in .env.example. Production must override
# this — the post-init validator below refuses to start if ENVIRONMENT is
# not "dev" and this string is still in use.
_DEV_PLACEHOLDER_SECRET = "dev-only-not-secret-replace-in-production"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Vedic & Nadi Astrology API"
    API_V1_STR: str = "/api/v1"

    # Deployment marker. Used by the SECRET_KEY validator + any future
    # environment-conditional logic (e.g., debug toolbar, verbose tracebacks).
    # Local dev defaults to "dev"; staging/prod manifests MUST set this
    # explicitly so misconfiguration fails loudly, not silently.
    ENVIRONMENT: Literal["dev", "staging", "prod"] = "dev"

    # Defaulting to SQLite for prototype.
    # Swap to postgresql://user:password@localhost/astro_db (engine adapts the prefix to asyncpg).
    DATABASE_URL: str = "sqlite+aiosqlite:///./astro.db"

    DAEMON_ENABLED: bool = True
    DAEMON_CHECK_INTERVAL_SECONDS: int = 3600
    TRANSIT_ORB_DEGREES: float = 3.0

    # Vendored Flask portal mounted at /portal/. Disabled in tests/CI so the
    # skyfield ephemeris (~16MB download) doesn't fire on every test session.
    PORTAL_ENABLED: bool = True

    # Auth & sessions. SECRET_KEY signs JWTs AND encrypts the OAuth state
    # cookie used by authlib during the Google redirect dance. Using one
    # secret for both is acceptable for a prototype; in production these
    # should be separate so a compromise of one doesn't grant the other.
    # Override with `SECRET_KEY=...` in .env or the deployment manifest.
    # The post-init validator REFUSES TO START in staging/prod if the
    # placeholder is still present.
    SECRET_KEY: str = _DEV_PLACEHOLDER_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_TTL_SECONDS: int = 86400 * 7  # 7 days

    # Google OAuth. Empty defaults let the app boot for tests/CI without
    # real credentials; the /auth/google/* routes will fail-fast if hit
    # while these are blank, but unauthenticated paths still work.
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # Rate-limit defaults. Overridable per-route via slowapi decorator strings.
    RATE_LIMIT_PROFILES_PER_MINUTE: int = 30
    RATE_LIMIT_AUTH_LOGIN_PER_MINUTE: int = 60
    RATE_LIMIT_AUTH_CALLBACK_PER_MINUTE: int = 10

    # Ollama LLM narrative layer. Disabled by default so CI / fresh checkouts
    # serve deterministic-template fallbacks without needing a local Ollama
    # daemon. Set OLLAMA_ENABLED=true and run `ollama serve` to switch to LLM
    # narratives. The default model is llama3.1; users can swap to qwen2.5,
    # phi3, etc. via the env var.
    OLLAMA_ENABLED: bool = False
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    OLLAMA_TIMEOUT_SECONDS: float = 30.0

    # Optional "deep" model override for layers that benefit from a more
    # capable (slower) model — currently only forecast event_text uses it.
    # Daily summaries stay on OLLAMA_MODEL (fast) because they're called
    # many times per request; per-event synthesis is called fewer times
    # AND benefits from better reasoning across multi-source citations.
    # Empty string = fall through to OLLAMA_MODEL (no split).
    # Timeout doubled because deep models take longer.
    OLLAMA_MODEL_DEEP: str = ""
    OLLAMA_DEEP_TIMEOUT_SECONDS: float = 120.0

    # Knowledge-library RAG citations attached to /interpret responses.
    # Disabled by default so tests/CI don't pay the embeddings load cost
    # (~2-3s + ~150MB of RAM) on every interpret call. Set true when the
    # RAG index has been built locally and you want chart narratives to
    # ship with grounding citations. Failures are always swallowed —
    # citations being broken never breaks chart interpretation.
    INTERPRET_CITATIONS_ENABLED: bool = False
    INTERPRET_CITATIONS_TOP_N: int = 3

    # Grounded LLM explainer / Q&A over the detailed report (/report/explain, /report/ask).
    # Disabled by default: fresh checkouts and CI serve the deterministic fallback (the
    # report's own plain prose) without needing an ANTHROPIC_API_KEY. Set true (and provide
    # the key) to enable the Sonnet-backed grounded explainer. The explainer NEVER generates a
    # verdict — it only translates the engine's already-computed, already-cited findings.
    REPORT_LLM_ENABLED: bool = False
    # Minimum share of sentences that must carry a VALID [Fact N]/[Ref N] anchor for an LLM
    # answer to be served at all; below this (or on any forbidden move / fabricated citation /
    # bad anchor) the route REFUSES the LLM text and serves the deterministic fallback instead.
    # 0.8 is deliberately strict — a safety-critical layer that could put words in Raman's mouth.
    REPORT_LLM_GROUNDING_MIN: float = 0.8

    # extra="forbid" makes Settings(...) instantiation reject unknown kwargs.
    # It does NOT scan os.environ for unknown keys — pydantic-settings only
    # reads vars matching declared fields — so unrelated env vars (PATH etc.)
    # are unaffected. This is a hygiene knob that catches typos in tests and
    # explicit instantiation.
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="forbid")

    @model_validator(mode="after")
    def _enforce_production_secret(self) -> "Settings":
        """Fail fast in staging/prod if SECRET_KEY is still the dev placeholder.

        This catches the most common deploy mistake: shipping an .env that
        was copied from .env.example without rotating the secret. JWT and
        the OAuth session cookie both depend on this; in production a
        leaked placeholder forges arbitrary identities and session state.
        """
        if self.ENVIRONMENT != "dev" and self.SECRET_KEY == _DEV_PLACEHOLDER_SECRET:
            raise ValueError(
                f"SECRET_KEY is the dev placeholder but ENVIRONMENT={self.ENVIRONMENT}. "
                "Generate a strong secret (e.g. `python -c \"import secrets; print(secrets.token_urlsafe(64))\"`) "
                "and set SECRET_KEY in the deployment env."
            )
        return self


settings = Settings()
