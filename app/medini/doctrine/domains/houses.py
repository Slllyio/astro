"""Domain engines — aggregate compendium rules per house/domain on a chart.

P7: the compendium (data) meets the chart (the engine). For each of the 12
houses this composes two independent readings:

  * the **three-pillar bhava verdict** from ``app/core/bhava_judge.py``
    (bhava / lord / karaka, the framework's classical scorer), and
  * the **compendium reading**: every executable rule whose provenance
    targets that house/domain is evaluated on the chart; the ones that fire
    are aggregated by consequent polarity into a doctrine score in [-1, +1].

The two are reported side by side (never silently merged) so a consumer can
see where Raman's book-level doctrine and the framework scorer agree or
diverge — the same "activation, not mutation" spirit as the conflict engine.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping

from app.core.bhava_judge import BhavaVerdict, judge_bhava
from app.medini.doctrine.compendium import load_compendium
from app.medini.doctrine.engine.evaluate import evaluate_rule
from app.medini.doctrine.engine.predicates import EvalContext
from app.medini.doctrine.raman_chart import RamanChart

# House -> the compendium domain that reads it (aligned to the 18-value
# taxonomy). Used to pull the relevant rules for each bhava.
HOUSE_DOMAIN: dict[int, str] = {
    1: "health_body", 2: "wealth", 3: "siblings", 4: "property",
    5: "children", 6: "enemies_obstacles", 7: "marriage", 8: "longevity",
    9: "fortune_father", 10: "career", 11: "gains", 12: "losses_moksha",
}

_POLARITY_SIGN = {"favorable": 1.0, "unfavorable": -1.0, "mixed": 0.0,
                  "neutral": 0.0}


@dataclasses.dataclass(frozen=True)
class FiredRule:
    rule_id: str
    polarity: str
    text: str
    book: str


@dataclasses.dataclass(frozen=True)
class DomainReading:
    house: int
    domain: str
    doctrine_score: float           # [-1, +1] from fired rules' polarities
    n_fired: int
    n_evaluable: int
    fired: tuple[FiredRule, ...]
    bhava_verdict: BhavaVerdict     # the three-pillar framework verdict

    @property
    def doctrine_label(self) -> str:
        s = self.doctrine_score
        if s >= 0.34:
            return "favourable"
        if s <= -0.34:
            return "afflicted"
        return "mixed"

    @property
    def agrees_with_framework(self) -> bool:
        """True when the compendium and the three-pillar verdict point the
        same way (both positive, both negative, or either neutral)."""
        fw = self.bhava_verdict.composite_score
        return (self.doctrine_score == 0.0 or fw == 0.0
                or (self.doctrine_score > 0) == (fw > 0))


def _rules_for_house(rules_by_domain: Mapping[str, list[dict]], house: int) -> list[dict]:
    """Executable rules that target this house: those whose provenance chapter
    is a house lord placement for it, plus rules tagged with its domain."""
    domain = HOUSE_DOMAIN[house]
    out: list[dict] = []
    seen: set[str] = set()
    for rule in rules_by_domain.get(domain, ()):  # domain-tagged
        if rule["antecedent"] is not None and rule["id"] not in seen:
            out.append(rule)
            seen.add(rule["id"])
    return out


def read_domain(chart: RamanChart, house: int, *,
                books: Mapping[str, list[dict]] | None = None,
                dasha: Mapping[str, str] | None = None) -> DomainReading:
    """Compose the compendium reading and the three-pillar verdict for one house."""
    if not 1 <= house <= 12:
        raise ValueError(f"house must be 1..12, got {house}")
    books = books or load_compendium()
    by_domain: dict[str, list[dict]] = {}
    for rules in books.values():
        for r in rules:
            by_domain.setdefault(r["domain"], []).append(r)

    ctx = EvalContext(chart=chart, dasha=dasha)
    fired: list[FiredRule] = []
    evaluable = 0
    score_sum = 0.0
    score_n = 0
    for rule in _rules_for_house(by_domain, house):
        outcome = evaluate_rule(rule, ctx)
        if not outcome.evaluable:
            continue
        evaluable += 1
        if outcome.fired:
            pol = rule["consequent"]["polarity"]
            fired.append(FiredRule(rule["id"], pol,
                                   rule["consequent"]["text"], rule["book"]))
            if pol in ("favorable", "unfavorable"):
                score_sum += _POLARITY_SIGN[pol]
                score_n += 1
    doctrine_score = round(score_sum / score_n, 4) if score_n else 0.0

    return DomainReading(
        house=house, domain=HOUSE_DOMAIN[house],
        doctrine_score=doctrine_score, n_fired=len(fired), n_evaluable=evaluable,
        fired=tuple(fired), bhava_verdict=judge_bhava(chart.bundle.chart, house),
    )


def read_all_domains(chart: RamanChart, *, dasha: Mapping[str, str] | None = None
                     ) -> dict[int, DomainReading]:
    """The full-chart doctrine reading: all 12 houses."""
    books = load_compendium()
    return {h: read_domain(chart, h, books=books, dasha=dasha) for h in range(1, 13)}
