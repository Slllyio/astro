# Kundli Analysis System — Design Spec (post-review revision 1)

**Status:** Reviewed by 7 parallel agents (architect, doctrine, ML-audit, code-quality, performance, QA, schema). Refinements integrated.
**Author:** Akshay (via brainstorming session 2026-05-27)
**Owner module:** `app/reading/`
**Target ship:** v1 engine-only in ~7–8 weeks
**Review verdicts:** Architect = Approve-with-changes · Doctrine = ambiguities+2 errors fixed · ML-audit = 3 NO-GO modules shipping with mandatory Methodology declarations · Performance = budget rewritten per Stage-8 batching plan · QA = test target raised 200→350+

---

## 1. Goals

Build a Python module `app/reading/` that, given **DOB + time + place** as input, emits a comprehensive **deterministic JSON** containing a structured Vedic kundli analysis. Output is rich enough to drive a future LLM narrative layer (v1.5) or any downstream UI.

The system implements the user's NotebookLM proforma (`Kundli Analysis Proforma`, notebook id `ea78b9da-…`) — six analytical methodologies sourced from BPHS, Varga System Handbook, KP literature, and "How to Judge a Mahadasha" — restricted to **Parashari + Jaimini** doctrine.

## 2. Scope (locked)

| Decision | Value |
|---|---|
| **Doctrine scope** | Parashari + Jaimini. **KP explicitly out.** |
| **Output shape** | Deterministic JSON. Full lifetime report + current-dasha deep dive + structured per-domain readings. |
| **Antardasha depth** | Current AD + leftover ADs of current MD + first 3 ADs of next MD. |
| **Domain coverage** | 6 domains: career, marriage, health, wealth, children, education. |
| **Surface** | CLI only for v1 (`python -m app.reading.cli`). No web UI. No HTTP route. |
| **MVP scope** | Engine-only: deterministic JSON. LLM narration is v1.5 (separate spec). |
| **Architectural style** | Approach A — module per notebook sequence, with shared `computations/` for primitives needed by multiple sequences. |
| **Enrichment tier** | Tier 0 + 1 + 2 + 3 (full depth, ~59 modules including D24, ~6300 LOC). |
| **Imports topology** | Strict downhill: `app/core/*` → `computations/*` → `sequences/*.py` → `domains/*` → `proforma.py` → `cli.py`. |
| **Schema versioning** | Lock at `1.0.0`. `Meta.stability = "experimental"` until first downstream consumer ships. Field-shape stable; values may shift as Methodology declarations evolve. |
| **Birth-time robustness** | Full ±5/±10min sub-runs ship in v1. Adds ~4s cold; cache miss expected on sub-runs (different `jd`). |
| **Phase 1 critical-path gate** | Doctrine lockfile (`docs/doctrine-decisions.md`) is Phase 1 sub-task #1 — must exist before any computation module is written. 16 locks documented in Section 13. |
| **Tier 3 discipline** | All 6 enrichment modules MUST publish a `Methodology:` docstring block per template in Section 14. Anti-prediction-trap discipline enforced by code review, not scope cuts. |

## 3. Existing-capability inventory (audited)

| Already in `app/core/*` | Status |
|---|---|
| Lahiri ayanamsa, JD math, planet positions | ✅ Ready |
| Whole-sign houses, ascendant | ✅ Ready |
| Dignity (exalt/debilitate/own/MT/naisargika) | ✅ Ready |
| Combustion, Vargottama detection | ✅ Ready |
| Avastha (Baladi, Jagradadi) | ✅ Ready |
| Shadbala Phase 0 (Sthana-bala only) | 🟡 Partial — Phase 1 (Dig/Kala/Cheshta/Naisargika/Drik) missing |
| Ashtakavarga (BAV + SAV) | ✅ Ready, but no interpretive layer |
| Shodashavarga D2–D60 | ✅ Ready |
| Mahadasha + Antardasha + Pratyantar | ✅ Ready |
| Yogas: Pancha Mahapurusha, Gajakesari, Budha-Aditya | ✅ Ready |
| Yoga strength (yoga_strength.py, yoga_types.py) | ✅ Ready |
| RAG knowledge index (paraphrase-multilingual-MiniLM-L12-v2) | ✅ Ready |
| LLM interpreter + citations | ✅ Ready (used only at v1.5) |
| Sade Sati transit | ✅ Ready, needs severity layer |
| Forecast cache (`forecast_cache.py`) | ✅ Reusable for reading cache |

**Gaps the v1 build addresses:** karakas, Arudha/Upapada, Karakamsha, Vimsopaka, Ishta Phal, residential strength, Gulika + upagrahas, Gandanta, functional nature per lagna, Bhava Chalit, Bhava-Bala, Shadbala Phase 1, ashtakavarga interpretive layer, Argala/Virodhargala, Jaimini drishti, karaka triangulation, 3-vote confidence, MKS, Trika doctrine, marriage trigger, 5-pillar D10, sade-sati severity, Graha Yuddha, special lagnas, eclipse activation, extended yogas catalog, remedies, rookie guards, D2/D3/D7/D9/D10/D12/D60 interpretive readings, all 4 sequence orchestrators, 6 domain synthesizers, 6 Tier-3 enrichments.

## 4. Module layout

