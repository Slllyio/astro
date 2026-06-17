# Acquisition runbook — grow the corpus & run the pre-registered replication

Exact commands to execute the corpus-growth pipeline built in
`vedastro_events_importer`, `wikidata_events_importer`, `astrodatabank_xml_importer`,
`match_events_to_charts`, and `aggregate_events`. **Run in an environment with
network egress to `huggingface.co` and `query.wikidata.org`** (this sandbox's
allowlist blocks both, which is why every importer isolates its network call and
ships schema-tolerant + fully unit-tested). Target from
`replication_preregistration.md`: **≥ ~9,000 auspicious first events** in band.

All paths are suggestions; `--help` on each module lists options.

## 0. Stage the licensed/public files
```bash
mkdir -p data/ext/{vedastro,wikidata,adb}
# VedAstro (MIT) — birth charts + dated marriages:
#   https://huggingface.co/datasets/vedastro-org/15000-Famous-People-Birth-Date-Location
#   https://huggingface.co/datasets/vedastro-org/15000-Famous-People-Marriage-Divorce-Info
# download both CSVs into data/ext/vedastro/ (e.g. `huggingface-cli download …`)
# ADB XML (charts public-domain; events need a signed Astrodienst licence) →
#   data/ext/adb/adb_export.xml   (optional)
```

## 1. VedAstro → charts + dated marriage events
```bash
# charts (raw.csv) — existing importer:
python -m app.medini.etl.vedastro_importer \
    --persons data/ext/vedastro/PersonList-15k.csv \
    --marriages data/ext/vedastro/MarriageInfoDataset.csv \
    --output data/ext/vedastro/raw.csv --allow-unlabeled
# dated marriage/divorce EVENTS (new importer):
python -m app.medini.etl.vedastro_events_importer \
    --marriages data/ext/vedastro/MarriageDivorceInfo.csv \
    --output data/ext/vedastro/events.csv
```

## 2. Wikidata → dated events (CC0)
```bash
python -m app.medini.etl.wikidata_events_importer \
    --classes marriage death career --page-size 5000 --max-pages 60 \
    --output data/ext/wikidata/wikidata_dated_events.parquet
```

## 3. (optional) Astro-Databank XML → charts (+ events if licensed dump)
```bash
python -m app.medini.etl.astrodatabank_xml_importer \
    --xml data/ext/adb/adb_export.xml \
    --raw data/ext/adb/raw.csv --events data/ext/adb/events.csv
```

## 4. Build charts for the new births (existing Stage-2/3 pipeline)
Run each new `raw.csv` through the same chart/dasha pipeline the corpus already
uses (sidereal Lahiri D1 + D9 + longitudes + Vimshottari windows), producing a
`persons.parquet` (person_id, name, birth_jd) and the chart/window parquets:
```bash
python -m app.medini.etl.databank_etl --raw data/ext/vedastro/raw.csv --out data/ext/vedastro
# …then build_charts_table / build_d9_charts / build_longitudes / build_dasha_windows
#    (same invocations used for the LunarAstro run; see SYNTHESIS "Reproduce").
```

## 5. Aggregate every event source + match to charts + funnel to target
```bash
python -m app.medini.etl.aggregate_events \
    --events \
        wikidata=data/ext/wikidata/wikidata_dated_events.parquet \
        vedastro=data/ext/vedastro/events.csv:data/ext/vedastro/persons.parquet \
        adb=data/ext/adb/events.csv:data/ext/adb/persons.parquet \
        lunarastro=app/medini/data/lunarastro_run/events.csv:…/persons.parquet \
    --persons data/ext/combined_persons.parquet \
    --output data/ext/events_unified.parquet --target 9000 -v
```
The `vedastro=events:persons` form enriches each source's events with `birth_year`
from its own persons table (Wikidata already carries it). The log prints the
funnel: `auspicious_first_events` vs `target`, by source and by class. **If
`fraction_of_target ≥ 1.0`, you have the power to run the confirmation.**

## 6. Join events to active MD/AD, then run the FROZEN confirmation
```bash
python -m app.medini.etl.build_event_dasha_join   # → events_with_dasha.parquet
# the one pre-registered primary test (do not run others first):
python -m app.medini.ml.dasha_timing_metrics --data-dir data/ext/combined_run --k 10000
```
Read off the **SCCS incidence-rate ratio + 95% CI** (Layer A) for the frozen S4
strength rule on pooled auspicious events. Apply the pre-committed rules in
`replication_preregistration.md`:
- **IRR > 1, one-sided p < 0.05, death not lifting** → confirm (real-but-small).
- **p ≥ 0.05** → bury the whisper; classical dasha timing is fully null.
- **death lifts comparably** → artifact, regardless of p.

## Dedup & independence (do not skip)
Most celebrity DBs derive from Astro-Databank, so before counting, run every new
persons set through `resolve_persons_dedup` (name + birth datetime) — overlapping
charts double-count events and break the replication's independence assumption.
For the cleanest confirmation, draw the sample from persons **not** in the current
LunarAstro corpus.
