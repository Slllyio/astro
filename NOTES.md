# Resume Notes

Snapshot of the project state as of **2026-04-28**, at commit `6e5f1c3` (Phase 5 Stage 3 ML trainer + dtype fix).

## What's shipped

**Three tabs of a unified astrology portal** + **a research/ML pipeline**.

| Surface | Path / CLI | What it does |
|---|---|---|
| 1. Nadi (precise natal) | `/chart/calculate`, `/profiles/*`, `/auth/google/*` | Sidereal Lahiri D1–D60, MD/AD/Pratyantar, Lagna+houses, Yogas, Panchanga, BAV/SAV, Avastha, Sade Sati. Google OAuth + JWT. Transit daemon. |
| 2. NumeroAstro | `/portal/*` | Vendored Flask app from [Slllyio/astro-web-portal](https://github.com/Slllyio/astro-web-portal). DOB-only "probability engine" + numerology + BAV-driven karma classification. |
| 3. Medini Phase 0+1 (Geo) | `/medini/*` | Kurma Chakra widget (`/medini/kurma-widget`) — 9 regions × 27 nakshatras × 5 tattvas. Personalized Astrocartography (`/medini/cartography/page`) — 36 planetary lines per chart over the Kurma layer. Both Leaflet + OSM, no API keys. |
| 4. Medini Phase 5 (ML) | `python -m app.medini.etl.scraper / databank_etl / ml.train_classifier` | Three-stage offline pipeline: scrape Astro-Databank → compute the **Vedic Tensor** (~150 features per chart) → XGBoost+SHAP rule discovery with magnitude-filtered output. CLI tools, not a web surface. Outputs to `data/ml_runs/{target}_{timestamp}/`. |

**Test suite**: 666 passing, ~84% coverage, GitHub Actions CI green.

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

1. **Phase 5 live run** — overnight scrape against real Astro-Databank, then ETL, then train one demo target (start with `--target politician` or similar broad token). Pipeline is fully tested on synthetic data; real data is the next gate. The scraper has a `--max-entries 100` flag for an initial validation pass before the full crawl.
2. **LLM Ollama narrative layer**. An agent's plan has already been written to `C:\Users\S.C.C\.claude\plans\phase-2-database-hashed-ritchie-agent-ac1cfc52ab1b0c960.md`. Decisions locked: Ollama backend, hybrid summary+drill-down endpoints, no auth on `/interpret/*`.
3. **Phase 5C — FastAPI prediction endpoint**. `POST /medini/predict/{target}` that loads a saved `model.json` from a `data/ml_runs/...` directory and returns probability + top-5 SHAP features. Trivial wiring once a real model exists.
4. **Phase 5D — SHAP rule explorer widget**. Interactive Leaflet/D3 page that visualizes a SHAP dependence plot with a slider — see plan file for spec.
5. **Tab 3 Phase 2 — Daily Mundane Forecast**. `/medini/today` page surfacing today's significant ingresses, retrogrades, eclipses, with activated Kurma regions highlighted. Reuses the existing transit daemon.
6. **Tab 3 Phase 3 — Eclipse Impact Mapper**. `swe.sol_eclipse_when_glob` + Kurma layer + natal chart impact.
7. **Unified-tabs frontend shell**. Currently each tab is reachable directly via URL but there's no nav between them.
8. **NumeroAstro re-branding**. The vendored portal still says "Stellar Blueprint" in templates — needs surface-level rename.
9. **PDF housekeeping**. `Geo-Astrological Planetary Intelligence Engine.pdf` was accidentally committed via `git add -A`. Repo is private so low-stakes, but cleaner to remove + add `*.pdf` to `.gitignore`.

## Phase 5 ML pipeline cheatsheet

Three CLIs, run in sequence:

```bash
# Stage 1: scrape Astro-Databank → CSV (overnight; resumable; SQLite-backed state)
python -m app.medini.etl.scraper --output data/astro_databank/raw.csv --max-entries 100   # smoke test first
python -m app.medini.etl.scraper --output data/astro_databank/raw.csv                     # full run, can take hours

# Stage 2: CSV → Vedic Tensor parquet (~150 features per AA-rated chart)
python -m app.medini.etl.databank_etl \
    --input data/astro_databank/raw.csv \
    --output app/medini/data/ml_astro_features.parquet

# Stage 3: train XGBoost + extract SHAP rules
python -m app.medini.ml.train_classifier \
    --features app/medini/data/ml_astro_features.parquet \
    --target politician \
    --output data/ml_runs/
# Outputs in data/ml_runs/politician_<UTC-timestamp>/:
#   model.json, shap_summary.png, shap_dependence_*.png,
#   feature_importance.csv, rules.csv, report.md
```

The Vedic Tensor's three feature vectors:
- **Base** (~70 cols): longitudes, pairwise angular distances, nakshatras, houses, tattvas
- **Kinematic** (~63 cols): velocity, retrograde, stationary, combustion intensity, ecliptic latitude, declination, Out-of-Bounds
- **Vedic** (~50 cols): SAV per house, BAV in current sign, D9/D10 placements, dispositors, dispositor chain depth, final dispositor

Phase A's `app/core/ashtakavarga.py` and `app/core/shodashavarga.py` are reused directly — Stage 2 flattens their existing outputs into ML columns. No new astronomy.

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
