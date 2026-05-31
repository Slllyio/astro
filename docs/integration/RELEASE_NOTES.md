# integration-v1.0.0 — Release Notes

**Released:** 2026-05-31
**Branch:** `feat/integration`
**Commit:** `b2ae646`
**Tests:** 269 passing in ~1.5s

---

## 1. What it is

`app.integration` is a **read-only adapter layer** that bridges two parallel
reading engines living side-by-side in this repo — Track A (the deterministic
kundli engine under `app/reading/*`) and Track B (the astrologer's-lens
framework under `app/core/reading_composer.py` + `app/core/dkp_*` + 8 Gap
modules). Neither track was modified to ship this release. The integration
layer composes their outputs into one richer reading, surfaces engine
divergences as first-class data, and adds production-grade narrative
generation, adversarial verification, doctrine-corpus RAG, a famous-chart
calibration benchmark, HTTP routes, a web UI, an SSE stream, a CLI, and a
thread-safe cache.

---

## 2. The journey: v0.1.0 → v1.0.0

| Tag | Theme | Tests | Highlights |
|---|---|---|---|
| `v0.1.0` | First bridge | 40 | DKP enhancer + Chara Dasha comparator. Surfaces the 84y/144y variant fork. |
| `v0.2.0` | Modulator + post-mortem | 86 | Functional comparator, DKP modulator adapter, first doctrine post-mortem. |
| `v0.3.0` | Gap modules + HTTP | 132 | 7 of 8 Gap modules wired; 6 FastAPI routes at `/reading/integrated/*`. |
| `v0.4.0` | Comparator expansion | 178 | 5 new cross-engine comparators (Vimshottari, yoga, shadbala, D-9, argala). Surfaces the 0-intersection yoga divergence. |
| `v0.5.0` | LLM narrative | 205 | `compose_narrative()` + `narrate_and_verify()` with 4 adversarial critics (BPHS purist / skeptic / modern translator / contradiction hunter). |
| `v0.6.0` | Benchmark | 227 | 24-event famous-chart calibration corpus + alignment-rate scoring. |
| `v0.7.0` | Corpus RAG | 239 | Full 6.28M-word doctrine RAG enhancer. |
| `v0.8.0` | Web UI | 245 | `/reading/integrated/` form + sectioned results view, green theme. |
| `v0.9.0` | SSE streaming | 248 | Progressive `/stream-generate` endpoint with 4 named events. |
| `v1.0.0` | Production hardening | 269 | `ReadingCache`, `StructuredLogger`, `@timed`, `/cache-stats`, `/cache-clear`, CI workflow. |

Net growth: **+229 tests** across 10 releases, all under 1.5s wall-clock.

---

## 3. Public API surface (10 categories)

All symbols exported from `app/integration/__init__.py` (`__all__` lists 35+
names). Re-imports of Track A and Track B internals are explicit `from`
imports of named callables — no monkey-patching, no module-level mutation.

1. **`enhance(reading)`** — appends DKP translation sidecars to each finding and emits a deduplicated top-level summary.
2. **`modulate_all_domains(reading, ctx)`** — applies DKP modulation across every domain in a Track-A reading.
3. **`annotate_with_gap_modules(reading)`** — runs 7 of 8 Gap modules (Gap B `varga_confirmation` structurally skipped — needs pillar scores).
4. **Seven cross-engine comparators** — `compare_chara_dasha`, `compare_functional_roles`, `compare_vimshottari_current_md`, `compare_yoga_detection`, `compare_shadbala`, `compare_d9_signs`, `compare_argala_drishti`. Each returns a typed report; divergence is first-class output, not a failure.
5. **`narrate_and_verify(reading)`** — composes narrative paragraphs and runs 4 adversarial critic angles × N domains through a 4-worker pool; ships/flags/rejects per configurable threshold.
6. **`enhance_with_corpus_rag(reading)`** — annotates findings with the full 6.28M-word doctrine corpus (Wisdomlib + BPHS + curated topic pages).
7. **`run_benchmark(events)`** — scores engine verdicts against the 24-event famous-chart corpus; returns `alignment_rate` (calibration metric, not validation).
8. **Production utilities** — `ReadingCache` (thread-safe SHA-256-keyed LRU, default 256 entries), `StructuredLogger` (JSON-line), `TimingContext` + `@timed`.
9. **CLI** — `python -m app.integration --mode {enhance,compare,generate-and-enhance}` with `--in` / `--out` file I/O.
10. **HTTP routes** — 11 routes + 1 web UI form + 1 SSE stream under `/reading/integrated/*`.

