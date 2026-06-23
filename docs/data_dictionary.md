# Medini Data Dictionary

Canonical reference for every Silver and Gold table in
`app/medini/data/`. Source of truth: this document. If a table exists
on disk but isn't here, it's not part of the canonical layer — either
add it here, or decommission it.

## Layout

```
app/medini/data/
├── persons.parquet              ← Silver (Tier 0 — person identity)
├── events.parquet               ← Silver (Tier 0 — event facts)
├── charts.parquet               ← Silver (Tier 1 — natal chart per person)
├── dasha_windows.parquet        ← Silver (Tier 1 — MD×AD windows per person)
├── dasha_tree.parquet           ← Silver (Tier 2 — MD↔AD mutual relations)
├── events_with_dasha.parquet    ← Silver (Tier 2 — event_jd ↔ active dasha)
├── chart_edges.parquet          ← Silver (Tier 2 — chart heterograph)
├── static_graph_edges.parquet   ← Silver (Tier 2 — fixed BPHS rulership)
├── person_id_map.parquet        ← Silver (Tier 3 — name_norm ↔ person_id)
├── event_class_taxonomy.parquet ← Silver (Tier 3 — granular ↔ harmonized)
├── resolved_persons.parquet     ← Silver (Tier 3 — cross-corpus dedup)
├── catalog.duckdb               ← DuckDB catalog (zero-copy views)
└── gold/                        ← Gold (materialized hot views)
    ├── v_event_survival.parquet
    ├── v_event_with_tree.parquet
    ├── v_chart_with_person.parquet
    ├── v_persons_canonical.parquet
    ├── v_chart_edge_summary.parquet
    └── v_natal_md_ads.parquet
```

## Tier 0 — Identity & facts (the relational core)

### `persons.parquet`

One row per unique human, deduplicated across the 3 corpora.

| Column | Type | Description |
|---|---|---|
| person_id | TEXT (PK) | Namespaced id: `ADB:{birth_jd:.4f}` / `WD:Q###` / `LA:{name_norm}` |
| name | TEXT | Lowercase normalized name (ADB / LA) or raw `person_name` (WD) |
| birth_date | TEXT | ISO `YYYY-MM-DD` |
| birth_time | TEXT | `HH:MM:SS` if known (ADB / LA); NULL for day-precision WD |
| birth_lat | FLOAT64 | WGS-84 latitude |
| birth_lon | FLOAT64 | WGS-84 longitude (east positive) |
| tz_offset | FLOAT64 | Local time minus UTC at birth (hours) |
| birth_jd | FLOAT64 | Julian Day for the precise birth moment |
| source | TEXT | `astro_databank` \| `wikidata` \| `lunarastro` |

**Build**: [`app/medini/etl/build_person_event_tables.py`](app/medini/etl/build_person_event_tables.py).
**Rows**: 75,149 (ADB 10,135 + WD 32,932 + LA 32,082).
**Notes**: Used as the **single source of truth** for who exists. All
downstream `person_id` references must resolve here.

### `events.parquet`

One row per dated life event with a person FK.

| Column | Type | Description |
|---|---|---|
| event_id | INT (PK) | Auto-increment |
| person_id | TEXT (FK→persons) | Owning person |
| event_class | TEXT | Harmonized 6-class: marriage \| career \| fame \| death_cause_unspecified \| relationships \| other |
| event_root | TEXT | Source-specific raw class (e.g. "Death of Mother", "death_by_disease") |
| event_subtype | TEXT | Optional finer subtype (mostly ADB) |
| event_date | TEXT | ISO `YYYY-MM-DD` of event (midpoint of dasha window for LA) |
| event_label | TEXT | Optional display label (event person, prize name, etc.) |
| source | TEXT | `astro_databank` \| `wikidata` \| `lunarastro` |

**Build**: same script.
**Rows**: 64,563 (ADB 14,166 + WD 46,351 + LA 10,075).
**Notes**: LA events have approximate `event_date` (midpoint of dasha
window because LA records per-window flags, not per-event timestamps).

## Tier 1 — Computed core (deterministic from Tier 0)

### `charts.parquet`

Canonical natal chart per person. One row per `person_id`.

| Column | Type | Description |
|---|---|---|
| person_id | TEXT (PK,FK) | Joins to persons |
| birth_jd_used | FLOAT64 | JD that was used for ephemeris (may be noon-UTC fallback for day-precision births) |
| time_precision | TEXT | `minute` (ADB/LA) or `day` (WD; ascendant unreliable) |
| asc_lon | FLOAT64 | Sidereal Lahiri ascendant longitude (0..360) |
| asc_sign | INT | 1..12 |
| `<graha>_lon` × 9 | FLOAT64 | Sidereal longitude per graha (Sun..Ketu) |
| `<graha>_sign` × 9 | INT | 1..12 per graha |
| `<graha>_house` × 9 | INT | Whole-sign house from Lagna, 1..12 |
| `<graha>_nakshatra` × 9 | INT | 0..26 (Ashwini..Revati) |

