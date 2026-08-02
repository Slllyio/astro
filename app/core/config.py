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
    # narratives. Default model matches the locally-installed quick-share model
    # (2026-07-28); swap to llama3.1, phi3, or the fine-tuned astro-analyst via
    # the env var.
    OLLAMA_ENABLED: bool = False
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:1.5b"
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

    # Model override for the Hindi translation pass only (report_routes._translation_client).
    # Live-tested 2026-07-29: the narrow astro-analyst LoRA (1.5B, fine-tuned only on English
    # chart analysis) cannot produce Hindi at all — a capability gap, not a prompt bug — while
    # a larger stock local model (e.g. gemma4:12b) translates correctly. Empty string = fall
    # through to OLLAMA_MODEL (same behavior as before this setting existed).
    OLLAMA_MODEL_TRANSLATE: str = ""

    # ── the report narrative model (measured 2026-08-03) ────────────────────────────────
    # Kept SEPARATE from OLLAMA_MODEL on purpose: OLLAMA_MODEL is the FAST model used by
    # high-frequency paths (daily summaries are called many times per request), so pointing it
    # at a 12B would slow those badly. This override applies only to the report's grounded
    # narrative surfaces, which are called a handful of times per report.
    #
    # Why a stock 12B rather than the fine-tuned 1.5B: measured head-to-head on the same 34
    # held-out rows, scored by the same guard the serving path uses —
    #   citation-clean answers   gemma4:12b 85.3%  |  astro-analyst LoRA 44.1%  |  Claude 91.2%
    #   guard pass               88.2%             |  73.5%                     |  100%
    #   crisp pass               70.6%             |  47.1%                     |  100%
    #   mis-attributed / answer  0.18              |  1.21                      |  0.09
    # The 12B wins on every axis WITHOUT any fine-tuning, including the two the LoRA was
    # trained for (voice, crispness), for ~4s more per answer (11.6s vs 7.6s measured on the
    # same prompt). The 1.5B is capacity-limited for citation precision across ~20 facts; that
    # is a size problem no corpus fixes. Empty string = fall through to OLLAMA_MODEL.
    REPORT_LLM_MODEL: str = "gemma4:12b"
    # Evidence prompts run ~3.1k tokens, so Ollama's 4k default leaves almost nothing for the
    # answer. 8192 gives the model room to actually write one.
    REPORT_LLM_NUM_CTX: int = 8192
    # Reasoning models (gemma4:12b advertises "thinking" in /api/show capabilities) otherwise
    # spend their ENTIRE token budget in the thinking channel on a long prompt and return
    # done_reason="length" with an EMPTY response — which the client raises as
    # OllamaUnavailable, silently degrading every single answer to the deterministic fallback.
    # Verified harmless on non-reasoning models (qwen2.5:1.5b ignores it and answers normally).
    REPORT_LLM_THINK: bool = False
    # A 12B on this class of hardware takes ~12s for a report answer; the 30s general default
    # leaves too little headroom for a longer section.
    REPORT_LLM_TIMEOUT_SECONDS: float = 120.0
    # A translation pass rewrites a full paragraph (not the short per-item calls the fast
    # default model is sized for) and, when OLLAMA_MODEL_TRANSLATE points at a larger model,
    # runs measurably slower besides — live-tested 2026-07-29: gemma4:12b took ~132s to
    # translate a full ~3.4K-character report explanation on the dev machine's hardware
    # (a 120s cap clipped it mid-generation); 180s leaves headroom for longer sections.
    # Longer timeout applies regardless of which model ends up serving the call.
    OLLAMA_TRANSLATE_TIMEOUT_SECONDS: float = 180.0

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
    # Which provider backs the grounded LLM surfaces (/report/explain, /report/insights,
    # /report/ask, and the walled /report/ai-interpret). "ollama" (default) keeps every model
    # call LOCAL — a shared instance can never spend the Anthropic key — served by
    # OLLAMA_HOST/OLLAMA_MODEL; if the Ollama daemon is down the routes degrade to the
    # deterministic fallback. "anthropic" restores the Claude-backed explainer (needs
    # ANTHROPIC_API_KEY). Re-enabled 2026-07-29: insights/explain were briefly made
    # deterministic-only during the share-the-app cost cut (when the only backend was paid
    # Anthropic); that cut no longer applies now that the app's own fine-tuned local model
    # serves for free, so all four surfaces use this backend again.
    REPORT_LLM_BACKEND: Literal["anthropic", "ollama"] = "ollama"
    # Optional adversarial self-critique over the grounded explainer/synthesis output: the model
    # drafts, an honesty-tuned critic checks that every claim is entailed by a [Fact N] and that no
    # prediction / new verdict / "these findings reinforce each other" compound claim leaked, then
    # the model refines once. A QUALITY pass, not the safety net — `refusal_reason` remains the
    # final gate regardless. Off by default because it costs 2-3x the LLM calls when enabled —
    # this was a real $ concern on the "anthropic" backend; on "ollama" (the default since
    # 2026-07-29) it costs 2-3x the LOCAL latency, not money, so it's worth trying more freely.
    REPORT_LLM_CRITIC_ENABLED: bool = False
    # Minimum share of PARAGRAPHS that must carry a VALID [Fact N]/[Ref N] anchor for an LLM
    # answer to be served; below this (or on any forbidden move / fabricated citation / bad
    # anchor) the route REFUSES the LLM text and serves the deterministic fallback. The hard
    # guards (prediction language, fabricated/absent citations) are the primary safety net and
    # are absolute; this ratio is the "did the model go off-script" floor. 0.6 is tuned to real
    # Sonnet output — which anchors each claim-cluster but writes benign unanchored framing/
    # summary paragraphs, so a stricter 0.8 false-refused genuinely-cited answers in live tests.
    REPORT_LLM_GROUNDING_MIN: float = 0.6

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