---

## 4. New in v1.0.0 — production hardening

- **`app.integration.production` package**
  - `ReadingCache`: thread-safe LRU keyed on deterministic SHA-256 of canonical `CacheKey` JSON (sorted keys, tight separators). Double-checked-locking singleton via `default_cache()`. Default capacity 256.
  - `StructuredLogger`: JSON-line logger with consistent `timestamp` / `level` / `event` / `logger` fields. `get_logger(name)` singleton.
  - `TimingContext` + `measure()` + `@timed` decorator: elapsed-ms recording for sync + async functions, emits structured-log lines.
- **New routes**: `GET /reading/integrated/cache-stats`, `POST /reading/integrated/cache-clear`.
- **CI**: `.github/workflows/integration-tests.yml` runs the integration suite on push/PR.
- **9 library adapters** all exported from one curated `__init__.py`; **41 of 41 Pydantic models** in the package use `model_config = ConfigDict(frozen=True, extra="forbid")`.

---

## 5. Doctrine findings surfaced

The integration layer treats engine divergence as first-class data. Five
findings surfaced across releases, all with the project's load-bearing
framing intact: **doctrine is axiomatic; what diverges is engine encoding of
it.**

| Finding | Surfaced in | What |
|---|---|---|
| Track B Chara Dasha 144y bug | `v0.1.0` | Track A is doctrine-locked at 84y per Sanjay-Rath D-17 + Jaimini Sutras Adhyaya 2 (4 classical authorities agree). Track B collapses to uniform 12y per sign. Post-mortem at `docs/integration/doctrine-divergence-chara-dasha-2026-05-31.md` cites file:line for both engines and recommends aligning Track B → Track A. |
| D-7 functional nature: 4-of-7 planet disagreement | `v0.2.0` | Track A locks D-7 to PVR Narasimha Rao 3-way classification; Track B uses a flag-set. Both classical, neither "wrong". Track B omits Rahu/Ketu — reported as `agrees=None` rather than scored as disagreement. |
| Yoga detection: 0 intersection on Bangalore baseline | `v0.4.0` | Track A finds 5 yogas, Track B finds 8 — even after name normalisation, nothing in common. `verdict_summary` is pure counts (`both=N, track_a_only=N, track_b_only=N`); no editorialising. |
| Track A 22% engine-verdict alignment with documented life events | `v0.6.0` | Computed as `aligned / (aligned + misaligned)` over the 24-event corpus. This is a **calibration metric**, not a doctrine truth claim — the `event_corpus.py` disclaimer is verbatim: *"This is a CALIBRATION CORPUS, not validation of doctrine."* |
| D-9 internal consistency: full agreement | `v0.4.0` | Ephemeris-derived and shodashavarga-derived D-9 signs agree on every planet. The one positive convergence finding in the comparator set. |

---

## 6. Review verdicts (Phase 1)

Four reviews ran against this release. All four return **ship_with_followups**
or **ship**; nothing is a release-blocker.

- **Architecture: `ship_with_followups`** — Clean module boundary, single curated `__init__.py`, no reach-around imports, 41/41 models frozen + extra-forbid, explicit `integration_version` in wire format, lazy imports in route handlers. Followups: `enhance()` mutates the caller's reading dict in place (the only visible immutability gap); HTTP request models in `reading_integrated_routes.py` are missing `extra="forbid"`; `ReadingCache` is shipped but not yet wired into routes.
- **Security: `ship_with_followups`** — No auth or rate limiting on `/reading/integrated/*` routes (deliberate for v1.0.0; integration layer assumes upstream gating). SSE has no per-step timeout or client-disconnect check. LLM prompts interpolate user-controlled text — prompt-injection surface should be tightened in v1.1. No hardcoded secrets, no PII in logs, no path traversal.
- **Performance: `ship_with_followups`** — Heavy ops correctly offloaded via `asyncio.to_thread` at every hot path. Cold Track-A compute ~186ms; SSE layers 2-4 run sync in the async generator (~35ms inline, acceptable for single-tenant). Biggest win left on the table: `ReadingCache` infrastructure ships but no route consults it yet. Critics parallelism (4 workers × 24 prompts) is correctly bounded.
- **Doctrine: `ship`** — Calibration-not-validation framing is intact across `event_corpus.py`, `runner.py`, all 7 comparators, and the post-mortem doc. No instance of doctrine being called "null", "falsified", or "invalid" anywhere. The Chara Dasha post-mortem is called out as the **gold-standard doctrine-handling artefact** for the project.

