# Resume Notes

Snapshot of the project state as of **2026-04-28** (Tasks 1–7 of the queued execution: PDF housekeeping, NumeroAstro rebrand, Daily Mundane Forecast, Eclipse Impact Mapper, Unified-tabs shell, Phase 5C `/medini/predict/{target}`, LLM Ollama narrative layer).

## What's shipped

**Three tabs of a unified astrology portal** + **a research/ML pipeline**.

| Surface | Path / CLI | What it does |
|---|---|---|
| 1. Nadi (precise natal) | `/chart/calculate`, `/profiles/*`, `/auth/google/*` | Sidereal Lahiri D1–D60, MD/AD/Pratyantar, Lagna+houses, Yogas, Panchanga, BAV/SAV, Avastha, Sade Sati. Google OAuth + JWT. Transit daemon. |
| 2. NumeroAstro | `/portal/*` | Vendored Flask app from [Slllyio/astro-web-portal](https://github.com/Slllyio/astro-web-portal). DOB-only "probability engine" + numerology + BAV-driven karma classification. |
| 3. Medini Phase 0+1 (Geo) | `/medini/*` | Kurma Chakra widget (`/medini/kurma-widget`) — 9 regions × 27 nakshatras × 5 tattvas. Personalized Astrocartography (`/medini/cartography/page`) — 36 planetary lines per chart over the Kurma layer. Both Leaflet + OSM, no API keys. |
| 4. Medini Phase 5 (ML) | `python -m app.medini.etl.scraper / databank_etl / ml.train_classifier` | Three-stage offline pipeline: scrape Astro-Databank → compute the **Vedic Tensor** (~150 features per chart) → XGBoost+SHAP rule discovery with magnitude-filtered output. CLI tools, not a web surface. Outputs to `data/ml_runs/{target}_{timestamp}/`. |
| 5. Medini Phase 2 (Daily Mundane) | `/medini/today`, `/medini/today/page` | Cosmic-weather feed: ingresses, stations, conjunctions over a ±3-day window, with Kurma regions intensity-graded by today's planetary load. |
| 6. Medini Phase 3 (Eclipses) | `/medini/eclipses`, `/medini/eclipses/page` | Eclipse Impact Mapper — next 5 solar + 5 lunar eclipses tagged with the Kurma region they activate via the luminary's nakshatra. Solar markers placed at the geographic point of greatest eclipse. |
| 7. Phase 5C predict | `POST /medini/predict/{target}`, `GET /medini/predict` | Loads the most recent trained run for a target, computes the Vedic Tensor for a new birth chart, returns probability + top-N SHAP contributors. Graceful 404 with `available_targets` when no model exists. |
| 8. LLM Narrative | `POST /interpret/chart`, `POST /interpret/chart/{section}`, `/interpret/page` | Ollama-backed natural-language readings — summary mode (whole chart) + drill-down mode (ascendant / mahadasha / yogas / panchanga / planetary / ashtakavarga). Defaults to deterministic templates when `OLLAMA_ENABLED=false`. |
| 9. Unified shell | `/` | Tab navigator over Nadi calculator (`/chart/page`), NumeroAstro, Kurma grid, Astrocartography, Cosmic Weather, Eclipses, Interpret, API Docs. URL-hash driven, single-iframe content area. |

**Test suite**: 803 passing (+57 across the new tasks), ~84% coverage, GitHub Actions CI green.

## Trained models (post-2026-04-28 batch)

| Run dir                              | Target          | Source             | Rows  | Base rate | CV AUC | Test AUC |
|---|---|---|---|---|---|---|
| `dissolution_20260428T064109Z`       | dissolution     | VedAstro alone     | 14,278| 0.2395    | 0.583  | 0.590    |
| `dissolution_20260428T090150Z`       | dissolution     | VedAstro + Wayback | 14,684| 0.2328    | 0.564  | 0.577    |
| `politics_20260428T090354Z`          | politics        | Wayback only       | 422   | 0.1351    | 0.529  | 0.417    |
| `entertainment_20260428T090406Z`     | entertainment   | Wayback only       | 422   | 0.3199    | 0.539  | 0.672    |
| `dissolution_20260617T161022Z`       | dissolution     | VedAstro (HF)      | 14,278| 0.2395    | 0.568  | 0.578    |

**2026-06-17 resume run**: re-ran the Phase-5 pipeline end-to-end on real data
pulled fresh from HuggingFace (`vedastro-org/15000-Famous-People-*`), since the
ephemeral container ships with no data on disk. VedAstro import → Vedic-Tensor ETL
(14,278 rows × 535 features) → `dissolution` model reproduced the historical
result (CV 0.568 ± 0.008, holdout 0.578). Top SHAP features: `aspect_orb_rahu_mercury`,
`aspect_orb_ketu_mercury`, `dist_moon_saturn`. Artifacts committed to branch
`data/vedastro-corpus` (raw.csv, features parquet, run dir) — gitignored elsewhere,
so the branch is the durable copy. Next scaling step (Wayback/lapaas) still pending:
archive.org's CDX API returns 403 from the sandbox, so the full crawl needs a
reachable CDX path or a user-provided CDX cache.

**2026-06-17 event-data ingest**: added the dated life-event corpus on the same
branch. `lapaasindia/good-time-finder` is gone (404), so the reachable source was
ASTROCRM's `astro_people.csv` (`jfsagro-glitch/ASTROCRM`, ~32 MB, fetched from the
repo root on `main`). `events_extractor` parsed its `raw_wikitext`
`{{ASTRODATABANK_evn}}` templates into `data/astro_databank/events.csv`:
**9,070 dated events** from 3,741 people (59% with full ISO dates; year range
202–2026). Top roots: Work (2,551), Death-cause-unspecified (1,743), Relationship
(1,569), Family (553), Death-by-Disease (507). Reproduce with:
`curl -sL https://raw.githubusercontent.com/jfsagro-glitch/ASTROCRM/main/astro_people.csv -o data/holos/astro_people.csv`
then `python -m app.medini.etl.events_extractor --input data/holos/astro_people.csv
--output data/astro_databank/events.csv`. Only the derived `events.csv` is committed
(the 32 MB source stays reproducible via the URL). Wiring these events into a trained
event-timing model still needs natal coordinates — ASTROCRM ships `place_of_birth`
as free text, so it requires a geocoding step before `event_corpus` → training.

