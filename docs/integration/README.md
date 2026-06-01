# `app.integration` — Track A + Track B bridge

**Status:** shipped — `integration-v1.0.0` (commit `b2ae646`, branch `feat/integration`)

This package is a **read-only adapter layer** between two parallel reading
engines that live in this repo. Neither original engine is modified by
anything under `app/integration/*` — every cross-track reference is a `from`
import of named callables/classes, and every output is a frozen Pydantic
envelope (`model_config = ConfigDict(frozen=True, extra="forbid")`) so
side-effects cannot leak back through the public surface.

For the ship-day announcement, scope summary, and per-tier breakdown, see
[`RELEASE_NOTES.md`](./RELEASE_NOTES.md). For the Chara Dasha doctrine
divergence post-mortem, see
[`doctrine-divergence-chara-dasha-2026-05-31.md`](./doctrine-divergence-chara-dasha-2026-05-31.md).

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
to bridge them without modifying either. Track A is the schema-locked
deterministic core; Track B carries the doctrine-translation depth, DKP
modulation, and Gap modules. The integration package marries the two.

## Public API surface (v1.0.0)

The package exports 35+ symbols via `app.integration.__init__.py`, all
explicitly listed in `__all__`. Ten functional categories:

1. `enhance(reading)` — DKP translation annotator
2. `modulate_all_domains(reading, dkp_context)` — DKP modulation
3. `annotate_with_gap_modules(reading)` — 7 of 8 Gap modules
4. **Seven cross-engine comparators** — Chara Dasha, functional roles,
   Vimshottari current MD, yoga detection, Shadbala, D-9, Argala/Drishti
5. `narrate_and_verify(reading)` — LLM narrative + 4-critic adversarial
   verification
6. `enhance_with_corpus_rag(reading)` — full 6.28M-word doctrine corpus RAG
7. `run_benchmark(events)` — 24-event famous-chart calibration benchmark
8. `ReadingCache` + `StructuredLogger` + `@timed` — production utilities
9. CLI at `python -m app.integration --mode {enhance,compare,generate-and-enhance}`
10. **11 HTTP routes** + **1 web UI** + **1 SSE stream** at
    `/reading/integrated/*`

### Annotators — augment a Track-A reading with Track-B data

```python
from app.integration import enhance

result = enhance(track_a_reading)
# result.reading                       → Track-A reading with per-Finding
#                                        dkp_translations sidecar appended
# result.dkp_translations_summary      → deduplicated top-level summary of
#                                        every cited TranslationRecord
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

### Gap-module annotator — depth from Track B's 8 Gap modules

```python
from app.integration import annotate_with_gap_modules