**Build**: [`app/medini/etl/build_charts_table.py`](app/medini/etl/build_charts_table.py).
**Rows**: 75,149.

### `dasha_windows.parquet`

Every (person, MD, AD) window. 81 rows per person (9 MDs × 9 ADs).

| Column | Type | Description |
|---|---|---|
| window_id | TEXT (PK) | `{person_id}::MD::{md_lord}::AD::{ad_lord}::{md_seq}` |
| person_id | TEXT (FK) | |
| md_lord | TEXT | One of 9 Vimshottari lords |
| ad_lord | TEXT | Same vocabulary |
| md_seq | INT | 0..8 (which MD in natal cycle) |
| ad_seq | INT | 0..8 (which AD within MD) |
| start_jd | FLOAT64 | Julian Day of AD start |
| end_jd | FLOAT64 | Julian Day of AD end |
| duration_days | FLOAT64 | `end_jd - start_jd` |

**Build**: [`app/medini/etl/build_dasha_windows.py`](app/medini/etl/build_dasha_windows.py).
**Rows**: 6,087,069 (75,149 × 81).

## Tier 2 — Derived doctrine layer

### `dasha_tree.parquet`

Per-window MD↔AD mutual-relation features (BPHS Ch.46-47).

| Column | Type | Description |
|---|---|---|
| window_id, person_id, md_lord, ad_lord, md_seq, ad_seq | (FK to dasha_windows) | |
| md_lord_house, md_lord_sign | INT | MD lord's natal placement |
| ad_lord_house, ad_lord_sign | INT | AD lord's natal placement |
| mutual_house_distance | INT | Whole-sign distance MD-sign → AD-sign (1..12) |
| mutual_aspect_md_to_ad | INT | 0 or drishti-distance if MD aspects AD |
| mutual_aspect_ad_to_md | INT | 0 or drishti-distance if AD aspects MD |
| md_dispositor, ad_dispositor | TEXT | Planet ruling MD/AD lord's sign |
| dispositor_md_is_ad | BOOL | AD lord is MD's dispositor (reception clue) |
| dispositor_ad_is_md | BOOL | MD lord is AD's dispositor |

**Build**: [`app/medini/etl/build_dasha_tree.py`](app/medini/etl/build_dasha_tree.py).
**Rows**: 6,087,069.

### `events_with_dasha.parquet`

Each event joined to the dasha window active at `event_jd`.

| Column | Type | Description |
|---|---|---|
| event_id, person_id, event_class, event_date, event_label, source | (from events) | |
| event_jd | FLOAT64 | Computed at noon-UTC of event_date |
| birth_jd | FLOAT64 | From charts |
| age_at_event_years | FLOAT64 | `(event_jd - birth_jd) / 365.2425` |
| md_lord_at_event | TEXT | Active MD lord at event_jd |
| ad_lord_at_event | TEXT | Active AD lord at event_jd |
| md_seq, ad_seq | INT | Indices into dasha cycle |
| md_elapsed_years | FLOAT64 | Years from MD start to event |
| ad_elapsed_years | FLOAT64 | Years from AD start to event |
| ad_duration_days | FLOAT64 | Length of the AD window |

**Build**: [`app/medini/etl/build_event_dasha_join.py`](app/medini/etl/build_event_dasha_join.py).
**Rows**: 64,563 (some unmatched if `event_date` is pre/post natal cycle).

### `event_transits.parquet`

Transit STATE of each planet at the moment of every dated event, plus
classical natal house lordship. Encodes BPHS Ch.31 + Phaladeepika Ch.26
"transit triggers" doctrine.

| Column | Type | Description |
|---|---|---|
| event_id | INT (FK→events_with_dasha) | The event being annotated |
| person_id | TEXT (FK) | Owning person |
| event_jd | FLOAT64 | Duplicated for convenience |
| transit_planet | TEXT | One of 9 grahas |
| transit_lon | FLOAT64 | Sidereal Lahiri longitude at event_jd |
| transit_sign | INT | 1..12 |
| transit_natal_house | INT | Whole-sign house from this person's Lagna where transit lands |
| natal_houses_ruled | TEXT | Comma-separated houses this planet rules natally (empty for Rahu/Ketu) |
| is_slow_mover | BOOL | True for Saturn, Jupiter, Rahu, Ketu, Mars |
| is_retrograde | BOOL | Sidereal retrograde at event_jd |
| has_natal_house_lordship | BOOL | False only for Rahu/Ketu |