**2026-06-17 event-timing model (geocoder + end-to-end)**: closed the geocoding
gap with a new offline importer `app/medini/etl/astrocrm_geocode_importer.py`
(city name → lat/lon via `geonamescache`, disambiguated by population; tz_offset
via `timezonefinder` + `zoneinfo`). Full chain on real data:
`astrocrm_geocode_importer` (4,692 geocoded / 6,488) → `databank_etl`
(3,964 AA+A natal charts) → `event_corpus --event-root Relationship`
(1,081 events + 1,081 month-anchored negatives, 1,072 natal+transit+dasha cols) →
`train_classifier --target-column is_event` → `data/ml_runs/is_event_20260617T184650Z/`.
Result: balanced base rate 0.50, CV ROC-AUC **0.542 ± 0.031**, holdout 0.542 —
weak but the **feature story is doctrinally coherent**: top SHAP features are
`cross_lon_saturn` (Saturn transit vs natal, dominant), then `active_md_lord` /
`active_ad_lord` / `active_pd_lord` (Vimshottari dasha lords) and Rahu/Jupiter
transits — exactly the classical relationship-timing drivers. Known limitation:
bare-city geocoding (population prior) misplaces ambiguous small-town names,
dampening house accuracy; region/country disambiguation is the next quality lever.

**2026-06-17 geocoder v2 + 3 event-root models**: improved the geocoder —
region/country hints from parentheticals + comma-tails (US-state and country
disambiguation before the population fallback), lowered the city-population
threshold for broader coverage, and switched tz resolution to each city's
bundled IANA zone (dropping the `timezonefinder` dep; geonamescache alone now).
Coverage rose 72%→82% (5,301/6,488 geocoded; misses 1,096→487) → 4,504 AA+A
natal charts. Trained event-timing models for three roots (balanced 0.50 base
rate, `is_event` target, runs under `data/ml_runs/{relationship,work,death}/`):