result = annotate_with_gap_modules(
    track_a_reading, day_of_week=6, is_day_birth=True,
)
# result.gap_modules["A"]  → Ashtakavarga predictive (SAV per bhava, kakshya)
# result.gap_modules["D"]  → Karakamsa + Arudha + Upapada padas
# result.gap_modules["E"]  → Bhrigu Bindu, Pranapada, Upagrahas, Maandi
# result.gap_modules["F"]  → Baladi + Deeptadi avasthas
# result.gap_modules["G"]  → Vimsopaka Bala multi-varga score
# result.gap_modules["H"]  → Nakshatra deep (Moon's nakshatra attributes)
# result.gap_modules["J"]  → Bhavat Bhavam
# Gap B (varga_confirmation) is structurally skipped — needs per-bhava
# pillar scores Track A doesn't expose directly.
```

### Comparators — diff Track A vs Track B on the SAME doctrine (v0.4.0 expansion)

Seven cross-engine comparators are now shipped. The Chara Dasha and
functional-roles comparators landed in v0.1/0.2; v0.4.0 added five more.

| Comparator | Adds |
|---|---|
| `compare_chara_dasha` | 12 MDWindowDiff entries, sign sequence agreement, boundary-JD agreement, current-MD-at-target-JD agreement |
| `compare_functional_roles` | Per-planet (9 planet) functional benefic/malefic agreement; Track B omits Rahu/Ketu so those report `agrees=None` |
| `compare_vimshottari_current_md` | Cross-engine current Mahadasha lord at `target_jd` |
| `compare_yoga_detection` | Set-difference on detected yogas (`both`, `track_a_only`, `track_b_only`); Bangalore baseline surfaces 0-intersection between Track A (5 yogas) and Track B (8 yogas) — an engine-detection-implementation divergence, not a doctrine claim |
| `compare_shadbala` | Six-fold strength components per planet across engines |
| `compare_d9_signs` | Navamsa sign agreement per planet (Bangalore baseline: full agreement) |
| `compare_argala_drishti` | Argala (intervention) and Drishti (aspect) tables |

All seven return frozen Pydantic envelopes with a `verdict_summary` string,
per-entity rows, and counts. Divergence is treated as a first-class output:
the doctrine itself is axiomatic; the two engine encodings of it are what
disagree.

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

### LLM narrative + adversarial verification (v0.5.0)

`compose_narrative` -> `run_critics` -> `narrate_and_verify` is a three-stage
pipeline. The integrated reading is ~1 MB of structured JSON; the narrative
layer composes it into a polished, doctrine-grounded paragraph per domain,
then immediately runs four adversarial critics that try to **refute** each
claim before it ships:

- **BPHS purist** — does this match canonical doctrine?
- **Skeptic** — is this claim plausible-but-wrong?
- **Modern translator** — does this apply to 2026 life context?
- **Contradiction hunter** — does this contradict another claim?

Each domain runs 4 critics; survival threshold is `>= 3 of 4 confirm`.
Domains below threshold are shipped with `status="flagged"` and the
dissenting verdicts attached; domains with majority-reject are `rejected`.

```python
from app.integration import narrate_and_verify

verified = narrate_and_verify(reading, integrated=integrated_payload)
# verified.overall_summary
# verified.survival_threshold       → 3
# verified.per_domain[*].status     → "shipped" / "flagged" / "rejected"
# verified.per_domain[*].confirm_count
# verified.per_domain[*].critic_reviews
# verified.domains_shipped / domains_flagged / domains_rejected
```

The `LLMClient` Protocol lets backends swap without touching the integration
layer; `StubClient` is used when none is configured so tests + offline usage
work without API keys or Ollama running. `OllamaClient` is shipped for local
inference (default 30s per-call timeout). Critics fan out via
`concurrent.futures.ThreadPoolExecutor(max_workers=4)` so 4 angles × 6
domains = 24 prompts complete in ~6 sequential batches.

### Famous-chart calibration benchmark (v0.6.0)

The benchmark scores the engine's verdict polarity against 24 well-documented
historical events across 6 charts:

| Chart | Source | Events |
|---|---|---|
| Albert Einstein | Astro-Databank | 4 (marriage, Annus Mirabilis, divorce, Nobel) |
| Mahatma Gandhi | Astro-Databank | events across career + life |
| Barack Obama | Astro-Databank | events across career + family |
| Steve Jobs | Astro-Databank | events across career + health |
| A.P.J. Abdul Kalam | Wikipedia | events across career + recognition |
| Ramana Maharshi | Wikipedia | events across spiritual life |

```python
from app.integration import FAMOUS_EVENTS, run_benchmark

report = run_benchmark(events=FAMOUS_EVENTS)
# report.alignment_rate     → fraction of events where engine verdict
#                             direction agreed with documented polarity
# report.per_chart[*]       → PerChartSummary (aligned/misaligned/neutral/mixed/skipped)
# report.per_domain[*]      → PerDomainSummary
# report.per_event[*]       → EventOutcome
```

The corpus carries an explicit doctrine disclaimer:

> **This is a CALIBRATION CORPUS, not validation of doctrine. Doctrine is
> axiomatic; we just check whether the engine's verdicts at event dates
> align with documented outcomes.**

Per-chart Track-A reading results are memoized inside the runner so the 24
events / 6 charts pass costs roughly 6 Track-A computes, not 24. Vocabulary
is engine-vs-event throughout: `aligned`, `misaligned`, `neutral`, `mixed`,
`skipped`. The word "accuracy" never appears.

Surfaced finding: Track A's overall verdict direction aligns with documented
event polarity in **~22% of cases** — read as a **calibration figure for the
engine's verdict polarity**, not a doctrine truth claim.

### Corpus RAG enhancer (v0.7.0)

`enhance_with_corpus_rag` walks every finding in a Track-A reading and
queries the **full 6.28M-word doctrine corpus** (918 artefacts, multilingual
RAG index) for the top-k passages most relevant to each finding's
`rule + verdict` text.

```python
from app.integration import enhance_with_corpus_rag

