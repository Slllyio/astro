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

    # extra="forbid" makes Settings(...) instantiation reject unknown kwargs.
    # It does NOT scan os.environ for unknown keys — pydantic-settings only
    # reads vars matching declared fields — so unrelated env vars (PATH etc.)
    # are unaffected. This is a hygiene knob that catches typos in tests and
    # explicit instantiation.
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="forbid")


settings = Settings()