| Event root            | Events | CV ROC-AUC      | Holdout |
|---|---|---|---|
| Relationship          | 1,179  | 0.542 ± 0.015   | 0.551   |
| Work                  | 2,039  | 0.512 ± 0.039   | 0.542   |
| Death (cause unspec.) | 1,341  | 0.439 ± 0.021   | 0.454   |

Relationship is the clearest (and CV variance tightened vs the v1 geocoder run,
0.015 vs 0.031). Work is near-random; Death is *below* 0.5 — death timing isn't
captured by this transit/dasha feature set + month-anchored sampling (honest
negative result). Across all three, `cross_lon_saturn` (Saturn transit vs natal)
is the #1 SHAP feature — Saturn as the classical timer — with Jupiter/Rahu
transits and dasha lords following. Geocoder dep: `pip install geonamescache`.

**2026-06-17 canonical Silver layer (data structuring)**: folded all collected
data into the documented Silver/Gold + DuckDB architecture instead of leaving it
as scattered CSVs. New adapter `app/medini/etl/build_silver_from_corpora.py` emits
canonical `persons.parquet` + `events.parquet` from `raw.csv` (VedAstro) +
`raw_astrocrm.csv` (ASTROCRM) + `events.csv`, reusing the schema + event-class
harmonization from `build_person_event_tables`. Then the existing pipeline ran
unchanged: `build_charts_table` → `build_dasha_windows` → `build_dasha_tree` →
`build_event_dasha_join` → `resolve_persons_dedup` → `build_duckdb_catalog` →
`materialize_gold_views`. Result (all committed):

| Table | Rows |
|---|---|
| persons (VedAstro 14,205 + ASTROCRM 5,301) | 19,506 |
| charts (1 per person) | 19,506 |
| dasha_windows (81 per person) | 1,579,986 |
| dasha_tree | 1,579,986 |
| events (linked, dated; 527 orphans + year-only dropped) | 4,833 |
| events_with_dasha (4,823 matched to a window) | 4,833 |
| resolved_persons (20 cross-corpus matches) | 19,486 |

`validate_silver_layer` → **9 PASS, 0 FAIL** (made the optional Round-9
`person_id_map` check skip-if-absent, matching the transit checks). DuckDB catalog
`app/medini/data/catalog.duckdb` exposes 10 Silver tables + 6 Gold views (incl. the
chart heterograph: `chart_edges` 897,276 + `static_graph_edges` 25 →
`v_chart_edge_summary` 78,024); verified a
persons⋈charts⋈events_with_dasha join resolves. `source` values: `vedastro` /
`astrocrm`; person_id tags `VA:` / `AC:` (= `{prefix}:{birth_jd:.4f}`).
Query it: `duckdb.connect("app/medini/data/catalog.duckdb", read_only=True)`.

**2026-06-18 scaled corpus 4× → 80,890 persons**. Added the holos corpus
(`jfsagro-glitch/ASTROCRM/holos_clean.csv`, 61,583 chart-grade records with
full date+time+coords+tz+vocation; fetched + run through the existing
`holos_importer` → `raw_holos.csv`), wired as a third corpus in
`build_silver_from_corpora` (`source=holos`, person_id `HO:`). Rebuilt the whole
Silver/Gold store unchanged:

| Table | Rows |
|---|---|
| persons (holos 61,384 + vedastro 14,205 + astrocrm 5,301) | 80,890 |
| charts | 80,890 |
| dasha_windows / dasha_tree | 6,552,090 |
| chart_edges | 3,720,940 |
| events / events_with_dasha (5,129 matched) | 5,139 |
| resolved_persons (4,592 cross-corpus matches) | 76,279 |

