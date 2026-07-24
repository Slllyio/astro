"""Rule-liveness ratchet — how much of the doctrine surface the goldens exercise.

The golden ratchet guards the engine's VERDICTS; this guards its rule COVERAGE. It measures how
many of the 716 evaluable rules (and 72 yogas) fire on >=1 golden chart, and ratchets the
never-fire count so it can only shrink: adding a rule no golden exercises, or breaking a rule so
it stops firing, raises the count and fails here. See tools/raman_saab/rule_liveness.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.raman_saab import rule_liveness as rl

_BASELINE = json.loads(
    Path("tests/fixtures/rule_liveness_baseline.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def summary() -> rl.LivenessSummary:
    """Cast every golden once and tally rule/yoga fires (module-scoped — the cast is the cost)."""
    return rl.liveness_summary()


def test_rule_liveness_does_not_regress(summary: rl.LivenessSummary) -> None:
    """The count of evaluable rules that never fire on any golden must not increase."""
    never = len(summary.never_fired)
    assert never <= _BASELINE["never_fired"], (
        f"{never} evaluable rules never fire on any golden (baseline {_BASELINE['never_fired']}). "
        f"A rule stopped firing or an unexercised rule was added. Never-firing ids:\n  "
        + "\n  ".join(summary.never_fired))


def test_yoga_liveness_does_not_regress(summary: rl.LivenessSummary) -> None:
    """The count of yogas that never fire on any golden must not increase."""
    never = len(summary.yogas_never)
    assert never <= _BASELINE["yogas_never"], (
        f"{never} yogas never fire on any golden (baseline {_BASELINE['yogas_never']}). "
        f"Never-firing yoga ids: {', '.join(summary.yogas_never)}")


def test_evaluable_rule_surface_is_not_silently_shrinking(summary: rl.LivenessSummary) -> None:
    """The evaluable-rule count should not drop below the baseline without re-baselining — a
    guard against a rule set silently disappearing from ALL_RULES (a broken import/aggregation)."""
    assert summary.evaluable_total >= _BASELINE["evaluable_total"], (
        f"evaluable rule count {summary.evaluable_total} < baseline "
        f"{_BASELINE['evaluable_total']} — did a rule-set module drop out of ALL_RULES?")


def test_majority_of_the_rule_surface_is_actually_exercised(summary: rl.LivenessSummary) -> None:
    """A sanity floor: most evaluable rules fire on the corpus (guards a catastrophic wiring
    break that silences the whole surface). Not a tight bound — just a smoke floor."""
    assert summary.evaluable_fired >= summary.evaluable_total * 0.75