```
app/reading/
├─ __init__.py
├─ schema.py                                # Pydantic models for all JSON output
│
├─ computations/                            # Pure-function primitives (no side effects)
│  │
│  │  ── Tier 0: chart primitives ───────────────────────────
│  ├─ karakas.py                            # Jaimini 7 karakas (AK, AmK, BK, MK, PK, GK, DK)
│  ├─ arudha_upapada.py                     # Arudha Lagna + A2..A12 + UL + UL_2
│  ├─ karakamsha.py                         # Karakamsha Lagna (D9 sign of AK)
│  ├─ vimsopaka.py                          # 20-point Shodashavarga-weighted scoring
│  ├─ ishta_phal.py                         # Ishta Phal + Kashta Phal
│  ├─ residential_strength.py               # Bhaav-madhya degree-distance
│  ├─ gulika.py                             # Gulika + Mandi/Yamakantaka/Kala upagrahas
│  ├─ gandanta.py                           # Water-to-fire nakshatra junction
│  ├─ planet_retrograde.py                  # ★ Retrogression flag (extends planet_state.py) — renamed from planet_state_ext.py per code-reviewer
│  ├─ avasthas.py                           # Deeptadi 9-state classification
│  ├─ panchanga_reader.py                   # Natal tithi/vara/nakshatra/yoga/karana interpretive
│  │
│  │  ── Tier 1: foundational doctrine ──────────────────────
│  ├─ functional_nature.py                  # Functional Benefic/Malefic per Lagna (Laghu Parashari)
│  ├─ bhava_chalit.py                       # Sripati cusps; rashi vs bhava placement
│  ├─ bhava_bala.py                         # 6-fold house strength
│  ├─ shadbala_phase1.py                    # Dig/Kala/Cheshta/Naisargika/Drik-bala
│  ├─ ashtakavarga_reader.py                # Interpretive layer over existing ashtakavarga.py
│  ├─ argala.py                             # Argala + Virodhargala (Jaimini intervention/blocking)
│  ├─ jaimini_drishti.py                    # Movable→fixed, fixed→movable, dual→dual
│  ├─ karaka_triangulation.py               # 7H from Lagna ∩ Moon ∩ Venus etc.
│  ├─ confidence_voting.py                  # 3-vote rule (house + lord + karaka)
│  │
│  │  ── Tier 2: practitioner-grade ─────────────────────────
│  ├─ marana_karaka_sthana.py               # MKS red-flag table
│  ├─ trika_doctrine.py                     # Trika-lord Vipareeta detection + 6/8/12 exchange
│  ├─ marriage_trigger.py                   # UL + 7L + D9 disp + transit compound rule
│  ├─ sade_sati_severity.py                 # AV-modulated phase severity
│  ├─ graha_yuddha.py                       # Planetary war (within 1°)
│  ├─ special_lagnas.py                     # Hora / Ghatika / Sree / Bhava / Pranapada
│  ├─ eclipse_natal_activation.py           # Eclipse degree ↔ natal nakshatra (6-month flags)
│  ├─ yogas_extended.py                     # Adhi/Lakshmi/Saraswati/Daridra/Chamara/Vipareeta/
│  │                                        # Parivartana/Kala Sarpa/Neech Bhanga
│  ├─ remedies.py                           # Mantras/gems/daan with lagna-suitability gating
│  ├─ rookie_guards.py                      # Refuse-to-output invariants
│  ├─ divisional_readings/                  # NOTE: positional-but-derived; lives in computations/ but functions as a Tier-1-equivalent
│  │   ├─ d2_hora.py                        # Wealth/source framing
│  │   ├─ d3_drekkana.py                    # Siblings/initiative
│  │   ├─ d7_saptamsa.py                    # Children (each parent's 7th from 5L)
│  │   ├─ d9_navamsha.py                    # Dharma/actual potential mapping
│  │   ├─ d10_dashamsha.py                  # Artha/karmic execution (absorbs 5-pillar voting)
│  │   ├─ d12_dwadasamsa.py                 # Parents/heritage
│  │   ├─ d24_chaturvimsamsa.py             # ★ NEW (doctrine-fix) — Education/learning. domains/education.py routes through this. BPHS 6.21.
│  │   └─ d60_shashtiamsa.py                # Past-life karma
│  │
│  │  ── Tier 3: ML/RAG descriptive enrichments ─────────────
│  ├─ rag_citations.py                      # Per-finding retrieval via knowledge_search.py
│  ├─ consensus_scoring.py                  # Agreement fraction across retrieved passages
│  ├─ contradiction_detector.py             # Cross-sequence verdict diff
│  ├─ dispute_surfacing.py                  # Doctrine-version disagreement flags
│  ├─ yoga_calibration.py                   # Strength score per yoga (extends yoga_strength.py)
│  └─ birth_time_robustness.py              # ±5/±10min sensitivity per judgment
│
├─ sequences/                               # ★ MOVED — was flat at root. Now mirrors computations/ and domains/. Future-proof for sequence_7_chara_dasha.
│  ├─ __init__.py                           # exports SEQUENCES = {"amsha_bala": run_1, "career": run_2, ...}
│  ├─ amsha_bala_krama.py                   # BPHS D1 → D9 → specific Varga → Dasha activation
│  ├─ career_executive.py                   # Notebook Sequence 2 (Vargottama → Gandanta → Vimsopaka → Gulika)
│  ├─ vimshottari_md.py                     # 19-step MD judgment. Pre-Phase-4 KP-contamination audit required.
│  └─ vimshottari_ad.py                     # 7-step AD judgment
│
├─ domains/
│  ├─ career.py
│  ├─ marriage.py
│  ├─ health.py
│  ├─ wealth.py
│  ├─ children.py
│  └─ education.py
│
├─ proforma.py                              # Orchestrator: chart → sequences → domains → JSON
└─ cli.py                                   # python -m app.reading.cli --dob ... --time ... --lat ... --lon ... --tz ...
```

