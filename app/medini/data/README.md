# `app/medini/data/` layout

Quick reference for what each file is. **Full schema docs live in
[`docs/data_dictionary.md`](../../../docs/data_dictionary.md)**.

## File groupings

### 🟢 Canonical Silver layer (the source of truth for new code)

```
persons.parquet              ← 75,149 humans across 3 corpora
events.parquet               ← 64,563 dated life events
charts.parquet               ← 75,149 natal charts
dasha_windows.parquet        ← 6.09M (MD × AD) windows
dasha_tree.parquet           ← 6.09M MD↔AD mutual-relation features
events_with_dasha.parquet    ← events joined to active dasha at event_jd
chart_edges.parquet          ← 3.46M heterograph edges
static_graph_edges.parquet   ← 25 fixed BPHS rulership / karaka edges
person_id_map.parquet        ← name_norm ↔ person_id bridge (Round-9 ↔ Silver)
event_class_taxonomy.parquet ← 56 granular ↔ 6 harmonized event classes
resolved_persons.parquet     ← cross-corpus dedup linkage
catalog.duckdb               ← DuckDB catalog (11 Silver + 7 Gold views)
```

**Rule**: new ML / analysis code should read FROM these via
`app/medini/ml/experiment_loader.py`, NOT from raw source corpora below.

### 🟡 Round-9 source corpora (inputs to the Silver layer)

```
# ADB (Astro-Databank) raw
dasha_corpus_birth_data.parquet  ← raw birth metadata for ADB persons
event_corpus_all.parquet         ← raw ADB event records
dasha_event_corpus.parquet       ← Round-9 ADB MD-level dasha-event corpus
natal_lord_houses.parquet        ← Round-9 ADB natal lord-house features
dasha_mdadpd_corpus.parquet      ← Round-9 ADB MD-AD-PD-level corpus
dasha_stage_d_features.parquet   ← Round-9 Stage D feature cache

# Wikidata raw
wikidata_dated_events.parquet    ← raw WD person + event records
wikidata_dasha_corpus.parquet    ← WD dasha corpus (Round-9 era)
wikidata_natal_lord_houses.parquet  ← WD natal features (Round-9 era)

# Lunarastro raw
lunarastro_natal.parquet         ← raw LA person + chart records
lunarastro_dasha_corpus.parquet  ← LA dasha + per-window event flags
lunarastro_natal_lord_houses.parquet ← LA natal features (Round-9 era)
```

**Rule**: these are INPUTS. The Silver builders (`app/medini/etl/build_*.py`)
read from these and produce the canonical Silver tables.
Old Round-9 ML scripts (~25 files in `app/medini/ml/`) still query these
directly — they will be migrated as those scripts are touched.

### 📦 `gold/` (materialized hot Gold views)

Physical parquets generated from catalog views for 10× query speed.
Regenerate with `python -m app.medini.etl.materialize_gold_views` after
any upstream Silver rebuild.

### 🗄️ `legacy/` (archived unreferenced parquets — 309 MB)

Round 5/6 era artifacts no longer referenced anywhere. Recoverable via
`mv legacy/foo.parquet ./` if anything breaks. Decommissioned by
`app/medini/etl/archive_legacy_parquets.py`.

## How to verify the layer is healthy

```bash
py -m app.medini.etl.validate_silver_layer
```

10 automated checks: FK integrity, PK uniqueness, range constraints,
taxonomy consistency. Exits 0 if clean.

## How to rebuild from scratch

See `docs/data_dictionary.md` section "Rebuild sequence". TL;DR:

```bash
py -m app.medini.etl.build_event_class_taxonomy
py -m app.medini.etl.build_person_event_tables
py -m app.medini.etl.build_charts_table --workers 6
py -m app.medini.etl.build_dasha_windows --workers 6
py -m app.medini.etl.build_dasha_tree
py -m app.medini.etl.build_event_dasha_join
py -m app.medini.etl.build_chart_heterograph
py -m app.medini.etl.build_person_id_map
py -m app.medini.etl.resolve_persons_dedup
py -m app.medini.etl.build_duckdb_catalog
py -m app.medini.etl.materialize_gold_views
py -m app.medini.etl.validate_silver_layer  # gate
```
