# `app.integration` — Track A + Track B bridge

This package is a **read-only adapter layer** between two parallel reading
engines that live in this repo. Neither original engine is modified.

## The two engines

| | Track A | Track B |
|---|---|---|
| Location | `app/reading/*` | `app/core/reading_composer.py` + `app/core/dkp_*` + 8 Gap modules |
| Identity | "Deterministic kundli engine" | "Astrologer's-lens framework" |
| Public entry | `app.reading.proforma.compute(dob, time, tz, lat, lon, ...)` | `app.core.reading_composer.compose_reading(chart, context, ...)` |
| Schema | Pydantic `ReadingOutput`, versioned 1.2.0, `extra="forbid"` | Frozen dataclasses |
| Tests | 1763 | ~182 framework + foundation |
| Branches | `feat/app-reading` | `round8-unification` |
| HTTP route | `/reading/v15/*` (web UI) | `/reading` (composer) |
| Doctrine | 18-decision lockfile (`docs/doctrine-decisions.md`) | Doctrine Translation Engine (27 records) + DKP modulation |

The integration layer was built **after both engines existed in parallel**
to bridge them without modifying either.

## Public API surface (v0.3.0)

### Annotators — augment a Track-A reading with Track-B data

```python
from app.integration import enhance

result = enhance(track_a_reading)
# result.reading          → original Track-A reading with per-Finding
#                           dkp_translations sidecar appended in place
# result.dkp_translations_summary
#                         → deduplicated top-level summary of every cited
#                           TranslationRecord + cross-references back to
#                           the Findings that surfaced them
```

```python
from app.integration import modulate_all_domains, build_dkp_context_from_reading

ctx = build_dkp_context_from_reading(
    reading,
    ashrama="grihastha",
    marital_status="married",
    profession="software_engineer",
)
result = modulate_all_domains(reading, dkp_context=ctx)
# result.per_domain[*].modulated  → Track-B's ModulatedVerdict
#                                   (confidence, context_completeness,
#                                    bhava_reading_focus, modulation_notes,
#                                    clarifying_questions)
# result.per_domain[*].original   → original Track-A DomainReading preserved
```

### Comparators — diff Track A vs Track B on the SAME doctrine

```python
from app.integration import compare_chara_dasha
from app.reading.sequences.chara_dasha import run_sequence

a_result = run_sequence(chart, asc_sign=6, moon_sign=11)
report = compare_chara_dasha(
    a_result,
    lagna_sign=6,
    birth_jd=2448088.2708333,
    target_jd=None,
)
# report.full_timeline_agrees  → bool
# report.per_md_diffs          → 12 MDWindowDiff entries
# report.verdict_summary       → human-readable one-liner
```

```python
from app.integration import compare_functional_roles

report = compare_functional_roles(lagna_sign=6)
# report.per_planet           → 9 PlanetFunctionalDiff entries
# report.disagreement_count   → int
# report.planets_only_in_a    → ["Rahu", "Ketu"]  (Track B omits these)
```

### Gap-module annotator — depth from Track B's 8 Gap modules (v0.3.0)

```python
from app.integration import annotate_with_gap_modules

result = annotate_with_gap_modules(
    track_a_reading, day_of_week=6, is_day_birth=True,
)
# result.chart_built       → True if a Track-B Chart was constructable
# result.gap_modules["A"]  → Ashtakavarga predictive (SAV per bhava, kakshya)
# result.gap_modules["D"]  → Karakamsa + Arudha + Upapada padas
# result.gap_modules["E"]  → Bhrigu Bindu, Pranapada, Upagrahas, Maandi
# result.gap_modules["F"]  → Baladi + Deeptadi avasthas
# result.gap_modules["G"]  → Vimsopaka Bala multi-varga score
# result.gap_modules["H"]  → Nakshatra deep (Moon's nakshatra attributes)
# result.gap_modules["J"]  → Bhavat Bhavam
# Each entry: {available: bool, result: dict | None, reason: str | None}
# Gap B (varga_confirmation) is structurally skipped — needs per-bhava
# pillar scores Track A doesn't expose directly.
```

## HTTP routes (v0.3.0)

