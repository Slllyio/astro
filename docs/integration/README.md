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

## Public API surface (v0.2.0)

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

- **Gap-module annotator not yet implemented.** Track B has 8 Gap modules
  (Ashtakavarga predictive, Bhavat Bhavam, Sensitive Points, Nakshatra
  deep, Varga confirmation, Avastha completion, Vimsopaka Bala,
  Karakamsa+Arudha). Wiring them requires constructing a Track-B `Chart`
  from a Track-A reading — substantial work left for v0.3.0.
- **`bhavat_bhavam` module has a CP1252 encoding bug** on Windows
  (Devanagari character `ā` in module docstring causes ImportError).
  Track B issue, independent of this integration.
- **HTTP routes not yet exposed.** Adapters are CLI + library-only. A
  FastAPI router at `/reading/integrated/*` is planned for v0.3.0.

## Testing

```powershell
# All integration tests
py -3.12 -m pytest tests/integration/ -q
# Expected: 86 passing in ~0.3s

# By module:
py -3.12 -m pytest tests/integration/test_dkp_enhancer.py        # 19
py -3.12 -m pytest tests/integration/test_chara_compare.py       # 15
py -3.12 -m pytest tests/integration/test_functional_compare.py  # 24
py -3.12 -m pytest tests/integration/test_dkp_modulator_adapter.py  # 22
py -3.12 -m pytest tests/integration/test_cli.py                 # 6
```

All tests are deterministic (no swisseph calls) and run in ~0.3s combined.

## Versioning

- **v0.1.0** (commit `0496264`, tag `integration-v0.1.0`):
  DKP enhancer + Chara Dasha comparator + CLI. 40 tests.
- **v0.2.0** (this version):
  + Functional comparator + DKP modulator adapter + Chara Dasha doctrine
  post-mortem. 86 tests.

## Where to read more

- [Chara Dasha doctrine divergence post-mortem](./doctrine-divergence-chara-dasha-2026-05-31.md)
- Track A spec: [`docs/superpowers/specs/2026-05-27-kundli-analysis-system-design.md`](../superpowers/specs/2026-05-27-kundli-analysis-system-design.md)
- Track A doctrine lockfile: [`docs/doctrine-decisions.md`](../doctrine-decisions.md)
- Track A schema reference: [`docs/reading/json-schema.md`](../reading/json-schema.md)
