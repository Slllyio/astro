"""The mandatory control arms.

Every locked registration declares these, and every scored test must produce an
outcome for each. They exist because each one corresponds to a specific way this
corpus has already fooled a previous round:

* **Sham target** — Round 11's ``personal`` RR looked like p=7.4e-9 and died at
  z=0.55 once permutation was run at K=100. A sham that does not read ~0.500 means
  the pipeline itself carries signal, and no real result from it is interpretable.
* **Chartless baseline** — lat/lon/date alone scores AUC 0.744 on marriage. A chart
  model reporting 0.78 has not beaten anything until it is scored as +0.036 over
  its own chartless twin.
* **Era stratification** — the one surviving positive from Round 11 (+0.043 AUC on
  Wikidata marriage) still has era-specific documentation bias as a live
  alternative, because slow planets proxy birth decade almost perfectly.
* **Person-leak preflight** — one person contributes many events; a row-level
  split scatters the same chart across the boundary.

Usage:
    from app.empirical.tournament.controls import sham_labels, check_sham_null
    y_sham = sham_labels(y, seed=17)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Iterable, Sequence

import numpy as np

logger = logging.getLogger(__name__)

__all__ = [
    "ArmOutcome",
    "SHAM_TOLERANCE",
    "SHAM_Z",
    "sham_labels",
    "era_strata",
    "null_auc_se",
    "sham_tolerance_for",
    "check_sham_null",
    "check_min_n",
    "check_tier",
    "check_era_coverage",
]

#: Fallback tolerance when the sample size is unknown. Prefer
#: :func:`sham_tolerance_for`, which derives the tolerance from the actual test
#: set — a fixed absolute band is either too tight on small samples (flagging
#: ordinary sampling noise as a broken pipeline) or too loose on large ones
#: (letting real leakage through).
SHAM_TOLERANCE: Final[float] = 0.03

#: How many null standard errors from 0.500 still counts as null.
SHAM_Z: Final[float] = 3.0

_TIER_ORDER: Final[dict[str, frozenset[str]]] = {
    "A": frozenset({"A"}),
    "AB": frozenset({"A", "B"}),
    "ABS": frozenset({"A", "B", "S"}),
}


@dataclass(frozen=True, slots=True)
class ArmOutcome:
    """The result of one control arm.

    Attributes:
      name: Arm name, matching the registration's ``control_arms``.
      passed: Whether the arm cleared.
      value: The measured quantity, where the arm has one.
      detail: Human-readable explanation, always populated on failure.
    """

    name: str
    passed: bool
    value: float | None
    detail: str


def sham_labels(y: Sequence[int] | np.ndarray, *, seed: int) -> np.ndarray:
    """A permuted copy of the target — same base rate, no relationship to features.

    Permuting the label (rather than generating fresh random labels) preserves
    the class balance exactly, so a sham AUC that departs from 0.500 cannot be
    blamed on a different prevalence.
    """
    rng = np.random.default_rng(seed)
    arr = np.asarray(y)
    return rng.permutation(arr)


def era_strata(birth_years: Sequence[int] | np.ndarray, *, width: int = 10) -> np.ndarray:
    """Birth-decade (or ``width``-year) strata labels.

    Returns the lower edge of each person's era bin, so 1947 with width 10 gives
    1940. Stratifying on this is what separates "the chart predicts" from "the
    chart encodes when you were born, and when you were born predicts".
    """
    if width <= 0:
        raise ValueError(f"width must be positive, got {width}")
    years = np.asarray(birth_years, dtype=int)
    return (years // width) * width


def null_auc_se(n_positive: int, n_negative: int) -> float:
    """Standard error of an AUC under the null, for one permutation.

    ``sqrt((n1 + n2 + 1) / (12 * n1 * n2))`` — the Hanley-McNeil null variance.
    On a 375-row test set with balanced classes this is ~0.030, which is why a
    fixed 0.03 band would flag roughly half of all healthy pipelines.
    """
    if n_positive <= 0 or n_negative <= 0:
        return float("inf")
    return float(
        np.sqrt((n_positive + n_negative + 1) / (12.0 * n_positive * n_negative))
    )


def sham_tolerance_for(
    n_positive: int,
    n_negative: int,
    *,
    n_permutations: int = 1,
    z: float = SHAM_Z,
) -> float:
    """The band around 0.500 that a mean sham statistic may occupy.

    Averaging over ``n_permutations`` shrinks the standard error by
    ``sqrt(n_permutations)``, so more permutations buy a tighter — and therefore
    more sensitive — gate rather than a looser one.
    """
    if n_permutations < 1:
        raise ValueError(f"n_permutations must be >= 1, got {n_permutations}")
    return z * null_auc_se(n_positive, n_negative) / np.sqrt(n_permutations)


def check_sham_null(sham_statistic: float, *, tolerance: float = SHAM_TOLERANCE) -> ArmOutcome:
    """The anti-peeking gate: the sham must read ~0.500.

    This is evaluated *before* the real result is read. A failure means the
    pipeline is broken, and the real number from that pipeline carries no
    information about the world regardless of how good it looks.
    """
    deviation = abs(sham_statistic - 0.5)
    passed = deviation <= tolerance
    detail = (
        f"sham={sham_statistic:.4f}, |Δ from 0.500|={deviation:.4f} <= {tolerance}"
        if passed
        else (
            f"SHAM NOT NULL: {sham_statistic:.4f} is {deviation:.4f} from 0.500 "
            f"(tolerance {tolerance}). The pipeline carries signal on a permuted "
            "target; the real result is uninterpretable."
        )
    )
    return ArmOutcome("sham_target", passed, float(sham_statistic), detail)


def check_min_n(n: int, min_n: int) -> ArmOutcome:
    """Registered minimum sample size, checked before anything is read."""
    passed = n >= min_n
    return ArmOutcome(
        "min_n",
        passed,
        float(n),
        f"n={n} >= registered min_n={min_n}" if passed else f"n={n} below registered min_n={min_n}",
    )


def check_tier(tiers: Iterable[str], requirement: str) -> ArmOutcome:
    """Every admitted person must meet the registered birth-time quality floor."""
    if requirement not in _TIER_ORDER:
        raise ValueError(f"unknown tier requirement {requirement!r}")
    allowed = _TIER_ORDER[requirement]
    observed = set(tiers)
    bad = observed - allowed
    passed = not bad
    return ArmOutcome(
        "tier_requirement",
        passed,
        None,
        f"all persons within tier {requirement}"
        if passed
        else f"tiers {sorted(bad)} present but requirement is {requirement} ({sorted(allowed)})",
    )


def check_era_coverage(
    strata: Sequence[int] | np.ndarray,
    *,
    min_per_stratum: int = 30,
) -> ArmOutcome:
    """Stratified analysis needs enough persons per era to be meaningful.

    A stratum of three people contributes noise with a confident-looking point
    estimate — the small-sample positive bias that made Round 11's within-lord
    RR=1.58 look like signal when the shuffled null sat at exactly the same value.
    """
    values, counts = np.unique(np.asarray(strata), return_counts=True)
    thin = [int(v) for v, c in zip(values, counts) if c < min_per_stratum]
    passed = not thin
    return ArmOutcome(
        "era_stratification",
        passed,
        float(len(values)),
        f"{len(values)} strata, all >= {min_per_stratum}"
        if passed
        else f"strata below {min_per_stratum}: {thin} — pool or drop before scoring",
    )
