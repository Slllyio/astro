"""Topologically-ordered rebuild of the Silver/Gold/Wide-dossier DAG.

Replaces the ad-hoc "which script do I run next?" mental model with a
declarative dependency graph. Each per-script freshness guard
(``app.medini.etl._freshness.skip_if_fresh``) keeps individual targets
idempotent — this runner just orchestrates them in the right order.

## DAG layers (top-down)

  bronze   raw scrapers (Wikidata / Lunarastro / etc.)         — manual
  silver-foundation   raw CSV → first-pass parquet              — manual
  silver-core         canonical persons + events + charts       — automated
  silver-derived      dasha / transits / divisional / karakas   — automated
  gold-wide           person_dossier + event_dossier            — automated
  application         readings + master_readings                — automated
  catalog             DuckDB views over everything above        — automated

This runner covers the four "automated" layers. Bronze and silver-
foundation are still manual (one-time scrapes, expensive).

Usage:
    python -m app.medini.etl.rebuild                  # build everything that's stale
    python -m app.medini.etl.rebuild --dry-run        # show what would run, in order
    python -m app.medini.etl.rebuild --graph          # print the dependency DAG
    python -m app.medini.etl.rebuild --target person_dossier   # build one target + its deps
    python -m app.medini.etl.rebuild --force          # rebuild everything (ignore freshness)
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")


@dataclass(frozen=True)
class Target:
    """One node in the rebuild DAG.

    name: short identifier used on the CLI (--target name)
    module: dotted module path invoked via ``py -3.12 -m <module>``
    output: relative parquet/duckdb path the module produces
    inputs: parquets the module reads (tuple — frozen for hashing)
    layer: one of silver-core / silver-derived / gold-wide / application / catalog
    """
    name: str
    module: str
    output: str
    inputs: tuple[str, ...]
    layer: str


# Order in this list IS the canonical topological order. Sibling-with-no-shared-dep
# targets are ordered alphabetically within each layer for predictability.
_DAG: Final[tuple[Target, ...]] = (
    # ─── silver-core (canonical Round-11 layer) ───
    Target(
        name="persons_events",
        module="app.medini.etl.build_person_event_tables",
        output="persons.parquet",
        inputs=(),  # reads merged_all.csv (Bronze, manual)
        layer="silver-core",
    ),
    Target(
        name="charts",
        module="app.medini.etl.build_charts_table",
        output="charts.parquet",
        inputs=("persons.parquet",),
        layer="silver-core",
    ),
    Target(
        name="resolved_persons",
        module="app.medini.etl.resolve_persons_dedup",
        output="resolved_persons.parquet",
        inputs=("persons.parquet",),
        layer="silver-core",
    ),
    Target(
        name="person_id_map",
        module="app.medini.etl.build_person_id_map",
        output="person_id_map.parquet",
        inputs=("persons.parquet", "resolved_persons.parquet"),
        layer="silver-core",
    ),
    Target(
        name="dasha_windows",
        module="app.medini.etl.build_dasha_windows",
        output="dasha_windows.parquet",
        inputs=("charts.parquet",),
        layer="silver-core",
    ),
    Target(
        name="event_class_taxonomy",
        module="app.medini.etl.build_event_class_taxonomy",
        output="event_class_taxonomy.parquet",
        inputs=(),
        layer="silver-core",
    ),

    # ─── silver-derived (built from silver-core) ───
    Target(
        name="dasha_pd_windows",
        module="app.medini.etl.build_dasha_pd_windows",
        output="dasha_pd_windows.parquet",
        inputs=("dasha_windows.parquet",),
        layer="silver-derived",
    ),
    Target(
        name="dasha_tree",
        module="app.medini.etl.build_dasha_tree",
        output="dasha_tree.parquet",
        inputs=("dasha_windows.parquet", "charts.parquet"),
        layer="silver-derived",
    ),
    Target(
        name="events_with_dasha",
        module="app.medini.etl.build_event_dasha_join",
        output="events_with_dasha.parquet",
        inputs=("events.parquet", "dasha_windows.parquet"),
        layer="silver-derived",
    ),
    Target(
        name="event_transits",
        module="app.medini.etl.build_event_transits",
        output="event_transits.parquet",
        inputs=("events_with_dasha.parquet", "charts.parquet"),
        layer="silver-derived",
    ),
    Target(
        name="divisional_charts",
        module="app.medini.etl.build_divisional_charts",
        output="divisional_charts.parquet",
        inputs=("charts.parquet",),
        layer="silver-derived",
    ),
    Target(
        name="jaimini_karakas",
        module="app.medini.etl.build_jaimini_karakas",
        output="jaimini_karakas.parquet",
        inputs=("charts.parquet",),
        layer="silver-derived",
    ),
    Target(
        name="chart_heterograph",
        module="app.medini.etl.build_chart_heterograph",
        output="chart_edges.parquet",
        inputs=("charts.parquet", "jaimini_karakas.parquet"),
        layer="silver-derived",
    ),

    # ─── gold-wide (denormalized dossiers) ───
    Target(
        name="person_dossier",
        module="app.medini.etl.build_person_dossier",
        output="person_dossier.parquet",
        inputs=("persons.parquet", "charts.parquet", "jaimini_karakas.parquet"),
        layer="gold-wide",
    ),
    Target(
        name="event_dossier",
        module="app.medini.etl.build_event_dossier",
        output="event_dossier.parquet",
        inputs=("events_with_dasha.parquet", "dasha_pd_windows.parquet",
                "event_transits.parquet", "charts.parquet"),
        layer="gold-wide",
    ),

    # ─── application (per-person reading materialization) ───
    Target(
        name="readings",
        module="app.medini.etl.build_person_readings",
        output="readings.parquet",
        inputs=("person_dossier.parquet",),
        layer="application",
    ),
    Target(
        name="master_readings",
        module="app.medini.etl.build_person_master_readings",
        output="master_readings.parquet",
        inputs=("person_dossier.parquet",),
        layer="application",
    ),

    # ─── catalog (registers everything above as DuckDB views) ───
    Target(
        name="catalog",
        module="app.medini.etl.build_duckdb_catalog",
        output="catalog.duckdb",
        inputs=("persons.parquet", "events.parquet", "charts.parquet",
                "dasha_windows.parquet", "resolved_persons.parquet"),
        layer="catalog",
    ),
)

_BY_NAME: Final = {t.name: t for t in _DAG}


def _needs_rebuild(target: Target, data_dir: Path, *, force: bool) -> bool:
    """Mirror app.medini.etl._freshness logic, applied to target paths."""
    if force:
        return True
    out_path = data_dir / target.output
    if not out_path.exists():
        return True
    out_mtime = out_path.stat().st_mtime
    for inp_name in target.inputs:
        inp_path = data_dir / inp_name
        if not inp_path.exists():
            return True
        if inp_path.stat().st_mtime > out_mtime:
            return True
    return False


def _transitive_deps(target_name: str, *, visited: set[str] | None = None) -> list[str]:
    """Return [target + all transitively-required deps] in topo order."""
    if visited is None:
        visited = set()
    if target_name in visited:
        return []
    visited.add(target_name)
    target = _BY_NAME.get(target_name)
    if target is None:
        raise SystemExit(f"Unknown target: {target_name}. "
                         f"Known: {sorted(_BY_NAME)}")
    chain: list[str] = []
    for inp in target.inputs:
        # Find any DAG target that produces this input
        for other in _DAG:
            if other.output == inp:
                chain.extend(_transitive_deps(other.name, visited=visited))
                break
    chain.append(target_name)
    return chain


def _run_target(target: Target) -> int:
    """Invoke the target's module as a subprocess."""
    cmd = [sys.executable, "-m", target.module]
    logger.info("RUN   %-22s  %s", target.name, " ".join(cmd))
    return subprocess.call(cmd)