**Module count:** 58 files. Each ≤400 LOC except `yogas_extended.py` (~600), `remedies.py` (~500), `sequence_5_vimshottari_md.py` (~600).

### Key boundary disciplines

1. **Domains are pure synthesizers** — they consume upstream Finding objects by id; they NEVER do D-chart math themselves.
2. **No cross-sequence imports** — `sequence_5_*` cannot import `sequence_6_*`. They only share via `computations/*`.
3. **`_run_core_pipeline` is private** — Birth-time robustness imports the private function directly, bypassing the Tier-3 wrapper. Eliminates recursion risk.
4. **Sequence file naming reserves the namespace** — `sequence_5_vimshottari_md.py` admits this is the Vimshottari-specific orchestrator, so `sequence_7_chara_dasha.py` is a natural future extension.

## 5. Data flow (pipeline)

Nine-stage DAG. Stages 0–7 are pure deterministic. Stage 8 is the Tier-3 afterpass (RAG, consensus, contradictions, robustness). Stage 9 is output write.

```
0. CLI input + validation          → ChartInput
1. Natal chart compute (app/core)  → NatalChart
2. Tier 0 primitives                → Primitives
3. Tier 1 foundations               → Foundations
4. Tier 2 practitioner              → Practitioner
5. Sequences (4)                    → SequenceResults
6. Domain synthesis (6)             → DomainReadings
7. Deterministic JSON assembly      → BaseOutput   ← _run_core_pipeline ends here
8. Tier 3 enrichment afterpass      → EnrichedOutput
9. Schema validate + write          → exit
```

### Public vs private orchestration

```python
# proforma.py
def _run_core_pipeline(chart_input: ChartInput) -> dict:
    """Executes Stages 1–7. Deterministic. No RAG. No recursion. Pure."""

def compute(chart_input: ChartInput, enrich: bool = True) -> dict:
    """Public orchestrator."""
    base = _run_core_pipeline(chart_input)
    if not enrich:
        return base
    return _apply_tier3_enrichments(base, chart_input)

# computations/birth_time_robustness.py
def score_robustness(chart_input, base_output) -> dict:
    from app.reading.proforma import _run_core_pipeline
    nudge_plus  = _run_core_pipeline(chart_input.shift_minutes(+5))
    nudge_minus = _run_core_pipeline(chart_input.shift_minutes(-5))
    # diff verdicts; emit per-finding flip_rate
```

### Properties

| Property | Implementation |
|---|---|
| **Reproducibility** | Identical inputs → identical JSON byte-for-byte. No RNG, no wall-clock-dependent computation, no LLM. |
| **Caching** | Stage 1 (`NatalChart`) is content-addressed by `(jd, lat, lon, tz)` — reuses `forecast_cache.py` pattern. |
| **Error handling** | Stage 0 fails fast on bad input. Stages 1–7 use `Result` types — sub-computation failures emit `Skipped(reason)` findings, not exceptions. |
| **CLI exit codes** | 0=success, 1=bad input, 2=ephemeris/chart failure, 3=schema validation failure, 4=RAG index missing (Tier 3 fallback: warn + skip + exit 0). |
| **Logging** | `logger = logging.getLogger("app.reading")`, INFO at stage boundaries, DEBUG inside modules; `--verbose` promotes DEBUG. |
| **Robustness recursion** | `score_robustness` imports private `_run_core_pipeline` directly. Cannot reach Tier 3 modules. Zero recursion risk. |

## 6. JSON output schema

Nine top-level keys mirroring pipeline stages 1–8:

```json
{
  "meta":           { /* schema_version, engine_version, chart_input, doctrines_used, timings_ms */ },
  "chart":          { /* Stage 1 natal raw */ },
  "primitives":     { /* Stage 2 Tier-0 outputs */ },
  "foundations":    { /* Stage 3 Tier-1 outputs */ },
  "practitioner":   { /* Stage 4 Tier-2 outputs */ },
  "sequences":      { /* Stage 5: 4 named sequence results */ },
  "domains":        { /* Stage 6: 6 named domain readings */ },
  "contradictions": [ /* Stage 8.3 cross-finding */ ],
  "warnings":       [ /* engine-level diagnostics */ ]
}
```

### Universal Finding model

Every judgment emitted by any module is shaped like this:

```python
class Finding(BaseModel):
    id: str                       # content-addressed: e.g. "seq_5.md_3.step_05_rashi_depositor"
    rule: str                     # human-readable name
    source_sequence: str | None
    classification: Literal["promise", "trigger", "affliction", "yoga", "primitive"]
    direction: Literal["positive", "negative", "neutral", "mixed"]
    verdict: str                  # ≤140 chars
    evidence: list[str]           # deterministic order
    confidence: ConfidenceScore   # 3-vote rule

    # Tier 3 enrichments (populated only when enrich=True)
    citations: list[Citation] = []
    consensus: ConsensusScore | None
    dispute: Dispute | None
    robustness: RobustnessScore | None
```

### ID grammar (stable across runs)

| ID pattern | Example |
|---|---|
| `seq_<N>.<scope>.<rule_slug>` | `seq_5.md_3.step_05_rashi_depositor` |
| `primitive.<module>.<rule_slug>` | `primitive.karakas.atmakaraka` |
| `foundation.<module>.<rule_slug>` | `foundation.argala.7th_house_argala` |
| `practitioner.<module>.<rule_slug>` | `practitioner.mks.saturn_in_1` |
| `domain.<name>.<rule_slug>` | `domain.marriage.7l_dasha_window` |