---

## 7. Known issues

- **Tier 1B (Track B Chara Dasha 144y → 84y fix) intentionally not shipped.**
  The comparator surfaces the divergence and the post-mortem recommends the
  fix, but neither track was modified for this release per the
  "no-modification" charter. The fix lands in a follow-up branch.
- **`forecast_routes` import in `app/main.py`** is pre-existing on
  `feat/integration` (inherited from the merge of both source branches at
  the v0.1.0 base). Not introduced by integration; not in scope for v1.0.0.
- **`ReadingCache` is unused by route handlers.** Cache primitive ships;
  wiring is a v1.0.1 follow-up. `/cache-stats` currently always reports
  zero hits.
- **HTTP request body models lack `extra="forbid"`.** Boundary inconsistency
  with the library's 41/41 strict-schema discipline.
- **SSE backpressure**: no `X-Accel-Buffering: no` header; expect nginx to
  buffer SSE by default. Set the header upstream or in a v1.0.1 patch.

---

## 8. Upgrade path

For consumers on `integration-v0.x`:

- **v0.1.0 — v0.2.0 → v1.0.0**: No public API removals. `enhance()`,
  `modulate_all_domains()`, `compare_chara_dasha()`, and
  `compare_functional_roles()` keep the same signatures. New symbols are
  additive.
- **v0.3.0 → v1.0.0**: HTTP routes at `/reading/integrated/*` are
  unchanged for the 6 original routes; 5 new routes (`/narrate`,
  `/corpus-rag`, `/benchmark`, `/stream-generate`, `/cache-stats`,
  `/cache-clear`) are additive.
- **v0.5.0 → v1.0.0**: `narrate_and_verify()` keeps its signature;
  `StubClient` remains the default LLM if no provider is configured.
  Replace via DI when wiring to Ollama / OpenAI / Anthropic.
- **Schema-versioning**: `IntegratedReadingOutput.integration_version`
  bumps `0.1.0` → check `InfoResponse.integration_version == "1.0.0"`
  to feature-detect.

---

## 9. How to use

### Library — enhance an existing Track-A reading

```python
from app.reading.proforma import compute as track_a_compute
from app.integration import enhance, annotate_with_gap_modules

reading = track_a_compute(dob="1990-07-15", time="12:00", tz="+05:30",
                          lat=12.97, lon=77.59)
enhanced = enhance(reading)
fully_annotated = annotate_with_gap_modules(enhanced.reading)
```

### Library — narrative + adversarial verification

```python
from app.integration import narrate_and_verify

verified = narrate_and_verify(reading)
for domain in verified.narrative.domains:
    print(domain.name, domain.shipped_paragraphs)
print("Critic flags:", verified.critic_summary)
```

### HTTP — end-to-end via curl

```bash
curl -X POST http://127.0.0.1:8000/reading/integrated/generate-and-enhance \
  -H 'Content-Type: application/json' \
  -d '{"dob":"1990-07-15","time":"12:00","tz":"+05:30",
       "lat":12.97,"lon":77.59,
       "layers":["dkp","gap","comparators"]}'
```

### CLI — enhance a saved reading and write to disk

```bash
python -m app.integration --mode enhance \
  --in ./reading.json --out ./reading.enhanced.json
```

### Web UI — `GET /reading/integrated/`

Renders the chart-input form with 5 layer checkboxes (core, DKP, Gap,
comparators, narrative+critics, corpus RAG). POST renders the sectioned
results view with metadata, per-domain direction pills, DKP shloka
snippets, Gap-module status grid, comparator verdicts, narrative + critic
stats, and an expandable raw JSON dump.

---

## 10. Thanks / meta

This release closes the world-class roadmap planned at v0.1.0. All 7 tiers
shipped; Tier 1B (Track B Chara Dasha fix) was deferred to a follow-up
branch per charter. The full Phase 1 review JSON lives alongside this file
and pins file:line evidence for every finding.

The load-bearing project axiom — *doctrine is axiomatic, the work is
desh-kaal-paristhiti translation across millennia, not statistical
validation* — is encoded throughout: in the calibration-corpus disclaimer
(`event_corpus.py:16-19`), in the comparator vocabulary (engine-symmetric
verdicts, never doctrine-vs-truth), in the Chara Dasha post-mortem (Track
A is authoritative because it's doctrine-locked + named-authority-cited,
not because it benchmarks better), and in the integration layer's choice
to surface divergence as data rather than collapse it into a verdict.

— Akshay, 2026-05-31