`validate_silver_layer` → **9 PASS, 0 FAIL** (added a birth-year sanity gate
`1 ≤ year ≤ 2100` in the adapter — holos ships a mythological "Thema Mundi" at
year 6050 that has no computable chart). Why Wikidata wasn't used: its WDQS
endpoint is reachable but **times out (60s)** on any bucket large enough to be
worth it (even one birth-year), and the bulk-downloadable people datasets
(Laouenan 2.2M, Yale 250k) are year-only / NLP-formatted — not chart-grade.

**2026-06-18 event layer 6.5× → 33,548 events + transits**. The event layer was
the weak point (5,139 dated, death-heavy). Mined **year-precision death events**
from the holos `categories` ("NNNN deaths" tags — 47% coverage) in
`build_silver_from_corpora`: +28,409 deaths (mid-year anchor, `event_date_precision="year"`),
for people we already have charts for. events 5,139 → **33,548** (30,943 death).
Then ran `build_event_transits` → `event_transits.parquet` (301,932 rows = 9 grahas
× 33,548 events) + Gold `v_event_transits_powerful` (167,740). `events_with_dasha`
now 33,510 matched; `validate_silver_layer` **11 PASS / 0 FAIL** (the transit
cardinality checks activated). Every event now carries active MD/AD dāśā + 9-graha
gochara — enabling population-scale dāśā+transit timing analysis (e.g. MD-lord-at-
death distribution over 30k deaths).

**Death-window predictor UI** (`templates/death_window.html`,
`GET /medini/doctrine/death-window/page`): birth-data form → ranked future windows
with calibrated probabilities, a risk bar, MD death-roles, and the
median-remaining / P(die≤5y,≤10y) summary. Static page calling the JSON endpoint
(matches the existing `/interpret/page` pattern); honest caveat rendered inline.

**Pivot to non-death events — marriage & career** (`EVENT_SIGNIFICATORS` +
`GET /medini/doctrine/event-significators`): ran the same machinery on the
relationships (1,385) and career (743) event classes. Finding: unlike death's
multi-significator *confluence*, both reduce to a **single kāraka — Jupiter MD**
(relationships lift **1.343 p=1e-6**; career **1.363 p=1e-4**), while the classical
7th-lord / Venus / 10th-lord / Saturn significators are weak or null in this corpus.
So the composite adds little beyond Jupiter (relationships confluence no-effect;
career ≥1 lift 1.178). Deliberately did NOT ship a marriage "confluence predictor"
(it would be noise beyond Jupiter) — exposed the validated analysis generically
instead. n is small + events skew to early adulthood (caveat noted).

**Transit (gochara) lever — validated NULL for death** (after rebuilding
`event_transits` over all 38,995 events): slow planets transiting natal dusthānas
at death show no signal — Saturn/Rahu/Ketu/Jupiter/Mars over 6/8/12 all lift ≈ 1.00,
p > 0.35; Saturn over {8}, {1,8}, {1} likewise null. Likely because natal house cusps
need exact birth time, which much of the corpus lacks. Deliberately **not** added to
the predictor (would inject noise) — an honest negative result.

**Pratyantardaśā (month-resolution) windows**: the predictor gained `depth="pd"` —
expands each AD into its 9 PDs (729 windows/chart) with the same proportional rule,
so predictions resolve to ~weeks–months instead of multi-year ADs. The PD lord's
confluence reinforces the MD risk at a down-weighted `PD_WEIGHT=0.25`. Calibration +
ranking are resolution-agnostic.

**Backtest of the assembled ranker** (`death_backtest.py`): validating the levers
individually isn't the same as validating the *predictor*. Held-out test (25% of
persons; factors calibrated only on the disjoint 75%), scoring three nested models of
P(death lands in window w): **M0** ∝ duration (time-at-risk), **M1** ∝ duration·bracket,
**M2** ∝ duration·bracket·composite. Results (9,157 test deaths): top-decile capture
**19.4% → 21.9%** vs 10% null (the predictor lands the real death window in its
riskiest 10% about **2× chance**); M0→M1 Δ logLik +0.021 (bracket = mostly the
actuarial age-of-death shape); **M1→M2 Δ +0.0008, z=2.85, p=0.0044** — the
lord-specific confluence is real and significant on held-out data but **tiny**
(realized lift 1.0013). Honest verdict: the ranker beats chance, but its power is
mostly time-at-risk + age; the astrology-specific signal is genuine yet marginal —
exactly what the small population lifts (~1.03–1.19) predict. 3 tests.