Birth-time robustness relies on these IDs being identical across `T`, `T-5min`, `T+5min` runs. Enumeration-based IDs (`finding_1`, `finding_2`) are forbidden.

### Named-dict sequence checks

`MD_CHECK_KEYS: Final[tuple[str, ...]]` enumerates the 19 named checks of Sequence 5 (`bhaav_from_lagna`, `commonality_significations`, …, `repeat_from_arudha_lagna`, `repeat_from_karakamsha_lagna`). Schema validation refuses any `MDJudgment` missing one of these.

Same pattern for Sequence 6 (7 names), Sequence 1 (4 names), Sequence 2 (4 names).

### Sub-models (summary)

```python
class Citation:        source, passage, relevance, knowledge_doc_id
class ConsensusScore:  score, sources_agreeing, sources_total, low_consensus_flag
class Dispute:         rule, sources_for, sources_against, canonical_example
class RobustnessScore: sensitive_to_birth_time, flip_rate_at_5min, flip_rate_at_10min, inputs_used
class ConfidenceScore: score, votes{house, lord, karaka}, band
class Contradiction:   finding_ids[], domain, description, severity{soft|hard}, suggested_arbitration
```

### Domain reading shape

```python
class DomainReading:
    domain: str
    promise: Finding
    triggers: list[Finding]
    timing_windows: list[TimingWindow]   # date ranges + driving dasha period
    afflictions: list[Finding]
    cross_checks: list[Finding]
    remedies: list[RemedyRecommendation]
    overall_verdict: Finding
    confidence: ConfidenceScore
```

### Design choices

- **Enrichments inline on each Finding** — consumers never need JOIN
- **Contradictions top-level** — cross-finding by definition
- **Schema versioning from day 1** (`schema_version: "1.0.0"` in meta) — semver
- **Pydantic frozen + strict mode** — catches typos at construction; mirrors `extra="forbid"` lock from CLAUDE.md
- **ISO-8601 dates in output**; Julian Day stays internal

## 7. Testing & validation

### Test pyramid

```
                Doctrine review (manual quarterly, NOT CI)
            E2E + sliced snapshots (Bangalore baseline)
        Famous-chart structure (10 charts, structure only)
    Integration tests (stage→stage, sequence→domain)
Unit tests + external-pinned correctness (~200 tests total)
```

### External pinning matrix (CLAUDE.md doctrine)

Pin against **externally-verifiable** sources only — never engine self-output.

| Computation | External source |
|---|---|
| Lagna degree | drikpanchang.com (Lahiri) |
| Planet longitudes | jagannathahora.io |
| D9 navamsa positions | Prokerala D9 chart |
| Atmakaraka | Jagannatha Hora desktop |
| Arudha Lagna | Astrosaxena calculator |
| Mahadasha sequence | jagannathahora.io |
| Gulika | drikpanchang Gulika calculator |
| Unpinnable primitives (Vimsopaka, Ishta Phal) | Doctrine-reviewed by `bphs-doctrine-reviewer` agent + BPHS-verse citation in pin file |

Pinned fixtures in `tests/reading/pinned/*.json`. **Static files — no automated scrapers.** Re-generation is manual + recorded-session per Section 4 refinement.

### Sliced snapshots (one per stage boundary, not one mega-file)

```
tests/reading/snapshots/
├─ bangalore_tier0_primitives.json
├─ bangalore_foundations.json
├─ bangalore_practitioner.json
├─ bangalore_sequences.json
└─ bangalore_domain_synthesis.json
```

Each isolates a layer's diff surface. Smaller PRs.

### Famous-chart corpus (10, structure only)

Einstein, Gandhi, Steve Jobs, Ramana Maharshi, Tagore, Vivekananda, Ramanujan, APJ Kalam, Obama, plus rectified-variant + edge cases (Sandhi 0°/29°, polar latitude, Graha Yuddha within 1°).

**ASSERT structure-validity, exit-code-zero, schema-conformance.** **NEVER assert life-event outcomes.** (See Section 11 / falsified-prediction trap.)

### Performance budget

| Stage | Cold cache | Warm cache |
|---|---|---|
| Stages 0–1 | < 550ms | < 100ms |
| Stages 2–4 | < 2s | < 200ms |
| Stage 5 (sequences) | < 1s | < 1s |
| Stage 6 (domains) | < 500ms | < 500ms |
| Stage 7 (assembly) | < 100ms | < 100ms |
| Stage 8.1–8.5 | < 5s | < 1s |
| Stage 8.6 (robustness) | < 4s | < 200ms |
| **Total** | **< 12s** | **< 3s** |

### Doctrine audit cadence

`bphs-doctrine-reviewer` agent runs quarterly via scheduled GitHub Actions cron; markdown report committed to `docs/audits/doctrine-YYYY-QN.md`. **NOT a blocking CI gate** (LLM-grader variance would create flaky CI).

### Coverage

80% per CLAUDE.md CI gate.

## 8. Build phasing

