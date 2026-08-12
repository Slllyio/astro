"""Scoring, in the one order that keeps a result honest.

The rule this module makes mechanical: **the sham is read first.** A test's real
number cannot be obtained until its sham has been recorded and has come back
null. Attempting it raises :class:`PeekError`.

That ordering is not bureaucratic. Round 11's ``personal`` result was read first
and controlled afterwards, and the controls then had to argue a headline
p=7.4e-9 down to a null — five separate analyses, one of which (K=20 permutation,
z=1.07) briefly looked like a rescue before K=100 settled it at z=0.55. Reading
the sham first would have closed it in one step.

The second rule: **a chart model's score is its delta over its own chartless
twin**, never its raw statistic. Birth latitude, longitude and date alone reach
AUC 0.744 on marriage. :class:`TestOutcome` therefore has no field for a bare
chart statistic that isn't paired with the baseline it must beat.

Benjamini-Hochberg at q=0.10 comes from ``tools/raman_saab/astrobank/_stats.py``
— imported, not re-implemented, so the tournament and the astrobank program
correct multiplicity identically.

Usage:
    scorer = GatedScorer(registration)
    scorer.record_controls([...])
    scorer.record_sham(sham_auc)          # must be ~0.500
    scorer.record_real(chart_auc, chartless_auc, p_value=..., n=...)
    outcome = scorer.outcome()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import ClassVar, Final, Iterable, Sequence

from app.empirical.tournament.controls import ArmOutcome, check_sham_null
from app.empirical.tournament.prereg import Registration
from tools.raman_saab.astrobank._stats import bh_fdr

logger = logging.getLogger(__name__)

__all__ = [
    "FDR_Q",
    "PeekError",
    "TestOutcome",
    "GatedScorer",
    "apply_fdr",
    "survivors",
    "summarize",
]

#: Family-wise false-discovery rate for the tournament family.
FDR_Q: Final[float] = 0.10


class PeekError(RuntimeError):
    """A real result was requested before its sham gate had cleared."""


@dataclass(frozen=True, slots=True)
class TestOutcome:
    """One test's complete, gate-cleared result.

    There is deliberately no "raw score" field standing alone: ``delta`` is the
    quantity that means anything, and it is always chart minus chartless.

    Attributes:
      test_id, feature_bank, target, stage: Copied from the registration.
      n: Qualifying rows scored.
      chart_statistic: The chart model's statistic.
      chartless_statistic: Its chartless twin's statistic on the same split.
      delta: ``chart_statistic - chartless_statistic``. The result.
      p_value: For the delta, under the registered direction.
      sham_statistic: What the permuted target read.
      arms: Every control arm's outcome.
      missing_arms: Arms the registration declared that produced no outcome at
        all. Non-empty means the harness did not run a control it promised to,
        which blocks admission regardless of how the other arms read.
      admitted: Every declared arm produced a passing outcome and n met the
        registered floor.
    """

    #: Tells pytest this is a domain class, not a test class, despite the name.
    __test__: ClassVar[bool] = False

    test_id: str
    feature_bank: str
    target: str
    stage: str
    n: int
    chart_statistic: float
    chartless_statistic: float
    delta: float
    p_value: float
    sham_statistic: float
    arms: tuple[ArmOutcome, ...]
    missing_arms: tuple[str, ...]
    admitted: bool

    @property
    def failed_arms(self) -> tuple[str, ...]:
        """Names of arms that ran and did not clear."""
        return tuple(a.name for a in self.arms if not a.passed)

    @property
    def unmet_arms(self) -> tuple[str, ...]:
        """Every arm that failed or never ran — the full admission blockers."""
        return tuple(sorted(set(self.failed_arms) | set(self.missing_arms)))


@dataclass
class GatedScorer:
    """Enforces sham-before-real for a single registered test.

    The scorer is stateful on purpose: the order in which its methods are called
    *is* the protocol, and calling them out of order is an error rather than a
    style issue.
    """

    registration: Registration
    sham_tolerance: float | None = None
    _arms: list[ArmOutcome] = field(default_factory=list, init=False, repr=False)
    _sham: ArmOutcome | None = field(default=None, init=False, repr=False)
    _real: tuple[float, float, float, int] | None = field(default=None, init=False, repr=False)

    def record_controls(self, outcomes: Iterable[ArmOutcome]) -> None:
        """Record non-sham control arms. May be called more than once."""
        self._arms.extend(outcomes)

    def record_sham(self, sham_statistic: float) -> ArmOutcome:
        """Read the sham. Must happen before :meth:`record_real`.

        Returns:
          The sham arm's outcome, so the caller can stop early on failure.
        """
        if self._sham is not None:
            raise PeekError(f"{self.registration.test_id}: sham already recorded")
        tol = self.sham_tolerance
        outcome = check_sham_null(sham_statistic) if tol is None else check_sham_null(
            sham_statistic, tolerance=tol
        )
        self._sham = outcome
        self._arms.append(outcome)
        if not outcome.passed:
            logger.warning("%s: %s", self.registration.test_id, outcome.detail)
        return outcome

    def record_real(
        self,
        chart_statistic: float,
        chartless_statistic: float,
        *,
        p_value: float,
        n: int,
    ) -> None:
        """Record the real result. Refused until the sham has cleared.

        Raises:
          PeekError: the sham was never read, or read and failed.
        """
        if self._sham is None:
            raise PeekError(
                f"{self.registration.test_id}: refusing to accept a real result before the sham "
                "has been read. Call record_sham() first — that ordering is the anti-peeking gate."
            )
        if not self._sham.passed:
            raise PeekError(
                f"{self.registration.test_id}: sham did not read null ({self._sham.detail}). "
                "The real result from this pipeline is uninterpretable and will not be recorded."
            )
        if self._real is not None:
            raise PeekError(f"{self.registration.test_id}: real result already recorded")
        self._real = (float(chart_statistic), float(chartless_statistic), float(p_value), int(n))

    def outcome(self) -> TestOutcome:
        """Assemble the final outcome.

        Raises:
          PeekError: called before both the sham and the real result are in.
        """
        if self._sham is None or self._real is None:
            raise PeekError(
                f"{self.registration.test_id}: outcome() needs both a sham and a real result"
            )
        chart, chartless, p_value, n = self._real
        arms = tuple(self._arms)
        # A declared arm that never produced an outcome has not been run, and
        # `all(...)` over a short list is vacuously true — so coverage must be
        # checked explicitly. Without this, a harness that quietly stopped
        # emitting an arm would keep admitting results as though it still ran it.
        missing = tuple(sorted(set(self.registration.control_arms) - {a.name for a in arms}))
        if missing:
            logger.warning(
                "%s: declared control arms produced no outcome: %s — not admitted",
                self.registration.test_id,
                list(missing),
            )
        admitted = (
            not missing
            and all(a.passed for a in arms)
            and n >= self.registration.min_n
        )
        return TestOutcome(
            test_id=self.registration.test_id,
            feature_bank=self.registration.feature_bank,
            target=self.registration.target,
            stage=self.registration.stage,
            n=n,
            chart_statistic=chart,
            chartless_statistic=chartless,
            delta=chart - chartless,
            p_value=p_value,
            sham_statistic=self._sham.value if self._sham.value is not None else float("nan"),
            arms=arms,
            missing_arms=missing,
            admitted=admitted,
        )


def apply_fdr(
    outcomes: Sequence[TestOutcome],
    *,
    q: float = FDR_Q,
) -> dict[str, bool]:
    """Benjamini-Hochberg across the family of admitted tests.

    Only admitted outcomes enter the family: a test that failed its controls is
    not a test that happened to come out negative, and including it would inflate
    *m* and make the surviving tests easier to pass.
    """
    pvals = {o.test_id: o.p_value for o in outcomes if o.admitted}
    flags = bh_fdr(pvals, q=q) if pvals else {}
    return {o.test_id: flags.get(o.test_id, False) for o in outcomes}


def survivors(
    outcomes: Sequence[TestOutcome],
    *,
    q: float = FDR_Q,
) -> tuple[TestOutcome, ...]:
    """Tests that cleared every gate: admitted, FDR-significant, and positive delta.

    A negative delta that is FDR-significant means the chart bank did *worse*
    than its chartless twin; it is a finding, but it is not a survivor.
    """
    flags = apply_fdr(outcomes, q=q)
    return tuple(o for o in outcomes if o.admitted and flags[o.test_id] and o.delta > 0.0)


def summarize(outcomes: Sequence[TestOutcome], *, q: float = FDR_Q) -> dict[str, object]:
    """A reportable summary, including the honest-null case.

    The empty-survivor result is a first-class outcome, not an error state: it
    reports what was tested and which controls each test faced, so a null is
    legible rather than merely disappointing.
    """
    kept = survivors(outcomes, q=q)
    return {
        "n_registered": len(outcomes),
        "n_admitted": sum(1 for o in outcomes if o.admitted),
        "n_survivors": len(kept),
        "fdr_q": q,
        "survivors": [
            {
                "test_id": o.test_id,
                "feature_bank": o.feature_bank,
                "target": o.target,
                "delta": o.delta,
                "chart_statistic": o.chart_statistic,
                "chartless_statistic": o.chartless_statistic,
                "p_value": o.p_value,
                "n": o.n,
            }
            for o in kept
        ],
        "not_admitted": [
            {
                "test_id": o.test_id,
                "failed_arms": list(o.failed_arms),
                "missing_arms": list(o.missing_arms),
                "n": o.n,
            }
            for o in outcomes
            if not o.admitted
        ],
        "verdict": (
            "NULL — no registered test beat its chartless baseline after control and "
            "multiplicity correction."
            if not kept
            else f"{len(kept)} of {len(outcomes)} registered tests survived."
        ),
    }