enriched = enhance_with_corpus_rag(
    reading, top_k=3, max_findings=50,
)
# enriched.reading                    → original reading with corpus citations
#                                       attached per finding
# enriched.corpus_citations_summary   → deduplicated top-level summary
# enriched.findings_processed         → int
```

The enhancer gracefully degrades when the RAG index is not available on the
host (e.g. dev laptops without the embedding model) — citations come back
empty rather than the route crashing. Server-side caps: callers can cap
`max_findings` and `top_k` to bound fan-out.

### Web UI (v0.8.0)

A pothi-manuscript-styled web UI is mounted at the router root:

| Route | Purpose |
|---|---|
| `GET /reading/integrated/` | Chart-input form (Bangalore baseline pre-fillable) |
| `POST /reading/integrated/generate` | Form submission renders the integrated view template with per-layer toggle checkboxes (`layer_dkp`, `layer_gap`, `layer_comparators`, `layer_narrative`, `layer_corpus`) so the user picks which slices of the pipeline they want rendered |

Renders Lagna summary, current Mahadasha lord, six domain verdict tiles,
DKP shloka panel (up to 10 records with first 200 chars each), Gap-module
summary, comparator results, and the narrative pane (per-domain paragraphs
with shipped/flagged/rejected status colour-coding). The full payload
(`core` + `integrated` + `modulated` + `gap_annotated` + `comparators` +
`narrative`) is exposed as a capped 50KB `raw_json` block for debugging.

### SSE streaming (v0.9.0)

```
POST /reading/integrated/stream-generate
Content-Type: application/json
Accept: text/event-stream

{ "dob": "1990-07-15", "time": "12:00", "tz": "+05:30",
  "lat": 12.97, "lon": 77.59, "enrich": false }
```

The endpoint emits four `layer` events plus a terminal `complete` event so
clients can render progressively without waiting on the full ~500-700ms
pipeline:

```
event: layer
data: {"layer": "core", "status": "running"}

event: layer
data: {"layer": "core", "status": "complete", "elapsed_ms": 612,
       "schema_version": "1.2.0"}

event: layer
data: {"layer": "dkp_enhance", "status": "running"}
...
event: complete
data: {"layers_completed": ["core","dkp_enhance","dkp_modulate","gap_modules"],
       "total_elapsed_ms": 681}