| Phase | Scope | Duration | Doctrine checkpoint |
|---|---|---|---|
| **1: Foundation** | schema + CLI + 11 Tier-0 + `functional_nature` + `bhava_chalit` | 1.5 weeks | ✅ Post-phase |
| **2: Tier 1 completion** | Remaining 7 Tier-1 modules | 1 week | — |
| **3: Tier 2 doctrine layer** | All 17 Tier-2 modules (yogas_extended, remedies are biggest) | 2 weeks | ✅ Post-phase |
| **4: Sequences** | 4 sequence orchestrators (Seq 5 with 19 checks is biggest) | 1 week | — |
| **5: Domains** | 6 domain synthesizers | 1 week | ✅ Post-phase ⭐ **V1 ENGINE-ONLY COMPLETE** |
| **6: Tier 3 enrichments** | 6 enrichment modules (RAG, consensus, contradictions, robustness) | 1 week | — |
| **7: Polish + spec close-out** | Famous-chart corpus, performance benchmarks, audit cron, docs | 3–5 days | — |

**Phase 5 is the v1 shipping milestone.** Tier 3 (Phase 6) is optional richness that lands on top of an already-working engine.

**Parallel-eligible modules per phase** are documented in the brainstorming session and inherited here.

## 9. Risk register

| Risk | Probability | Mitigation |
|---|---|---|
| Doctrine ambiguity (7 vs 8 karaka mode, Drik-bala variants, navamsa pada definitions) | HIGH | Configurable mode flags + `docs/doctrine-decisions.md` recording each choice with BPHS verse citation |
| Swiss Ephemeris version drift breaks pinned positions | MEDIUM | Pin `pyswisseph==N.N.N` in pyproject.toml; CI asserts version match |
| External pinning source layout change | MEDIUM | Static fixtures; regen is manual + recorded-session |
| Performance regression as Tier-2 module count grows | MEDIUM | Layer 8 benchmark tests; informational CI; profile every 2 weeks |
| Module sprawl beyond 58 | LOW | Spec amendment required to add modules |
| Pydantic strict mode bites downstream v1.5 consumers | LOW | `schema_version` in meta enables version detection |
| Cache key collision | LOW | Cache key is `(jd, lat, lon, tz)`; uniqueness test in fixtures |
| Birth-time robustness amplifies determinism bugs | MEDIUM | Robustness test asserts global flip_rate ceiling on Bangalore baseline |
| Tier 3 RAG hangs on knowledge_search.py cold boot | LOW | LRU cache + CLI warmup; `--no-enrich` flag for fast deterministic-only runs |

## 10. v1.5 boundary (explicitly out of scope)

- LLM narrative synthesis (deterministic JSON → prose)
- Free-form chart query ("when will X happen?")
- Tattwa-based birth-time rectification (LLM-graded narrative-fit)
- Mental-health framing, queer-aware partnership language
- Modern-domain mapping (software career, social media, IVF)
- Chara Dasha (Jaimini sign-based timing)
- Tajik / Varshaphala annual chart system
- Yogini Dasha, Shoola Dasha, Sudasa, Tithi Pravesh
- Similarity-of-charts retrieval (needs canonical-chart corpus first)
- Web UI / chart-entry form

## 11. Falsified-prediction-trap guardrails

The project memory records 4 independent ML methodologies that tried to *predict life events from natal patterns* and all returned NULL (doctrine RR × 3 corpora, non-structural XGBoost, LLM real-vs-shuffled, Dynamic-DeepHit competing risks).

This spec is **structurally orthogonal** to those methodologies. We do not predict events. We compute and describe.

| What v1 does | What v1 does NOT do |
|---|---|
| Compute karakas, Arudha, yogas, dasha-period structure | Predict "you will get married in 2027" |
| Describe a Mahadasha via 19 named checks | Score "good" / "bad" outcomes empirically |
| Retrieve doctrine citations grounding each finding | Train a regressor / classifier on outcome labels |
| Score consensus among classical sources | Forecast life-event probabilities |
| Detect cross-sequence contradictions | Calibrate predictions against historical outcomes |
| Score yoga strength from rule aggregation | Validate yoga strength against empirical fortune |

The Tier 3 ML/RAG enrichments are **descriptive**, not predictive. Each Tier 3 module has been explicitly screened against this constraint.

## 12. Open questions — RESOLVED by review pass

Originally pre-review open questions; now answered:

1. **7th domain (spirituality)?** — Deferred to v1.5. Practitioner-research item; notebook proforma doesn't include it.
2. **Panchanga & avasthas tier placement?** — **Stay in Tier 0** (architect-reviewer). They are *positional measurements*, not interpretive judgments.
3. **Split `remedies.py`?** — Hold at one file; pre-plan internal section markers; split only if it exceeds 800 LOC during Phase 3.
4. **Pipeline as class vs function?** — **Keep as functions for v1**. Two-function (`_run_core_pipeline` + `compute`) is sufficient. Revisit at v1.5 if Tier 3 proliferates.
5. **Consensus min-sources threshold?** — Lock at `min_sources=3, agreement_threshold=0.66` in `Meta.doctrine_config`. Configurable per chart but with this default.
6. **CLI `--config` file?** — **Yes**. Add `--config <path.yaml>` flag; default `docs/doctrine-decisions.md` companion `doctrine.yaml`. Echo into `Meta.doctrine_config`.
7. **Sub-split Seq 5 (19 checks → 19 files)?** — **Keep whole**. Split only if file exceeds 800 LOC (architect-reviewer + spec-CLAUDE.md alignment).
8. **Tier-3-only snapshot?** — **Add a 6th snapshot** `bangalore_tier3_enrichments.json`. Confirmed by QA review.

## 13. Doctrine lockfile (`docs/doctrine-decisions.md`)

**Phase 1 sub-task #1.** Must exist before any computation module is written. Without this, the 11 Tier-0 modules will silently encode arbitrary choices that propagate to all sequences and domains.

