"""Initialise the DuckDB catalog that fronts the Silver-layer parquets.

The catalog is the single entry point downstream ML code should use to
read data — never direct ``pd.read_parquet`` of a Silver parquet. This
keeps the data architecture honest: Silver schemas change in one place,
Gold-layer features get added as views, no experiment ever produces a
new Silver parquet of its own.

DuckDB ``read_parquet`` is zero-copy and zero-config: parquet files act
as native tables. No data is duplicated into the .duckdb file — only
view definitions are stored.

Catalog tables registered:
  persons              -- Silver (one row per person, namespaced person_id)
  events               -- Silver (one row per event with FK)
  charts               -- Silver (canonical natal chart per person)
  dasha_windows        -- Silver (MD x AD windows per person)
  resolved_persons     -- Silver (cross-corpus dedup linkage)

Gold views (initial set; extend as new experiments arrive):
  v_persons_canonical  -- persons LEFT JOIN resolved_persons on canonical_id;
                          gives a corpus-agnostic view of unique humans.
  v_chart_with_person  -- charts JOIN persons (preserves birth metadata).

Usage:
    python -m app.medini.etl.build_duckdb_catalog
    python -m app.medini.etl.build_duckdb_catalog --data-dir app/medini/data
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

import duckdb

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")
CATALOG_FILE: Final = "catalog.duckdb"

# Silver tables to register, each as a view over its parquet file.
# Order is irrelevant for views — they resolve at query time.
_SILVER_TABLES: Final[tuple[tuple[str, str], ...]] = (
    ("persons", "persons.parquet"),
    ("events", "events.parquet"),
    ("charts", "charts.parquet"),
    ("dasha_windows", "dasha_windows.parquet"),
    ("resolved_persons", "resolved_persons.parquet"),
    ("events_with_dasha", "events_with_dasha.parquet"),
    # Phase 4 — chart heterograph (BPHS Ch.26 drishti + Ch.34 karakas).
    ("chart_edges", "chart_edges.parquet"),
    ("static_graph_edges", "static_graph_edges.parquet"),
    # Phase 5 — dasha tree (BPHS Ch.46-47 MD↔AD mutual relations).
    ("dasha_tree", "dasha_tree.parquet"),
    # Pratyantar-level (PD) windows — completes the MD/AD/PD hierarchy.
    ("dasha_pd_windows", "dasha_pd_windows.parquet"),
    # Event transits — planet transit state + natal house lordship per event.
    ("event_transits", "event_transits.parquet"),
    # Canonical name_norm ↔ person_id bridge across Round-9 and Silver eras.
    ("person_id_map", "person_id_map.parquet"),
    # Canonical event-class taxonomy: 56 granular ADB → 6 harmonized + category.
    ("event_class_taxonomy", "event_class_taxonomy.parquet"),
    # Divisional charts (Shodashavarga: D1 + 14 sub-vargas) per person.
    ("divisional_charts", "divisional_charts.parquet"),
    # Jaimini 8-karaka assignments (AK, AmK, ..., DK, PK2) per person.
    ("jaimini_karakas", "jaimini_karakas.parquet"),
    # Wide-format per-person dossier — identity + natal + karaka in one row.
    ("person_dossier", "person_dossier.parquet"),
    # Wide-format per-event dossier — event + dasha + 9 transits in one row.
    ("event_dossier", "event_dossier.parquet"),
    # Structured attributes + derived labels mined from the categories field.
    ("person_attributes", "person_attributes.parquet"),
    ("person_labels", "person_labels.parquet"),
)


# Optional Silver tables: registered only if the file exists. Lets the
# catalog initialise on a partially-built corpus (e.g. before Phase 2 runs).
_OPTIONAL_SILVER: Final[set[str]] = {
    "events_with_dasha", "chart_edges", "static_graph_edges", "dasha_tree",
    "person_id_map", "event_class_taxonomy", "dasha_pd_windows",
    "event_transits", "divisional_charts", "jaimini_karakas",
    "person_dossier", "event_dossier", "person_attributes", "person_labels",
}


def _register_silver_views(con: duckdb.DuckDBPyConnection, data_dir: Path) -> None:
    """Bind each Silver parquet as a DuckDB view (zero copy).

    Optional tables (declared in ``_OPTIONAL_SILVER``) silently skip if
    their parquet file is missing — they get registered on a later
    re-run after the upstream ETL runs.
    """
    for view_name, fname in _SILVER_TABLES:
        path_obj = data_dir / fname
        if not path_obj.exists():
            if view_name in _OPTIONAL_SILVER:
                logger.info("Skipped optional Silver view %s (file not built yet)", view_name)
                continue
            raise FileNotFoundError(f"Required Silver parquet missing: {path_obj}")
        path = path_obj.resolve().as_posix()
        con.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT * FROM read_parquet('{path}')"
        )
        n = con.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
        logger.info("Registered Silver view %-20s (%d rows)", view_name, n)


def _create_gold_views(con: duckdb.DuckDBPyConnection) -> None:
    """Create the initial Gold-layer views.

    Gold views materialise lazily — DuckDB caches nothing. Each query
    re-executes the join, but on parquet that is fast (~ms for these
    sizes). When a Gold view becomes a hot path, ``CREATE TABLE AS``
    can promote it to a cached Silver-layer parquet via a deliberate
    ETL step.
    """
    con.execute("""
        CREATE OR REPLACE VIEW v_persons_canonical AS
        SELECT
            p.*,
            r.canonical_id,
            r.n_corpora
        FROM persons p
        LEFT JOIN resolved_persons r
          ON list_contains(r.source_ids, p.person_id)
    """)

    con.execute("""
        CREATE OR REPLACE VIEW v_chart_with_person AS
        SELECT
            c.*,
            p.name,
            p.birth_date,
            p.source
        FROM charts c
        JOIN persons p USING (person_id)
    """)

    # ---------------- Bridge view (name_norm ↔ person_id) ----------------
    has_id_map = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'person_id_map'"
    ).fetchone()[0]
    bridge_views: tuple[str, ...] = ()
    if has_id_map:
        # Helper view: ADB+WD persons that are joined to the Silver layer,
        # restricted to the bridged subset (excludes the LA gap).
        con.execute("""
            CREATE OR REPLACE VIEW v_bridged_persons AS
            SELECT corpus_tag, name_norm, birth_jd, person_id
            FROM person_id_map
            WHERE is_silver_resident
        """)
        bridge_views = ("v_bridged_persons",)

    # ---------------- Gold views over Phase 4/5 tables ----------------
    # Whether the Phase 4/5 tables are registered (built).
    has_chart_edges = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'chart_edges'"
    ).fetchone()[0]
    has_dasha_tree = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'dasha_tree'"
    ).fetchone()[0]

    heterograph_views: tuple[str, ...] = ()
    if has_chart_edges:
        # Convenience view: edge counts per chart per edge type.
        con.execute("""
            CREATE OR REPLACE VIEW v_chart_edge_summary AS
            SELECT
                person_id,
                edge_type,
                COUNT(*) AS n_edges
            FROM chart_edges
            GROUP BY person_id, edge_type
        """)
        heterograph_views += ("v_chart_edge_summary",)

    dasha_tree_views: tuple[str, ...] = ()
    if has_dasha_tree:
        # Convenience view: dasha_tree restricted to the natal MD (md_seq=0)
        # for fast natal-window queries (per-person 9 rows).
        con.execute("""
            CREATE OR REPLACE VIEW v_natal_md_ads AS
            SELECT *
            FROM dasha_tree
            WHERE md_seq = 0
        """)
        dasha_tree_views += ("v_natal_md_ads",)

    # ---------------- Event-transit views ----------------
    has_transits = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'event_transits'"
    ).fetchone()[0]
    transit_views: tuple[str, ...] = ()
    if has_transits:
        # The classical "powerful trigger" view: slow-mover transit
        # landing in a house this planet is natal lord of, joined with
        # event class and dasha context for one-query analysis.
        con.execute("""
            CREATE OR REPLACE VIEW v_event_transits_powerful AS
            SELECT
                t.event_id,
                t.person_id,
                t.transit_planet,
                t.transit_sign,
                t.transit_natal_house,
                t.natal_houses_ruled,
                t.is_retrograde,
                e.event_class,
                e.event_date,
                e.md_lord_at_event,
                e.ad_lord_at_event,
                e.age_at_event_years,
                e.source AS corpus,
                -- Is the transit planet currently transiting one of its OWN
                -- natal-lord houses? This is the classical "self-trigger" pattern.
                CASE
                    WHEN t.has_natal_house_lordship
                     AND list_contains(
                            string_split(t.natal_houses_ruled, ','),
                            CAST(t.transit_natal_house AS TEXT))
                    THEN TRUE ELSE FALSE END AS in_own_lord_house,
                -- Is the transit landing in a trikona (1, 5, 9) or 10th?
                t.transit_natal_house IN (1, 5, 9, 10) AS in_auspicious_house,
                -- Is the transit landing in a dusthana (6, 8, 12)?
                t.transit_natal_house IN (6, 8, 12) AS in_difficult_house
            FROM event_transits t
            JOIN events_with_dasha e USING (event_id)
            WHERE t.is_slow_mover
        """)
        transit_views = ("v_event_transits_powerful",)

    # Mutual-relation enriched survival view — joins events_with_dasha to
    # dasha_tree to add MD↔AD mutual relations alongside each event. This
    # is the canonical training view for doctrine-aware survival ML.
    has_phase2 = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'events_with_dasha'"
    ).fetchone()[0]
    if has_phase2 and has_dasha_tree:
        con.execute("""
            CREATE OR REPLACE VIEW v_event_with_tree AS
            SELECT
                e.event_id, e.person_id, e.event_class,
                e.event_jd, e.birth_jd, e.age_at_event_years,
                e.md_lord_at_event, e.ad_lord_at_event,
                e.md_seq, e.ad_seq, e.md_elapsed_years, e.ad_elapsed_years,
                e.source AS corpus,
                t.md_lord_house, t.md_lord_sign,
                t.ad_lord_house, t.ad_lord_sign,
                t.mutual_house_distance,
                t.mutual_aspect_md_to_ad,
                t.mutual_aspect_ad_to_md,
                t.md_dispositor, t.ad_dispositor,
                t.dispositor_md_is_ad, t.dispositor_ad_is_md
            FROM events_with_dasha e
            JOIN dasha_tree t
              ON e.person_id = t.person_id
             AND e.md_seq = t.md_seq
             AND e.ad_seq = t.ad_seq
            WHERE e.md_lord_at_event IS NOT NULL
        """)
        dasha_tree_views += ("v_event_with_tree",)

    # Survival-ready feature view: events joined to chart + active dasha.
    # This is what Stage D should consume to retarget at time-to-event.
    # Built only if events_with_dasha was registered (Phase 2 has run).
    has_phase2 = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'events_with_dasha'"
    ).fetchone()[0]
    survival_views: tuple[str, ...] = ()
    if has_phase2:
        con.execute("""
            CREATE OR REPLACE VIEW v_event_survival AS
            SELECT
                e.event_id, e.person_id, e.event_class,
                e.event_jd, e.birth_jd,
                (e.event_jd - e.birth_jd) AS time_to_event_days,
                e.age_at_event_years,
                e.md_lord_at_event, e.ad_lord_at_event,
                e.md_seq, e.ad_seq,
                e.md_elapsed_years, e.ad_elapsed_years,
                e.ad_duration_days,
                e.source AS corpus,
                c.asc_sign, c.moon_lon, c.moon_nakshatra,
                c.sun_sign, c.mars_sign, c.mercury_sign,
                c.jupiter_sign, c.venus_sign, c.saturn_sign,
                c.rahu_sign, c.ketu_sign,
                c.time_precision
            FROM events_with_dasha e
            JOIN charts c USING (person_id)
            WHERE e.md_lord_at_event IS NOT NULL
        """)
        survival_views = ("v_event_survival",)

    for v in (
        ("v_persons_canonical", "v_chart_with_person")
        + heterograph_views + dasha_tree_views + survival_views
        + bridge_views + transit_views
    ):
        n = con.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
        logger.info("Created Gold view    %-20s (%d rows)", v, n)


def initialise_catalog(data_dir: Path, catalog_path: Path) -> duckdb.DuckDBPyConnection:
    """Create or update the DuckDB catalog at ``catalog_path``.

    Returns the open connection (caller closes). Safe to re-run — uses
    ``CREATE OR REPLACE VIEW`` everywhere.
    """
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(catalog_path))
    _register_silver_views(con, data_dir)
    _create_gold_views(con)
    return con


def main() -> int:
    """CLI entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--catalog-path", type=Path, default=None,
                        help=f"Defaults to <data-dir>/{CATALOG_FILE}")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    catalog_path = args.catalog_path or (args.data_dir / CATALOG_FILE)
    con = initialise_catalog(args.data_dir, catalog_path)
    try:
        logger.info("Catalog ready at %s", catalog_path)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