**Build**: [`app/medini/etl/build_event_transits.py`](app/medini/etl/build_event_transits.py).
**Rows**: 555,678 (61,742 events × 9 planets).
**Gold view**: `v_event_transits_powerful` — filters to slow movers AND
adds `in_own_lord_house`, `in_auspicious_house`, `in_difficult_house`
flags + dasha context. 308,710 rows.

**Example query** — classical "self-trigger" pattern (lord of natal H
transiting natal H itself) at death events:

```sql
SELECT transit_planet, COUNT(*) AS n_self_triggered
FROM v_event_transits_powerful
WHERE event_class = 'death_cause_unspecified'
  AND in_own_lord_house
GROUP BY transit_planet
ORDER BY n_self_triggered DESC;
-- Saturn: 2,220
-- Jupiter: 1,844
-- Mars: 1,727
```

### `chart_edges.parquet`

Per-chart heterograph edges (BPHS Ch.26 drishti + Ch.34 karaka + dispositor + nakshatra).

| Column | Type | Description |
|---|---|---|
| person_id | TEXT (FK) | |
| edge_type | TEXT | `occupies` \| `drishti` \| `dispositor_of` \| `nakshatra_of` |
| src_type | TEXT | Always `Graha` here |
| src_idx | INT | Graha index 0..8 |
| dst_type | TEXT | `Bhava` \| `Graha` \| `Nakshatra` |
| dst_idx | INT | 0..11 (Bhava) / 0..8 (Graha) / 0..26 (Nakshatra) |
| attr_value | FLOAT64 | Aspect-distance for drishti edges, 0.0 otherwise |

**Build**: [`app/medini/etl/build_chart_heterograph.py`](app/medini/etl/build_chart_heterograph.py).
**Rows**: 3,456,854 (~46 edges per chart).

### `static_graph_edges.parquet`

Chart-independent edges (12 sign rulerships + per-class karakas).

| Column | Type | Description |
|---|---|---|
| edge_type | TEXT | `rules` (Graha→Rasi) or `karaka_for` (Graha→EventClass) |
| src_type, src_idx | (Graha) | |
| dst_type, dst_idx | (Rasi or EventClass) | |
| attr_value | FLOAT64 | Always 1.0 |
| attr_label | TEXT | Event class name for karaka_for edges |

**Rows**: 25.

## Tier 3 — Bridges (the schema-drift killers)

### `person_id_map.parquet`

Canonical `name_norm` ↔ `person_id` mapping across Round-9 corpora and Silver.

| Column | Type | Description |
|---|---|---|
| corpus_tag | TEXT | `ADB` \| `WD` \| `LA` (Round-9 corpus origin) |
| name_norm | TEXT | Round-9 join key |
| birth_jd | FLOAT64 | Canonical link |
| person_id | TEXT (FK→persons) | Silver person_id |
| is_silver_resident | BOOL | True if person_id matches a row in persons |
| name_in_persons | TEXT | The name as stored in persons.parquet |

**Build**: [`app/medini/etl/build_person_id_map.py`](app/medini/etl/build_person_id_map.py).
**Rows**: 75,205 (ADB 10,239 + WD 32,884 + LA 32,082).
**Notes**: After LA promotion to Silver, `is_silver_resident` is 100%.

### `event_class_taxonomy.parquet`

56 ADB granular event classes ↔ 6 harmonized + 7 BPHS categories.

| Column | Type | Description |
|---|---|---|
| granular_class | TEXT (PK) | One of 56 ADB granular classes |
| harmonized_class | TEXT | One of 6 cross-corpus classes (matches events.event_class) |
| category | TEXT | BPHS domain rollup: death / family_loss / relationships / career / fame / personal / misc |
| is_death_subclass | BOOL | True for any death_* / death_of_* / *_death |
| description | TEXT | Human-readable note |

**Build**: [`app/medini/etl/build_event_class_taxonomy.py`](app/medini/etl/build_event_class_taxonomy.py).
**Rows**: 56.

### `resolved_persons.parquet`

Cross-corpus dedup linkage (one row per unique human).

| Column | Type | Description |
|---|---|---|
| canonical_id | TEXT | Highest-precision source person_id (ADB > WD > LA) |
| source_ids | LIST<TEXT> | All merged source person_ids |
| name_key | TEXT | Normalized matching key |
| birth_date | TEXT | ISO date |
| n_corpora | INT | 1..3 |
| match_method | TEXT | `exact_name_date` (v1) |

**Build**: [`app/medini/etl/resolve_persons_dedup.py`](app/medini/etl/resolve_persons_dedup.py).
**Rows**: 73,305 (1,714 cross-corpus matches; 118 are 3-way).

## Gold layer (materialized convenience views)

Located in `app/medini/data/gold/`. Each is a physical parquet
generated from a catalog view; rebuild via
`python -m app.medini.etl.materialize_gold_views` when upstream Silver
changes.