The lockfile is a markdown document with one section per decision, structured as:

```markdown
## D-N: <Decision title>

**Status:** Locked 2026-MM-DD
**Used by:** <list of modules consuming this decision>
**Source citation:** <BPHS verse / Phaladeepika chapter / commentator>
**Decision:** <one-paragraph commitment>
**Alternatives considered:** <briefly>
**Rationale for choice:** <one paragraph; including cross-check with external pinning source>
```

### The 16 locked decisions

| # | Decision | Value |
|---|---|---|
| D-1 | Karaka mode | **8-karaka (PVR Narasimha Rao)** — matches jagannathahora.io pinning source |
| D-2 | Arudha exception rule | **1/7 → 10 shift** applied to all A1–A12, UL, UL₂ |
| D-3 | Vimsopaka scheme | **Shodashavarga 16-varga**, BPHS Ch.9 vv.7-10 weights: `{D1:3.5, D2:1, D3:1, D7:0.5, D9:3, D10:0.5, D12:0.5, D16:2, D20:0.5, D24:0.5, D27:0.5, D30:1, D40:0.5, D45:0.5, D60:5}` |
| D-4 | Ishta Phal formula | **BPHS Ch.47 v.3**: `Ishta = sqrt(Cheshta_bala × Uchcha_bala)`; `Kashta = 60 - Ishta`. Phaladeepika variant surfaced via `dispute_surfacing.py`. |
| D-5 | Residential strength falloff | **Linear, zero at sandhi**. `strength = 60 × (1 - distance_from_madhya / 30)`. The 8°-strong / 3°-very-strong is a classification band on top, not the formula. |
| D-6 | Gulika vs Mandi | **Two distinct upagrahas**. Gulika = portion of Saturn's day-segment; Mandi = midpoint of that segment. BPHS Vol.I Ch.5 + Phaladeepika Ch.25. |
| D-7 | Functional nature table | **PVR / Sanjay Rath synthesis** (full 12-lagna matrix). Attribution corrected from "Laghu Parashari" — that source covers only the kendra+kona dual-rulership rule. |
| D-8 | Bhava Chalit cusps | **Sripati** (BPHS Vol.II Ch.51). KP/Placidus excluded per Section 2 scope. |
| D-9 | MKS table | **Canonical 8-row**: Su-12, Mo-8, Ma-7, Me-7, Ju-3, Ve-6, Sa-1, Ra-9. Ketu = not-applicable. |
| D-10 | Karaka triangulation reading | **Sanjay-Rath formulation**: "7th from Lagna AND 7th from Moon AND 7th from karaka Venus." Module renamed inside `karaka_triangulation.py` docstring with `reading: "sanjay_rath"` lock. BPHS Vol.I Ch.11 variant surfaced via `dispute_surfacing.py`. |
| D-11 | Neech Bhanga primary rule | **BPHS Vol.I Ch.39 v.10**: exalted-lord-of-debilitation-sign in kendra from Lagna or Moon. Other 3 BPHS variants flagged as supplementary in finding evidence. |
| D-12 | Kala Sarpa primary definition | **Strict 180° Rahu-leading**. Yoga vs Dosha distinction surfaced via finding `classification`. Partial variants in dispute layer. |
| D-13 | Graha Yuddha winner | **Northern-latitude wins** (BPHS Ch.27 v.13). Matches jagannathahora.io pinning. |
| D-14 | Sequence 5 — 19 check keys | Verbatim list in spec Section 6 (`MD_CHECK_KEYS`). **KP-contamination audit BEFORE Phase 4** — any "sub-lord/cuspal-sub" check stripped or re-derived via Parashari rashi-depositor only. |
| D-15 | Sequence 6 — 7 check keys | Verbatim list in spec Section 6 (`AD_CHECK_KEYS`). |
| D-16 | Education divisional chart | **D24 Chaturvimsamsa** (BPHS Ch.6 v.21). `domains/education.py` routes through `divisional_readings/d24_chaturvimsamsa.py`. D9/D4 NOT used for education. |

These decisions feed `Meta.doctrine_config` in every output JSON, making each reading self-describing about which doctrine variants produced it.

## 14. Tier 3 Methodology declaration template

**Mandatory** for all 6 Tier 3 modules. Each must publish, in its module docstring, a `Methodology:` block before the first function definition. Template:

```python
"""<Module purpose>

Methodology:
    Type: <descriptive | sensitivity-analysis>
    Inputs to retrieval/scoring: <rule_slug + structural_slots OR Finding.direction enum>
    Explicitly NOT used: <Finding.verdict free-text — banned per anti-confirmation-bias>
    Thresholds & their source: <BPHS verse / classical text — never historical-outcome fitting>
    Famous-chart anti-contamination: <how biographical passages on named charts are filtered>
    Null-baseline test required: <shuffled passages / random chart / N/A>
    Prediction-trap declaration: "This module does NOT predict outcomes. It <retrieves / scores / diffs>
                                  pre-existing computed findings. No fitting against any chart corpus
                                  with outcome labels."
"""
```

### Per-module commitments (from ML-audit refinement)

**`rag_citations.py`** — Query construction uses `rule_id + structural slots {planet, house, lord}` ONLY. NEVER `Finding.verdict` text (confirmation-bias trap). Biographical passages matching famous-chart names (Einstein, Gandhi, etc.) are filtered or down-weighted via name-mention detector.

