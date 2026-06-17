# RESUME — cold-start handoff for the dasha-timing audit

**Read this first in a new session.** The container is ephemeral; only what is
committed to the branch survives. This file is the single source of truth for
picking up exactly where the last session ended.

- **Branch (develop + push here only):** `claude/latest-updates-yu88e5`
- **Project hub:** `data/ml_runs/lunarastro_dignity/` (this dir) — `SYNTHESIS.md`
  (full findings) + `README.md` (capstone). Everything is committed & pushed.
- **Last commit:** `aggregate_events + acquisition runbook` (the corpus-growth glue).

## The verdict so far (one paragraph)

On 17,912 dated real life events (3,779 charts), **Vedic dasha timing does not
predict *when* life events happen beyond a person's age.** Every pillar of the
method was tested on its own terms (Findings 1–17): single significators, the
disjunctive dictums as astrologers state them (76–90% hits = chance), convergence/
weight-of-evidence (flat), the verses verbatim incl. Parashara's from-the-dasha-
lord mechanism (null), the fixed-age tables (era custom), and the dasha+transit
"double confirmation" (lift 1.002). Scored as a forecaster with proper scoring
rules, it is **calibrated but empty** (≈0 bits over the age base-rate). Two
residues: the **7th-lord-MD→marriage** association (real, modest, lift ≈1.15), and
a **strong-benefic sub-period rate whisper** (SCCS IRR **1.13**, 95% CI 0.998–1.29)
that has **no ranking/forecasting skill** (C-index 0.50) and is not auspicious-
specific — its fate awaits the pre-registered external replication.

## ⚠ Environment gotchas (will bite on resume)

1. **The analysis corpus is NOT in the repo.** All analyses read a `--data-dir`
   (last session used `/tmp/la_run`, 5 parquets: charts, charts_d9, charts_lon,
   dasha_windows, events_with_dasha). **`/tmp` is wiped in a new container** and
   the LunarAstro source export (`kundlis.jsonl`) is *not committed*. → To re-run
   any analysis you must first rebuild/re-supply the run-data via
   `app.medini.etl.lunarastro_kundli_pipeline` from the source export, or stage
   the parquets into a data-dir. The *code* is fully resumable; the *data* is not.
   (Committed in this dir: `charts_d9/charts_lon/events_enriched/events_promise`
   parquets only — not the full run.)
2. **Network allowlist:** WebSearch works; `WebFetch` 403s on HuggingFace/
   datasets-server and many sites; sandbox `curl` is host-allowlist-blocked
   (Wikidata/HF unreachable). That is why every importer isolates its network call
   and is unit-tested with mocks/fixtures.
3. **Model is fixed at session start** — `/model` is unavailable in this remote env.
4. **Run tests with:** `PYTHONPATH=. python3 -m pytest <file> --noconftest -p no:asyncio`
   (the repo's conftest/asyncio config interferes otherwise).
5. `git add -f data/ml_runs/lunarastro_dignity/<file>` — `data/` is gitignored, so
   report/markdown artifacts need `-f`.

## What exists (modules → purpose)

**Analysis (findings):** `app/medini/ml/` — `dasha_verse_timing` (Finding 14),
`dasha_confluence_timing` (13), `dasha_strength_confirm` (15, pre-reg split-half),
`dasha_timing_metrics` (15b: SCCS IRR + C-index Layers A/B), `dasha_forecast_skill`
(15c: proper scores + calibration, Layer C), `dasha_transit_trigger` (16),
`bphs_fixed_age` (17), `dasha_classical_dictums` (12). Each has a report `.md` in
this dir and a `tests/test_*.py`.

**Acquisition toolchain (this session, ready to run when network exists):**
`app/medini/etl/` — `vedastro_events_importer` (MIT dated marriages),
`wikidata_events_importer` (CC0 marriages/deaths/careers; produces the long-missing
`wikidata_dated_events.parquet`), `astrodatabank_xml_importer` (ADB XML charts
public-domain; events only on a licensed dump), `match_events_to_charts` (attaches
`person_id` by name+birth-year; the multiplier), `aggregate_events` (merges all
sources → dedup → match → **funnel vs the 9,000 target**). 34 tests, all green.

**Key docs in this dir:** `replication_preregistration.md` (frozen confirmatory
protocol + power table), `data_acquisition_plan.md` (ranked sources, verified),
`acquisition_runbook.md` (exact command sequence), `evaluation_methodology.md`
(why the better metrics), `dictum_catalog_v2.md` + `dictum_research/` (70 verse-
level sourced dictums).

## Next actions (in priority order)

1. **Run the acquisition pipeline** (needs network to HF + `query.wikidata.org`):
   follow `acquisition_runbook.md` steps 0–6 → grows the dated-event corpus →
   `aggregate_events` prints `auspicious_first_events` vs 9,000. If
   `fraction_of_target ≥ 1.0`, run the **frozen** `dasha_timing_metrics` and apply
   the pre-committed rules in `replication_preregistration.md`.
2. **(offered, not yet built) End-to-end dry run** on the existing LunarAstro data
   to prove the new event sources flow through `build_event_dasha_join` — the last
   confidence-builder that needs no new data (still needs the run-data rebuilt, see
   gotcha #1).
3. **(offered) A dedup/independence checker** module to auto-enforce the runbook's
   warning (most celebrity DBs derive from Astro-Databank).
4. **NCDS/BCS70 gold-standard track** — UK Data Service application (offline/paperwork,
   not code): the only fully-independent corpus with birth *time* + dated life events.

## To confirm the repo is intact on resume
```bash
git log --oneline -12
PYTHONPATH=. python3 -m pytest tests/test_aggregate_events.py \
  tests/test_match_events_to_charts.py tests/test_wikidata_events_importer.py \
  tests/test_vedastro_events_importer.py tests/test_astrodatabank_xml_importer.py \
  tests/test_dasha_timing_metrics.py --noconftest -p no:asyncio   # expect 39 passed
```
