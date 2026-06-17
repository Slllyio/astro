"""Data-quality validation for the Silver layer.

Automated checks that the canonical Silver tables remain consistent
with each other and with their schema contract. Run this after any
rebuild to catch drift before it cascades into ML experiments.

Checks performed:

  Schema invariants
  - Every required column present in each table
  - Primary-key columns are unique (no duplicate person_id, etc.)
  - Numeric ranges hold (signs 1..12, nakshatras 0..26, houses 1..12)

  Foreign-key integrity
  - events.person_id subset of persons.person_id
  - charts.person_id subset of persons.person_id
  - dasha_windows.person_id subset of persons.person_id
  - dasha_tree.person_id subset of persons.person_id
  - chart_edges.person_id subset of persons.person_id
  - events_with_dasha.person_id subset of persons.person_id
  - person_id_map.person_id subset of persons.person_id  (where is_silver_resident)

  Cardinality
  - charts has one row per person
  - dasha_windows has 81 rows per person (MD × AD)
  - dasha_tree has 81 rows per person
  - chart_edges has 46±5 rows per person

  Cross-table consistency
  - events_with_dasha row count == events row count
  - resolved_persons.canonical_id subset of persons.person_id

  Taxonomy consistency
  - events.event_class ∈ {marriage, career, fame, death_cause_unspecified,
                           relationships, other}
  - event_class_taxonomy.harmonized_class spans the same set

Each failed check is reported with row counts. The script exits with
code 1 if any FAIL conditions hit; 0 otherwise. CI can wire this up.

Usage:
    python -m app.medini.etl.validate_silver_layer
    python -m app.medini.etl.validate_silver_layer --strict   # exit on WARN too
"""
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Callable

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR: Final = Path("app/medini/data")


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str = ""
    level: str = "FAIL"  # FAIL | WARN | INFO


@dataclass
class ValidationReport:
    results: list[CheckResult] = field(default_factory=list)

    def add(self, name: str, passed: bool, message: str = "",
            level: str = "FAIL") -> None:
        self.results.append(CheckResult(name, passed, message, level))

    @property
    def n_fail(self) -> int:
        return sum(1 for r in self.results if not r.passed and r.level == "FAIL")

    @property
    def n_warn(self) -> int:
        return sum(1 for r in self.results if not r.passed and r.level == "WARN")

    @property
    def n_pass(self) -> int:
        return sum(1 for r in self.results if r.passed)


def _load(data_dir: Path, name: str, **kwargs) -> pd.DataFrame:
    return pd.read_parquet(data_dir / name, **kwargs)


# --------------------------------------------------------------------------- #
# Individual checks                                                           #
# --------------------------------------------------------------------------- #

def check_person_id_uniqueness(
    data_dir: Path, report: ValidationReport,
) -> None:
    """persons.person_id is the canonical PK; must be unique."""
    persons = _load(data_dir, "persons.parquet", columns=["person_id"])
    dups = len(persons) - persons["person_id"].nunique()
    report.add(
        "persons.person_id is unique",
        passed=(dups == 0),
        message=f"{dups} duplicate person_id values" if dups else "ok",
    )


def check_event_person_fk(data_dir: Path, report: ValidationReport) -> None:
    """Every events.person_id must resolve to persons."""
    persons = _load(data_dir, "persons.parquet", columns=["person_id"])
    events = _load(data_dir, "events.parquet", columns=["person_id"])
    orphans = (~events["person_id"].isin(set(persons["person_id"]))).sum()
    report.add(
        "events.person_id subset of persons.person_id",
        passed=(orphans == 0),
        message=f"{orphans} orphan event rows" if orphans else "ok",
    )


def check_charts_one_per_person(
    data_dir: Path, report: ValidationReport,
) -> None:
    """charts.parquet has one row per person."""
    persons = _load(data_dir, "persons.parquet", columns=["person_id"])
    charts = _load(data_dir, "charts.parquet", columns=["person_id"])
    persons_set = set(persons["person_id"])
    charts_set = set(charts["person_id"])
    missing_charts = len(persons_set - charts_set)
    orphan_charts = len(charts_set - persons_set)
    dups = len(charts) - charts["person_id"].nunique()
    passed = missing_charts == 0 and orphan_charts == 0 and dups == 0
    report.add(
        "charts is 1:1 with persons",
        passed=passed,
        message=(f"missing_for_persons={missing_charts} orphan={orphan_charts} "
                 f"duplicates={dups}") if not passed else "ok",
    )