| View | Rows | Purpose |
|---|---:|---|
| `v_event_survival.parquet` | 61,140 | Survival-ready features per event (chart + active dasha) |
| `v_event_with_tree.parquet` | 61,140 | + mutual-relation features (BPHS Ch.46-47) |
| `v_chart_with_person.parquet` | 75,149 | charts JOIN persons (one query for chart + birth metadata) |
| `v_persons_canonical.parquet` | 75,149 | persons + cross-corpus dedup linkage |
| `v_chart_edge_summary.parquet` | 300,596 | Per-chart edge count by edge_type |
| `v_natal_md_ads.parquet` | 676,341 | dasha_tree restricted to natal MD (md_seq=0) |

## Catalog access patterns

```python
from app.medini.ml.experiment_loader import build_experiment_matrix

# Recommended: use the loader (whitelist-validated, SQL-injection-safe).
df = build_experiment_matrix(
    view="v_event_survival",
    label_col="event_class",
    cohort_filter="corpus = 'astro_databank'",
    temporal_cutoff_jd=2440000.0,
)
```

Or directly with DuckDB:

```python
import duckdb
con = duckdb.connect("app/medini/data/catalog.duckdb", read_only=True)
df = con.execute("SELECT * FROM v_event_with_tree LIMIT 100").df()
```

## Lineage diagram

```
                ┌──────────────────┐
                │  raw corpora     │
                │  (Round-9 era,   │
                │   pre-Round-11)  │
                └────────┬─────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │ Tier 0: persons + events       │
         │  (identity & facts)             │
         └───┬───────────────────┬───────┘
             │                   │
             ▼                   ▼
   ┌──────────────────┐    ┌──────────────────┐
   │ Tier 1: charts    │   │ Tier 1: dasha_   │
   │ (per-person       │   │ windows (per-    │
   │  natal chart)     │   │  person MD×AD)   │
   └──────────────────┘    └──────────────────┘
             │                   │
             └────────┬──────────┘
                      ▼
        ┌──────────────────────────┐
        │ Tier 2: dasha_tree,       │
        │ events_with_dasha,        │
        │ chart_edges               │
        └────────┬──────────────────┘
                 ▼
        ┌──────────────────────────┐
        │ Tier 3: bridges           │
        │ (person_id_map,           │
        │  event_class_taxonomy,    │
        │  resolved_persons)        │
        └────────┬──────────────────┘
                 ▼
        ┌──────────────────────────┐
        │ Gold: materialized        │
        │ join views                │
        └──────────────────────────┘
```

## Rebuild sequence

If you re-ingest source data:

```bash
# Tier 0 (foundation)
py -m app.medini.etl.build_person_event_tables

# Tier 1 (cascades from persons)
py -m app.medini.etl.build_charts_table --workers 6
py -m app.medini.etl.build_dasha_windows --workers 6

# Tier 2 (cascades from charts + dasha_windows)
py -m app.medini.etl.build_dasha_tree
py -m app.medini.etl.build_event_dasha_join
py -m app.medini.etl.build_chart_heterograph

# Tier 3 (bridges & dedup)
py -m app.medini.etl.build_event_class_taxonomy
py -m app.medini.etl.build_person_id_map
py -m app.medini.etl.resolve_persons_dedup

# Catalog + Gold materialization
py -m app.medini.etl.build_duckdb_catalog
py -m app.medini.etl.materialize_gold_views
```

## Building from the VedAstro + ASTROCRM corpora (no Round-9 sources)

`build_person_event_tables` needs the Round-9 source parquets. When those are
absent, build the Tier-0 `persons` + `events` directly from the session corpora
with **`build_silver_from_corpora`**, then run the rest of the sequence unchanged:

```bash
py -m app.medini.etl.build_event_class_taxonomy
py -m app.medini.etl.build_silver_from_corpora     # raw.csv + raw_astrocrm.csv + events.csv → persons/events
py -m app.medini.etl.build_charts_table --workers 4
py -m app.medini.etl.build_dasha_windows --workers 4
py -m app.medini.etl.build_dasha_tree
py -m app.medini.etl.resolve_persons_dedup         # before event_dasha_join (catalog needs it)
py -m app.medini.etl.build_event_dasha_join
py -m app.medini.etl.build_duckdb_catalog
py -m app.medini.etl.materialize_gold_views
py -m app.medini.etl.validate_silver_layer         # gate
```

Provenance for this variant: `persons.source ∈ {vedastro, astrocrm}` and
`person_id = {VA|AC}:{birth_jd:.4f}` (vs. the Round-9 `ADB:`/`WD:`/`LA:` tags).
`v_chart_edge_summary` Gold view is skipped unless `build_chart_heterograph` is
also run.
