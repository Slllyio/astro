"""The shipped claim set — and the machinery that keeps it honest.

A claim reaches this module only by surviving the full protocol: locked
pre-registration, sham gate cleared, positive delta over its own chartless twin,
FDR-corrected, confirmed on the frozen holdout. Nothing else may be served.

**The empty set is a valid, expected, first-class state.** On the corpus acquired
so far it is the actual state: the Gauquelin screening returned no survivor on
any of eighteen tests. An engine with no claims is a measurement, not a
malfunction, and :func:`from_screening_report` builds that empty set with the
full record of what was tested attached — so the null can be *read*, not merely
reported as a blank.

Every claim carries an isotonic calibration table fitted on training data and
evaluated on the holdout, so a served probability means what it says rather than
being a model score with a percent sign on it.

Usage:
    from app.empirical.engine.survivors import load_survivors, from_screening_report
    survivor_set = load_survivors("data/empirical/survivors.json")
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

logger = logging.getLogger(__name__)

__all__ = [
    "Claim",
    "SurvivorSet",
    "CalibrationBin",
    "load_survivors",
    "write_survivors",
    "from_screening_report",
]

#: Stage a claim must have reached. Screening survivors are candidates, never
#: claims — promoting one without a confirmatory run is the whole failure mode
#: the holdout exists to prevent.
_REQUIRED_STAGE: Final[str] = "confirmatory"


@dataclass(frozen=True, slots=True)
class CalibrationBin:
    """One row of an isotonic calibration table.

    Attributes:
      score_low, score_high: The model-score interval this bin covers.
      observed_rate: The outcome rate actually observed in this bin on the
        holdout — not the model's predicted rate.
      n: How many holdout rows landed here. A bin of four people is not a
        calibrated probability and must be shown with its n.
    """

    score_low: float
    score_high: float
    observed_rate: float
    n: int


@dataclass(frozen=True, slots=True)
class Claim:
    """One validated association, with everything needed to read it honestly.

    Attributes:
      test_id: The locked pre-registration row this came from.
      feature_bank, target: What predicted what.
      delta: Advantage over the chartless twin. The claim IS the delta; the raw
        statistic alone would overstate it.
      ci_low, ci_high: Confidence interval on the delta.
      p_value: Under the registered direction, after FDR.
      n: Holdout rows the confirmatory statistic was computed on.
      base_rate: Outcome rate in the holdout, so a reader can see what "raised
        the rate" is measured against.
      calibration: Isotonic table, fitted on train, evaluated on holdout.
      coverage: Share of the population this claim can be evaluated for — a
        claim needing a tier-A birth time does not apply to most people.
      corpus_hash, prereg_sha256, holdout_sha256: Provenance.
    """

    test_id: str
    feature_bank: str
    target: str
    delta: float
    ci_low: float
    ci_high: float
    p_value: float
    n: int
    base_rate: float
    coverage: float
    calibration: tuple[CalibrationBin, ...] = ()
    corpus_hash: str = ""
    prereg_sha256: str = ""
    holdout_sha256: str = ""

    def __post_init__(self) -> None:
        if self.delta <= 0.0:
            raise ValueError(
                f"{self.test_id}: a claim must beat its chartless twin; delta={self.delta}"
            )
        if not 0.0 <= self.base_rate <= 1.0:
            raise ValueError(f"{self.test_id}: base_rate out of range: {self.base_rate}")


@dataclass(frozen=True, slots=True)
class SurvivorSet:
    """Everything the engine may serve, plus the record of what it rejected.

    Attributes:
      claims: The survivors. Often — and currently — empty.
      tested: Every test that was run, whether or not it survived. This is what
        makes an empty set legible instead of blank.
      controls: The control arms every test faced.
      corpus: Human name of the corpus.
      corpus_hash: Content hash, so a claim cannot outlive its data.
      generated_from: Which report produced this set.
      stage: ``confirmatory`` for shippable claims; anything else means the set
        is exploratory and :meth:`is_shippable` is False.
      notes: Free text carried to the surface.
    """

    claims: tuple[Claim, ...] = ()
    tested: tuple[Mapping[str, Any], ...] = ()
    controls: tuple[str, ...] = ()
    corpus: str = ""
    corpus_hash: str = ""
    generated_from: str = ""
    stage: str = "screening"
    notes: str = ""

    @property
    def is_empty(self) -> bool:
        """True when nothing survived. Expected, not exceptional."""
        return not self.claims

    @property
    def is_shippable(self) -> bool:
        """Only a confirmatory set may be served as claims.

        A screening set can still be *displayed* — as an honest null with its
        working shown — but its contents are candidates, not findings.
        """
        return self.stage == _REQUIRED_STAGE

    def to_dict(self) -> dict[str, Any]:
        return {
            "claims": [asdict(c) for c in self.claims],
            "tested": [dict(t) for t in self.tested],
            "controls": list(self.controls),
            "corpus": self.corpus,
            "corpus_hash": self.corpus_hash,
            "generated_from": self.generated_from,
            "stage": self.stage,
            "notes": self.notes,
        }


def corpus_hash(path: str | Path) -> str:
    """SHA-256 of a corpus file — a claim is pinned to the data that made it."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def write_survivors(path: str | Path, survivor_set: SurvivorSet) -> None:
    """Write the survivor set as JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(survivor_set.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def load_survivors(path: str | Path) -> SurvivorSet:
    """Read a survivor set, rejecting any claim that did not earn its place.

    Raises:
      ValueError: a claim has a non-positive delta or an out-of-range base rate.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    claims = tuple(
        Claim(
            **{
                **{k: v for k, v in c.items() if k != "calibration"},
                "calibration": tuple(CalibrationBin(**b) for b in c.get("calibration", ())),
            }
        )
        for c in data.get("claims", ())
    )
    return SurvivorSet(
        claims=claims,
        tested=tuple(data.get("tested", ())),
        controls=tuple(data.get("controls", ())),
        corpus=data.get("corpus", ""),
        corpus_hash=data.get("corpus_hash", ""),
        generated_from=data.get("generated_from", ""),
        stage=data.get("stage", "screening"),
        notes=data.get("notes", ""),
    )