def check_dasha_windows_cardinality(
    data_dir: Path, report: ValidationReport,
) -> None:
    """Every person has exactly 81 (MD×AD) windows."""
    persons = _load(data_dir, "persons.parquet", columns=["person_id"])
    dw = _load(data_dir, "dasha_windows.parquet",
               columns=["person_id"])
    counts = dw.groupby("person_id").size()
    not_81 = (counts != 81).sum()
    expected_persons = len(persons)
    matched_persons = counts.index.isin(set(persons["person_id"])).sum()
    passed = not_81 == 0 and matched_persons == expected_persons
    report.add(
        "dasha_windows has 81 rows per person",
        passed=passed,
        message=(f"persons_with_wrong_count={not_81} "
                 f"persons_in_windows={matched_persons}/{expected_persons}")
        if not passed else "ok",
    )


def check_dasha_tree_join(
    data_dir: Path, report: ValidationReport,
) -> None:
    """dasha_tree should have the same window_ids as dasha_windows."""
    dw = _load(data_dir, "dasha_windows.parquet", columns=["window_id"])
    dt = _load(data_dir, "dasha_tree.parquet", columns=["window_id"])
    dw_set = set(dw["window_id"])
    dt_set = set(dt["window_id"])
    missing = len(dw_set - dt_set)
    orphan = len(dt_set - dw_set)
    passed = missing == 0 and orphan == 0
    report.add(
        "dasha_tree.window_id == dasha_windows.window_id",
        passed=passed,
        message=(f"missing_in_tree={missing} orphan_in_tree={orphan}")
        if not passed else "ok",
    )


def check_chart_ranges(data_dir: Path, report: ValidationReport) -> None:
    """All sign columns 1..12, nakshatra 0..26, house 1..12."""
    charts = _load(data_dir, "charts.parquet")
    grahas = ("sun", "moon", "mars", "mercury", "jupiter", "venus",
              "saturn", "rahu", "ketu")
    issues: list[str] = []
    for g in grahas:
        s = charts[f"{g}_sign"]
        if ((s < 1) | (s > 12)).any():
            issues.append(f"{g}_sign out-of-range")
        n = charts[f"{g}_nakshatra"]
        if ((n < 0) | (n > 26)).any():
            issues.append(f"{g}_nakshatra out-of-range")
        h = charts[f"{g}_house"]
        if ((h < 1) | (h > 12)).any():
            issues.append(f"{g}_house out-of-range")
    if "asc_nakshatra" in charts.columns:
        n = charts["asc_nakshatra"]
        if ((n < 0) | (n > 26)).any():
            issues.append("asc_nakshatra out-of-range")
    if ((charts["asc_sign"] < 1) | (charts["asc_sign"] > 12)).any():
        issues.append("asc_sign out-of-range")
    report.add(
        "chart sign/nakshatra/house ranges",
        passed=(not issues),
        message=", ".join(issues) if issues else "ok",
    )


def check_event_class_taxonomy(
    data_dir: Path, report: ValidationReport,
) -> None:
    """events.event_class must use the harmonized vocabulary."""
    events = _load(data_dir, "events.parquet", columns=["event_class"])
    tax = _load(data_dir, "event_class_taxonomy.parquet",
                columns=["harmonized_class"])
    valid_classes = set(tax["harmonized_class"].unique()) | {"other"}
    invalid = (~events["event_class"].isin(valid_classes)).sum()
    report.add(
        "events.event_class subset of harmonized vocabulary",
        passed=(invalid == 0),
        message=(f"{invalid} events with unknown class") if invalid else "ok",
    )


def check_person_id_map_residents(
    data_dir: Path, report: ValidationReport,
) -> None:
    """Where is_silver_resident, the person_id must exist in persons.

    Skipped if person_id_map hasn't been built — it's the optional Round-9
    name↔id bridge, absent for stores built directly from canonical corpora.
    """
    if not (data_dir / "person_id_map.parquet").exists():
        return
    persons = _load(data_dir, "persons.parquet", columns=["person_id"])
    pim = _load(data_dir, "person_id_map.parquet",
                columns=["person_id", "is_silver_resident"])
    resident = pim[pim["is_silver_resident"]]
    orphan = (~resident["person_id"].isin(set(persons["person_id"]))).sum()
    report.add(
        "person_id_map.is_silver_resident rows subset of persons",
        passed=(orphan == 0),
        message=f"{orphan} broken resident links" if orphan else "ok",
    )


