# Resume Notes

Snapshot of the project state as of **2026-04-27**, at commit `b680c6d` (Phase 1 Medini Astrocartography MVP).

## What's shipped

**Three tabs of a unified astrology portal**, all served by a single FastAPI app.

| Tab | Path | What it does |
|---|---|---|
| 1. Nadi (precise natal) | `/chart/calculate`, `/profiles/*`, `/auth/google/*` | Sidereal Lahiri D1–D60, MD/AD/Pratyantar, Lagna+houses, Yogas, Panchanga, BAV/SAV, Avastha, Sade Sati. Google OAuth + JWT. Transit daemon. |
| 2. NumeroAstro | `/portal/*` | Vendored Flask app from [Slllyio/astro-web-portal](https://github.com/Slllyio/astro-web-portal). DOB-only "probability engine" + numerology + BAV-driven karma classification. |
| 3. Medini (Geo-Astrology) | `/medini/*` | **Phase 0**: Kurma Chakra educational widget (`/medini/kurma-widget`) — 9 regions × 27 nakshatras × 5 tattvas on a Leaflet world map. **Phase 1**: Personalized Astrocartography (`/medini/cartography/page`) — 36 planetary lines per chart over the Kurma layer. |

**Test suite**: 514 passing, ~89% coverage, GitHub Actions CI green.

## Run locally

```bash
cd e:/astro
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then visit:
- http://localhost:8000/docs — OpenAPI schema for all endpoints
- http://localhost:8000/medini/kurma-widget — the educational widget
- http://localhost:8000/medini/cartography/page — your astrocartography map (auto-loads with the Bangalore default)
- http://localhost:8000/portal/ — the NumeroAstro Flask sub-app

To run the test suite:

```bash
python -m pytest -q
python -m pytest --cov=app --cov-report=term-missing -q
```

## Pending work (priority order)

1. **LLM Ollama narrative layer**. An agent's plan has already been written to `C:\Users\S.C.C\.claude\plans\phase-2-database-hashed-ritchie-agent-ac1cfc52ab1b0c960.md`. Decisions locked: Ollama backend, hybrid summary+drill-down endpoints, no auth on `/interpret/*`. Re-dispatch a fresh agent against that plan.
2. **Tab 3 Phase 2 — Daily Mundane Forecast**. `/medini/today` page surfacing today's significant ingresses, retrogrades, eclipses, with the activated Kurma regions highlighted. Reuses the existing transit daemon's reconcile loop.
3. **Tab 3 Phase 3 — Eclipse Impact Mapper**. `swe.sol_eclipse_when_glob` + Kurma layer + natal chart impact.
4. **Unified-tabs frontend shell**. Currently each tab is reachable directly via URL but there's no nav between them.
5. **NumeroAstro re-branding**. The vendored portal still says "Stellar Blueprint" in templates — needs surface-level rename.
6. **PDF housekeeping**. `Geo-Astrological Planetary Intelligence Engine.pdf` was accidentally committed via `git add -A`. Repo is private so low-stakes, but cleaner to remove + add `*.pdf` to `.gitignore`.

## Configuration the next dev needs to know

`.env` (gitignored) holds local secrets. See `.env.example` for the full list. Notable:

- `DATABASE_URL` — defaults to SQLite at `./astro.db`. Override with Postgres URL for production.
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — for OAuth. Without these, `/auth/google/login` returns 503 but the rest of the app works.
- `PORTAL_ENABLED=true` (default) loads the Flask sub-app and triggers a one-time skyfield ephemeris download (~16MB) into `portal/_skyfield_cache/` (gitignored). Tests force `false` to keep CI fast.
- `SECRET_KEY` — signs JWT and the OAuth state cookie. For prototype, the default is fine; production should use a random 48-byte token.

## Canonical test baseline

Most tests pin against the **Bangalore 1990-07-15 12:00 IST** birth (lat 12.97, lon 77.59, tz_offset 5.5). This produces:
- Mercury Mahadasha (1978-03-26 → 1995-03-26)
- Virgo Lagna (~173.99° sidereal)
- Moon at Revati pada 3, lord Mercury
- Saturn Avastha = Mrita / Swapna
- Sun-MC astrocartography line at ~84° E (near solar-noon meridian)

All values cross-checked against external Vedic-astrology sources (Wikipedia, Prokerala, drikpanchang, Jagannatha Hora) so they regress reliably.

## Locked-in technical decisions (don't relitigate)

- **Lahiri sidereal ayanamsa** for all Vedic calculations.
- **`DAYS_PER_VEDIC_YEAR = 365.2425`** for Vimshottari (NOT 365.25).
- **Whole-sign Vedic aspects**, not degree-orb-gated.
- **Floor division** (`int(lon // span)`) for nakshatra cusps.
- **JD arithmetic** for calendar dates, never `datetime.timedelta`.
- **Astrocartography in equatorial coords** (`FLG_EQUATORIAL`), not ecliptic.
- **Leaflet + OpenStreetMap** for maps (NOT Mapbox), no API keys.
- **In-process asyncio daemon**, not Celery.
- **SQLite + WAL** by default; Postgres+asyncpg in production.
- **Google OAuth via authlib + JWT (HS256, 7-day TTL)** via pyjwt. Account keyed on `google_sub`.

## Where to find more context

- **Repo**: https://github.com/Slllyio/astro
- **Architectural blueprint** (mundane-astrology vision): `Geo-Astrological Planetary Intelligence Engine.pdf` (still in repo at the time of writing; flagged for removal).
- **Most recent execution plan**: `C:\Users\S.C.C\.claude\plans\phase-2-database-hashed-ritchie.md` (the Tab 3 Medini plan).
- **Scheduled remote agent**: `trig_01Ngco8W19HrbVgbQ3RGFDrH`, fires 2026-05-14 to revisit Phase-2 Tier-3 deferred items.