`app.api.reading_integrated_routes.router` exposes:

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| GET | `/reading/integrated/info` | — | Integration metadata + adapter list + DKP registry size |
| POST | `/reading/integrated/enhance` | `{"reading": {...}}` | `IntegratedReadingOutput` |
| POST | `/reading/integrated/modulate` | `{"reading": {...}, "dkp_context_overrides": {...}}` | `DkpModulatedReading` |
| POST | `/reading/integrated/compare-chara` | `{"track_a_chara_dasha": {...}, "lagna_sign": N, "birth_jd": F, "target_jd": F?}` | `CharaComparisonReport` |
| GET | `/reading/integrated/compare-functional` | `?lagna_sign=N` | `FunctionalComparisonReport` |
| POST | `/reading/integrated/generate-and-enhance` | `{"dob": "...", "time": "...", "tz": "...", "lat": F, "lon": F, "enrich": bool}` | `IntegratedReadingOutput` (runs Track A's compute() internally) |

Wired into `app/main.py` at the same place as `reading_v15_router`. The
generate-and-enhance route offloads the heavy `compute()` call to a worker
thread via `asyncio.to_thread` so the event loop stays responsive.

## CLI

```powershell
# Enhance a saved reading.json with DKP translations:
py -3.12 -m app.integration --mode enhance --in reading.json --out enhanced.json

# Generate + enhance in one shot:
py -3.12 -m app.integration --mode generate-and-enhance \
    --dob=1990-07-15 --time=12:00 --tz=+05:30 \
    --lat=12.97 --lon=77.59 --out=enhanced.json

# Compare Chara Dasha implementations against a saved reading:
py -3.12 -m app.integration --mode compare --in reading.json --target-jd 2462000.5
```

## Architecture (text diagram)

```
   ┌─────────────────────────┐    ┌─────────────────────────┐
   │  Track A                │    │  Track B                │
   │  app/reading/*          │    │  app/core/*             │
   │                         │    │                         │
   │  • proforma.compute()   │    │  • reading_composer     │
   │  • ReadingOutput        │    │  • dkp_translation      │
   │    (Pydantic, frozen)   │    │  • dkp_modulation       │
   │  • 6 DomainReadings     │    │  • functional_roles     │
   │  • Vimshottari + Chara  │    │  • chara_dasha          │
   │    + Yogini sequences   │    │  • 8 Gap modules        │
   │  • 18 D-N decisions     │    │  • 27 TranslationRecords│
   │  • 1763 tests           │    │  • 182 framework tests  │
   └────────────┬────────────┘    └────────────┬────────────┘
                │                              │
                │     READ-ONLY OVER BOTH      │
                ▼                              ▼
        ┌──────────────────────────────────────────────────┐
        │  app/integration/  (this package, v0.2.0)        │
        │                                                  │
        │  Annotators                                      │
        │    • enhance()         — DKP translations onto   │
        │                          findings                │
        │    • modulate_all_domains() — DKP modulation     │
        │                          via BhavaVerdict adapter│
        │                                                  │
        │  Comparators                                     │
        │    • compare_chara_dasha()        — 12 MDs diff  │
        │    • compare_functional_roles()   — 9 planets    │
        │                                                  │
        │  Outputs                                         │
        │    • IntegratedReadingOutput                     │
        │    • DkpModulatedReading                         │
        │    • CharaComparisonReport                       │
        │    • FunctionalComparisonReport                  │
        │    • GapAnnotatedReading                         │
        │                                                  │
        │  HTTP routes (v0.3.0)                            │
        │    • GET  /reading/integrated/info               │
        │    • POST /reading/integrated/enhance            │
        │    • POST /reading/integrated/modulate           │
        │    • POST /reading/integrated/compare-chara      │
        │    • GET  /reading/integrated/compare-functional │
        │    • POST /reading/integrated/generate-and-enhance│
        └──────────────────────────────────────────────────┘
```

## Doctrine findings surfaced

### 1. Chara Dasha — Track B has a uniform-12y bug (CRITICAL)

The Chara Dasha comparator immediately exposed two divergence axes:

- **Starting sign**: Track A uses Sanjay-Rath rule (movable=self,
  fixed=5th, dual=9th). Track B starts at the lagna unconditionally.
- **Period length**: Track A produces variable 3/7/11 years totalling
  **84 years**. Track B's `_pick_lord_sign` + `period_for` interact
  pathologically to produce uniform **12 years per MD** totalling 144
  years — almost certainly a bug, not a deliberate variant.

Full post-mortem with file:line citations:
[`doctrine-divergence-chara-dasha-2026-05-31.md`](./doctrine-divergence-chara-dasha-2026-05-31.md)

### 2. Functional benefic/malefic — D-7 doctrine divergence

For Virgo lagna, Track A (D-7 PVR Narasimha Rao) and Track B disagree on
**4 of 7 classical planets**:

| Planet | Track A | Track B |
|---|---|---|
| Sun | neutral | malefic |
| Moon | malefic | (no flags) |
| Mars | malefic | malefic ✓ |
| Mercury | benefic | (lagna_lord, defaults to positive) ✓ |
| Jupiter | malefic | Maraka + Badhakesh |
| Venus | benefic | Maraka + benefic ≈✓ |
| Saturn | benefic | (no flags → neutral) |

Track B also **omits Rahu and Ketu entirely** from
`functional_roles(lagna_sign)` output. Comparator surfaces this via
`planets_only_in_a == ["Rahu", "Ketu"]` and per-planet `agrees=None`.

## Known gaps

- **Gap B (`varga_confirmation`) is structurally skipped.** The Track-B
  function needs per-bhava pillar scores as input which Track A doesn't
  expose directly. A bridge that synthesises pillar scores from
  `DomainReading.confidence.votes` would unlock it; not yet built.
- **`bhavat_bhavam` `__doc__` reading fails on Windows CP1252** (Devanagari
  character `ā` in module docstring). The module IMPORTS cleanly and
  `bhavat_bhavam` is callable from the Gap annotator — only attempting
  to read the docstring via `inspect.getdoc()` or `__doc__` printing
  triggers the encoding error. A Track B issue, independent of this
  integration.
- **`app/main.py` has pre-existing broken imports** (`forecast_routes` and
  `knowledge_routes` from another branch don't exist on `feat/integration`).
  Integration tests sidestep this by using `FastAPI(router=router) +
  TestClient` directly. The route file itself is correct and ready to
  use once main.py is fixed.
- **Adversarial verification of doctrine findings** was planned but the
  workflow agent A3 stalled. The doctrine post-mortem was written by
  manual code-read instead and its conclusions are well-evidenced from
  source citations.

## Testing

```powershell
# All integration tests + HTTP route tests
py -3.12 -m pytest tests/integration/ tests/api/test_reading_integrated_routes.py -q
# Expected: 132 passing in ~0.7s

# By module:
py -3.12 -m pytest tests/integration/test_dkp_enhancer.py             # 19
py -3.12 -m pytest tests/integration/test_chara_compare.py            # 15
py -3.12 -m pytest tests/integration/test_functional_compare.py       # 24
py -3.12 -m pytest tests/integration/test_dkp_modulator_adapter.py    # 22
py -3.12 -m pytest tests/integration/test_gap_annotator.py            # 22
py -3.12 -m pytest tests/integration/test_cli.py                      # 6
py -3.12 -m pytest tests/api/test_reading_integrated_routes.py        # 24
```

Most tests are deterministic and run in microseconds. The Gap-annotator
suite and `generate-and-enhance` HTTP test invoke Track A's actual
`compute()` pipeline once (module-scoped fixture) which adds ~0.6s.

## Versioning

- **v0.1.0** (commit `0496264`, tag `integration-v0.1.0`):
  DKP enhancer + Chara Dasha comparator + CLI. 40 tests.
- **v0.2.0** (commit `deaa8e1`, tag `integration-v0.2.0`):
  + Functional comparator + DKP modulator adapter + Chara Dasha doctrine
  post-mortem. 86 tests.
- **v0.3.0** (this version):
  + Gap-module annotator (7 of 8 modules wireable; Gap B intentionally
  skipped) + FastAPI HTTP routes at `/reading/integrated/*` (6 routes).
  132 tests.

## Where to read more

- [Chara Dasha doctrine divergence post-mortem](./doctrine-divergence-chara-dasha-2026-05-31.md)
- Track A spec: [`docs/superpowers/specs/2026-05-27-kundli-analysis-system-design.md`](../superpowers/specs/2026-05-27-kundli-analysis-system-design.md)
- Track A doctrine lockfile: [`docs/doctrine-decisions.md`](../doctrine-decisions.md)
- Track A schema reference: [`docs/reading/json-schema.md`](../reading/json-schema.md)
