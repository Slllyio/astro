# V1.5.0 Session Handoff

**Date:** 2026-05-29
**Branch:** `feat/app-reading` (pushed to `origin/feat/app-reading`)
**Last commit:** `45d7411` (D-17 lockfile recovery)
**Worktree:** `e:\astro-reading` (sibling of `e:\astro`)
**Test count:** 1758 passing in 18.43s

## Tags published

```
reading-phase1-complete    → 13 foundation modules
reading-phase2-complete    → +7 Tier-1 modules
reading-phase3-complete    → +31 Tier-2 doctrine modules
reading-phase4-complete    → +4 sequence orchestrators
reading-v1-engine-complete → +6 domains + famous-chart corpus
reading-v1.0.0             → V1.0.0 SHIPPING MILESTONE
reading-v1.5.0             → V1.5.0 SHIPPING MILESTONE
```

All 7 tags pushed to `https://github.com/Slllyio/astro`.

## What V1.5.0 added (since V1.0.0)

| Capability | Module | Tests | Commit |
|---|---|---|---|
| LLM narrative (deterministic + LLM modes) | `app/reading/narrative/` | +47 | `9a949f1` |
| Free-form chart Q&A | `app/reading/query/` | +75 | `39417a3` |
| Modern-life domain signals | `app/reading/modern_life/` | +72 | `a1a93ac` |
| Chara Dasha sequence | `sequences/chara_dasha.py` | +25 | `5fdecf6` |
| Yogini Dasha sequence | `sequences/yogini_dasha.py` | +31 | `76bed73` |
| Web UI (Jinja + Bootstrap 5) | `app/api/reading_v15_routes.py` + 2 templates | +8 | `06e8c5d` |
| D-17 lockfile recovery (race fix) | `docs/doctrine-decisions.md` | 0 | `45d7411` |

Total: ~3800 LOC implementation + ~2500 LOC tests across 6 parallel implementer dispatches.

## Parallel-write race condition — postmortem

The V1.5 wave dispatched 6 parallel implementers. Two of them (`chara_dasha`, `yogini_dasha`) both needed to add a new D-N entry to `docs/doctrine-decisions.md`. Race condition:

- Commit `5fdecf6` announced "D-17 added" in its message
- Commit `5fdecf6` diff actually contained D-18 prose (the Yogini section)
- D-17 was silently lost

Detection: the Yogini implementer's report flagged the gap immediately ("the chara_dasha commit's title mentions D-17 but the lockfile diff only contains my D-18 prose"). Recovery: manual `Edit` of the lockfile to insert D-17 between D-16 and D-18 with inline postmortem note. Time cost: ~5 minutes.

**Lesson for future parallel dispatches**: when multiple implementers must touch the same shared file (like a lockfile), give each implementer a distinct anchor marker to append before, and verify via grep after both complete. Or: serialize the file-touching commits even when other code is parallel.

## Pipeline-wiring gaps (small, intentional, easy)

Two V1.5 additions are NOT yet wired into `_run_core_pipeline`:

1. **`sequences/chara_dasha.py` + `sequences/yogini_dasha.py`** — they emit results via their own local Pydantic models (`CharaDashaResult`, `YoginiDashaResult`), keeping `app/reading/schema.py` untouched per their briefs. Wiring them into the main pipeline requires:
   - Either: extend `schema.py` to include `CharaDashaResult` and `YoginiDashaResult` in `SequencesBlock` (would be a `MINOR` schema version bump)
   - Or: keep local-model approach and have `_run_core_pipeline` call them and store under a new `sequences["chara_dasha"]` / `sequences["yogini_dasha"]` key (no schema bump needed if `SequencesBlock` is `extra="allow"`; but spec locks `extra="forbid"`)

2. **`modern_life/enrich_with_modern_signals()`** is consumer-callable but not auto-invoked. To enable: add a call inside `_apply_tier3_enrichments` (it's classification-safe — emits "primitive" Findings, not "trigger" or "promise").

Both are small Phase 7-style polish tasks; intentionally deferred to keep V1.5 release clean.

## Documentation produced

- `docs/superpowers/specs/2026-05-27-kundli-analysis-system-design.md` — the spec
- `docs/superpowers/plans/2026-05-27-kundli-analysis-system.md` — the plan
- `docs/doctrine-decisions.md` — 18 doctrine commitments D-1..D-18
- `docs/perf/phase1-spikes.md` — pre-build perf measurements
- `docs/reading/cli-reference.md` — user-facing CLI docs
- `docs/reading/json-schema.md` — human-readable schema reference
- `docs/reading/json-schema.json` — auto-generated 35 KB Pydantic JSON Schema
- `scripts/generate_schema_json.py` — schema regeneration helper
- `.github/workflows/doctrine-audit.yml` — quarterly cron (NOT a blocking gate)

## V2.0 explicitly deferred (need their own design)

| Item | Why deferred |
|---|---|
| **Tajik / Varshaphala** | Whole new doctrine system (Persian-influenced annual chart aspects, different orbs, Sahams). Needs new lockfile entries D-19..D-2x. ~2 weeks of design work before any code can be written. |
| **Birth-time rectification** | Multi-modal LLM scoring against life events. No existing precedent for the scoring methodology. Needs its own spec + doctrine reviewer round. |
| **Similarity-of-charts retrieval** | Chicken-and-egg: needs a canonical-chart corpus (probably ~1000 hand-verified historical figures with locked ayanamsa) before similarity is meaningful. Building the corpus is itself a multi-week ETL project. |

## How to pick this up next session

1. **Pure consumption**: invoke the CLI; the engine is fully working
2. **Wire the V1.5 sequences into the main pipeline**: see "Pipeline-wiring gaps" above (~30 min task)
3. **Wire modern_life into Tier 3**: ~15 min task
4. **Start a v2.0 item**: each needs a spec + doctrine review before implementation; budget ~1 week each
5. **Polish**: stricter typing in narrative prompts; expand the famous-chart corpus; add more test charts at extreme latitudes/dates

## Quick verification

```powershell
cd e:\astro-reading

# Tests
py -3.12 -m pytest tests/reading/ tests/api/test_reading_v15_routes.py -q
# Expect: 1758 passed in ~18s

# CLI smoke
py -3.12 -m app.reading.cli --dob=1990-07-15 --time=12:00 --tz=+05:30 --lat=12.97 --lon=77.59 --out=verify.json --no-enrich
# Expect: exit 0, file ~1 MB

# Tag list
git tag -l "reading-*"
# Expect: 7 tags

# Last commit
git log -1 --oneline
# Expect: 45d7411 docs(reading): recover D-17 ...
```