def from_screening_report(
    report: Mapping[str, Any],
    *,
    corpus: str,
    corpus_hash_value: str = "",
    generated_from: str = "",
) -> SurvivorSet:
    """Build a survivor set from a screening report.

    Screening survivors are deliberately NOT promoted to claims: the resulting
    set carries ``stage="screening"``, which makes :meth:`is_shippable` False.
    What it does carry in full is ``tested`` — every test, its delta, and which
    control arms it faced — because that is what turns "no results" into a
    readable measurement.
    """
    tested: list[dict[str, Any]] = []
    survivor_ids = {e.get("test_id") for e in report.get("survivors", ())}
    unmet = {e.get("test_id"): e.get("failed_arms", []) for e in report.get("not_admitted", ())}

    # Prefer the full per-test record when the report carries it. Falling back to
    # survivors-only would make a null look like an empty search.
    for entry in report.get("all_outcomes", ()):
        test_id = entry.get("test_id")
        if test_id in survivor_ids:
            outcome = "survived_screening"
        elif test_id in unmet:
            outcome = "not_admitted"
        else:
            outcome = "tested_no_effect"
        tested.append({**entry, "outcome": outcome})

    if not tested:
        for entry in report.get("survivors", ()):
            tested.append({**entry, "outcome": "survived_screening"})
        for entry in report.get("not_admitted", ()):
            tested.append({**entry, "outcome": "not_admitted"})

    n_registered = int(report.get("n_registered", 0))
    n_survivors = int(report.get("n_survivors", 0))
    if n_registered and not tested:
        tested.append(
            {
                "note": f"{n_registered} tests run, {n_survivors} survived",
                "outcome": "summary_only",
            }
        )

    return SurvivorSet(
        claims=(),  # screening never produces claims
        tested=tuple(tested),
        controls=(
            "sham_target",
            "chartless_baseline",
            "era_stratification",
            "person_leak_preflight",
        ),
        corpus=corpus,
        corpus_hash=corpus_hash_value,
        generated_from=generated_from,
        stage="screening",
        notes=str(report.get("verdict", "")),
    )
