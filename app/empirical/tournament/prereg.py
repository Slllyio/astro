"""Pre-registration — the record of what was going to be tested, made before testing it.

The tournament's whole claim to honesty rests on this file being written first and
hashed. One CSV row per test: feature bank × target × statistic × baseline model ×
control arms × min n × tier requirement. A row is scorable **only** when its status
is ``locked``, and locking freezes the file's hash into the empirical ratchet.

Three rules are enforced in code rather than left to discipline:

* **Only locked rows score.** A ``draft`` row can be edited freely; the moment it
  locks it becomes evidence. :func:`scorable` is the only way to obtain rows for
  scoring, and it filters to locked.
* **Every locked row carries the mandatory control arms.** A test registered
  without its sham gate or its chartless twin is not a test — it is a result
  waiting to be believed. :func:`validate` refuses to lock such a row.
* **The registry is content-addressed.** :func:`registry_fingerprint` is what the
  ratchet stores, so a row edited after locking is detectable, not deniable.

Usage:
    python -m app.empirical.tournament.prereg --registry tools/empirical/prereg.csv --validate
    python -m app.empirical.tournament.prereg --registry tools/empirical/prereg.csv --lock T001
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path
from typing import Final, Iterable, Sequence

logger = logging.getLogger(__name__)

__all__ = [
    "Status",
    "Registration",
    "RegistrationError",
    "FIELDNAMES",
    "MANDATORY_CONTROL_ARMS",
    "FEATURE_BANKS",
    "STATISTICS",
    "STAGES",
    "TIER_REQUIREMENTS",
    "validate",
    "load_registry",
    "write_registry",
    "scorable",
    "registry_fingerprint",
]


class Status(str, Enum):
    """Lifecycle of a registered test."""

    DRAFT = "draft"
    LOCKED = "locked"
    RETIRED = "retired"


#: The three chart feature banks the tournament pits against each other, plus the
#: chartless bank that every one of them must beat to count for anything.
FEATURE_BANKS: Final[frozenset[str]] = frozenset(
    {"western", "vedic_timing", "raw_astronomy", "chartless"}
)

STATISTICS: Final[frozenset[str]] = frozenset({"auc", "cox_hr", "risk_ratio", "within_person_rank"})

STAGES: Final[frozenset[str]] = frozenset({"screening", "confirmatory"})

#: Birth-time quality required for the row to admit a person.
#: A = registry/certified, AB = A or B, ABS = A, B, or self-reported (exploratory only).
TIER_REQUIREMENTS: Final[frozenset[str]] = frozenset({"A", "AB", "ABS"})

#: Control arms every locked test must declare. These are not defaults that can be
#: switched off — a row lacking any of them fails validation.
#:
#: sham_target          the anti-peeking gate: a permuted target must read ~0.500
#:                      before the real result may be read at all
#: chartless_baseline   the AUC-0.744 bar; a chart model scores as delta over its
#:                      chartless demographic twin, never as a raw number
#: era_stratification   birth-decade strata, because planet positions proxy birth era
#: person_leak_preflight  no person may appear in both train and holdout
MANDATORY_CONTROL_ARMS: Final[frozenset[str]] = frozenset(
    {"sham_target", "chartless_baseline", "era_stratification", "person_leak_preflight"}
)

#: Extra arms that are optional but registrable.
OPTIONAL_CONTROL_ARMS: Final[frozenset[str]] = frozenset(
    {"within_person_control_dates", "immortal_time_capping", "no_default_time_charts"}
)

_ARM_SEPARATOR: Final[str] = "|"


class RegistrationError(ValueError):
    """A registration row is malformed or cannot legally be locked."""


@dataclass(frozen=True, slots=True)
class Registration:
    """One pre-registered test.

    Attributes:
      test_id: Stable identifier; unique within the registry.
      feature_bank: Which bank supplies the predictors.
      target: The outcome being predicted.
      statistic: The test statistic.
      baseline_model: Identifier of the chartless twin this is scored against.
      control_arms: Declared control arms; must be a superset of
        :data:`MANDATORY_CONTROL_ARMS` to lock.
      min_n: Minimum qualifying rows; below this the row is not scored at all.
      tier_requirement: Birth-time quality floor.
      stage: ``screening`` or ``confirmatory``.
      direction: ``greater`` or ``less`` — registered in advance so a result
        cannot be reinterpreted after the fact.
      status: See :class:`Status`.
      notes: Free text; never load-bearing.
    """

    test_id: str
    feature_bank: str
    target: str
    statistic: str
    baseline_model: str
    control_arms: tuple[str, ...]
    min_n: int
    tier_requirement: str
    stage: str
    direction: str
    status: Status
    notes: str = ""

    @property
    def is_scorable(self) -> bool:
        """Only a locked row may be scored."""
        return self.status is Status.LOCKED


FIELDNAMES: Final[tuple[str, ...]] = tuple(f.name for f in fields(Registration))


def validate(reg: Registration, *, for_locking: bool = False) -> None:
    """Raise :class:`RegistrationError` if the row is malformed.

    Args:
      reg: The row to check.
      for_locking: When True, also enforce the rules that only bind at lock time
        (mandatory control arms present). A draft may be incomplete; a locked row
        may not.
    """
    if not reg.test_id.strip():
        raise RegistrationError("test_id must be non-empty")
    if reg.feature_bank not in FEATURE_BANKS:
        raise RegistrationError(f"{reg.test_id}: unknown feature_bank {reg.feature_bank!r}")
    if reg.statistic not in STATISTICS:
        raise RegistrationError(f"{reg.test_id}: unknown statistic {reg.statistic!r}")
    if reg.stage not in STAGES:
        raise RegistrationError(f"{reg.test_id}: unknown stage {reg.stage!r}")
    if reg.tier_requirement not in TIER_REQUIREMENTS:
        raise RegistrationError(f"{reg.test_id}: unknown tier_requirement {reg.tier_requirement!r}")
    if reg.direction not in {"greater", "less"}:
        raise RegistrationError(f"{reg.test_id}: direction must be 'greater' or 'less'")
    if reg.min_n <= 0:
        raise RegistrationError(f"{reg.test_id}: min_n must be positive, got {reg.min_n}")
    if not reg.target.strip():
        raise RegistrationError(f"{reg.test_id}: target must be non-empty")

    unknown = set(reg.control_arms) - MANDATORY_CONTROL_ARMS - OPTIONAL_CONTROL_ARMS
    if unknown:
        raise RegistrationError(f"{reg.test_id}: unknown control arms {sorted(unknown)}")

    if for_locking or reg.status is Status.LOCKED:
        missing = MANDATORY_CONTROL_ARMS - set(reg.control_arms)
        if missing:
            raise RegistrationError(
                f"{reg.test_id}: cannot lock without mandatory control arms {sorted(missing)}"
            )
        # A chart bank scored against itself is not scored against anything.
        if reg.feature_bank != "chartless" and not reg.baseline_model.strip():
            raise RegistrationError(
                f"{reg.test_id}: a chart bank must name its chartless baseline_model"
            )


def _parse_row(row: dict[str, str], line: int) -> Registration:
    try:
        arms = tuple(a for a in row["control_arms"].split(_ARM_SEPARATOR) if a.strip())
        return Registration(
            test_id=row["test_id"].strip(),
            feature_bank=row["feature_bank"].strip(),
            target=row["target"].strip(),
            statistic=row["statistic"].strip(),
            baseline_model=row["baseline_model"].strip(),
            control_arms=arms,
            min_n=int(row["min_n"]),
            tier_requirement=row["tier_requirement"].strip(),
            stage=row["stage"].strip(),
            direction=row["direction"].strip(),
            status=Status(row["status"].strip()),
            notes=row.get("notes", ""),
        )
    except (KeyError, ValueError) as exc:
        raise RegistrationError(f"line {line}: {exc}") from exc


def load_registry(path: str | Path) -> tuple[Registration, ...]:
    """Read and validate a registry CSV.

    Raises:
      RegistrationError: on a malformed row or a duplicate test_id.
      FileNotFoundError: if the registry is absent.
    """
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    regs = tuple(_parse_row(row, i + 2) for i, row in enumerate(rows))
    seen: set[str] = set()
    for reg in regs:
        if reg.test_id in seen:
            raise RegistrationError(f"duplicate test_id {reg.test_id!r}")
        seen.add(reg.test_id)
        validate(reg)
    return regs


def write_registry(path: str | Path, registrations: Iterable[Registration]) -> None:
    """Write a registry CSV with a stable column order and row order.

    Rows are sorted by ``test_id`` so the file's hash depends on content alone,
    not on the order rows happened to be appended.
    """
    ordered = sorted(registrations, key=lambda r: r.test_id)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for reg in ordered:
            writer.writerow(
                {
                    "test_id": reg.test_id,
                    "feature_bank": reg.feature_bank,
                    "target": reg.target,
                    "statistic": reg.statistic,
                    "baseline_model": reg.baseline_model,
                    "control_arms": _ARM_SEPARATOR.join(sorted(reg.control_arms)),
                    "min_n": reg.min_n,
                    "tier_requirement": reg.tier_requirement,
                    "stage": reg.stage,
                    "direction": reg.direction,
                    "status": reg.status.value,
                    "notes": reg.notes,
                }
            )


def scorable(
    registrations: Sequence[Registration],
    *,
    stage: str | None = None,
) -> tuple[Registration, ...]:
    """The subset that may legally be scored: locked rows only.

    This is the only sanctioned route from a registry to a scoring run. Filtering
    by ``status`` at the call site would make forgetting it possible.
    """
    if stage is not None and stage not in STAGES:
        raise RegistrationError(f"unknown stage {stage!r}")
    out = tuple(r for r in registrations if r.is_scorable and (stage is None or r.stage == stage))
    logger.info("scorable: %d of %d rows (stage=%s)", len(out), len(registrations), stage or "any")
    return out


def registry_fingerprint(path: str | Path) -> str:
    """SHA-256 of the registry file's bytes — what the ratchet stores."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lock(registrations: Sequence[Registration], test_id: str) -> tuple[Registration, ...]:
    """Return the registry with one row moved to ``locked``.

    Validates against the lock-time rules first, so an under-specified row cannot
    become evidence.

    Raises:
      RegistrationError: unknown test_id, already locked, or missing mandatory arms.
    """
    import dataclasses

    found = [r for r in registrations if r.test_id == test_id]
    if not found:
        raise RegistrationError(f"no such test_id {test_id!r}")
    target = found[0]
    if target.status is Status.LOCKED:
        raise RegistrationError(f"{test_id} is already locked")
    validate(target, for_locking=True)
    locked = dataclasses.replace(target, status=Status.LOCKED)
    return tuple(locked if r.test_id == test_id else r for r in registrations)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Validate or lock tournament pre-registrations.")
    parser.add_argument("--registry", required=True, help="path to the prereg CSV")
    parser.add_argument("--validate", action="store_true", help="validate every row and exit")
    parser.add_argument("--lock", metavar="TEST_ID", help="move one row to locked")
    parser.add_argument("--fingerprint", action="store_true", help="print the registry SHA-256")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    registrations = load_registry(args.registry)

    if args.lock:
        registrations = lock(registrations, args.lock)
        write_registry(args.registry, registrations)
        logger.info("locked %s", args.lock)

    if args.validate:
        logger.info("%d rows valid (%d locked)", len(registrations), len(scorable(registrations)))

    if args.fingerprint or args.lock:
        logger.info("registry sha256: %s", registry_fingerprint(args.registry))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
