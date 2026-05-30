# astro

FastAPI Vedic & Nadi astrology engine. Sidereal Lahiri D1/D9/D10 charts via
[`pyswisseph`](https://github.com/astrorigin/pyswisseph), Vimshottari Mahadasha
calendar dates computed in Julian-Day arithmetic, and an in-process asyncio
Nadi Transit Daemon that reconciles real-time planetary positions against
stored natal charts on a configurable interval.

## Requirements

- Python 3.12+
- pyswisseph 2.10+
- SQLite (default) or PostgreSQL

## Install

```
pip install -r requirements.txt
```

## Run

```
uvicorn app.main:app --reload
```

The default database is SQLite at `./astro.db` with WAL journaling enabled for
concurrent read/write between the API and the daemon. Override for Postgres:

```
DATABASE_URL=postgresql://user:pass@host/astro_db uvicorn app.main:app
```

The URL prefix is rewritten to `postgresql+asyncpg://` automatically.

## Test

```
pytest --cov=app --cov-report=term-missing
```

72 tests, ~84% line coverage as of Phase 2 close.

## Configuration

| Env var                          | Default                              | Purpose |
| -------------------------------- | ------------------------------------ | ------- |
| `DATABASE_URL`                   | `sqlite+aiosqlite:///./astro.db`     | Async DB connection string. |
| `DAEMON_ENABLED`                 | `true`                               | Whether the transit daemon starts on FastAPI lifespan. |
| `DAEMON_CHECK_INTERVAL_SECONDS`  | `3600`                               | Daemon cycle period. |
| `TRANSIT_ORB_DEGREES`            | `3.0`                                | Orb (in degrees) for upgrading a conjunction to `is_exact=True`. Whole-sign drishti fires regardless of orb. |

## Endpoints

### Public
- `POST /chart/calculate` — stateless: compute D1/D9/D10 + Lagna + current Mahadasha for given birth data.

### Auth flow (Google OAuth)
- `GET /auth/google/login` → 302 to Google's consent screen.
- `GET /auth/google/callback` → exchanges code for token, upserts an `Account`, returns `{ access_token, token_type, account }` as JSON.
- `GET /auth/me` → returns the authenticated `Account` (Bearer token required).

### Auth-gated (require `Authorization: Bearer <jwt>`)
- `POST /profiles` — persist a `UserProfile` + natal chart owned by the current account. Rate-limited per account (default 30/min).
- `GET /profiles/{user_id}/transits` — list active transit alerts for a profile. Returns 404 (not 403) if the profile belongs to another account, to avoid leaking existence.

## Auth setup

1. Create OAuth credentials at <https://console.cloud.google.com/apis/credentials>. Choose **Web application** as the type.
2. Add `http://localhost:8000/auth/google/callback` (or your deployment URL) to the client's Authorized redirect URIs.
3. `cp .env.example .env` and fill in `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and a fresh `SECRET_KEY`.
4. `uvicorn app.main:app --reload`, visit `http://localhost:8000/auth/google/login` in a browser, sign in, copy the JWT from the callback response, and use it for subsequent `/profiles` calls.

## Status

Phase 3 in progress (auth shipped; ascendant/houses shipped). Antardasha
sub-periods, rate-limit refinements, and a frontend are the next milestones.

## App Reading — Kundli Analysis System

A deterministic Vedic-astrology engine that produces a complete kundli
analysis as structured JSON given DOB + time + place.

### Quick start

```
py -3.12 -m app.reading.cli --dob=1990-07-15 --time=12:00 --tz=+05:30 \
    --lat=12.97 --lon=77.59 --out=reading.json
```

### Documentation

- [CLI reference](docs/reading/cli-reference.md) — synopsis, flags, exit codes, worked examples.
- [JSON output schema](docs/reading/json-schema.md) — human-readable contract for downstream consumers.
- [JSON Schema (machine)](docs/reading/json-schema.json) — auto-generated from Pydantic; regenerate with `py -3.12 scripts/generate_schema_json.py`.
- [Doctrine decisions lockfile](docs/doctrine-decisions.md) — the 16 D-N locked choices.
- [Architecture spec](docs/superpowers/specs/2026-05-27-kundli-analysis-system-design.md).

### Doctrine compliance

- 16 doctrine decisions locked (D-1 through D-16) in the lockfile.
- Quarterly doctrine audit via the `bphs-doctrine-reviewer` agent — staged
  by `.github/workflows/doctrine-audit.yml` (cron only, not a blocking CI
  gate per spec Section 7); verdicts filed under `docs/audits/`.
- Anti-prediction-trap discipline: Tier-3 modules carry mandatory
  Methodology declarations and never auto-pick winners between disputed
  doctrines.
