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

- `POST /chart/calculate` — stateless: compute D1/D9/D10 + current Mahadasha for given birth data.
- `POST /profiles` — persist a user + natal chart in one transaction.
- `GET /profiles/{user_id}/transits` — list active transit alerts for a user.

## Status

Phase 2 complete (persistence + transit daemon). Phase 3 (auth, ascendant /
houses, Antardasha sub-periods) is the next milestone.