def print_graph() -> None:
    """Print the DAG as a layered text diagram."""
    layers = ("silver-core", "silver-derived", "gold-wide",
              "application", "catalog")
    for layer in layers:
        print(f"\n## {layer}")
        for t in _DAG:
            if t.layer != layer:
                continue
            deps_str = ", ".join(t.inputs) if t.inputs else "(no parquet deps)"
            print(f"  {t.name:22s} -> {t.output:35s}  <- {deps_str}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--target", type=str, default=None,
                        help="Build only this target + its transitive deps.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would run without invoking anything.")
    parser.add_argument("--graph", action="store_true",
                        help="Print the DAG and exit.")
    parser.add_argument("--force", action="store_true",
                        help="Rebuild everything in the plan (ignore freshness).")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    if args.graph:
        print_graph()
        return 0

    if args.target:
        plan_names = _transitive_deps(args.target)
    else:
        plan_names = [t.name for t in _DAG]

    plan = [_BY_NAME[n] for n in plan_names]
    needs = [t for t in plan if _needs_rebuild(t, args.data_dir, force=args.force)]
    skip = [t for t in plan if t not in needs]

    logger.info("Plan: %d targets — %d to rebuild, %d fresh (skip)",
                len(plan), len(needs), len(skip))
    for t in plan:
        marker = "RUN " if t in needs else "SKIP"
        logger.info("  [%s] %-22s  (%s)", marker, t.name, t.layer)

    if args.dry_run:
        logger.info("Dry-run — no commands executed.")
        return 0

    failed: list[str] = []
    for t in needs:
        rc = _run_target(t)
        if rc != 0:
            failed.append(t.name)
            logger.error("Target %s failed (exit %d) — stopping", t.name, rc)
            break

    logger.info(
        "Done: %d ran, %d skipped, %d failed",
        len(needs) - len(failed), len(skip), len(failed),
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
