"""The frozen holdout — 25% of persons, hash-committed, touched exactly once.

A holdout that can be looked at twice is not a holdout; it is a slow training
set. This module makes "touched exactly once" mechanical rather than
aspirational: :class:`HoldoutGuard` records every confirmatory read to a ledger
on disk and refuses a second read for the same test.

The split is **deterministic and person-level**, derived by hashing the person id
with a salt rather than by an RNG. Two consequences that both matter:

* Re-running never reshuffles, so the holdout cannot be quietly re-rolled until
  it gives a better answer.
* Assignment is a pure function of the id, so a person added to the corpus later
  lands on the same side they would have landed on originally — no leakage from
  corpus growth.

Person-level, not row-level: one person contributes many events, and splitting
by row would put the same chart on both sides.

Usage:
    from app.empirical.tournament.holdout import assign_holdout, write_manifest
    holdout = assign_holdout(person_ids, salt="empirical-v1")
    write_manifest("tools/empirical/holdout_manifest.json", person_ids, holdout, salt="empirical-v1")
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable, Sequence

logger = logging.getLogger(__name__)

__all__ = [
    "HOLDOUT_FRACTION",
    "HoldoutError",
    "HoldoutReuseError",
    "Manifest",
    "assign_holdout",
    "build_manifest",
    "write_manifest",
    "load_manifest",
    "HoldoutGuard",
    "check_person_leak",
]

#: Fraction of persons frozen out of all screening work.
HOLDOUT_FRACTION: Final[float] = 0.25

_HASH_SPACE: Final[int] = 2**32


class HoldoutError(RuntimeError):
    """The holdout contract was violated."""


class HoldoutReuseError(HoldoutError):
    """A test tried to read the holdout a second time."""


def _uniform(person_id: str, salt: str) -> float:
    """Map a person id to a stable uniform value in ``[0, 1)``.

    SHA-1 of ``salt|person_id``, truncated to 32 bits. Deterministic across
    processes, platforms, and Python versions — unlike ``hash()``, which is
    randomized per interpreter run and would silently reshuffle the split.
    """
    digest = hashlib.sha1(f"{salt}|{person_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / _HASH_SPACE


def assign_holdout(
    person_ids: Iterable[str],
    *,
    fraction: float = HOLDOUT_FRACTION,
    salt: str,
) -> frozenset[str]:
    """The frozen person ids.

    Args:
      person_ids: All persons in the corpus.
      fraction: Share to freeze.
      salt: Namespacing string; changing it re-rolls the entire split and must
        therefore be treated as a new pre-registration, not a tweak.

    Returns:
      The holdout person ids.
    """
    if not 0.0 < fraction < 1.0:
        raise ValueError(f"fraction must be in (0, 1), got {fraction}")
    if not salt:
        raise ValueError("salt must be non-empty — an unsalted split is not reproducible by intent")
    return frozenset(pid for pid in person_ids if _uniform(pid, salt) < fraction)


@dataclass(frozen=True, slots=True)
class Manifest:
    """A hash-committed record of one holdout split.

    Attributes:
      salt: The salt used.
      fraction: The requested fraction.
      n_total: Persons considered.
      n_holdout: Persons frozen.
      population_sha256: Hash of the sorted full population — detects a corpus
        that changed under a split that claims to describe it.
      holdout_sha256: Hash of the sorted holdout ids.
    """

    salt: str
    fraction: float
    n_total: int
    n_holdout: int
    population_sha256: str
    holdout_sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "salt": self.salt,
            "fraction": self.fraction,
            "n_total": self.n_total,
            "n_holdout": self.n_holdout,
            "population_sha256": self.population_sha256,
            "holdout_sha256": self.holdout_sha256,
        }


def _sha_of_ids(ids: Iterable[str]) -> str:
    joined = "\n".join(sorted(ids)).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()


def build_manifest(
    person_ids: Sequence[str],
    holdout: Iterable[str],
    *,
    salt: str,
    fraction: float = HOLDOUT_FRACTION,
) -> Manifest:
    """Summarize a split into a committable manifest."""
    holdout = frozenset(holdout)
    return Manifest(
        salt=salt,
        fraction=fraction,
        n_total=len(person_ids),
        n_holdout=len(holdout),
        population_sha256=_sha_of_ids(person_ids),
        holdout_sha256=_sha_of_ids(holdout),
    )


def write_manifest(
    path: str | Path,
    person_ids: Sequence[str],
    holdout: Iterable[str],
    *,
    salt: str,
    fraction: float = HOLDOUT_FRACTION,
) -> Manifest:
    """Write the manifest JSON and return it."""
    manifest = build_manifest(person_ids, holdout, salt=salt, fraction=fraction)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    logger.info("holdout manifest written: %d/%d frozen", manifest.n_holdout, manifest.n_total)
    return manifest


def load_manifest(path: str | Path) -> Manifest:
    """Read a manifest JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Manifest(
        salt=data["salt"],
        fraction=float(data["fraction"]),
        n_total=int(data["n_total"]),
        n_holdout=int(data["n_holdout"]),
        population_sha256=data["population_sha256"],
        holdout_sha256=data["holdout_sha256"],
    )


def check_person_leak(train_ids: Iterable[str], holdout_ids: Iterable[str]) -> None:
    """Raise if any person appears on both sides.

    The single most common way a survival/event corpus leaks: one person
    contributes many rows, and a row-level split scatters them across the
    boundary.
    """
    overlap = set(train_ids) & set(holdout_ids)
    if overlap:
        sample = sorted(overlap)[:5]
        raise HoldoutError(
            f"person leak: {len(overlap)} persons in both train and holdout (e.g. {sample})"
        )


class HoldoutGuard:
    """Enforces that each test reads the holdout at most once.

    The ledger lives on disk, so the guarantee survives process restarts — an
    in-memory flag would reset on every re-run, which is exactly when the
    temptation to peek again arrives.

    Usage:
        guard = HoldoutGuard("data/empirical/holdout_ledger.json")
        guard.claim("T001")     # first confirmatory read: allowed
        guard.claim("T001")     # raises HoldoutReuseError
    """

    def __init__(self, ledger_path: str | Path) -> None:
        self.ledger_path = Path(ledger_path)

    def _read(self) -> dict[str, str]:
        if not self.ledger_path.is_file():
            return {}
        return json.loads(self.ledger_path.read_text(encoding="utf-8"))

    def claimed(self) -> frozenset[str]:
        """Test ids that have already consumed their single read."""
        return frozenset(self._read())

    def claim(self, test_id: str, *, manifest_sha: str = "") -> None:
        """Record a confirmatory read.

        Raises:
          HoldoutReuseError: this test already read the holdout.
        """
        ledger = self._read()
        if test_id in ledger:
            raise HoldoutReuseError(
                f"{test_id} already read the holdout (recorded under manifest "
                f"{ledger[test_id] or 'unknown'}). The holdout is touched exactly once; "
                "a second read requires a new pre-registration and a new split."
            )
        ledger[test_id] = manifest_sha
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(
            json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        logger.info("holdout claimed by %s", test_id)