**Wikidata day-precision death enrichment** (`enrich_deaths_wikidata.py`): the holos
"NNNN deaths" mine gave year-precision (mid-year-anchored) deaths, which blur dāśā
timing. Matched our charted, death-less persons to Wikidata P570 by exact English
label + birth-year (±1), multi-token names only → **+5,448 fresh day-precision
deaths** (events 33,548 → 38,996; death events with MD known 30,910 → **36,355**).
A second **recover-dropped pass** (`--recover-dropped`) caught the names the first
pass missed — mononyms (gated by exact-label + birth-year) and accented names (queried
with their original accent-preserving spelling, since Wikidata's exact-label join is
accent-sensitive): **+604 more day-precision deaths** (events 38,996 → 39,600; deaths
with MD known → **36,959**). All findings held steady (composite 1.025/1.093/1.187;
bracket madhya 1.09; backtest top-decile capture 19.3%→21.9%, M1→M2 z=2.72 p=0.0065).
Re-validating on the richer corpus **confirmed and sharpened every finding**:
significators third_lord/navāṁśa_64 lift 1.044, maraka_full 1.036 (p≈0); composite
dose-response now **1.026 / 1.096 / 1.189** at ≥1/2/3 roles (was 1.022/1.086/1.151);
longevity bracket madhya 1.092 (p≈0), alpa 0.895 (under-represented), pūrṇa 1.016.
The predictor's baked-in default factors were updated to these refreshed lifts. Raw
matches cached/auditable in `data/astro_databank/wikidata_deaths.csv`.

**Persistence note**: at this scale `dasha_windows.parquet` is **154 MB**, over
GitHub's hard 100 MB file limit, so it (and the sibling `dasha_tree.parquet`,
68 MB) are **NOT committed** — both are untracked/gitignored and regenerated
deterministically. After a fresh checkout, rebuild them (and refresh the catalog
views over them) in ~30s:
`python -m app.medini.etl.build_dasha_windows --workers 4 && python -m app.medini.etl.build_dasha_tree && python -m app.medini.etl.build_divisional_charts --workers 4 && python -m app.medini.etl.build_duckdb_catalog`.
(`divisional_charts.parquet` is 219 MB — also untracked/regenerable for the same reason.)
The committed compact Gold views (`v_natal_md_ads`, `v_event_with_tree`,
`v_event_survival`) already carry the query-ready answers derived from them.


**Reading the AUCs**: 0.5 = random, 0.6 = small but real, 0.7+ = strong. The dissolution-on-VedAstro number (0.59) is the most credible — large sample, good label discipline. Politics on a 422-row corpus (only 57 positives) is dominated by overfitting noise; entertainment's 0.67 holdout is encouraging but the high CV variance (±0.05) suggests it's not yet stable. Scaling the Wayback crawl to ~5,000 AA-complete rows (~12k fetches, ~13hr) would tighten these.

## Data pipeline (post-batch)

```
Stage 1a: VedAstro importer  (instant, MIT license — already in repo)
Stage 1b: Wayback scraper    (overnight, CDX-driven, archive.org-friendly)
Stage 1c: Corpus merger      (instant, dedup by name+DOB, union categories)
Stage 2:  Vedic Tensor ETL   (~2 sec for 15k rows, 28 workers)
Stage 3:  XGBoost+SHAP train (~2 sec per target on 15k rows)
```

Each stage is a CLI module under `app/medini/etl/` or `app/medini/ml/`.

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

