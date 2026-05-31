# astro — project conventions for Claude

This file is loaded into every Claude Code session in this repo. It captures
**locked-in decisions** that should not be relitigated and **conventions that
shape the right way to add code here.** Update sparingly; this is the
team-shared brain.

## Project shape

- Python **3.12** primary interpreter (`py -3.12` on Windows, `.venv/Scripts/python.exe` for the local venv).
- **FastAPI** application at `app/main.py` with three router groups (auth, chart+profile, medini) + a vendored **Flask** portal mounted at `/portal/*` (NumeroAstro).
- **SQLAlchemy 2.0 async** ORM, `aiosqlite` for dev (WAL mode), `asyncpg` for prod via `DATABASE_URL`.
- In-process **asyncio daemon** started in FastAPI lifespan (NOT Celery).
- **Pytest** for tests (`pythonpath = ["."]`, `asyncio_mode = "auto"`) — 48+ test files, coverage gate 80% in CI.
- ETL/ML pipeline lives under `app/medini/etl/` (31 scripts) and `app/medini/ml/` (44 scripts), all CLI-invoked via `python -m app.medini.<...>`.
- Data outputs flow to `data/` (gitignored) and `app/medini/data/*.parquet` (kept).

## Locked astrology-domain conventions — do NOT change

| Rule | Why |
|---|---|
| **Lahiri sidereal ayanamsa** for all Vedic calculations | Not tropical, not Raman, not KP. |
| `DAYS_PER_VEDIC_YEAR = 365.2425` for Vimshottari math | Gregorian mean year; 365.25 (Julian) drifts ~5 days over a 19-yr Saturn MD. |
| **Whole-sign Vedic aspects (drishti)** | Conjunction/opposition fire by sign membership; orb only sets `is_exact=True`. |
| **Circular orb distance**: `min(diff, 360 - diff)` where `diff = abs(lon1 - lon2) % 360` | Naive `abs()` silently fails at the 359°/2° Pisces/Aries cusp. |
| **Floor division for nakshatra cusps**: `int(moon_lon // nak_span)` | Differs from `/` cast-to-int at exact boundaries (e.g. `40.0`). |
| **JD arithmetic for calendar dates** — never `datetime.timedelta` | Use `birth_jd ± years * 365.2425` then `swe.revjul(jd, swe.GREG_CAL)`. |
| **Rahu/Ketu drishti = Jupiter-style 5/9** (modern Sukra Nadi) | Not BV Raman (no nodal drishti), not KP. |
| **Avastha benefics**: Jupiter, Venus, Mercury, Moon. **Malefics**: Sun, Mars, Saturn, Rahu, Ketu. | |
| **Astrocartography in EQUATORIAL** (`FLG_EQUATORIAL`) | Ayanamsa doesn't enter line geometry. |
| **Chara Karakas: strict 7-karaka Jaimini, NO Rahu/Ketu** | Rahu/Ketu are chayagrahas and cannot signify the soul or any karaka role. AK can NEVER be Rahu or Ketu. Use only the 7 visible planets (Sun..Saturn) ranked by degree-within-sign descending. The 8-karaka extension (Rahu degree-inverted as PK2_PutraKaraka2) is a Narasimha-Rao modern-minority interpretation that the project doctrinally rejects per BV Raman / Sanjay Rath / Jaimini Sutras strict reading. **Locked 2026-06-01 after a real reading error.** |

## Locked architecture decisions — do NOT change

- `extra="forbid"` on Settings — kwargs typos fail loudly.
- `asyncio.to_thread` for CPU-bound ephemeris calls in async route handlers.
- `yield_per` streaming in `process_natal_charts` to bound memory.
- `Account` keyed on `google_sub` (NOT email — email can change).
- Per-account rate limiting via `slowapi` with JWT-aware key function.
- **Tab 3 (Medini)**: Leaflet + OSM (NOT Mapbox), axis-aligned bbox tiling (NOT PostGIS), safe DOM construction (`createElement` + `textContent`, never innerHTML).
- Single source of truth for Kurma GeoJSON: `/medini/regions` is consumed by both the educational widget and the personalized cartography page.