**`consensus_scoring.py`** — Agreement is computed over **rule applicability statements** ("this configuration is *called* Gajakesari"), NOT outcome claims ("Gajakesari produces wealth"). Outcome-bearing passages stripped from agreement denominator. `score` units literally: "fraction of retrieved passages whose normative rule matches the finding's `rule_id`." Null baseline (shuffled passages) required before Phase 6 ships.

**`contradiction_detector.py`** — Verdicts compared on `direction` enum {positive, negative, neutral, mixed} ONLY. NEVER on `verdict` free-text. `suggested_arbitration` is descriptive ("Sequence 5 says positive, Sequence 6 says negative") and NEVER picks a winner.

**`dispute_surfacing.py`** — Report-only contract: `Dispute` carries `sources_for[]` and `sources_against[]` but emits NO `is_correct`, `recommended_side`, or `engine_preferred` field. Locked via Pydantic `Literal` typing.

**`yoga_calibration.py`** — Strength function is a **closed-form aggregation of doctrine-cited inputs** (count of supporting Vimsopaka points + dignity + drishti contributions) with **constants taken from cited BPHS verses**. Explicit module docstring: "No threshold or weight in this module has been fit, tuned, or selected against any dataset of historical outcomes."

**`birth_time_robustness.py`** — Ship `flip_rate_at_5min` and `flip_rate_at_10min` raw numerics. The boolean `sensitive_to_birth_time` flag is labeled `EXPERIMENTAL` in Meta until a threshold methodology is published.

## 15. Schema additions (from API-documenter refinement)

### `Meta` block additions

```python
class Meta(BaseModel):
    schema_version: str               # "1.0.0"
    stability: Literal["experimental", "beta", "stable"] = "experimental"   # ★ NEW
    engine_version: str               # git sha7
    swiss_ephemeris_version: str
    python_version: str
    generated_at: str                 # ISO-8601 UTC
    chart_input: ChartInput
    doctrines_used: list[str]
    doctrine_config: DoctrineConfig   # ★ NEW — echoes all 16 lockfile decisions
    enrichment_enabled: bool
    robustness_enabled: bool
    stage_timings_ms: dict[str, int]
    schema_changelog_url: str = "docs/reading/CHANGELOG.md"   # ★ NEW

class DoctrineConfig(BaseModel):
    """Records the doctrine variant chosen for THIS reading. Locks reproducibility."""
    karaka_mode: Literal[7, 8] = 8
    arudha_exception: Literal["1_7_to_10", "none"] = "1_7_to_10"
    vimsopaka_scheme: Literal["shodashavarga", "saptavarga", "dashavarga"] = "shodashavarga"
    ishta_formula: Literal["bphs_47_3", "phaladeepika_6"] = "bphs_47_3"
    bhava_chalit_system: Literal["sripati", "porphyry"] = "sripati"
    karaka_triangulation_reading: Literal["sanjay_rath", "bphs_classical"] = "sanjay_rath"
    neech_bhanga_rule: Literal["bphs_39_10", "alt_1", "alt_2", "alt_3"] = "bphs_39_10"
    kala_sarpa_definition: Literal["strict_180_rahu_leading", "loose", "partial"] = "strict_180_rahu_leading"
    graha_yuddha_winner: Literal["northern_latitude", "size", "brightness"] = "northern_latitude"
    consensus_min_sources: int = 3
    consensus_agreement_threshold: float = 0.66
```

### `Finding` model additions

```python
class Finding(BaseModel):
    id: str
    rule: str
    source_sequence: str | None
    classification: Literal["promise", "trigger", "affliction", "yoga", "primitive"]
    direction: Literal["positive", "negative", "neutral", "mixed"]
    verdict: str                       # ≤140 chars; English by default
    verdict_language: Literal["en"] = "en"               # ★ NEW for v1.5 i18n
    evidence: list[str]
    confidence: ConfidenceScore
    enrichment_level: Literal[0, 1, 2, 3] = 0            # ★ NEW — disambiguates "Tier 3 disabled" from "ran but no results"

    # Tier 3 enrichments (populated only when enrich=True)
    citations: list[Citation] = []
    consensus: ConsensusScore | None = None
    consensus_status: Literal["not_computed", "no_agreement", "computed"] = "not_computed"  # ★ NEW
    dispute: Dispute | None = None
    robustness: RobustnessScore | None = None
    contradicts_finding_ids: list[str] = []              # ★ NEW — eliminates JOIN to top-level contradictions[]
```

### Time representation: dual JD + ISO-8601

```python
class MDPeriod(BaseModel):
    md_lord: str
    start_date: str         # ★ NEW — ISO-8601 (e.g., "1995-03-14")
    end_date: str           # ★ NEW
    start_jd: float         # retained for precision-sensitive consumers
    end_jd: float
    age_at_start: float
    age_at_end: float
```

### Pydantic field constraints (from QA refinement)

All numeric ranges enforced at model level:
- `ConfidenceScore.score: float = Field(ge=0.0, le=1.0)`
- `ConsensusScore.score: float = Field(ge=0.0, le=1.0)`
- `RobustnessScore.flip_rate_at_5min: float = Field(ge=0.0, le=1.0)`
- `Finding.verdict: str = Field(max_length=140)`
- `Vimsopaka per-planet: float = Field(ge=0.0, le=20.0)`

## 16. Performance budget (rewritten per perf-engineer)

### Original stated budget (Stage 8 cold < 5s) was unachievable. Three mandatory wins applied:

1. **Batch RAG encoding** — `rag_citations.py` collects all finding queries into a list, calls `model.encode([200 queries])` once. CPU batch=200 on MiniLM ≈ 400-800ms total (vs 200 × 30ms = 6s sequential). New abstraction: `KnowledgeSearchService.batch_search(queries: list[str]) -> list[tuple[SearchResult, ...]]`.

2. **Lazy import of `sentence_transformers`** — moved inside `_apply_tier3_enrichments` function body, NOT at module top. Saves 200-600ms from cold Stage 0-1.

3. **Cap citations to high-confidence findings** — `rag_citations.py` filters to `confidence.band ∈ {high, medium}` AND `classification ∈ {promise, yoga, trigger}`. Cuts retrieval count from ~200 to ~80. Improves quality (citations on uncertain findings are noise) AND latency proportionally.

### Revised budget

| Stage | Cold cache | Warm cache | Notes |
|---|---|---|---|
| Stages 0-1 | < 700ms | < 100ms | Lazy import eliminates sentence-transformers from cold path |
| Stages 2-4 | < 2s | < 200ms | Unchanged |
| Stage 5 (sequences) | < 1s | < 1s | Unchanged |
| Stage 6 (domains) | < 500ms | < 500ms | Unchanged |
| Stage 7 (assembly) | < 100ms | < 100ms | Unchanged |
| Stage 8.1-8.5 | **< 4s** (revised) | **< 1.5s** | Batch encode + 80-finding cap |
| Stage 8.6 (robustness) | < 4s | < 4s | Sub-runs miss cache (different `jd`); intentional |
| **Total** | **< 12s** | **< 7s** (revised) | Warm-total grew because robustness sub-runs always miss cache |

### Pre-Phase-1 spike investigations (mandatory)

1. **Import-chain cold-start** — `time python -m app.reading.cli --help` with stub CLI; measure each heavy import separately.
2. **RAG batch-encode latency at N={1, 50, 200}** — actual hardware measurement.
3. **Shodashavarga full-16-vargas marginal cost vs used-7** — confirm <5ms delta or justify decision.

Each spike: ~30 minutes. Total: 1.5 hours. Investment removes "budget is fiction" risk.

## 17. Testing strategy (revised per QA-expert)

### Test count target raised: 200 → 350+

Original ~200 was undercounting by 2× for 80% coverage at real assertion depth.

### Mandatory additions

1. **Property-based tests via `hypothesis`** for natural invariants:
   - Sum of all 9 Vimshottari dasha periods = exactly 120 years
   - All karaka degrees ∈ [0, 30)
   - Vimsopaka score ∈ [0, 20]
   - Confidence band is a deterministic function of vote count
   - All Finding IDs unique within a reading

2. **CLI subprocess integration test** — runs `python -m app.reading.cli` as subprocess; asserts exit 0 + valid JSON on stdout. One happy-path + one bad-input (exit 1).

3. **Prediction-trap regression test** — runs Bangalore baseline reading; asserts `json.dumps(output)` contains NONE of: `"will get married"`, `"will succeed"`, `"guaranteed"`, `"definitely"`, `"you will"`, `"going to happen"`. Auto-enforces Section 11 ban.

4. **Swiss Ephemeris global-state isolation fixture** — `@pytest.fixture(autouse=True)` resets `swe.set_sid_mode(swe.SIDM_LAHIRI)` before each test. Eliminates cross-test ayanamsa contamination.

5. **Worked-example pins for unpinnable computations** — Vimsopaka, Ishta Phal, residential strength get pins from **Phaladeepika / Saravali published worked examples**, not just doctrine-reviewer self-validation.

### Additional edge cases for famous-chart corpus

- Atmakaraka tie-breaker (two karakas within 0.001°)
- All fast planets retrograde simultaneously
- Southern Hemisphere birth
- Equinox-zero-Aries Lagna
- Zero-yogas chart (rare)
- Gandanta Moon chart

### Snapshot maintenance policy

Add `tests/reading/snapshots/README.md`:
- Five (now six) snapshots own different pipeline stages
- Tier-0 fix triggers cascade in downstream snapshots (expected)
- Approval policy: update earliest-stage changed snapshot first; cascading downstream updates are expected artifacts

## 18. Build phasing — Phase 1 update

Phase 1 sub-tasks (in order):

| # | Task | Duration | Output |
|---|---|---|---|
| 1.0 | **Doctrine lockfile** (`docs/doctrine-decisions.md`) | 1 day | 16 decisions written + reviewed by `bphs-doctrine-reviewer` agent |
| 1.1 | Pre-Phase-1 spikes (3 perf investigations) | 0.5 day | Profile report committed to `docs/perf/phase1-spikes.md` |
| 1.2 | `schema.py` + `CorePipelineOutput` Pydantic model + `Result` type definitions | 2 days | Schema testable in isolation |
| 1.3 | `cli.py` skeleton + `proforma.py` `_run_core_pipeline` + `compute` split | 1 day | Stub CLI emits valid empty JSON |
| 1.4 | 11 Tier-0 computations + paired tests | 4 days | Primitives block populated for Bangalore baseline |
| 1.5 | `functional_nature.py` + `bhava_chalit.py` (Tier-1 foundation atoms) | 1.5 days | Cross-cutting Tier-1 modules complete |
| 1.6 | Doctrine checkpoint #1 — `bphs-doctrine-reviewer` audit | 0.5 day | Audit report committed |

**Phase 1 total: 10 working days (~2 weeks)** — was originally estimated 1.5 weeks; revision is honest about lockfile + spikes overhead.

---

**End of revision 1. Awaiting formal spec-document-reviewer pass.**