```

The heavy `track_a_compute` call is offloaded via `asyncio.to_thread` so the
event loop stays responsive. On error, an `event: error` frame names the
failing layer and the response terminates cleanly.

### Production hardening (v1.0.0)

Three primitives under `app/integration/production/*`:

- **`ReadingCache`** — thread-safe in-memory LRU cache (default capacity 256)
  with deterministic SHA-256 fingerprinting of canonical input. Singleton
  via `default_cache()` with double-checked locking. `get_or_compute(key,
  compute_fn)` is the primary API. Cache keys are produced via
  `make_cache_key(...)` which JSON-serializes inputs with `sort_keys=True`
  + tight separators before hashing, so semantically-identical inputs
  always produce the same fingerprint regardless of dict ordering. An
  opaque `extras` tag lets callers vary by layer-combo without changing the
  schema.

- **`StructuredLogger`** — JSON-line logger with consistent fields (`event`,
  `correlation_id`, `elapsed_ms`, ...) for trace correlation in
  production. `get_logger(name)` returns the project-standard instance.

- **Timing primitives** — `TimingContext` context manager, `measure(name)`
  factory, and `@timed` decorator for measuring adapter call latency.

```python
from app.integration import ReadingCache, default_cache, make_cache_key, timed

cache = default_cache()
key = make_cache_key(dob="1990-07-15", time="12:00", tz="+05:30",
                    lat=12.97, lon=77.59, extras="enrich=false")
reading = cache.get_or_compute(key, lambda: track_a_compute(ci))
```

```python
from app.integration import timed

@timed("dkp_enhance")
def my_pipeline(reading):
    ...
```

Two observability routes are wired up:

| Route | Purpose |
|---|---|
| `GET /reading/integrated/cache-stats` | Returns the default `ReadingCache` size, hit rate, evictions |
| `POST /reading/integrated/cache-clear` | Clears the default cache and returns the post-clear stats |

The cache primitives ship in v1.0.0 as **infrastructure**; wiring them into
the existing `enhance` / `generate-and-enhance` / `stream-generate` routes
is a deliberate v1.1.0 follow-up so the routes don't change behaviour at
the v1.0.0 release boundary.

## HTTP routes — full surface (v1.0.0)

`app.api.reading_integrated_routes.router` exposes 11 JSON routes, 1
HTML form, 1 HTML view, and 1 SSE stream — all under `/reading/integrated/*`:

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| GET  | `/reading/integrated/` | — | HTML form (web UI) |
| POST | `/reading/integrated/generate` | form-encoded `dob, time, tz, lat, lon, layer_*` | HTML view rendering selected layers |
| GET  | `/reading/integrated/info` | — | Integration metadata + adapter list + DKP registry size |
| POST | `/reading/integrated/enhance` | `{"reading": {...}}` | `IntegratedReadingOutput` |
| POST | `/reading/integrated/modulate` | `{"reading": {...}, "dkp_context_overrides": {...}}` | `DkpModulatedReading` |
| POST | `/reading/integrated/compare-chara` | `{"track_a_chara_dasha": {...}, "lagna_sign": N, "birth_jd": F, "target_jd": F?}` | `CharaComparisonReport` |
| GET  | `/reading/integrated/compare-functional` | `?lagna_sign=N` | `FunctionalComparisonReport` |
| POST | `/reading/integrated/corpus-rag` | `{"reading": {...}, "top_k"?: int, "max_findings"?: int}` | `CorpusRAGEnhancedReading` |
| GET  | `/reading/integrated/benchmark` | `?chart_name=...` (optional filter) | `BenchmarkReport` |
| POST | `/reading/integrated/narrate` | `{"reading": {...}, "integrated"?: {...}}` | `VerifiedNarrative` |
| POST | `/reading/integrated/stream-generate` | `GenerateAndEnhanceRequest` | `text/event-stream` (SSE) |
| POST | `/reading/integrated/generate-and-enhance` | `GenerateAndEnhanceRequest` | `IntegratedReadingOutput` (runs Track A's compute() internally) |
| GET  | `/reading/integrated/cache-stats` | — | `ReadingCache` stats |
| POST | `/reading/integrated/cache-clear` | — | Post-clear stats |

Wired into `app/main.py` at the same place as `reading_v15_router`. All
heavy compute paths offload to a worker thread via `asyncio.to_thread` so
the event loop stays responsive. Lazy imports inside route handlers keep
the router module's cold-start path fast.

## CLI

```powershell
# Enhance a saved reading.json with DKP translations:
py -3.12 -m app.integration --mode enhance --in reading.json --out enhanced.json

# Generate + enhance in one shot:
py -3.12 -m app.integration --mode generate-and-enhance `
    --dob=1990-07-15 --time=12:00 --tz=+05:30 `
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
        │  app/integration/  (this package, v1.0.0)        │
        │                                                  │
        │  Annotators                                      │
        │    • enhance()              — DKP translations   │
        │    • modulate_all_domains() — DKP modulation     │
        │    • annotate_with_gap_modules() — 7/8 Gap mods  │
        │    • enhance_with_corpus_rag() — 6.28M-word RAG  │
        │                                                  │
        │  Comparators (7)                                 │
        │    • compare_chara_dasha                         │
        │    • compare_functional_roles                    │
        │    • compare_vimshottari_current_md              │
        │    • compare_yoga_detection                      │
        │    • compare_shadbala                            │
        │    • compare_d9_signs                            │
        │    • compare_argala_drishti                      │
        │                                                  │
        │  Narrative + verification                        │
        │    • compose_narrative()  — LLM domain paras     │
        │    • run_critics()        — 4 angles × N domains │
        │    • narrate_and_verify() — combined pipeline    │
        │                                                  │
        │  Calibration benchmark                           │
        │    • run_benchmark()  — 24 events × 6 charts     │
        │    • FAMOUS_EVENTS    — ground-truth corpus      │
        │    • CHART_REGISTRY   — 6 famous charts          │
        │                                                  │
        │  Production utilities                            │
        │    • ReadingCache + default_cache()              │
        │    • StructuredLogger + get_logger()             │
        │    • @timed + measure() + TimingContext          │
        │                                                  │
        │  Output envelopes (Pydantic, frozen, extra=forbid)│
        │    • IntegratedReadingOutput                     │
        │    • DkpModulatedReading                         │
        │    • CharaComparisonReport, FunctionalComp...    │
        │    • VimshottariCurrentMDReport, YogaComp...     │
        │    • ShadbalaComparisonReport, D9Comp..., Argala │
        │    • GapAnnotatedReading                         │
        │    • NarrativeOutput, CriticReview, VerifiedNarr │
        │    • BenchmarkReport, PerChartSummary, ...       │
        │    • CorpusRAGEnhancedReading                    │
        │                                                  │
        │  HTTP surface (15 endpoints)                     │
        │    • 1 HTML form + 1 HTML view                   │
        │    • 11 JSON routes                              │
        │    • 1 SSE streaming route                       │
        │    • 2 cache observability routes                │
        └──────────────────────────────────────────────────┘
```

## Doctrine findings surfaced

The comparator suite treats doctrine as axiomatic and surfaces engine-vs-engine
divergence as **data**. Five concrete findings shipped with v1.0.0:

### 1. Chara Dasha — Track B has a uniform-12y bug (CRITICAL)

The Chara Dasha comparator immediately exposed two divergence axes:

- **Starting sign**: Track A uses Sanjay-Rath rule (movable=self,
  fixed=5th, dual=9th). Track B starts at the lagna unconditionally.
- **Period length**: Track A produces variable 3/7/11 years totalling
  **84 years** (Jaimini Sutras Adhyaya 2 + Sanjay-Rath Crux Ch.16 — D-17).
  Track B's `_pick_lord_sign` + `period_for` interact pathologically to
  produce uniform **12 years per MD** totalling **144 years** — almost
  certainly a bug, not a deliberate variant. Track A is treated as
  authoritative because of its explicit D-17 doctrine lockfile + named
  classical authority sentinel at `chara_dasha.py:114-116`, not because
  it benchmarks better.

Full post-mortem with file:line citations (Sanjay-Rath, K.N. Rao, Iranganti
Rangacharya, PVR Narasimha Rao consensus on 84y):
[`doctrine-divergence-chara-dasha-2026-05-31.md`](./doctrine-divergence-chara-dasha-2026-05-31.md)

### 2. Functional benefic/malefic — D-7 doctrine encoding divergence

For Virgo lagna, Track A (D-7 PVR Narasimha Rao 3-way classification) and
Track B (flag-set system) disagree on **4 of 7 classical planets**:

| Planet | Track A | Track B |
|---|---|---|
| Sun | neutral | malefic |
| Moon | malefic | (no flags) |
| Mars | malefic | malefic OK |
| Mercury | benefic | (lagna_lord, defaults to positive) OK |
| Jupiter | malefic | Maraka + Badhakesh |
| Venus | benefic | Maraka + benefic approx-OK |
| Saturn | benefic | (no flags → neutral) |

Track B also **omits Rahu and Ketu entirely** from
`functional_roles(lagna_sign)`. The comparator surfaces this via
`planets_only_in_a == ["Rahu", "Ketu"]` and per-planet `agrees=None` for
those planets — modelled as "one engine doesn't speak to this", not as
disagreement.

### 3. Yoga detection — 0 intersection on Bangalore baseline

`compare_yoga_detection` on the Bangalore baseline (1990-07-15, Virgo lagna)
finds Track A detects 5 yogas, Track B detects 8 yogas, and the
intersection is empty. This is an **engine-detection-implementation
divergence** (different detection orders, different yoga sets carried),
not a yoga-doctrine truth claim. The comparator reports pure counts
(`both=N, track_a_only=N, track_b_only=N`) without editorialising.

### 4. D-9 internal consistency — full agreement

`compare_d9_signs` on the Bangalore baseline produces full per-planet
agreement between Track A and Track B Navamsa sign assignments — a healthy
shared foundation amid the dasha-system divergences.

### 5. Track A calibration — 22% verdict-polarity alignment

The famous-chart benchmark surfaced that Track A's overall verdict
direction aligns with the documented polarity of historical events in
~22% of cases. This is a **calibration figure for the engine's verdict
polarity**, not a doctrine truth claim, and not "doctrine is 22% true".
The corpus disclaimer (`event_corpus.py:16-19`) and the runner's
vocabulary (`aligned`, `misaligned`, `neutral`, `mixed`, `skipped` —
never `accuracy`, `truth`, or `validation`) preserve this framing
end-to-end.

## Known gaps + v1.1.0 follow-ups

- **Gap B (`varga_confirmation`) is structurally skipped.** The Track-B
  function needs per-bhava pillar scores as input which Track A doesn't
  expose directly. A bridge that synthesises pillar scores from
  `DomainReading.confidence.votes` would unlock it; not yet built.
- **`bhavat_bhavam` `__doc__` reading fails on Windows CP1252** (Devanagari
  character in module docstring). The module IMPORTS cleanly and is
  callable from the Gap annotator — only attempting to read the docstring
  via `inspect.getdoc()` triggers the encoding error. A Track B issue,
  independent of this integration.
- **`ReadingCache` is shipped but not wired into routes.** v1.0.0 ships the
  cache primitive as infrastructure; the existing `enhance` /
  `generate-and-enhance` / `stream-generate` routes still compute fresh
  per request. Wiring `default_cache().get_or_compute(...)` into those
  routes is a deliberate v1.1.0 follow-up so route behaviour doesn't
  change at the v1.0.0 release boundary.
- **Auth + rate-limiting on `/reading/integrated/*`.** The router is mounted
  without `Depends(CurrentAccount)` and without `@limiter.limit(...)` in
  v1.0.0 — consistent with the route module's "thin HTTP veneer" framing
  but a known gap before public exposure. Tracked for v1.1.0 alongside
  the cache wiring.

## Testing

```powershell
# All integration tests + HTTP route tests
py -3.12 -m pytest tests/integration/ tests/api/test_reading_integrated_routes.py -q
# Expected: 269 passing in ~1.5s
```

```powershell
# By module:
py -3.12 -m pytest tests/integration/test_dkp_enhancer.py             # DKP enhancer
py -3.12 -m pytest tests/integration/test_chara_compare.py            # Chara comparator
py -3.12 -m pytest tests/integration/test_functional_compare.py       # D-7 comparator
py -3.12 -m pytest tests/integration/test_dkp_modulator_adapter.py    # DKP modulator
py -3.12 -m pytest tests/integration/test_gap_annotator.py            # Gap modules
py -3.12 -m pytest tests/integration/test_vimshottari_compare.py      # Vimshottari comparator
py -3.12 -m pytest tests/integration/test_yoga_compare.py             # Yoga comparator
py -3.12 -m pytest tests/integration/test_shadbala_compare.py         # Shadbala comparator
py -3.12 -m pytest tests/integration/test_d9_compare.py               # D-9 comparator
py -3.12 -m pytest tests/integration/test_argala_drishti_compare.py   # Argala/Drishti comparator
py -3.12 -m pytest tests/integration/narrative/                        # composer + critics + synthesizer
py -3.12 -m pytest tests/integration/benchmark/                        # benchmark runner
py -3.12 -m pytest tests/integration/test_corpus_rag_enhancer.py      # corpus RAG enhancer
py -3.12 -m pytest tests/integration/test_production.py               # ReadingCache + logger + timing
py -3.12 -m pytest tests/integration/test_cli.py                      # CLI
py -3.12 -m pytest tests/api/test_reading_integrated_routes.py        # HTTP routes (incl. SSE)
```

Most tests are deterministic and run in microseconds. The Gap-annotator
suite, `generate-and-enhance` HTTP test, and benchmark runner invoke Track A's
actual `compute()` pipeline (module-scoped fixtures + per-chart memoization
inside the benchmark runner) — those dominate the 1.5s total.

Total: **269 tests** across the 9 integration modules + LLM narrative
sub-suite + benchmark sub-suite + production hardening + 24 HTTP route
tests. All green at commit `b2ae646`.

## Versioning

Ten tags shipped — `integration-v0.1.0` through `integration-v1.0.0`:

| Tag | Commit | Adds | Tests |
|---|---|---|---|
| `integration-v0.1.0` | `0496264` | DKP enhancer + Chara Dasha comparator + CLI | 40 |
| `integration-v0.2.0` | `deaa8e1` | Functional comparator + DKP modulator adapter + Chara Dasha doctrine post-mortem | 86 |
| `integration-v0.3.0` | `5bcd768` | Gap-module annotator (7 of 8 modules; Gap B structurally skipped) + 6 FastAPI HTTP routes at `/reading/integrated/*` | 132 |
| `integration-v0.4.0` | `b8f107a` | **5 new cross-engine comparators** — Vimshottari current MD, yoga detection, Shadbala, D-9 signs, Argala/Drishti | ~175 |
| `integration-v0.5.0` | `464146f` | **LLM narrative + 4-critic adversarial verification** — `compose_narrative` / `run_critics` / `narrate_and_verify` over an `LLMClient` Protocol with `StubClient` + `OllamaClient` backends | ~205 |
| `integration-v0.6.0` | `b4f3ab7` | **Famous-chart calibration benchmark** — 24 events / 6 charts / 6 domains with per-chart Track-A memoization, alignment-rate scoring vocabulary | ~225 |
| `integration-v0.7.0` | `f435a1f` | **Full 6.28M-word doctrine-corpus RAG enhancer** — `enhance_with_corpus_rag` with graceful fallback when the index is absent | ~240 |
| `integration-v0.8.0` | `4132de2` | **Polished web UI** at `/reading/integrated/` — chart-input form + view template with per-layer toggles + DKP shloka panel + comparator + narrative panes | ~250 |
| `integration-v0.9.0` | `ab1e249` | **SSE streaming** at `/reading/integrated/stream-generate` — 4 layer events + terminal complete event, `asyncio.to_thread` for the heavy compute | ~260 |
| `integration-v1.0.0` | `b2ae646` | **Production hardening (Tier 4)** — `ReadingCache` (thread-safe LRU, SHA-256 fingerprint, `default_cache()` singleton) + `StructuredLogger` + `@timed` / `TimingContext` / `measure` + `/cache-stats` + `/cache-clear` observability routes. `InfoResponse.integration_version` bumped to `1.0.0`. | **269** |

The v1.0.0 release surface is feature-complete for the integration layer's
charter: **read-only over Track A + Track B, no engine modification, every
output a frozen Pydantic envelope, doctrine treated as axiomatic with
divergence surfaced as data, full HTTP + CLI + SSE surface, production
observability primitives in place**.

Benchmark run time end-to-end: **~1.5s for the full 269-test suite** on
the canonical dev hardware (Windows 11, Python 3.12).

## Where to read more

- **Ship-day announcement** — [`RELEASE_NOTES.md`](./RELEASE_NOTES.md)
- **Chara Dasha doctrine divergence post-mortem** —
  [`doctrine-divergence-chara-dasha-2026-05-31.md`](./doctrine-divergence-chara-dasha-2026-05-31.md)
- **Track A spec** —
  [`docs/superpowers/specs/2026-05-27-kundli-analysis-system-design.md`](../superpowers/specs/2026-05-27-kundli-analysis-system-design.md)
- **Track A doctrine lockfile** — [`docs/doctrine-decisions.md`](../doctrine-decisions.md)
- **Track A schema reference** — [`docs/reading/json-schema.md`](../reading/json-schema.md)
- **Project-wide CLAUDE.md** — locked astrology-domain conventions
  (Lahiri ayanamsa, `DAYS_PER_VEDIC_YEAR=365.2425`, whole-sign drishti,
  circular orb distance, floor-division nakshatra cusps, JD arithmetic
  for calendar dates) all of which the integration layer respects via
  Track A's locked enforcement.