## Test-pinning policy

- **Canonical baseline**: Bangalore 1990-07-15 12:00 IST, lat 12.97, lon 77.59, tz +5.5.
  Produces Mercury MD, Virgo Lagna ~173.99°, Moon at Revati pada 3, Saturn Avastha = Mrita/Swapna.
- **Pin against externally-verifiable sources**, never engine self-output: Wikipedia, Prokerala, Jagannatha Hora, drikpanchang.com.
- The PDF `Geo-Astrological Planetary Intelligence Engine.pdf` is the source of truth for the Kurma Chakra 27-nakshatra → region table.

## Style conventions

- `from __future__ import annotations` at the top of every new module.
- Every CLI-invokable module has a module docstring with a `Usage:` block showing the exact `python -m` command and arg names.
- Logging via `logger = logging.getLogger(__name__)`. Avoid `print()` outside scripts.
- Type annotations on all public function signatures. Prefer `from typing import ...` over postponed-string forms beyond annotations.
- Test classes named `Test<Subject>`, methods `test_<scenario>_<expected>`, each with a one-line docstring stating the astronomical fact being verified.

## Operational

- Repo branch policy: **commit directly to `main`**. No PRs, no branch protection in v1.
- **Co-authored-by attribution is disabled globally.** Do not add `Co-Authored-By` trailers to commits.
- Commit message style: conventional (`feat(medini): …`, `fix(core): …`, `docs(medini): …`).
- CI: GitHub Actions runs `pytest --cov=app` with 80% coverage gate.

## Running the project

```powershell
# tests
py -3.12 -m pytest -q
py -3.12 -m pytest --cov=app --cov-report=term-missing -q

# live app
py -3.12 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# then visit /docs, /medini/kurma-widget, /medini/cartography/page, /portal/
```

## Where to put things

| Adding... | Goes in... | Paired test in... |
|---|---|---|
| New core engine code | `app/core/<name>.py` | `tests/test_<name>.py` |
| New API endpoint | `app/api/<group>_routes.py` | `tests/test_<name>.py` |
| New ETL stage | `app/medini/etl/<name>.py` | `tests/test_<name>.py` |
| New ML experiment | `app/medini/ml/<name>.py` | `tests/test_<name>.py` (when stateless logic is testable) |
| Throwaway exploration | `scratch_<topic>.py` at repo root — **but promote or delete before merge.** |
| New Medini doctrine source | `data/knowledge_library/` (manifest in `topics.yaml`) | — |

## Files NOT to edit blindly

- `.env`, `.env.example` — secrets.
- `data/ml_runs/**/*.parquet` — generated artifacts.
- `app/medini/data/*.parquet` — generated artifacts (rebuild via ETL).
- `Geo-Astrological Planetary Intelligence Engine.pdf` — source-of-truth reference.

The `.claude/settings.json` PreToolUse hook enforces some of this automatically.

## Custom skills, subagents, and hooks in this repo

- `.claude/skills/bphs-rule-validator/` — validate ML-discovered rules against BPHS classical doctrine.
- `.claude/skills/medini-etl-scaffold/` — scaffold a new `app/medini/etl/` module + paired test from the canonical pattern.
- `.claude/agents/bphs-doctrine-reviewer.md` — read-only reviewer for doctrine compliance.
- `.claude/agents/ml-experiment-auditor.md` — read-only reviewer for ML pitfalls (data leakage, CV, target alignment).
- `.claude/settings.json` hooks: auto-run paired tests on edit; block edits to `.env`/`data/**/*.parquet`.

Invoke a skill with `/<skill-name>`. Dispatch a subagent via the `Agent` tool with `subagent_type="bphs-doctrine-reviewer"` or `"ml-experiment-auditor"`.