1. **Phase 5 live run** — overnight scrape against real Astro-Databank, then ETL, then train one demo target (start with `--target politician` or similar broad token). Pipeline is fully tested on synthetic data; real data is the next gate. The scraper has a `--max-entries 100` flag for an initial validation pass before the full crawl. Once a model exists, `POST /medini/predict/politician` will surface real probabilities + SHAP contributors.
2. **Wire Ollama for live LLM narratives**. The `/interpret/*` endpoints work in fallback mode out of the box; setting `OLLAMA_ENABLED=true` plus `ollama serve` running locally with `llama3.1` (or override `OLLAMA_MODEL`) flips them to LLM mode. The fallback responses tag `source: "fallback"` so the UI can prompt the user.
3. **Phase 5D — SHAP rule explorer widget**. Interactive Leaflet/D3 page that visualizes a SHAP dependence plot with a slider — see plan file for spec.
4. **Optional: persist + cache model artifacts in S3/object storage** so the predict endpoint can serve from a fleet without each pod needing `data/ml_runs/` on local disk.
5. **Optional: streaming SSE for /interpret/*** so the LLM tokens arrive incrementally instead of waiting on the full response.

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
- **Architectural blueprint** (mundane-astrology vision): `Geo-Astrological Planetary Intelligence Engine.pdf` (gitignored after Task 1; still on disk locally for reference).
- **Most recent execution plan**: `C:\Users\S.C.C\.claude\plans\phase-2-database-hashed-ritchie.md` (the Tab 3 Medini plan).
- **Scheduled remote agent**: `trig_01Ngco8W19HrbVgbQ3RGFDrH`, fires 2026-05-14 to revisit Phase-2 Tier-3 deferred items.

## New endpoints from this execution batch

| Method | Path | Purpose |
|---|---|---|
| GET  | `/` | Unified-tabs HTML shell (replaces JSON welcome) |
| GET  | `/chart/page` | Nadi chart calculator UI |
| GET  | `/medini/today` / `/medini/today/page` | Daily mundane forecast JSON + map page |
| GET  | `/medini/eclipses` / `/medini/eclipses/page` | Eclipse Impact Mapper JSON + map page |
| GET  | `/medini/predict` | List trained-model targets |
| POST | `/medini/predict/{target}` | Predict probability + top SHAP contributors |
| GET  | `/interpret/sections` | List allowed drill-down sections |
| POST | `/interpret/chart` | LLM summary of the whole chart |
| POST | `/interpret/chart/{section}` | LLM drill-down for one section |
| GET  | `/interpret/page` | Interpret UI (form + LLM/Fallback badge) |
| GET  | `/medini/doctrine/death-significators` | Classical death-timing significators, head-to-head by lift |
| GET  | `/medini/doctrine/death-composite` | Composite confluence dose-response (maraka+3rd+64th-navāṁśa) |
| GET  | `/medini/doctrine/longevity-bracket` | Significator lift by āyurdāya bracket (alpa/madhya/pūrṇa) |
| GET  | `/medini/doctrine/death-window` | **Per-chart death-window predictor** — rank a living person's future dāśā periods |
| GET  | `/medini/doctrine/death-window/page` | Interactive UI for the predictor (form → ranked windows + probabilities) |
| GET  | `/medini/doctrine/event-significators` | Generic per-event-class significator panel (death / marriage / career) |

### Per-chart death-window predictor (`death_window_predictor.py`)

Turns the population findings into a forward, per-chart tool. Given birth data it
casts the natal chart (reusing the Silver `_compute_chart`), enumerates the 81
Vimśottarī MD×AD windows (reusing `build_dasha_windows`), keeps the future ones
(end after an as-of date), and ranks them by **composite × bracket** risk:
- **composite** — how many of {maraka_full, 3rd-lord, 64th-navāṁśa} the running MD
  lord plays (measured dose-response, lift 1.022/1.086/1.151 at score ≥1/2/3);
- **bracket** — the āyurdāya window the period lands in (alpa 0.89 / madhya 1.085 /
  pūrṇa 1.01, from the maraka_full bracket test);
- a down-weighted AD reinforcement (AD lord's own confluence).

Risk factors default to this session's measured lifts but can be re-derived live
from the catalog (`?calibrate=true` → `calibrate_factors`; verified to reproduce the
baked-in values). Core path needs only swisseph — no catalog — so it stays
serveable + CI-testable. 8 tests in `tests/test_death_window_predictor.py`.
