# astro — project conventions for Claude

This file is loaded into every Claude Code session in this repo. It captures
**locked-in decisions** that should not be relitigated and **conventions that
shape the right way to add code here.** Update sparingly; this is the
team-shared brain.

## ★ PRIME DIRECTIVE — the North Star (never forget this)

**The one aim: build the truest, most accurate Vedic-astrology engine ever encoded
to Sri B. V. Raman's system.** Everything else — architecture, speed, product
polish — is subordinate to *fidelity to Raman's siddhanta*.

We are building this as a **fresh unified engine** (see `unified_engine/`, kept
local). Because it is fresh, we take **every step and process required** for maximal
truth and accuracy to Raman — no shortcuts that trade doctrinal correctness for
convenience:

- **Doctrine first.** Every rule, verdict, dignity, aspect, dasha, and longevity
  judgment must trace to Raman's own texts (*How to Judge a Horoscope* Vol I & II,
  *Hindu Predictive Astrology*, *Three Hundred Combinations*, *Studies in Jaimini*)
  with a verbatim citation. If Raman and another authority disagree, **Raman wins.**
- **Verify against Raman, never against engine self-output.** Pin accuracy on his
  own published worked nativities (e.g. the Mainpuri chart) and printed verdicts.
- **No silent approximation.** Where a technique has variants, encode the one Raman
  taught, name it, and cite it; document any deliberate omission.
- **Measure honestly.** Distinguish textbook fidelity from real-outcome
  generalization; report both; overfitting to worked examples is not accuracy.
- **Take all the steps.** Full ephemeris precision, full doctrine coverage, adversarial
  validation, regression guardrails — completeness over expedience, always.

This directive overrides expedience. When in doubt, choose the path that makes the
engine *more faithful to B. V. Raman*.

### ★★ MEASURED TRUTH (2026-07-24) — the directive's own verdict, binding on all future sessions

The directive was carried out in full, and then honored to its last clause ("measure honestly;
report both"). The results are settled and MUST NOT be re-litigated by re-running what is closed:

- **Textbook fidelity: ACHIEVED and at its proven ceiling — 261/293 = 89.1% exact** against
  Raman's own printed verdicts, externally verified casting (96.7% ascendant agreement with
  AstroDatabank's published placements). Five independent methods proved the ceiling cannot be
  faithfully exceeded (placement harvest exhausted, karaka frames over-fire, tuner null on 5x data,
  no clean cited-fix patterns, ML on the same features loses to the hand-tuned judge). **Do not
  chase accuracy further; it is not there without overfitting.**
- **Real-outcome generalization: NULL — measured, not assumed.** 22,177 verified charts, 47k dated
  events, pre-registered, sham-gated, controls valid in both directions: engine verdicts, raw rule
  evidence, the 91 classical conditionals, dasha/maraka timing, and the doctrine's own primitives
  tested directly (Kuja dosha OR 1.09; Moon-Saturn OR 1.13) — all null. One thread remains
  suggestive-unconfirmed (suicide → afflicted 8th: 0.535 exploratory, 0.528 held-out, p=.062,
  underpowered; `confirmatory_study.py` is pre-registered and waiting if ~500 new cases arrive).
- **The mechanism is measured**: the median chart carries 19 afflicted AND 31 favourable
  significations simultaneously (97.1% of charts offer both poles at all times) — indications
  abundant enough to explain any life are non-differential and cannot predict one. Raman's books
  validate at 89% because they are a curated gallery of agreement (his charts are astronomically
  ordinary — rule fire-rates identical to the population).
- **What the engine IS**: a faithful scholarly instrument answering "what would Raman say"
  (legitimate, preserved, ratcheted) + the population-calibration overlay that makes every reading
  disclose its own information content — NOT a validated predictor of lives, and it must never be
  presented as one.
- Canonical records: `docs/raman_saab/REAL_OUTCOME_GENERALIZATION.md` (that it fails),
  `WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md` (why — two levels), `FAILURE_ATLAS.md` (where, per
  case). Guards: the golden ratchet (fidelity) + `test_astrobank_ratchet.py` (generalization
  floors). The two axes are reported side by side, never averaged.

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
| **Dasha/bhukti house-activation = Raman's "When Do Indications Fructify?" method (HTJAH-I ch.1)** | A planet INFLUENCES a house if it owns, occupies, or aspects **the house OR its lord** — i.e. the five/six factors: house-lord, occupants, aspecters, planets aspecting the lord, planets conjoining the lord, and the lord-from-the-Moon (HTJAH-I:1586-1589). This is exactly the broad `timer_set` — do NOT narrow it to own/occupy/aspect only. **Grading is a four-tier scheme, UNIFORM for all 12 houses** (Raman states this repeatedly: HTJAH-I:1588-1589, 2617, 3522, 4333, 8294, 16435 — "the general principles… hold equally good"): both MD & AD lord influence the house **and AD lord is _associated_ (conjunct / mutual aspect) with the MD lord → par excellence**; both influence but AD **not** associated → **ordinary**; **only the bhukti (AD) lord influences → limited**; **only the MD lord influences → feeble** (HTJAH-I:1592-1596, 1635-1640; 2588-2599 incl. "feeble"; recurs 16404 / 17746). The method is house-agnostic; only the *inputs* (each house's own lord/karaka/occupants) differ. NOT a Shadbala "supersession" (that was a wrong guess, reverted). Encoded in `vimshottari.bhukti_tier` + `lords_associated`; surfaced in `detailed_report`. **Locked 2026-07-25 after re-deriving it from the source (this had been done before and lost).** |

## Locked architecture decisions — do NOT change

- `extra="forbid"` on Settings — kwargs typos fail loudly.
- `asyncio.to_thread` for CPU-bound ephemeris calls in async route handlers.
- `yield_per` streaming in `process_natal_charts` to bound memory.
- `Account` keyed on `google_sub` (NOT email — email can change).
- Per-account rate limiting via `slowapi` with JWT-aware key function.
- **Tab 3 (Medini)**: Leaflet + OSM (NOT Mapbox), axis-aligned bbox tiling (NOT PostGIS), safe DOM construction (`createElement` + `textContent`, never innerHTML).
- Single source of truth for Kurma GeoJSON: `/medini/regions` is consumed by both the educational widget and the personalized cartography page.

## ★ REPORT COMPLETENESS — do NOT omit anything (locked 2026-07-27, after a real error)

**Every report surface shows EVERYTHING the report computes. We only ADD, never remove or hide.**
This is a standing user directive, confirmed twice and once violated — treat it as inviolable:

- The interactive page (`app/medini/templates/report.html`), the standalone HTML
  (`report_html.py`), and the markdown (`to_markdown`) must each render **every field of every
  section** the report produces. If the engine computed a value, it appears in the reading.
- **No collapsing a section to a bare count** (e.g. "Ishta/Kashta outlook (18)" with the rows
  hidden). A `<details>` drill-down is fine ONLY if its summary already shows the substantive
  content or it is `open` by default; never hide data behind a click that shows only a number.
- **No dropping columns.** A generic table renderer must render nested-object / list values
  (format them), never silently skip a column because its value is not a scalar. This was the
  exact bug: `gochara.vedha_by`, `yoga_timing.quality`, the dashboard `reader`, and the
  preponderance `testimonies`/`absent` all vanished this way.
- When adding a section or field, add it to ALL renderers (append-only per the template contract).
- If a value is genuinely not meaningful to show, that is a product decision for the USER to make
  — surface it and ask; do not drop it unilaterally.

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
