from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Vedic & Nadi Astrology API"
    API_V1_STR: str = "/api/v1"

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
    SECRET_KEY: str = "dev-only-not-secret-replace-in-production"
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

    # extra="forbid" makes Settings(...) instantiation reject unknown kwargs.
    # It does NOT scan os.environ for unknown keys — pydantic-settings only
    # reads vars matching declared fields — so unrelated env vars (PATH etc.)
    # are unaffected. This is a hygiene knob that catches typos in tests and
    # explicit instantiation.
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="forbid")


settings = Settings()
