"""Fidelity metrics for the Raman Doctrine Compendium.

"Truest to Raman" is measured, not asserted. Two complementary checks:

* **Mechanism fidelity** (precision/recall): for a golden chart built to
  satisfy a rule's PROSE definition, does the ENCODED antecedent fire? And
  on a control chart that violates the prose, does it correctly stay quiet?
  A divergence means the DSL encoding drifted from Raman's stated mechanism
  — this catches encoding bugs non-circularly, because the chart is built
  from the prose, never from the antecedent.

* **Polarity agreement**: when a rule fires on a golden chart, does its
  consequent polarity match the verdict Raman states for that chart?

The mechanism-overlap Jaccard (fired rule ids vs. the mechanisms Raman
names for a printed chart) is computed by ``mechanism_jaccard`` for the
printed-chart cases.
"""
from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class PRResult:
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 1.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 1.0

    @property
    def accuracy(self) -> float:
        d = self.tp + self.fp + self.fn + self.tn
        return (self.tp + self.tn) / d if d else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def score_mechanism(outcomes: list[tuple[bool, bool]]) -> PRResult:
    """``outcomes`` = list of (expected_fire, actual_fire). Positive class is
    "the rule should fire", so a missed positive is a recall failure and a
    spurious fire on a control is a precision failure."""
    tp = fp = fn = tn = 0
    for expected, actual in outcomes:
        if expected and actual:
            tp += 1
        elif expected and not actual:
            fn += 1
        elif not expected and actual:
            fp += 1
        else:
            tn += 1
    return PRResult(tp=tp, fp=fp, fn=fn, tn=tn)


def polarity_agreement(pairs: list[tuple[str, str]]) -> float:
    """Fraction of (rule_polarity, chart_verdict_polarity) pairs that agree.
    'mixed'/'neutral' rule polarity is treated as compatible with anything."""
    if not pairs:
        return 1.0
    ok = 0
    for rule_pol, chart_pol in pairs:
        if rule_pol in ("mixed", "neutral") or rule_pol == chart_pol:
            ok += 1
    return ok / len(pairs)


def mechanism_jaccard(fired: set[str], named: set[str]) -> float:
    """Jaccard overlap between the mechanisms that fired and those Raman
    names for a chart. 1.0 when both empty (nothing to explain, nothing
    fired)."""
    if not fired and not named:
        return 1.0
    union = fired | named
    return len(fired & named) / len(union) if union else 1.0