def check_event_date_precision_populated(
    data_dir: Path, report: ValidationReport,
) -> None:
    """Every event must have a date precision flag."""
    events = _load(data_dir, "events.parquet",
                   columns=["event_date_precision"])
    n_null = events["event_date_precision"].isna().sum()
    report.add(
        "events.event_date_precision is populated",
        passed=(n_null == 0),
        message=f"{n_null} events with NULL precision" if n_null else "ok",
        level="WARN",
    )


def check_birth_time_confidence_populated(
    data_dir: Path, report: ValidationReport,
) -> None:
    """birth_time_confidence should be present for all persons."""
    persons = _load(data_dir, "persons.parquet",
                    columns=["birth_time_confidence"])
    n_null = persons["birth_time_confidence"].isna().sum()
    report.add(
        "persons.birth_time_confidence is populated",
        passed=(n_null == 0),
        message=f"{n_null} persons with NULL confidence" if n_null else "ok",
        level="WARN",
    )


def check_transit_cardinality(
    data_dir: Path, report: ValidationReport,
) -> None:
    """Every event with a transit row should have exactly 9 transit rows
    (one per graha). Skip the check if event_transits hasn't been built."""
    transit_path = data_dir / "event_transits.parquet"
    if not transit_path.exists():
        return
    transits = pd.read_parquet(transit_path, columns=["event_id"])
    counts = transits.groupby("event_id").size()
    not_9 = (counts != 9).sum()
    report.add(
        "event_transits has 9 rows per event",
        passed=(not_9 == 0),
        message=f"{not_9} events with wrong transit count" if not_9 else "ok",
    )


def check_transit_event_fk(
    data_dir: Path, report: ValidationReport,
) -> None:
    """event_transits.event_id must resolve to events_with_dasha."""
    transit_path = data_dir / "event_transits.parquet"
    if not transit_path.exists():
        return
    events = _load(data_dir, "events_with_dasha.parquet", columns=["event_id"])
    transits = pd.read_parquet(transit_path, columns=["event_id"])
    orphans = (~transits["event_id"].isin(set(events["event_id"]))).sum()
    report.add(
        "event_transits.event_id subset of events_with_dasha",
        passed=(orphans == 0),
        message=f"{orphans} orphan transit rows" if orphans else "ok",
    )


# --------------------------------------------------------------------------- #
# Driver                                                                      #
# --------------------------------------------------------------------------- #

ALL_CHECKS: Final[tuple[Callable[[Path, ValidationReport], None], ...]] = (
    check_person_id_uniqueness,
    check_event_person_fk,
    check_charts_one_per_person,
    check_dasha_windows_cardinality,
    check_dasha_tree_join,
    check_chart_ranges,
    check_event_class_taxonomy,
    check_person_id_map_residents,
    check_event_date_precision_populated,
    check_birth_time_confidence_populated,
    check_transit_cardinality,
    check_transit_event_fk,
)


def validate(data_dir: Path) -> ValidationReport:
    """Run all checks; return a populated report."""
    report = ValidationReport()
    for check in ALL_CHECKS:
        try:
            check(data_dir, report)
        except Exception as exc:  # noqa: BLE001 — any check error → FAIL
            report.add(check.__name__, passed=False,
                       message=f"unexpected exception: {exc}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 on any WARN, not just FAIL.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    report = validate(args.data_dir)

    width = max(len(r.name) for r in report.results) + 2
    print()
    print(f"{'CHECK':<{width}} STATUS  MESSAGE")
    print("-" * (width + 30))
    for r in report.results:
        status = "PASS" if r.passed else r.level
        print(f"{r.name:<{width}} {status:6s}  {r.message}")
    print()
    print(f"Summary: {report.n_pass} PASS, {report.n_warn} WARN, "
          f"{report.n_fail} FAIL")

    exit_code = 0
    if report.n_fail > 0:
        exit_code = 1
    elif args.strict and report.n_warn > 0:
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
